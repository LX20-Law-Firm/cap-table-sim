"""Exact rational arithmetic for a documented pre-money conversion model."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from fractions import Fraction

Scalar = str | int | Decimal | Fraction


def rational(value: Scalar, name: str, *, positive: bool = False) -> Fraction:
    if isinstance(value, (bool, float)):
        raise ValueError(f"Use a decimal string, integer, Decimal or Fraction for {name}")
    try:
        result = value if isinstance(value, Fraction) else Fraction(Decimal(value))
    except (TypeError, ValueError, InvalidOperation, OverflowError) as exc:
        raise ValueError(f"Invalid {name}") from exc
    if result < 0 or (positive and result == 0):
        raise ValueError(f"Invalid {name}")
    return result


@dataclass(frozen=True)
class Instrument:
    holder: str
    principal: Scalar
    cap: Scalar | None = None
    discount: Scalar = "0"
    annual_interest: Scalar = "0"
    years: Scalar = "0"
    kind: str = "safe"

    def terms(self, pre_money: Fraction) -> tuple[Fraction, Fraction]:
        if not isinstance(self.holder, str) or not self.holder or self.holder == "Employee pool":
            raise ValueError("Instrument holder must be named and cannot be Employee pool")
        principal = rational(self.principal, "principal")
        discount = rational(self.discount, "discount")
        rate = rational(self.annual_interest, "interest")
        years = rational(self.years, "years")
        if discount >= 1 or self.kind not in {"safe", "note"}:
            raise ValueError("Discount must be below one; kind must be safe or note")
        if self.kind == "safe" and (rate or years):
            raise ValueError("SAFE inputs cannot accrue interest")
        amount = principal * (1 + rate * years)
        price_numerator = min(pre_money, pre_money * (1 - discount))
        if self.cap is not None:
            price_numerator = min(price_numerator, rational(self.cap, "cap", positive=True))
        return amount, price_numerator


@dataclass(frozen=True)
class Conversion:
    holder: str
    price: Fraction
    units: Fraction
    unconverted_amount: Fraction


@dataclass(frozen=True)
class RoundResult:
    holdings: dict[str, Fraction]
    ownership: dict[str, Fraction]
    round_price: Fraction
    pool_added: Fraction
    pool_fraction: Fraction
    new_investor_units: Fraction
    unallocated_cash: Fraction
    conversions: tuple[Conversion, ...]
    unit: str


def rounded_units(value: Fraction, quantum: Fraction | None) -> Fraction:
    return value if quantum is None else (value // quantum) * quantum


def simulate_round(
    holdings: Mapping[str, Scalar],
    pre_money: Scalar,
    investment: Scalar,
    instruments: Sequence[Instrument] = (),
    pool_target: Scalar = "0",
    pool_timing: str = "pre",
    quantum: Scalar | None = None,
    investor: str = "New investor",
    unit: str = "SPA shares",
) -> RoundResult:
    """Convert simultaneously against frozen capitalization, then issue new money."""
    if unit not in {"SPA shares", "SRL quota units"}:
        raise ValueError("Unit must be SPA shares or SRL quota units")
    if pool_timing not in {"pre", "post"}:
        raise ValueError("Pool timing must be pre or post")
    if not isinstance(investor, str) or not investor or investor == "Employee pool":
        raise ValueError("Invalid investor name")
    owners = {name: rational(value, "holding") for name, value in holdings.items()}
    if any(not isinstance(name, str) or not name for name in owners):
        raise ValueError("Every holder needs a name")
    base = sum(owners.values(), Fraction())
    if not base:
        raise ValueError("Existing units must be positive")
    valuation = rational(pre_money, "pre-money", positive=True)
    cash = rational(investment, "investment")
    target = rational(pool_target, "pool target")
    if target >= 1:
        raise ValueError("Pool target must be below one")
    step = None if quantum is None else rational(quantum, "quantum", positive=True)
    if step and any(value % step for value in owners.values()):
        raise ValueError("Existing holdings must be multiples of quantum")
    terms = [instrument.terms(valuation) for instrument in instruments]
    existing_pool = owners.get("Employee pool", Fraction())
    added = Fraction()
    if pool_timing == "pre":
        factor = 1 + cash / valuation + sum((a / v for a, v in terms), Fraction())
        denominator = 1 - target * factor
        if denominator <= 0:
            raise ValueError("Pool target cannot be reached under this pre-money model")
        added = rounded_units(
            max(Fraction(), (target * factor * base - existing_pool) / denominator), step
        )
    capitalization = base + added
    price = valuation / capitalization
    conversions = []
    for instrument, (amount, numerator) in zip(instruments, terms, strict=True):
        conversion_price = numerator / capitalization
        units = rounded_units(amount / conversion_price, step)
        owners[instrument.holder] = owners.get(instrument.holder, Fraction()) + units
        conversions.append(
            Conversion(
                instrument.holder, conversion_price, units, amount - units * conversion_price
            )
        )
    new_units = rounded_units(cash / price, step)
    owners[investor] = owners.get(investor, Fraction()) + new_units
    if pool_timing == "post":
        subtotal = sum(owners.values(), Fraction())
        added = rounded_units(
            max(Fraction(), (target * subtotal - existing_pool) / (1 - target)), step
        )
    if existing_pool or added:
        owners["Employee pool"] = existing_pool + added
    total = sum(owners.values(), Fraction())
    ownership = {name: units / total for name, units in owners.items()}
    return RoundResult(
        owners,
        ownership,
        price,
        added,
        ownership.get("Employee pool", Fraction()),
        new_units,
        cash - new_units * price,
        tuple(conversions),
        unit,
    )
