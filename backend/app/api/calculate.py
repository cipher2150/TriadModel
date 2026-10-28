from fastapi import APIRouter

from app.schemas.model import ModelPayload
from app.schemas.result import CalculationOut
from app.services.calculation import calculate_payload
from app.services.demo import demo_payload

router = APIRouter(prefix="/api", tags=["calculation"])


@router.post("/calculate")
def calculate(payload: ModelPayload, include_trace: bool = False) -> CalculationOut:
    """Stateless: calculate all three scenarios for a posted model without saving it."""
    return calculate_payload(payload, include_trace)


@router.get("/demo")
def demo() -> ModelPayload:
    """Demo company input (illustrative data, flagged with is_demo)."""
    return demo_payload()
