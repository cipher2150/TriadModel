"""Each integrity check must fire when its relationship is deliberately broken."""

from dataclasses import replace
from decimal import Decimal as D

from app.engine.calculate import calculate
from app.engine.checks import check_integrity
from app.engine.types import FlagCode, ForecastYear
from tests.fixtures.company import historical_2024, sample_model

OPENING = historical_2024().balance_sheet
TOLERANCE = D("0.01")


def good_year() -> ForecastYear:
    return calculate(sample_model(years=1)).years[0]


def flags_for(year: ForecastYear) -> dict[FlagCode, D]:
    return {f.code: f.amount for f in check_integrity(OPENING, [year], TOLERANCE)}


def test_correct_output_has_no_integrity_flags() -> None:
    assert flags_for(good_year()) == {}


def test_balance_sheet_imbalance_is_flagged_with_amount() -> None:
    year = good_year()
    broken = replace(year, balance_sheet=replace(year.balance_sheet, inventory=D(1000)))
    flags = flags_for(broken)
    assert flags[FlagCode.BS_IMBALANCE] == D(1000) - year.balance_sheet.inventory


def test_cash_flow_not_tying_to_running_cash_is_flagged() -> None:
    year = good_year()
    flags = flags_for(replace(year, ledger_cash=year.ledger_cash + D(7)))
    assert flags[FlagCode.CASH_TIE_OUT] == D(-7)


def test_net_income_mismatch_between_statements_is_flagged() -> None:
    year = good_year()
    broken = replace(year, cash_flow=replace(year.cash_flow, net_income=D(1)))
    assert FlagCode.NI_TIE_OUT in flags_for(broken)


def test_retained_earnings_rollforward_break_is_flagged() -> None:
    year = good_year()
    broken = replace(year, balance_sheet=replace(year.balance_sheet, retained_earnings=D(999)))
    assert FlagCode.RE_ROLLFORWARD in flags_for(broken)


def test_ppe_rollforward_break_is_flagged() -> None:
    year = good_year()
    broken = replace(year, balance_sheet=replace(year.balance_sheet, ppe_net=D(1)))
    assert FlagCode.PPE_ROLLFORWARD in flags_for(broken)


def test_debt_rollforward_break_is_flagged() -> None:
    year = good_year()
    broken = replace(year, balance_sheet=replace(year.balance_sheet, term_loan=D(5)))
    assert FlagCode.DEBT_ROLLFORWARD in flags_for(broken)


def test_difference_within_tolerance_is_not_flagged() -> None:
    year = good_year()
    nudged = replace(year, ledger_cash=year.ledger_cash + D("0.005"))
    assert FlagCode.CASH_TIE_OUT not in flags_for(nudged)


def test_difference_just_beyond_tolerance_is_flagged() -> None:
    year = good_year()
    nudged = replace(year, ledger_cash=year.ledger_cash + D("0.011"))
    assert FlagCode.CASH_TIE_OUT in flags_for(nudged)
