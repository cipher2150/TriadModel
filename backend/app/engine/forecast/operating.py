"""Revenue, operating costs, fixed assets, tax and net income for one forecast period."""

from decimal import Decimal

from app.engine.graph import Node, Values, key
from app.engine.types import YearAssumptions

ZERO = Decimal(0)


def operating_nodes(p: int, a: YearAssumptions) -> list[Node]:
    prev = p - 1
    revenue, prev_revenue = key("revenue", p), key("revenue", prev)
    cogs, sga = key("cogs", p), key("sga", p)
    capex, depreciation = key("capex", p), key("depreciation", p)
    ppe, prev_ppe = key("ppe", p), key("ppe", prev)
    ebt, interest = key("pre_tax_income", p), key("interest_expense", p)
    tax, net_income = key("tax_expense", p), key("net_income", p)

    def calc_revenue(v: Values) -> Decimal:
        return v[prev_revenue] * (1 + a.revenue_growth)

    def calc_ebt(v: Values) -> Decimal:
        return v[revenue] - v[cogs] - v[sga] - v[depreciation] - v[interest]

    def calc_tax(v: Values) -> Decimal:
        return max(ZERO, v[ebt]) * a.tax_rate

    return [
        Node(revenue, f"{prev_revenue} × (1 + {a.revenue_growth})", (prev_revenue,), calc_revenue),
        Node(cogs, f"{revenue} × {a.cogs_pct}", (revenue,), lambda v: v[revenue] * a.cogs_pct),
        Node(sga, f"{revenue} × {a.sga_pct}", (revenue,), lambda v: v[revenue] * a.sga_pct),
        Node(capex, f"{revenue} × {a.capex_pct}", (revenue,), lambda v: v[revenue] * a.capex_pct),
        Node(
            depreciation,
            f"{prev_ppe} × {a.depreciation_rate}",
            (prev_ppe,),
            lambda v: v[prev_ppe] * a.depreciation_rate,
        ),
        Node(
            ppe,
            f"{prev_ppe} + {capex} - {depreciation}",
            (prev_ppe, capex, depreciation),
            lambda v: v[prev_ppe] + v[capex] - v[depreciation],
        ),
        Node(
            ebt,
            f"{revenue} - {cogs} - {sga} - {depreciation} - {interest}",
            (revenue, cogs, sga, depreciation, interest),
            calc_ebt,
        ),
        Node(
            tax,
            f"max(0, {ebt}) × {a.tax_rate}",
            (ebt,),
            calc_tax,
        ),
        Node(net_income, f"{ebt} - {tax}", (ebt, tax), lambda v: v[ebt] - v[tax]),
    ]
