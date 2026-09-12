# Compute supply and requested-service demand

An aggregate US scenario model of new energized IT capacity, requested-service
cohorts and merchant occupancy. It evaluates conditional capacity gaps; it does
not establish which constraint binds the industry, measure chip shipments, or
prove a shortage. The parameters mix inherited public reporting, estimates and
explicit judgments. Most inherited source attributions have not been reverified.

Open `deliverable_capacity.html` locally for the interactive model. It embeds
the JSON registries and the same JavaScript exercised by parity tests; it requires
no server, network connection or packages in the browser.

## Run and review

Python 3.10+, NumPy and pandas; Node.js is required for parity. From this folder:

```sh
python run_scenarios.py
python run_demand.py
python build_dashboard.py
python -m unittest discover -s tests -v
```

Set `NODE_BINARY` if Node is not on PATH. Drivers resolve files relative to their
own location, so they also work from the repository root. Generated CSVs live in
`outputs/`. Rebuild the HTML after changing either registry, `model.js`, or its
template. The test suite rejects a stale HTML artifact.

## Supply mechanics

Each announcement cohort is allocated once among four mutually exclusive routes,
passed through development and conditional power gates, and scheduled using
`max(component readiness months)`. Milestones run from the same announcement
origin and are treated as parallel. Commissioning is an elapsed milestone that
includes build readiness, not a duration added to the maximum. This simplifying
assumption cannot replace a project dependency schedule.

Base critical paths are grid interconnection (60 months), large-frame generation
(66 months), and transformers for aero generation and new colocation (37 months
each). Shortening aero generation below transformer readiness does not accelerate
delivery. Colocation means a new-build category, not a lease on capacity already
counted under another route.

Fractional-year lead times split converted volume between adjacent calendar years.
After readiness, turbine allocations limit BTM deliveries; undelivered volume
carries forward in a FIFO queue. The turbine range is inherited industry reporting;
US, data-center and aero shares and the generation/IT ratio are assumptions.
This is an illustrative turbine-route ceiling, not a measured whole-system ceiling.
Unused large-frame allocations do not transfer to aero, or vice versa. There is
**no transformer throughput ceiling**, because no defensible transformer GW/year
series is supplied. Transformers constrain lead time only.

Generation queue completion does not measure load-side conversion.
`model.grid_lifetime_conversion_proxy` explicitly labels that transfer as an
assumption. The conditional power gate is `min(1, proxy / development share)`;
the two gates do not multiply the same unconditional completion rate twice.

## Opening cohorts and window boundaries

`model.opening_announcements_gw` supplies an illustrative 2020–25 US backcast.
Only the portion scheduled on or after the reference year enters the run. These
cohorts **replace construction-stock seeding entirely**. Disclosed pipeline and
North America construction stocks remain context; neither is added to the ledger.
Changing those stocks therefore cannot increase output.

Pre-reference energized capacity and equipment backlog are excluded. This is a
material initialization assumption. An explicit announcement mapping passed to
`run()` replaces the entire ledger, including opening cohorts; `{}` produces zero
supply. `include_in_flight=False` excludes default opening cohorts. Opening
sensitivity is exported at 0.5×, 1× and 1.5×; these are not confidence bounds.

The seeded base case removes the previous artificial 2030 dip. It does not
guarantee smooth delivery under other parameters. Real dips and surplus outcomes
are retained. Reports separate opening and forecast cohort deliveries; scheduled
post-horizon volume and ending equipment backlog are separate. A later reporting
slice still simulates queue history from the reference year. The headline delivery
ratio is window-censored, not a lifetime conversion rate or LBNL comparison.

## Demand timing and denominators

Two independent lenses are retained and **never summed**:

1. **Bookings:** the inherited North America H1 absorption figure is treated as a
   signing-flow proxy. An explicit H1 annualization assumption initializes annual
   signing volume; `bookings_us_share` bridges it to the US. Lag weights allocate
   signing cohorts across requested-service years, including pre-window bookings
   and the tail beyond the forecast. `booking_service_cohorts.csv` preserves signing
   year, requested year, allocated GW and window status. `demand_vs_supply.csv`
   compares US requested service with US energized additions. Signed-booking
   columns are context, not same-year delivery demand.
2. **Capital:** estimated company-wide AI capex is divided by a calibrated cost
   per GW, allocated by assumed funding and merchant shares, and bridged to the US
   by `us_capacity_share`. Capital cohorts have their own requested-service lags
   and opening tail. This does not measure chip buyers or shipments.
   `capital_service_cohorts.csv` preserves capital and service years separately.

