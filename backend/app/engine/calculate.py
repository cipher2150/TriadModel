from decimal import Context, localcontext

from app.engine.checks import check_integrity, check_liquidity
from app.engine.constants import DECIMAL_PRECISION
from app.engine.forecast import build_nodes
from app.engine.graph import evaluate
from app.engine.statements import build_forecast_year
from app.engine.types import (
    BalanceSheet,
    ForecastYear,
    InvalidInputError,
    ModelInput,
    ModelResult,
)


def _validate(model: ModelInput) -> None:
    if not model.historicals:
        raise InvalidInputError("At least one historical year is required")
    if not model.assumptions.years:
        raise InvalidInputError("At least one forecast year of assumptions is required")
    if model.tolerance < 0:
        raise InvalidInputError("Tolerance must not be negative")
    years = [h.year for h in model.historicals]
    if years != list(range(years[0], years[0] + len(years))):
        raise InvalidInputError(f"Historical years must be contiguous and ascending, got {years}")
    for h in model.historicals:
        bs = h.balance_sheet
        gap = bs.total_assets - (bs.total_liabilities + bs.total_equity)
        if abs(gap) > model.tolerance:
            raise InvalidInputError(
                f"Historical balance sheet for {h.year} does not balance (gap {gap})"
            )


def calculate(model: ModelInput) -> ModelResult:
    """Forecast the three statements for one set of assumptions.

    Financial problems (imbalances, shortfalls) are returned as flags. Exceptions are raised
    only for contract violations such as non-contiguous years or an unbalanced opening
    balance sheet.
    """
    _validate(model)
    with localcontext(Context(prec=DECIMAL_PRECISION)):
        values, trace = evaluate(build_nodes(model))
        last = model.historicals[-1]
        previous: BalanceSheet = last.balance_sheet
        years: list[ForecastYear] = []
        for period in range(1, len(model.assumptions.years) + 1):
            forecast_year = build_forecast_year(period, last.year + period, values, previous)
            years.append(forecast_year)
            previous = forecast_year.balance_sheet

    flags = [
        *check_integrity(last.balance_sheet, years, model.tolerance),
        *check_liquidity(years, model.assumptions, model.tolerance),
    ]
    return ModelResult(years=tuple(years), flags=tuple(flags), trace=trace)
