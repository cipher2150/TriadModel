from decimal import Decimal

DAYS_IN_YEAR = Decimal(365)
ZERO = Decimal(0)
ONE = Decimal(1)

# Divisions such as DSO/365 do not terminate, so accounting identities are compared
# within an absolute tolerance rather than for exact equality.
DEFAULT_TOLERANCE = Decimal("0.01")

DECIMAL_PRECISION = 28
