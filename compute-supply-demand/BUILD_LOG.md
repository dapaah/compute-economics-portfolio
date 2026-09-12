# Hardening record — 2026-09-07

The portfolio checkout did not contain `compute-supply-demand`. It was imported
from the local `compute portfolio extension` folder used in the earlier task.
That task was interrupted after partial Python changes; HTML, README and build
narrative still described the original model. The source folder was read but not
modified by this task. This Git diff therefore shows a new module, not a tracked
before/after revision of its original source files.

Earlier partial work supplied max-based pathways and illustrative opening cohorts.
This pass audited those changes, completed the registry and service cohort
ledgers, clarified readiness versus occupied capacity, and replaced the stale
browser implementation and documentation. The calibrated $35bn/GW and opening
volumes were retained, not optimized against a shortage. Sensitivities preserve
contrary outputs.

The original 9.432 GW delivery benchmark is actually CBRE primary-market year-end
inventory. It is rejected. No substitute national historical flow was invented.
The scoring API supports frozen historical snapshots and same-year observations;
current data do not establish a backtest. Other inherited sources are largely
unverified, as marked in the registry.

Bookings and capital are separate demand lenses with US bridges and service lags.
Opening announcements replace construction stock; opening booking/capital cohorts
are demand, never extra supply. Equipment and demand backlogs carry independently.
The merchant base case clears backlog and develops spare capacity; this remains
visible.

The HTML embeds canonical registries and tested JavaScript. Parity exercises
numerical fields and boundary scenarios; the generated-file check prevents browser
artifact drift. No commit or push is part of this workflow.


## 2026-09-10 — Dynamic customer funding mix

Extended the existing local working tree without committing, pushing, or changing
the pre-existing Git index. Added four explicit annual 2026–2033 funding-share
paths and a frozen-share regression control. All new endpoints are assumptions;
annual interpolation is derived. No paths were fitted to a preferred conclusion,
backlog clearance, or a supply shortage. Existing source claims were not promoted
to verified evidence, and the inherited calibrated cost/GW was retained.

Aggregate capital growth is common across paths. Mix changes merchant investment
and capital-implied service cohorts, flowing into occupancy, unmet demand, spare
capacity, and annual revenue opportunity. Buyer funding stays distinct from
consumer usage. No contract, churn, customer-specific allocation, or actual GPU
utilization data were invented. Added annual mix/impact CSVs, dashboard selection,
documented denominators, and regression/behavior/parity tests.

The pre-extension merchant backlog cleared in 2029. The new base, hyperscaler-heavy,
and neocloud-growth paths also clear in 2029; enterprise/sovereign growth clears in
2028 because its assumed self-build share reduces merchant requests. Merchant
ready-additions/requested-service crossover remains 2027 in every path. The
independent all-market base bookings lens has no crossover through 2033 and is
unaffected. Base ending spare capacity changes from 16.77 to 16.49 GW. These
conditional results are retained, including spare capacity in every scenario.


Verification: all 45 tests passed across `compute-supply-demand/tests` and
`model_06_datacenter_capital_forecasting/tests` using pytest, including the latter's
function-based tests. Supply/demand alone has 22 passing tests. Numerical parity
covers 30 cases: five original supply boundaries, ten scenario/supply combinations,
and fifteen seeded parameter variations, including all annual funding shares and
merchant fields. Missing test libraries were installed in an isolated task folder,
outside the repository; project dependencies and other models were not edited.
Both report drivers and the dashboard builder completed. The generated HTML
consistency test passed. Visual browser inspection was unavailable because browser
policy blocked the local file URL; no visual-verification claim is made.
`git diff --check` and the cached-diff check passed. No commit or push was made.


## 2026-09-10 — Verification pass

Re-checked the funding-mix change without editing model code, registries, tests
or generated outputs. The registry stores 2033 endpoints, not eight annual values;
annual shares are derived at run time. Every varying segment takes eight distinct
values, and each year sums to one within 2.2e-16. Base and frozen control differ
by 0.28 GW of ending spare capacity because the base merchant fraction barely
moves (44.8% to 45.2%). The other paths range from 10.92 to 20.67 GW.

Parity used the JavaScript and registries embedded in the shipped HTML. Supply
fields are bitwise identical. Demand fields agree within 1.2e-13 GW; the residual
differences come from floating-point operation order. All 22 module tests passed
with Node 24 supplied through `NODE_BINARY`. Without Node, the two parity tests
fail as designed. Regenerated CSVs, `results.md` and HTML were byte-identical to
the shipped files. README now states the mix-sensitivity result and the
merchant/all-market lens distinction. No commit or push was made.

Follow-up: the dashboard's funding-mix note stated merchant allocations as fixed
text (40% / 100% / 0%). It now reads the three deployment-mode shares from the
embedded demand registry, and the HTML was rebuilt. The rejected 9.432 GW
benchmark was also written as fixed text in the dashboard, the `validate()` reason
and the `results.md` note. All three now read
`validation.cbre_primary_inventory_2025_gw`. Regenerated outputs were
byte-identical to the shipped files.

Named companies in the registries were kept for source traceability; README
now documents that exception. The earlier model_06 test run had rewritten
`site_summary.csv` with float noise (about 1e-13 in IRR columns); that file was
reverted to its committed version.


## Macro/site alignment and financing correction

Added executable cost-scope and conditional announcement-to-power reconciliation
tables in model_06; see its ALIGNMENT.md. Macro parameters and outputs remain
unchanged. Corrected site project cash flows to use taxes before interest and to
deduct maintenance consistently. Financing cash flows retain their interest tax
shields. The fixed 12% project hurdle is distinguished from optional, currently
unset sponsor hurdles. All 55 tests passed, including macro Python/JS parity;
all affected model_06 outputs and executive artifacts were regenerated. No commit,
push, or change to the pre-existing staged index was made by this task.

Follow-up: the root README findings and the GitHub Pages copy in `docs/` now use
the corrected model_06 outputs. `test_alignment.py` now imports from its own module
folder, so both suites can be collected together. ALIGNMENT.md states how grants
and customer prepayments are treated.


## 2026-09-11 — Alternative BTM topology

Added a registry-defined conditional aero equipment exclusion scenario, mirrored
in Python and JavaScript, with separate dashboard selection and component/supply
exports. Base topology remains unchanged. Alternative feasibility is unverified;
no cost or arbitrage claim follows from its shorter modeled readiness.
