from app.data.demo import (
    DEMO_BASE_YEAR,
    DEMO_COMPANY_NAME,
    DEMO_FORECAST_YEARS,
    DEMO_HISTORICALS,
)
from app.engine.scenarios import BASE, DOWNSIDE, UPSIDE, default_scenarios
from app.schemas.model import ModelPayload, YearAssumptionsIn


def demo_payload() -> ModelPayload:
    """Build the demo model; Upside and Downside are derived from Base by the engine."""
    base_year = YearAssumptionsIn(**DEMO_BASE_YEAR)
    base_rows = [base_year] * DEMO_FORECAST_YEARS
    draft = ModelPayload(
        company_name=DEMO_COMPANY_NAME,
        is_demo=True,
        historicals=DEMO_HISTORICALS,
        scenarios={BASE: base_rows, UPSIDE: base_rows, DOWNSIDE: base_rows},
    )
    derived = default_scenarios(draft.to_engine_assumptions()[BASE])
    return draft.model_copy(
        update={
            "scenarios": {
                name: [YearAssumptionsIn(**vars(year)) for year in assumptions.years]
                for name, assumptions in derived.items()
            }
        }
    )
