from dataclasses import replace
from decimal import Decimal as D

import pytest

from app.engine.calculate import calculate
from app.engine.forecast import build_nodes
from app.engine.graph import downstream
from app.engine.types import FlagCode, InvalidInputError
from tests.fixtures.company import (
    LAST_HISTORICAL_YEAR,
    historical_2024,
    model_with,
    sample_model,
    year_assumptions,
)


def codes(result_flags: tuple) -> set[FlagCode]:  # type: ignore[type-arg]
    return {f.code for f in result_flags}


def test_first_forecast_year_matches_hand_calculation() -> None:
    year = calculate(sample_model(years=1)).years[0]
    income, bs, cf = year.income_statement, year.balance_sheet, year.cash_flow

    assert year.year == 2025
    assert income.revenue == D(1100)
    assert income.cogs == D(660)
    assert income.sga == D(220)
    assert income.depreciation == D(50)
    assert income.interest_expense == D(3)  # 100 x 5% - 100 cash x 2%
    assert income.pre_tax_income == D(167)
    assert income.tax_expense == D("33.4")
    assert income.net_income == D("133.6")

    assert bs.accounts_receivable == D(110)
    assert bs.inventory == D(99)
    assert bs.accounts_payable == D(66)
    assert bs.ppe_net == D(516)  # 500 + 66 capex - 50 depreciation
    assert bs.term_loan == D(80)
    assert bs.revolver == D(0)
    assert bs.retained_earnings == D("520.2")  # 420 + 133.6 - 33.4 dividends
    assert bs.cash == D("151.2")

    assert cf.operating_cash_flow == D("170.6")  # 133.6 + 50 - 13 working capital
    assert cf.investing_cash_flow == D(-66)
    assert cf.financing_cash_flow == D("-53.4")  # -20 term loan - 33.4 dividends
    assert cf.ending_cash == D("151.2")


def test_base_case_balances_and_raises_no_flags_in_every_year() -> None:
    result = calculate(sample_model(years=5))
    assert result.flags == ()
    for year in result.years:
        bs = year.balance_sheet
        assert abs(bs.total_assets - bs.total_liabilities - bs.total_equity) < D("1e-20")


def test_years_continue_from_last_historical_year() -> None:
    result = calculate(sample_model(years=3))
    assert [y.year for y in result.years] == [
        LAST_HISTORICAL_YEAR + 1,
        LAST_HISTORICAL_YEAR + 2,
        LAST_HISTORICAL_YEAR + 3,
    ]


def test_revolver_draws_to_hold_minimum_cash() -> None:
    year = calculate(sample_model(years=1, capex_pct=D("0.20"))).years[0]
    assert year.balance_sheet.revolver == D("52.8")
    assert year.balance_sheet.cash == D(50)
    assert year.cash_flow.revolver_net_borrowing == D("52.8")


def test_revolver_is_repaid_from_surplus_in_later_year() -> None:
    heavy_capex = year_assumptions(capex_pct=D("0.20"))
    normal = year_assumptions()
    result = calculate(model_with([heavy_capex, normal]))
    first, second = result.years
    assert first.balance_sheet.revolver > 0
    assert second.balance_sheet.revolver < first.balance_sheet.revolver
    assert second.balance_sheet.cash >= D(50)
    assert result.flags == ()


def test_shortfall_beyond_revolver_limit_is_flagged_not_funded() -> None:
    result = calculate(sample_model(years=1, capex_pct=D("0.50"), revolver_limit=D(10)))
    year = result.years[0]
    assert year.balance_sheet.revolver == D(10)
    assert year.balance_sheet.cash == D("-322.8")
    assert year.unfunded_shortfall == D("372.8")
    flags = {f.code: f for f in result.flags}
    assert set(flags) == {FlagCode.REVOLVER_LIMIT_EXCEEDED, FlagCode.NEGATIVE_CASH}
    assert flags[FlagCode.REVOLVER_LIMIT_EXCEEDED].year == 2025
    assert flags[FlagCode.REVOLVER_LIMIT_EXCEEDED].amount == D("372.8")
    # Even an unfunded year must still balance: the model never plugs.
    assert FlagCode.BS_IMBALANCE not in flags


