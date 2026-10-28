"""Request contracts. Untrusted input becomes engine types only after passing these."""

from decimal import Decimal
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.engine.constants import DEFAULT_TOLERANCE
from app.engine.scenarios import SCENARIO_NAMES
from app.engine.types import (
    Assumptions,
    BalanceSheet,
    CashFlow,
    HistoricalYear,
    IncomeStatement,
    YearAssumptions,
)

MAX_HISTORICAL_YEARS = 5
MAX_FORECAST_YEARS = 10
MAX_AMOUNT = Decimal("1e15")

Amount = Annotated[Decimal, Field(ge=-MAX_AMOUNT, le=MAX_AMOUNT, allow_inf_nan=False)]
NonNegativeAmount = Annotated[Decimal, Field(ge=0, le=MAX_AMOUNT, allow_inf_nan=False)]
Growth = Annotated[Decimal, Field(ge=Decimal(-1), le=Decimal(10), allow_inf_nan=False)]
Fraction = Annotated[Decimal, Field(ge=0, le=1, allow_inf_nan=False)]
Ratio = Annotated[Decimal, Field(ge=0, le=Decimal(5), allow_inf_nan=False)]
Days = Annotated[Decimal, Field(ge=0, le=Decimal(730), allow_inf_nan=False)]
Rate = Annotated[Decimal, Field(ge=0, le=Decimal(1), allow_inf_nan=False)]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class IncomeStatementIn(Strict):
    revenue: NonNegativeAmount
    cogs: NonNegativeAmount
    sga: NonNegativeAmount
    depreciation: NonNegativeAmount
    interest_expense: Amount
    tax_expense: Amount


class BalanceSheetIn(Strict):
    cash: Amount
    accounts_receivable: NonNegativeAmount
    inventory: NonNegativeAmount
    other_current_assets: NonNegativeAmount
    ppe_net: NonNegativeAmount
    accounts_payable: NonNegativeAmount
    other_current_liabilities: NonNegativeAmount
    revolver: NonNegativeAmount
    term_loan: NonNegativeAmount
    common_stock: Amount
    retained_earnings: Amount


class CashFlowIn(Strict):
    beginning_cash: Amount
    net_income: Amount
    depreciation: Amount
    change_in_receivables: Amount
    change_in_inventory: Amount
    change_in_other_current_assets: Amount
    change_in_payables: Amount
    change_in_other_current_liabilities: Amount
    capex: Amount
    revolver_net_borrowing: Amount
    term_loan_repayment: Amount
    dividends: Amount


class HistoricalYearIn(Strict):
    year: Annotated[int, Field(ge=1900, le=2200)]
    income_statement: IncomeStatementIn
    balance_sheet: BalanceSheetIn
    cash_flow: CashFlowIn


class YearAssumptionsIn(Strict):
    revenue_growth: Growth
    cogs_pct: Ratio
    sga_pct: Ratio
    depreciation_rate: Fraction
    capex_pct: Ratio
    dso: Days
    dio: Days
    dpo: Days
    tax_rate: Fraction
    term_loan_rate: Rate
    revolver_rate: Rate
    cash_yield: Rate
    term_loan_repayment: NonNegativeAmount
    min_cash: NonNegativeAmount
    revolver_limit: NonNegativeAmount
    dividend_payout: Fraction


class ModelPayload(Strict):
    """A complete model: history plus one full assumption set per scenario."""

    company_name: Annotated[str, Field(min_length=1, max_length=120)]
    is_demo: bool = False
    historicals: Annotated[
        list[HistoricalYearIn], Field(min_length=1, max_length=MAX_HISTORICAL_YEARS)
    ]
    scenarios: dict[
        str, Annotated[list[YearAssumptionsIn], Field(min_length=1, max_length=MAX_FORECAST_YEARS)]
    ]
    tolerance: Annotated[Decimal, Field(ge=0, le=Decimal(100), allow_inf_nan=False)] = (
        DEFAULT_TOLERANCE
    )

    @model_validator(mode="after")
    def check_consistency(self) -> Self:
        years = [h.year for h in self.historicals]
        if years != list(range(years[0], years[0] + len(years))):
            raise ValueError(f"historical years must be contiguous and ascending, got {years}")
        if set(self.scenarios) != set(SCENARIO_NAMES):
            raise ValueError(f"scenarios must be exactly {sorted(SCENARIO_NAMES)}")
        lengths = {name: len(rows) for name, rows in self.scenarios.items()}
        if len(set(lengths.values())) != 1:
            raise ValueError(
                f"every scenario needs the same number of forecast years, got {lengths}"
            )
        for h in self.historicals:
            bs = h.balance_sheet
            assets = (
                bs.cash
                + bs.accounts_receivable
                + bs.inventory
                + bs.other_current_assets
                + bs.ppe_net
            )
            claims = (
                bs.accounts_payable
                + bs.other_current_liabilities
                + bs.revolver
                + bs.term_loan
                + bs.common_stock
                + bs.retained_earnings
            )
            if abs(assets - claims) > self.tolerance:
                raise ValueError(
                    f"historical balance sheet for {h.year} does not balance (assets differ from "
                    f"liabilities + equity by {assets - claims})"
                )
        return self

    def to_engine_historicals(self) -> tuple[HistoricalYear, ...]:
        return tuple(
            HistoricalYear(
                year=h.year,
                income_statement=IncomeStatement(**dict(h.income_statement)),
                balance_sheet=BalanceSheet(**dict(h.balance_sheet)),
                cash_flow=CashFlow(**dict(h.cash_flow)),
            )
            for h in self.historicals
        )

    def to_engine_assumptions(self) -> dict[str, Assumptions]:
        return {
            name: Assumptions(years=tuple(YearAssumptions(**dict(y)) for y in rows))
            for name, rows in self.scenarios.items()
        }
