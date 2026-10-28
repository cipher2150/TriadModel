"""Small test company with round numbers so expected values can be computed by hand.

Last historical year (2024): revenue 1000, cogs 600, sga 200, depreciation 50, net interest 10,
tax 28 -> net income 112. Working-capital days are chosen so the 2024 balances equal the
2025 forecast ratios exactly (AR 100 = 1000 x 36.5/365, etc.).
"""

from dataclasses import replace
from decimal import Decimal as D

from app.engine.constants import DEFAULT_TOLERANCE
from app.engine.types import (
    Assumptions,
    BalanceSheet,
    CashFlow,
    HistoricalYear,
    IncomeStatement,
    ModelInput,
    YearAssumptions,
)

LAST_HISTORICAL_YEAR = 2024


def historical_2024() -> HistoricalYear:
    income = IncomeStatement(
        revenue=D(1000),
        cogs=D(600),
        sga=D(200),
        depreciation=D(50),
        interest_expense=D(10),
        tax_expense=D(28),
    )
    balance = BalanceSheet(
        cash=D(100),
        accounts_receivable=D(100),
        inventory=D(90),
        other_current_assets=D(10),
        ppe_net=D(500),
        accounts_payable=D(60),
        other_current_liabilities=D(20),
        revolver=D(0),
        term_loan=D(100),
        common_stock=D(200),
        retained_earnings=D(420),
    )
    cash_flow = CashFlow(
        beginning_cash=D(100),
        net_income=income.net_income,
        depreciation=D(50),
        change_in_receivables=D(0),
        change_in_inventory=D(0),
        change_in_other_current_assets=D(0),
        change_in_payables=D(0),
        change_in_other_current_liabilities=D(0),
        capex=D(-50),
        revolver_net_borrowing=D(0),
        term_loan_repayment=D(-20),
        dividends=D(-92),
    )
    return HistoricalYear(LAST_HISTORICAL_YEAR, income, balance, cash_flow)


def year_assumptions(**overrides: D) -> YearAssumptions:
    base = YearAssumptions(
        revenue_growth=D("0.10"),
        cogs_pct=D("0.60"),
        sga_pct=D("0.20"),
        depreciation_rate=D("0.10"),
        capex_pct=D("0.06"),
        dso=D("36.5"),
        dio=D("54.75"),
        dpo=D("36.5"),
        tax_rate=D("0.20"),
        term_loan_rate=D("0.05"),
        revolver_rate=D("0.08"),
        cash_yield=D("0.02"),
        term_loan_repayment=D(20),
        min_cash=D(50),
        revolver_limit=D(200),
        dividend_payout=D("0.25"),
    )
    return replace(base, **overrides)


def sample_model(years: int = 3, **overrides: D) -> ModelInput:
    return model_with([year_assumptions(**overrides) for _ in range(years)])


def model_with(year_list: list[YearAssumptions]) -> ModelInput:
    return ModelInput(
        historicals=(historical_2024(),),
        assumptions=Assumptions(years=tuple(year_list)),
        tolerance=DEFAULT_TOLERANCE,
    )
