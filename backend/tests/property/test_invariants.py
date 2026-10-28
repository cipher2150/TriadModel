"""Accounting identities must hold for every valid assumption set, not just hand-picked ones."""

from decimal import Decimal as D

from hypothesis import given, settings
from hypothesis import strategies as st

from app.engine.calculate import calculate
from app.engine.types import FlagCode, YearAssumptions
from tests.fixtures.company import model_with

INTEGRITY_CODES = {
    FlagCode.BS_IMBALANCE,
    FlagCode.CASH_TIE_OUT,
    FlagCode.NI_TIE_OUT,
    FlagCode.RE_ROLLFORWARD,
    FlagCode.PPE_ROLLFORWARD,
    FlagCode.DEBT_ROLLFORWARD,
}


def money(low: str, high: str) -> st.SearchStrategy[D]:
    return st.decimals(min_value=D(low), max_value=D(high), places=4)


year_assumptions = st.builds(
    YearAssumptions,
    revenue_growth=money("-0.9", "1.0"),
    cogs_pct=money("0", "1.2"),
    sga_pct=money("0", "0.8"),
    depreciation_rate=money("0", "0.5"),
    capex_pct=money("0", "0.5"),
    dso=money("0", "180"),
    dio=money("0", "240"),
    dpo=money("0", "180"),
    tax_rate=money("0", "0.6"),
    term_loan_rate=money("0", "0.25"),
    revolver_rate=money("0", "0.3"),
    cash_yield=money("0", "0.1"),
    term_loan_repayment=money("0", "300"),
    min_cash=money("0", "400"),
    revolver_limit=money("0", "600"),
    dividend_payout=money("0", "1"),
)

scenarios = st.lists(year_assumptions, min_size=1, max_size=6)


@settings(max_examples=300, deadline=None)
@given(scenarios)
def test_integrity_flags_never_fire_for_valid_assumptions(years: list[YearAssumptions]) -> None:
    result = calculate(model_with(years))
    assert INTEGRITY_CODES.isdisjoint({f.code for f in result.flags})


@settings(max_examples=200, deadline=None)
@given(scenarios)
def test_calculation_is_deterministic(years: list[YearAssumptions]) -> None:
    model = model_with(years)
    assert calculate(model) == calculate(model)


@settings(max_examples=200, deadline=None)
@given(scenarios)
def test_revolver_balance_is_never_negative_and_only_grows_up_to_its_limit(
    years: list[YearAssumptions],
) -> None:
    result = calculate(model_with(years))
    previous = D(0)  # opening revolver in the fixture company
    for year, assumption in zip(result.years, years, strict=True):
        revolver = year.balance_sheet.revolver
        assert revolver >= 0
        assert revolver <= max(assumption.revolver_limit, previous)
        previous = revolver


@settings(max_examples=200, deadline=None)
@given(scenarios)
def test_cash_misses_the_minimum_only_by_the_unfunded_shortfall(
    years: list[YearAssumptions],
) -> None:
    result = calculate(model_with(years))
    epsilon = D("1e-20")
    for year, assumption in zip(result.years, years, strict=True):
        assert year.unfunded_shortfall >= 0
        assert year.balance_sheet.cash >= assumption.min_cash - year.unfunded_shortfall - epsilon
        if year.unfunded_shortfall > 0:
            # A shortfall means the revolver was drawn to its limit.
            assert year.balance_sheet.revolver >= assumption.revolver_limit - epsilon
