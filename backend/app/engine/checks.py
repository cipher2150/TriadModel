"""Accounting-identity and liquidity checks over calculated forecast years.

Integrity flags (errors) indicate the model is internally inconsistent; liquidity flags
describe the forecast business outcome.
"""

from collections.abc import Sequence
from decimal import Decimal

from app.engine.types import (
    Assumptions,
    BalanceSheet,
    Flag,
    FlagCode,
    ForecastYear,
    Severity,
)

ZERO = Decimal(0)


def check_integrity(
    opening: BalanceSheet, years: Sequence[ForecastYear], tolerance: Decimal
) -> list[Flag]:
    flags: list[Flag] = []
    previous = opening
    for fy in years:
        bs, cf, income = fy.balance_sheet, fy.cash_flow, fy.income_statement

        def error(code: FlagCode, message: str, amount: Decimal, year: int = fy.year) -> None:
            flags.append(Flag(code, Severity.ERROR, year, message, amount))

        gap = bs.total_assets - (bs.total_liabilities + bs.total_equity)
        if abs(gap) > tolerance:
            error(FlagCode.BS_IMBALANCE, f"Assets differ from liabilities + equity by {gap}", gap)

        cash_gap = cf.ending_cash - fy.ledger_cash
        if abs(cash_gap) > tolerance:
            error(
                FlagCode.CASH_TIE_OUT,
                f"Cash flow ending cash differs from the running cash balance by {cash_gap}",
                cash_gap,
            )

        ni_gap = income.net_income - cf.net_income
        if abs(ni_gap) > tolerance:
            error(
                FlagCode.NI_TIE_OUT,
                f"Income statement and cash flow net income differ by {ni_gap}",
                ni_gap,
            )

        re_gap = bs.retained_earnings - (
            previous.retained_earnings + income.net_income + cf.dividends
        )
        if abs(re_gap) > tolerance:
            error(
                FlagCode.RE_ROLLFORWARD, f"Retained earnings roll-forward off by {re_gap}", re_gap
            )

        ppe_gap = bs.ppe_net - (previous.ppe_net - cf.capex - income.depreciation)
        if abs(ppe_gap) > tolerance:
            error(FlagCode.PPE_ROLLFORWARD, f"PP&E roll-forward off by {ppe_gap}", ppe_gap)

        debt_change = (bs.revolver + bs.term_loan) - (previous.revolver + previous.term_loan)
        debt_gap = debt_change - (cf.revolver_net_borrowing + cf.term_loan_repayment)
        if abs(debt_gap) > tolerance:
            error(FlagCode.DEBT_ROLLFORWARD, f"Debt roll-forward off by {debt_gap}", debt_gap)

        previous = bs
    return flags


def check_liquidity(
    years: Sequence[ForecastYear], assumptions: Assumptions, tolerance: Decimal
) -> list[Flag]:
    flags: list[Flag] = []
    for fy, a in zip(years, assumptions.years, strict=True):
        bs = fy.balance_sheet
        if fy.unfunded_shortfall > tolerance:
            flags.append(
                Flag(
                    FlagCode.REVOLVER_LIMIT_EXCEEDED,
                    Severity.ERROR,
                    fy.year,
                    f"Funding need exceeds the revolver limit by {fy.unfunded_shortfall}",
                    fy.unfunded_shortfall,
                )
            )
        if bs.cash < ZERO - tolerance:
            flags.append(
                Flag(
                    FlagCode.NEGATIVE_CASH,
                    Severity.ERROR,
                    fy.year,
                    f"Ending cash is negative ({bs.cash})",
                    bs.cash,
                )
            )
        elif bs.cash < a.min_cash - tolerance:
            flags.append(
                Flag(
                    FlagCode.CASH_BELOW_MINIMUM,
                    Severity.WARNING,
                    fy.year,
                    f"Ending cash {bs.cash} is below the minimum {a.min_cash}",
                    a.min_cash - bs.cash,
                )
            )
        if bs.total_equity < ZERO:
            flags.append(
                Flag(
                    FlagCode.NEGATIVE_EQUITY,
                    Severity.WARNING,
                    fy.year,
                    f"Total equity is negative ({bs.total_equity})",
                    bs.total_equity,
                )
            )
    return flags