def test_cash_between_zero_and_minimum_is_a_warning() -> None:
    result = calculate(sample_model(years=1, min_cash=D(500)))
    assert FlagCode.CASH_BELOW_MINIMUM in codes(result.flags)
    assert FlagCode.NEGATIVE_CASH not in codes(result.flags)


def test_loss_year_pays_no_tax_or_dividends() -> None:
    year = calculate(sample_model(years=1, sga_pct=D("0.90"))).years[0]
    assert year.income_statement.pre_tax_income < 0
    assert year.income_statement.tax_expense == 0
    assert year.cash_flow.dividends == 0


def test_negative_equity_is_flagged() -> None:
    result = calculate(sample_model(years=1, sga_pct=D("2.0")))
    assert FlagCode.NEGATIVE_EQUITY in codes(result.flags)


def test_term_loan_repayment_cannot_exceed_balance() -> None:
    year = calculate(sample_model(years=1, term_loan_repayment=D(500))).years[0]
    assert year.balance_sheet.term_loan == 0
    assert year.cash_flow.term_loan_repayment == D(-100)


def test_zero_revenue_company_still_calculates() -> None:
    last = historical_2024()
    result = calculate(
        replace(
            sample_model(years=2, revenue_growth=D(-1)),
            historicals=(last,),
        )
    )
    assert result.years[0].income_statement.revenue == 0
    assert result.years[1].income_statement.revenue == 0


def test_interest_uses_opening_balances() -> None:
    result = calculate(model_with([year_assumptions(capex_pct=D("0.20")), year_assumptions()]))
    first, second = result.years
    # Year 2 interest = 80 x 5% + 52.8 x 8% - 50 x 2% (opening balances from year 1)
    expected = D(80) * D("0.05") + first.balance_sheet.revolver * D("0.08") - D(50) * D("0.02")
    assert second.income_statement.interest_expense == expected


def test_calculation_is_deterministic() -> None:
    model = sample_model(years=4)
    assert calculate(model) == calculate(model)


def test_changing_a_later_year_leaves_earlier_years_untouched() -> None:
    base = calculate(sample_model(years=3))
    edited_years = [
        year_assumptions(),
        year_assumptions(revenue_growth=D("0.30")),
        year_assumptions(),
    ]
    edited = calculate(model_with(edited_years))
    assert edited.years[0] == base.years[0]
    assert edited.years[1].income_statement.revenue > base.years[1].income_statement.revenue
    assert edited.years[2].income_statement.revenue > base.years[2].income_statement.revenue


def test_change_impact_of_growth_assumption_reaches_all_three_statements() -> None:
    nodes = build_nodes(sample_model(years=2))
    affected = downstream(nodes, "revenue@0")
    for name in ("revenue", "net_income", "retained_earnings", "cash", "accounts_receivable"):
        assert f"{name}@1" in affected
        assert f"{name}@2" in affected
    # Opening balances that no assumption touches are never downstream of revenue.
    assert "term_loan@0" not in affected


def test_trace_explains_a_forecast_value() -> None:
    result = calculate(sample_model(years=1))
    entry = result.trace["revenue@1"]
    assert entry.value == D(1100)
    assert dict(entry.inputs) == {"revenue@0": D(1000)}
    assert "revenue@0" in entry.formula


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda m: replace(m, historicals=()), "historical year"),
        (lambda m: replace(m, assumptions=replace(m.assumptions, years=())), "forecast year"),
        (lambda m: replace(m, tolerance=D(-1)), "Tolerance"),
    ],
)
def test_structurally_invalid_input_is_rejected(mutate, message: str) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(InvalidInputError, match=message):
        calculate(mutate(sample_model()))


def test_unbalanced_historical_balance_sheet_is_rejected_with_year_and_gap() -> None:
    last = historical_2024()
    broken = replace(last, balance_sheet=replace(last.balance_sheet, cash=D(105)))
    with pytest.raises(InvalidInputError, match=r"2024.*gap 5"):
        calculate(replace(sample_model(), historicals=(broken,)))


def test_non_contiguous_historical_years_are_rejected() -> None:
    last = historical_2024()
    earlier = replace(last, year=2020)
    with pytest.raises(InvalidInputError, match="contiguous"):
        calculate(replace(sample_model(), historicals=(earlier, last)))
