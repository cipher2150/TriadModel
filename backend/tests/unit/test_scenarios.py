from decimal import Decimal as D

from app.engine.scenarios import (
    BASE,
    DOWNSIDE,
    SCENARIO_NAMES,
    UPSIDE,
    calculate_scenarios,
    default_scenarios,
)
from app.engine.types import Assumptions, FlagCode
from tests.fixtures.company import historical_2024, model_with, sample_model, year_assumptions

TOLERANCE = D("0.01")


def results_for(base: Assumptions):  # type: ignore[no-untyped-def]
    return calculate_scenarios((historical_2024(),), default_scenarios(base), TOLERANCE)


def test_default_scenarios_contain_all_three_names() -> None:
    scenarios = default_scenarios(sample_model().assumptions)
    assert tuple(scenarios) == SCENARIO_NAMES


def test_base_scenario_is_the_input_unchanged() -> None:
    base = sample_model().assumptions
    assert default_scenarios(base)[BASE] == base


def test_upside_and_downside_shift_the_documented_drivers() -> None:
    base = sample_model(years=1).assumptions
    scenarios = default_scenarios(base)
    b, u, d = (scenarios[n].years[0] for n in (BASE, UPSIDE, DOWNSIDE))
    assert u.revenue_growth == b.revenue_growth + D("0.03")
    assert d.revenue_growth == b.revenue_growth - D("0.06")
    assert u.cogs_pct < b.cogs_pct < d.cogs_pct
    assert u.dso < b.dso < d.dso
    # Drivers not covered by the deltas stay identical.
    assert (u.tax_rate, u.min_cash, u.capex_pct) == (b.tax_rate, b.min_cash, b.capex_pct)


def test_derived_values_are_clamped_at_zero() -> None:
    base = Assumptions(years=(year_assumptions(cogs_pct=D("0.005"), dso=D(1), dpo=D(2)),))
    scenarios = default_scenarios(base)
    assert scenarios[UPSIDE].years[0].cogs_pct == 0
    assert scenarios[UPSIDE].years[0].dso == 0
    assert scenarios[DOWNSIDE].years[0].dpo == 0


def test_every_year_is_adjusted() -> None:
    base = sample_model(years=4).assumptions
    derived = default_scenarios(base)[UPSIDE]
    assert len(derived.years) == 4
    assert all(y.revenue_growth == D("0.13") for y in derived.years)


def test_outcomes_are_ordered_upside_over_base_over_downside() -> None:
    results = results_for(sample_model(years=3).assumptions)
    revenue = {n: results[n].years[-1].income_statement.revenue for n in SCENARIO_NAMES}
    income = {n: results[n].years[-1].income_statement.net_income for n in SCENARIO_NAMES}
    assert revenue[UPSIDE] > revenue[BASE] > revenue[DOWNSIDE]
    assert income[UPSIDE] > income[BASE] > income[DOWNSIDE]


def test_all_scenarios_keep_the_accounts_balanced() -> None:
    results = results_for(sample_model(years=5).assumptions)
    for result in results.values():
        assert not {f.code for f in result.flags} & {FlagCode.BS_IMBALANCE, FlagCode.CASH_TIE_OUT}


def test_downside_can_exhaust_the_revolver_while_base_stays_funded() -> None:
    tight = [year_assumptions(capex_pct=D("0.13"), revolver_limit=D(30)) for _ in range(3)]
    results = results_for(model_with(tight).assumptions)
    base_codes = {f.code for f in results[BASE].flags}
    downside_codes = {f.code for f in results[DOWNSIDE].flags}
    assert FlagCode.REVOLVER_LIMIT_EXCEEDED not in base_codes
    assert FlagCode.REVOLVER_LIMIT_EXCEEDED in downside_codes
