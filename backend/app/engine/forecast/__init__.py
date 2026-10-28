from decimal import Decimal

from app.engine.forecast.financing import financing_nodes
from app.engine.forecast.operating import operating_nodes
from app.engine.forecast.working_capital import working_capital_nodes
from app.engine.graph import Node, key
from app.engine.types import HistoricalYear, ModelInput


def _anchor(name: str, value: Decimal) -> Node:
    return Node(key(name, 0), "last historical year", (), lambda _: value)


def opening_nodes(last: HistoricalYear) -> list[Node]:
    """Constant nodes (period 0) carrying the last historical balances and revenue."""
    bs = last.balance_sheet
    anchors = {
        "revenue": last.income_statement.revenue,
        "cash": bs.cash,
        "accounts_receivable": bs.accounts_receivable,
        "inventory": bs.inventory,
        "other_current_assets": bs.other_current_assets,
        "ppe": bs.ppe_net,
        "accounts_payable": bs.accounts_payable,
        "other_current_liabilities": bs.other_current_liabilities,
        "revolver": bs.revolver,
        "term_loan": bs.term_loan,
        "retained_earnings": bs.retained_earnings,
        "net_working_capital": (
            bs.accounts_receivable
            + bs.inventory
            + bs.other_current_assets
            - bs.accounts_payable
            - bs.other_current_liabilities
        ),
    }
    return [_anchor(name, value) for name, value in anchors.items()]


def build_nodes(model: ModelInput) -> list[Node]:
    nodes = opening_nodes(model.historicals[-1])
    for index, assumptions in enumerate(model.assumptions.years, start=1):
        nodes += operating_nodes(index, assumptions)
        nodes += working_capital_nodes(index, assumptions)
        nodes += financing_nodes(index, assumptions)
    return nodes
