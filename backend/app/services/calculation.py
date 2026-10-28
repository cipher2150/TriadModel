from app.engine.scenarios import calculate_scenarios
from app.schemas.model import ModelPayload
from app.schemas.result import CalculationOut, historical_out, scenario_result_out


def calculate_payload(payload: ModelPayload, include_trace: bool = False) -> CalculationOut:
    historicals = payload.to_engine_historicals()
    results = calculate_scenarios(historicals, payload.to_engine_assumptions(), payload.tolerance)
    return CalculationOut(
        company_name=payload.company_name,
        is_demo=payload.is_demo,
        historicals=[historical_out(h) for h in historicals],
        scenarios={
            name: scenario_result_out(result, include_trace) for name, result in results.items()
        },
    )