Signing interpretation, annualization, geographic bridges and lags need compatible
project/customer data to estimate empirically. CBRE primary-market occupancy change
is a third, narrower measure retained only as context. Population differences
remain after geographic alignment: bookings and new capacity may include non-AI
uses; merchant allocation assumes a portion of total supply can serve the AI
merchant lens. A geographic bridge does not prove identical populations or matching.

## Energized, ready, occupied, consumed

Energized GW is new capacity with power available, expressed as IT capacity.
`live_load_weights` is an assumed lag to **readiness for occupancy**, not proof of
consumption. Occupied additions match ready capacity (including spare carryover)
with requested service (including unmet carryover). This occupied-capacity proxy
assumes fungibility across regions, buyers and configurations. Customer-level
matching is absent.

`serviceable_demand.csv` separates energized, ready and occupied additions, unmet
demand, spare ready capacity and energized-but-not-ready capacity. Actual live IT
electrical load and compute utilization are **not estimated**. The segment-mix
report adds an occupancy ratio for modeled ready capacity; this is not GPU activity. Occupied capacity does not
imply full electricity consumption. Existing occupied fleet, retirements and
cancellations are excluded explicitly in the registry; nonzero unsupported settings
fail. Revenue is cumulative incremental occupied GW times an illustrative
revenue/GW-year proxy: a year-end annual run rate, not recognized calendar-year
revenue or contracted sales.

## Evidence and calibration

Model inputs reside in `parameters.json` or `demand_parameters.json`, including
horizons, cohort lags, opening balances, geography, gates and sensitivity/control
ranges. Unit conversions (12 months/year, 1,000 MW/GW), accounting identities and
numerical tolerances are code constants rather than empirical assumptions.

| Kind | Meaning |
|---|---|
| observed | Source-reported historical measurement; verification is separate |
| derived | Arithmetic from named inputs or a documented reported range |
| calibrated | Chosen partly to reconcile an output; not independent evidence |
| assumption | Judgment, estimate, extrapolation, reported forecast or scenario |

Entries carry source, date, URL (null for local judgments), notes and verification
status. Where an inherited figure comes from a company's own disclosure, the
registry keeps that company's name in the key, source or note so the figure stays
traceable. This is a deliberate exception to keeping the module generic. Apart
from the registries and their generated copies (registry CSVs and the dashboard's
registry tables), companies are named only as source attributions. Primary and secondary sources are mixed. Guidance is not a realized
observation. Annual announcement flow is recomputed from its registered quarterly
input and annualization factor. Context such as OEM backlogs and ERCOT snapshots
does not automatically add constraints. ERCOT queue, approval and consumption
snapshots are not a matched-cohort funnel; the former conversion ratio and claimed
regional timing simulation are removed.

Registry CSVs also identify parameters read by the report run. A read can support
a diagnostic or contextual table; it does not necessarily affect the supply curve.

