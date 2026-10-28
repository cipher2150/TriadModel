"""Receivables, inventory and payables driven by DSO/DIO/DPO. Other items are held flat."""

from decimal import Decimal

from app.engine.constants import DAYS_IN_YEAR
from app.engine.graph import Node, Values, key
from app.engine.types import YearAssumptions


def working_capital_nodes(p: int, a: YearAssumptions) -> list[Node]:
    prev = p - 1
    revenue, cogs = key("revenue", p), key("cogs", p)
    ar, inventory, ap = (
        key("accounts_receivable", p),
        key("inventory", p),
        key("accounts_payable", p),
    )
    oca, ocl = key("other_current_assets", p), key("other_current_liabilities", p)
    prev_oca, prev_ocl = key("other_current_assets", prev), key("other_current_liabilities", prev)
    nwc, prev_nwc = key("net_working_capital", p), key("net_working_capital", prev)
    nwc_change = key("nwc_change", p)

    def calc_nwc(v: Values) -> Decimal:
        return v[ar] + v[inventory] + v[oca] - v[ap] - v[ocl]

    return [
        Node(
            ar,
            f"{revenue} × {a.dso} / {DAYS_IN_YEAR}",
            (revenue,),
            lambda v: v[revenue] * a.dso / DAYS_IN_YEAR,
        ),
        Node(
            inventory,
            f"{cogs} × {a.dio} / {DAYS_IN_YEAR}",
            (cogs,),
            lambda v: v[cogs] * a.dio / DAYS_IN_YEAR,
        ),
        Node(
            ap,
            f"{cogs} × {a.dpo} / {DAYS_IN_YEAR}",
            (cogs,),
            lambda v: v[cogs] * a.dpo / DAYS_IN_YEAR,
        ),
        Node(oca, f"{prev_oca} (held flat)", (prev_oca,), lambda v: v[prev_oca]),
        Node(ocl, f"{prev_ocl} (held flat)", (prev_ocl,), lambda v: v[prev_ocl]),
        Node(
            nwc,
            f"{ar} + {inventory} + {oca} - {ap} - {ocl}",
            (ar, inventory, oca, ap, ocl),
            calc_nwc,
        ),
        Node(nwc_change, f"{nwc} - {prev_nwc}", (nwc, prev_nwc), lambda v: v[nwc] - v[prev_nwc]),
    ]
