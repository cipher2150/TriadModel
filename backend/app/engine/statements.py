"""Assemble the three statements for one forecast year from calculated node values.

The cash flow statement is built from balance sheet movements, and balance sheet cash is
the cash flow statement's ending cash. Nothing is plugged: the balance sheet either
balances because the model is internally consistent, or the checks flag it.
"""

from decimal import Decimal

from app.engine.graph import Values, key
from app.engine.types import BalanceSheet, CashFlow, ForecastYear, IncomeStatement


def build_forecast_year(
    period: int, year: int, values: Values, previous: BalanceSheet
) -> ForecastYear:
    def v(name: str) -> Decimal:
        return values[key(name, period)]

    income = IncomeStatement(
        revenue=v("revenue"),
        cogs=v("cogs"),
        sga=v("sga"),
        depreciation=v("depreciation"),
        interest_expense=v("interest_expense"),
        tax_expense=v("tax_expense"),
    )
    cash_flow = CashFlow(
        beginning_cash=previous.cash,
        net_income=income.net_income,
        depreciation=income.depreciation,
        change_in_receivables=previous.accounts_receivable - v("accounts_receivable"),
        change_in_inventory=previous.inventory - v("inventory"),
        change_in_other_current_assets=previous.other_current_assets - v("other_current_assets"),
        change_in_payables=v("accounts_payable") - previous.accounts_payable,
        change_in_other_current_liabilities=v("other_current_liabilities")
        - previous.other_current_liabilities,
        capex=-v("capex"),
        revolver_net_borrowing=v("revolver_draw") - v("revolver_repayment"),
        term_loan_repayment=-v("term_loan_repayment"),
        dividends=-v("dividends"),
    )
    balance = BalanceSheet(
        cash=cash_flow.ending_cash,
        accounts_receivable=v("accounts_receivable"),
        inventory=v("inventory"),
        other_current_assets=v("other_current_assets"),
        ppe_net=v("ppe"),
        accounts_payable=v("accounts_payable"),
        other_current_liabilities=v("other_current_liabilities"),
        revolver=v("revolver"),
        term_loan=v("term_loan"),
        common_stock=previous.common_stock,
        retained_earnings=v("retained_earnings"),
    )
    return ForecastYear(
        year=year,
        income_statement=income,
        balance_sheet=balance,
        cash_flow=cash_flow,
        ledger_cash=v("cash"),
        unfunded_shortfall=v("unfunded_shortfall"),
    )