The old calibration was invalid: **9.432 GW is CBRE's year-end primary-market
inventory**, not new US capacity delivered in 2025. This was checked against
[CBRE's February 26, 2026 release](https://www.cbre.com/press-releases/fast-growing-north-american-data-center-market-set-records-in-2025).
`validation_diagnostic.csv` rejects that stock/flow benchmark and makes no historical
accuracy claim. The $35bn/GW cost remains calibrated because the original model
chose it partly against the old supply comparison. It has not been retuned.

`SupplyModel.backtest()` scores supplied **same-year US all-market annual energized
IT additions** against output from a frozen pre-period snapshot. It requires
`snapshot_as_of` before the first scored year and the exact scope identifier
`US_all_new_energized_IT_GW`, rejects missing years, and reports signed/absolute
errors with percentage error undefined for zero observations. Supply an archived
registry with its historical reference year and opening ledger, announcement
vintage, and realized series. The caller must authenticate the archive; the date
argument cannot prove absence of look-ahead. No compatible historical dataset is
supplied here. Synthetic tests verify scoring, not predictive performance.

## Results and limits

See the generated [results snapshot](outputs/results.md) and CSVs. Base bookings
show a gap, while the merchant capital lens clears its initial backlog and
accumulates spare ready capacity. Contrary outputs remain visible. No parameter
is optimized to force a shortage or support a preferred conclusion.

The two lenses answer different questions and diverge in the base case. The
merchant lens is closer to a merchant provider's planning question: does
merchant-owned supply (an assumed 45% of new energized capacity) keep pace with
capital-implied merchant requests? Ready additions cover new requests from 2027.
The bookings lens is the industry aggregate: does all new US energized capacity
keep pace with booking-implied requested service? Base supply stays below it
through 2033 (−26.71 GW in 2026, −16.05 GW in 2033); only the low booking-growth
path crosses, in 2031. A merchant surplus alongside an all-market gap is not a
contradiction, and it does not show merchant providers oversupplied while the
industry is short. The lenses use different demand measures and populations, and
the merchant result depends on assumed supply ownership, US share and cost per GW.

The model does not establish that the binding constraint has moved off chips:
chip supply, water, labor, transmission dependencies and regional compatibility
are absent. It does not prove vertical-integration arbitrage, price pass-through,
customer utilization or a capex bubble. Scenarios are not probability distributions.

Tests cover critical paths, single-cohort conservation, equipment queues, opening
stock exclusion, service timing, geography, occupancy balances, contrary outcomes,
invalid inputs and historical scoring guards. Python/JS parity compares every
supply-detail, annual-summary, demand-comparison and merchant field across base,
boundary and 15 seeded parameter variations.

## Files

| Files | Role |
|---|---|
| `model_core.py`, `supply_model.py`, `demand_model.py` | Registry, cohorts, Python calculations |
| `model.js` | Independent browser/Node calculations |
| `run_scenarios.py`, `run_demand.py` | CSV and result generation |
| `build_dashboard.py`, `dashboard.template.html` | Self-contained HTML generation |
| `parameters.json`, `demand_parameters.json` | Canonical registries |
| `tests/test_hardening.py`, `tests/test_segment_mix.py` | Accounting, regression, funding-mix and parity checks |
| `tests/fixtures/static_mix_serviceable.csv` | Frozen-share regression fixture; not observed data |
| `BUILD_LOG.md`, `DEPLOY.md` | Provenance and local review workflow |


## Dynamic customer funding mix (2026–2033)

`DemandModel(..., mix_scenario="base")` and JavaScript `runDemand(p, supply,
scenario)` use the same registered scenario definitions. The dashboard selector
updates annual funding shares and merchant service/occupation. Python exports all
four scenarios plus `static-control` in one run.

| Path | 2026 H / N / E-S | 2033 H / N / E-S | Classification |
|---|---|---|---|
| base | 72% / 16% / 12% | 68% / 18% / 14% | Assumed modest diversification |
| hyperscaler-heavy | 72% / 16% / 12% | 82% / 10% / 8% | Assumed concentration stress |
| neocloud-growth | 72% / 16% / 12% | 58% / 30% / 12% | Assumed resale-owner growth |
| enterprise-sovereign-growth | 72% / 16% / 12% | 58% / 16% / 26% | Assumed self-build growth |
| static-control | 72% / 16% / 12% | 72% / 16% / 12% | Frozen pre-extension control |

H = hyperscaler; N = neocloud; E-S = enterprise/sovereign. These are **capacity
funding shares**, not end-customer consumption, direct chip purchasing, or observed
customer-segment revenue shares. No observed longitudinal series is available in
the model. Both the inherited opening shares and the new endpoints are assumptions;
intermediate years are derived by linear interpolation. None of the paths is
calibrated or estimated from contracts. The inherited $35bn/GW remains calibrated
and unchanged. No source verification, live contract, renewal, churn, or predictive
accuracy claim is added. Endpoint magnitudes are illustrative scenario judgments;
no probability is attached. Scenario endpoints were specified before running the
new mix scenarios and were not subsequently adjusted to their backlog results.
The original fixed-share model's results were already known.

For year y, total capital is the original 2026 AI-tied hyperscaler capital divided
by the **2026** hyperscaler share, multiplied by the existing aggregate growth
factor to the power y−2026. Each year's shares allocate that fixed aggregate.
We do not hold future hyperscaler capex fixed and divide it by a changing share:
that would confound mix with total market growth. The 2026 capital/TAM snapshot
functions remain available; `capital_by_buyer(calendar_year=2030)` gives an annual
allocation. Unsupported years and malformed shares fail rather than extrapolating
or silently normalizing.

The merchant fraction is H×(1−hyperscaler self-use) + N×neocloud resale +
E-S×enterprise merchant share. Existing defaults are 40%, 100%, and 0%, respectively.
Thus enterprise/sovereign growth means more self-build in this model, not an assumed
increase in enterprises renting from neoclouds. A hyperscaler renting from a
neocloud is not counted again as funding the same physical capacity. Ultimate
consumers remain unidentified; training/inference measures keep their separate
denominators.

Annual merchant capital is converted to GW, US-allocated, and passed through the
existing capital-to-service lag weights. Opening capital, opening balances, supply
ownership share, supply deliveries, readiness ramp, and matching rules stay fixed
across scenarios. This isolates mix sensitivity; supply ownership does not
automatically rebalance to meet demand. Regional and customer compatibility remain
unmodeled, and no segment-specific service queues or revenue yields are invented.

New outputs:

- `customer_segment_mix.csv`: scenario/year/segment shares, capital spending,
  capacity, merchant allocation, US allocation, and evidence classifications.
- `segment_mix_impact.csv`: scenario/year service requests, occupied capacity,
  backlog, spare capacity, merchant provider capital spend, annual revenue
  opportunity, occupancy ratio, and deltas against frozen shares.

Provider capital spend is merchant funding allocated to the US, not provider
operating expense. Requested additions times the inherited revenue/GW-year proxy
is hypothetical annual spending at full occupation of those new requests; it is
not realized spend or a cumulative series. Revenue opportunity uses cumulative
occupied capacity, including prior served cohorts, and remains a year-end annual
run rate. The occupancy ratio is cumulative incremental occupied GW divided by
occupied plus spare ready GW (including opening ready capacity). It is undefined
with no ready capacity and does not measure GPU utilization or electricity demand.

The merchant crossover is the first year ready additions cover new requested
service; backlog-clear year separately accounts for carryover. First crossing
does not guarantee sustained coverage. The all-market bookings comparison is an
independent lens and remains unchanged. See `outputs/results.md` for all dates.

Within these assumed paths, funding mix changes the size of the merchant surplus
but not its sign or first-year timing. Backlog first clears in 2029 (2028 under
enterprise/sovereign growth). Ready additions first cover new requests in 2027
and stay above them through 2033 in every path. Ending spare ready capacity
ranges from 10.92 GW (neocloud growth) to 20.67 GW (enterprise/sovereign growth),
against 16.77 GW frozen. The base path moves it only to 16.49 GW (−1.7%), largely
by construction: its 2033 merchant fraction is 45.2% versus 44.8% frozen, because
the hyperscaler decline (40% merchant) is nearly offset by neocloud growth (100%
merchant). The base comparison mainly shows the wiring is live; the four-path
range is the sensitivity test. Supply, aggregate growth, supply ownership,
geography and cost per GW stay fixed, and no probability is attached. Those fixed
inputs matter more than mix: in `merchant_sensitivity.csv` (base mix), $25bn/GW
at a 70% US share leaves 7.13 GW of merchant requests unmet in 2033, and a 90% US
share at $35bn/GW leaves 0.38 GW.
Regression tests compare the frozen control with a captured pre-extension output;
scenario tests cover monotonic paths, constant aggregate capital, service lags,
accounting conservation, zero supply, reporting slices, and invalid inputs.
Python/JS parity also covers all scenarios with normal and zero supply and seeded
parameter variations. The fixture is not observed data or a target for fitting.


## Connection to the site capital engine

The [macro/site reconciliation](../model_06_datacenter_capital_forecasting/ALIGNMENT.md)
compares cost scope and announcement-to-power timing with the synthetic site plan.
It exposes differences without retuning macro costs or claiming an identified site
mapping to national opening cohorts.


## Alternative BTM topology

`model.supply_topologies` separates the unchanged base from `alternative-btm`.
The alternative excludes HV substation transformer and GSU procurement from only
`btm_aeroderivative`. This is an unverified equipment-scope assumption: it assumes
those procurement milestones are unnecessary and other electrical readiness is
covered by the retained switchgear, site, fit-out and commissioning milestones.
It is not evidence that transformers are unnecessary in BTM projects generally.
No engineering feasibility, equipment availability, cost savings or economic
arbitrage is established. No alternative equipment cost is supplied.

Readiness remains the maximum of included components, giving 27 months for aero
under current inputs versus 37 in the base. Increasing any retained milestone can
remove that advantage. Pathway shares, conversion gates and separate turbine
ceilings are unchanged. The scenario replaces the aero topology; it adds no fifth
route. Grid, large-frame and new-build colocation retain their original mapping.
Opening announcement volumes remain fixed; changing readiness can move some
opening-cohort deliveries before the reporting window, so horizon totals alone
are not a measure of acceleration. Compare with opening cohorts disabled as well.

Select supply topology independently of funding mix in the dashboard. Python uses
`SupplyModel.run(scenario="alternative-btm")`; JavaScript uses the same scenario
option. `topology_components.csv` reports included readiness milestones and
`topology_supply_comparison.csv` reports annual supply. Existing reports and the
model_06 schedule reconciliation continue to use the base topology.
