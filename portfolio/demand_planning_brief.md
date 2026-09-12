# Demand, deliverable capacity, and mix — executive note

Synthetic / public-input portfolio. Not a Crusoe forecast. Not an industry proof.

## The planning objects

Treat four objects as distinct. Do not add them together.

1. **Paper demand** — announced MW, marketed pipeline, capital-implied GW.
2. **Requested service** — bookings or capital converted through a lag into the year capacity is actually wanted.
3. **Deliverable capacity** — announcement cohorts that clear development, interconnection, equipment, energization, readiness, and occupancy gates.
4. **Addressable merchant demand** — the slice of (2) that a non-hyperscaler owner can serve, after self-build and self-use.

A market that is “short” on paper demand can still be long merchant ready capacity, or the reverse. Both statements can be true at once because the populations differ.

## What the current base case produces

Under the registered assumptions — not as a prediction:

- All-market bookings stay above new US energized additions through the window (gap of roughly 27 GW in 2026 and 16 GW in 2033 in the base bookings lens).
- The merchant-capital lens clears its initial backlog in 2029 and then accumulates spare ready capacity.
- Funding-mix paths (hyperscaler-heavy, neocloud growth, enterprise/sovereign self-build) change the size of that merchant surplus. They do not flip its sign in the current wiring, because supply ownership, US share, and $/GW are held fixed.

Those two lenses are kept visible on purpose. A planning system that forces them to agree is no longer a planning system.

## What would change the recommendation

A Crusoe-internal version of this model should be rebuilt around deal-level objects the public file does not have:

- signed MW, reserved MW, and verbal pipeline, separately;
- renewal, churn, and slip by segment;
- product mix across cloud, colo, owned campus, and Spark modular;
- interconnection and equipment queues that are site-specific, not national averages;
- a pricing forecast whose accuracy is scored each quarter.

Until those exist, the public model can only show the *shape* of the decision: tightness is not the same as addressable tightness, and announced GW is not a build signal.

## Deployment mix (the missing output on purpose)

Colo vs. owned vs. Spark is a function of ramp speed, contract tenor, power certainty, and who owns the residual utilization risk.

- **Hyperscaler training / campus offtake:** owned or dedicated campus when power and tenor are contracted; colo only as a bridge.
- **Neocloud / reseller:** owned or leased blocks sized to contracted utilization floors; Spark is usually the wrong primitive at that scale.
- **Enterprise / inference / edge:** Spark and smaller colo nodes win on lead time; full builds win only where occupancy is already visible.

The public file does not yet emit that recommendation as a table. That is the next artifact, and it should be driven by segment + ramp + power-certainty flags, not by a single scarcity narrative.

## Limits

The model does not measure chip shipments, water, labor, or regional compatibility. Occupied GW is a matching proxy, not live IT load. Scenarios are not probabilities. Revenue-opportunity dollars are a run-rate sketch, not recognized sales. Read the registries before quoting a number.
