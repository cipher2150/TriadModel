"""Interest, dividends, term loan, revolver, cash and retained earnings for one period.

Interest uses opening balances, so net income does not depend on the revolver draw it
helps to cause (no circular reference).
"""

from decimal import Decimal

from app.engine.graph import Node, Values, key
from app.engine.types import YearAssumptions

ZERO = Decimal(0)


def financing_nodes(p: int, a: YearAssumptions) -> list[Node]:
    prev = p - 1
    net_income, depreciation = key("net_income", p), key("depreciation", p)
    capex, nwc_change = key("capex", p), key("nwc_change", p)
    interest = key("interest_expense", p)
    dividends = key("dividends", p)
    term_prev, term_repay, term = (
        key("term_loan", prev),
        key("term_loan_repayment", p),
        key("term_loan", p),
    )
    rev_prev, rev_draw, rev_repay, rev = (
        key("revolver", prev),
        key("revolver_draw", p),
        key("revolver_repayment", p),
        key("revolver", p),
    )
    cash_prev, cash_pre, cash = key("cash", prev), key("cash_before_revolver", p), key("cash", p)
    shortfall = key("unfunded_shortfall", p)
    re_prev, re = key("retained_earnings", prev), key("retained_earnings", p)

    def calc_interest(v: Values) -> Decimal:
        return (
            v[term_prev] * a.term_loan_rate
            + v[rev_prev] * a.revolver_rate
            - v[cash_prev] * a.cash_yield
        )

    def calc_cash_pre(v: Values) -> Decimal:
        return (
            v[cash_prev]
            + v[net_income]
            + v[depreciation]
            - v[nwc_change]
            - v[capex]
            - v[term_repay]
            - v[dividends]
        )

    def funding_need(v: Values) -> Decimal:
        return a.min_cash - v[cash_pre]

    def calc_draw(v: Values) -> Decimal:
        headroom = max(ZERO, a.revolver_limit - v[rev_prev])
        return min(max(ZERO, funding_need(v)), headroom)

    def calc_repay(v: Values) -> Decimal:
        return min(v[rev_prev], max(ZERO, -funding_need(v)))

    def calc_shortfall(v: Values) -> Decimal:
        return max(ZERO, funding_need(v)) - v[rev_draw]

    return [
        Node(
            interest,
            f"{term_prev} × {a.term_loan_rate} + {rev_prev} × {a.revolver_rate}"
            f" - {cash_prev} × {a.cash_yield}",
            (term_prev, rev_prev, cash_prev),
            calc_interest,
        ),
        Node(
            dividends,
            f"max(0, {net_income}) × {a.dividend_payout}",
            (net_income,),
            lambda v: max(ZERO, v[net_income]) * a.dividend_payout,
        ),
        Node(
            term_repay,
            f"min({term_prev}, {a.term_loan_repayment})",
            (term_prev,),
            lambda v: min(v[term_prev], a.term_loan_repayment),
        ),
        Node(
            term,
            f"{term_prev} - {term_repay}",
            (term_prev, term_repay),
            lambda v: v[term_prev] - v[term_repay],
        ),
        Node(
            cash_pre,
            f"{cash_prev} + {net_income} + {depreciation} - {nwc_change} - {capex}"
            f" - {term_repay} - {dividends}",
            (cash_prev, net_income, depreciation, nwc_change, capex, term_repay, dividends),
            calc_cash_pre,
        ),
        Node(
            rev_draw,
            f"min(max(0, {a.min_cash} - {cash_pre}), max(0, {a.revolver_limit} - {rev_prev}))",
            (cash_pre, rev_prev),
            calc_draw,
        ),
        Node(
            rev_repay,
            f"min({rev_prev}, max(0, {cash_pre} - {a.min_cash}))",
            (cash_pre, rev_prev),
            calc_repay,
        ),
        Node(
            rev,
            f"{rev_prev} + {rev_draw} - {rev_repay}",
            (rev_prev, rev_draw, rev_repay),
            lambda v: v[rev_prev] + v[rev_draw] - v[rev_repay],
        ),
        Node(
            cash,
            f"{cash_pre} + {rev_draw} - {rev_repay}",
            (cash_pre, rev_draw, rev_repay),
            lambda v: v[cash_pre] + v[rev_draw] - v[rev_repay],
        ),
        Node(
            shortfall,
            f"max(0, {a.min_cash} - {cash_pre}) - {rev_draw}",
            (cash_pre, rev_draw),
            calc_shortfall,
        ),
        Node(
            re,
            f"{re_prev} + {net_income} - {dividends}",
            (re_prev, net_income, dividends),
            lambda v: v[re_prev] + v[net_income] - v[dividends],
        ),
    ]
