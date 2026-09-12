# Build-ahead vs. build-to-order

The same three deployment modes, cut by contract quality rather than by buyer.

Planning judgment. The public model does not yet score bookings as signed / reserved / verbal.

## Capital rule

Build-ahead puts steel, power, and GPUs at risk before offtake is fully firm. Build-to-order waits on a signed MW or GPU-hour contract. Reserved is the only band where a limited, reversible ahead-spend is allowed. Verbal pipeline funds origination and site options, not campuses. If power is the long pole, the option you buy early is interconnection and land — not a hall full of GPUs.

## Mix

| Demand object | Owned campus / full build | Colo / leased MW | Spark modular |
|---|---|---|---|
| **Signed** — contracted MW or GPU-hours, termination and utilization language that survives a slip. Only this object can pull a full build. | **Build-to-order, then limited ahead.** Commit the campus against signed MW. Add a named reserved tranche only if power lead time exceeds contract start and the customer has a documented expansion option. No second hall on the same signature. | **Build-to-order.** Lease the gap between signature and energization. Exit colo as owned MW comes online unless the customer wants multi-region diversity as a standing product. | **Build-to-order.** Deploy modules against the signed start date for inference, edge, or a construction-period bridge. Do not pre-position a Spark fleet against a campus contract that has not asked for it. |
| **Reserved** — written option, LOI with a deposit, or allocation hold. Expires. Converts to signed or dies. Only build-ahead band. | **Narrow ahead.** Spend only on items that keep option value if the reserve dies: land, interconnection queue position, long-lead electrical. Not GPUs. Not a poured hall. Cap ahead-spend to the deposit plus a board-set ceiling. | **Preferred ahead vehicle.** A colo hold or short lease is reversible. Protects a start date without owning residual utilization if the reserve expires. | **Small ahead.** Factory slots and a thin finished-goods buffer only if lead time is inside Spark’s cycle and the reserve has a drop-dead date. No speculative yard of modules. |
| **Verbal** — pipeline, RFP, banker tour, “we will need 200 MW.” Forecast input with a haircut. Not a demand object. | **Do not build.** No campus, no GPU PO, no generation commitment. Origination and site screening only. If this number is in the long-range plan, it sits in a separate, non-capital column. | **Do not hold MW.** A colo reservation against a verbal is how merchant capacity gets stranded. Broker conversation, not a deposit. | **Do not pre-build.** Spark’s short cycle is why you can wait. Verbal demand sizes the sales motion and flexible factory capacity — not this quarter’s production release. |

## Portfolio test

Build-ahead is justified only when the cost of missing a signed start date exceeds the cost of a dead reserve.

- (a) cash at risk if the reserve dies
- (b) revenue and contractual delay damages if you are late on signed MW
- (c) alternative use of the asset (another tenant, Spark redeploy, colo release)

If (a) > (b) − (c), you are speculating. GPU generation risk makes (c) decay fast on owned halls and slowly on Spark, which is why reserved-band ahead-spend prefers colo and interconnection over GPUs.

## What this page refuses

It will not assign a percentage of a 40 GW-class pipeline to build-ahead. Announced pipeline is not reserved MW. The public bookings lens is a signing-flow proxy, not a contract-quality stack. Until internal bookings are tagged signed / reserved / verbal with expiry dates, any “build 30% ahead” rule is a slogan.

Pair with the segment mix page: a signed hyperscaler campus is owned; a reserved neocloud block is colo; a verbal enterprise RFP is a forecast line only.
