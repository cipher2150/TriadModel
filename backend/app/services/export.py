import csv
import io

from app.schemas.result import ScenarioResultOut, StatementsYearOut, format_money

_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def neutralise(cell: str) -> str:
    """Stop spreadsheets treating a text cell (e.g. a company name) as a formula."""
    return "'" + cell if cell.startswith(_FORMULA_PREFIXES) else cell


def statements_csv(
    company_name: str,
    scenario: str,
    historicals: list[StatementsYearOut],
    result: ScenarioResultOut,
) -> str:
    years = [*historicals, *result.years]
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow([neutralise(f"{company_name} - {scenario} scenario")])
    writer.writerow(["statement", "line_item", *[str(y.year) for y in years]])
    for statement in ("income_statement", "balance_sheet", "cash_flow"):
        lines = list(getattr(years[0], statement).model_dump())
        for line in lines:
            values = [getattr(getattr(y, statement), line) for y in years]
            writer.writerow([statement, line, *[format_money(v) for v in values]])
    return out.getvalue()
