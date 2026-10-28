"""Scenario handling.

A scenario is always a complete `Assumptions` object. The helpers here only *derive*
Upside and Downside starting points from Base; once derived, users edit them freely.
"""

from collections.abc import Mapping
from dataclasses import dataclass, replace
from decimal import Decimal

from app.engine.calculate import calculate
from app.engine.constants import ZERO
from app.engine.types import Assumptions, HistoricalYear, ModelInput, ModelResult, YearAssumptions

BASE = "base"
UPSIDE = "upside"
DOWNSIDE = "downside"
SCENARIO_NAMES = (BASE, UPSIDE, DOWNSIDE)


@dataclass(frozen=True)
class ScenarioDeltas:
    """Additive adjustments to Base drivers. Percentages are fractions; working capital in days."""

    revenue_growth: Decimal
    cogs_pct: Decimal
    dso: Decimal
    dio: Decimal
    dpo: Decimal


UPSIDE_DELTAS = ScenarioDeltas(
    revenue_growth=Decimal("0.03"),
    cogs_pct=Decimal("-0.01"),
    dso=Decimal(-2),
    dio=Decimal(-3),
    dpo=Decimal(2),
)
DOWNSIDE_DELTAS = ScenarioDeltas(
    revenue_growth=Decimal("-0.06"),
    cogs_pct=Decimal("0.02"),
    dso=Decimal(5),
    dio=Decimal(5),
    dpo=Decimal(-5),
)


def _apply(year: YearAssumptions, deltas: ScenarioDeltas) -> YearAssumptions:
    return replace(
        year,
        revenue_growth=year.revenue_growth + deltas.revenue_growth,
        cogs_pct=max(ZERO, year.cogs_pct + deltas.cogs_pct),
        dso=max(ZERO, year.dso + deltas.dso),
        dio=max(ZERO, year.dio + deltas.dio),
        dpo=max(ZERO, year.dpo + deltas.dpo),
    )


def derive(base: Assumptions, deltas: ScenarioDeltas) -> Assumptions:
    return Assumptions(years=tuple(_apply(year, deltas) for year in base.years))


def default_scenarios(base: Assumptions) -> dict[str, Assumptions]:
    return {
        BASE: base,
        UPSIDE: derive(base, UPSIDE_DELTAS),
        DOWNSIDE: derive(base, DOWNSIDE_DELTAS),
    }


def calculate_scenarios(
    historicals: tuple[HistoricalYear, ...],
    scenarios: Mapping[str, Assumptions],
    tolerance: Decimal,
) -> dict[str, ModelResult]:
    return {
        name: calculate(ModelInput(historicals, assumptions, tolerance))
        for name, assumptions in scenarios.items()
    }
