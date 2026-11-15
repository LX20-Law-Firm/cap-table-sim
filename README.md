# cap-table-sim

Pure Python arithmetic for successive funding rounds, SAFE and convertible note
conversion, and employee pool additions. Includes an offline HTML calculator in
`docs/index.html`. Units can be labelled `SRL quota units` or `SPA shares`; labels
do not change the calculation or encode corporate rules.

## Run

Requires Python 3.11 or later. No runtime dependencies.

```sh
python -m pip install -e '.[dev]'
python -m unittest discover -s tests -v
ruff check .
ruff format --check .
node --test tests/*.test.cjs
```

Open `docs/index.html` directly in a browser. It uses local assets and JavaScript
BigInt rational arithmetic, without network requests or storage. Inputs are editable
JSON; exact fractional outputs such as `1/5` mean 20% for ownership fields.

```python
from cap_table_sim.core import Instrument, simulate_round

result = simulate_round(
    holdings={"Founder": 1000},
    pre_money=10000,
    investment=2000,
    instruments=[
        Instrument("SAFE holder", 1000, cap=5000, discount="0.2"),
        Instrument(
            "Note holder", 1000, discount="0.2", annual_interest="0.1", years=2, kind="note"
        ),
    ],
    pool_target="0.2",
    pool_timing="pre",
    unit="SPA shares",
)
print(result.holdings)
print(result.ownership)
next_round = simulate_round(result.holdings, 20000, 5000, investor="Next investor")
```

`examples.json` contains the same synthetic input. Monetary values use one currency.
Python accepts integers, decimal strings, `Decimal` or `Fraction`, and rejects floats.
Browser inputs accept decimal strings or safe integers. Python outputs `Fraction`
values; browser outputs are exact fraction strings. Rates and ownership are fractions.

## Conversion convention

This is an explicit **pre-money cap** model. The capitalization denominator is
existing fully diluted units plus any pool added before pricing. Existing reserved
pool units belong in holdings under the reserved name `Employee pool`.
All instruments convert simultaneously against that denominator; converted units
and new cash units are excluded from it. Input order has no effect on units issued.
Multiple instruments may share a holder and are aggregated in final holdings.

Let `V` be pre-money valuation, `I` new cash, `B` existing fully diluted units,
`P` newly added pool units and `S` pricing capitalization.

- Priced round: `price = V / S`; new investor units = `I / price`.
- SAFE amount: principal, without interest.
- Note amount: `A = principal * (1 + annual_interest * years)`, using simple interest.
- Conversion price: `min(V / S, cap / S, (V / S) * (1 - discount))`.
- Omit the cap term when no cap is supplied. Discount defaults to zero.
- Conversion units: `A / conversion_price`.

Cap and discount are alternatives: the lower price applies. They are not multiplied.
This convention does not implement post-money SAFEs, contractual capitalization
exceptions, maturity, repayment, preferences or voting rights. No instrument terms
or unit granularity are selected by the package.

## Employee pool

`pool_target` is the desired pool fraction **after** conversion and new cash.
A target of zero adds no units. The model never removes an existing pool.

For a pre-money pool, set `K = sum(A_i / min(V, cap_i, V*(1-discount_i)))`
and `F = 1 + I/V + K`. Without rounding:

```text
P = max(0, (target * F * B - existing_pool) / (1 - target * F))
S = B + P
```

The target is unreachable if `1 - target * F <= 0`; the function rejects it.
For a post-money pool, price and convert using `S = B`. Let `T` be total units after
conversions and new cash, including the existing pool:

```text
P = max(0, (target * T - existing_pool) / (1 - target))
```

For 1,000 founder units, pre-money 10,000, cash 2,500 and target 20%, the pre-money
pool adds `1000/3` units, the round price is `15/2`, and new cash owns 20%.
The post-money pool adds `625/2` units, the price is 10, and new cash owns 16%.
Both pools own 20%.

## Rounding and edge cases

`quantum=None` retains exact rational units. A positive quantum rounds each issuance
down to that increment. Choose a quantum explicitly when whole or fractional units
are required. Existing holdings must already be multiples of that quantum.

For pre-money pools, solve the exact target first, round added pool units down,
then freeze capitalization and round each conversion and cash issuance separately.
For post-money pools, round conversion and cash issuances first, then compute and
round the pool addition. Rounding can move actual pool ownership away from the
requested target. `pool_fraction` reports the achieved result; the target is not
silently claimed as achieved.

`unallocated_cash` and each conversion's `unconverted_amount` report arithmetic
residuals. The model does not assign a disposition to them.
For three existing units, valuation 10, cash 1 and quantum 1, no new unit is issued
and unallocated cash is 1. With quantum `0.01`, new cash receives `3/10` of a unit.

Tests cover sequential rounds, cap versus discount, simultaneous conversions,
simple interest, existing pools, pool additions during rounds, exact ownership
conservation, fractional units, residuals and unreachable targets.

## License and citation

Code: [Apache-2.0](LICENSE). Original example data: [CC BY 4.0](LICENSE-DATA).
Citation metadata: [CITATION.cff](CITATION.cff) and [.zenodo.json](.zenodo.json).
Repository: [LX20-Law-Firm/cap-table-sim](https://github.com/LX20-Law-Firm/cap-table-sim).
