# Deployment mix recommendation

Colo vs. owned campus vs. Spark modular — by buyer segment.

Planning judgment for discussion. The supply-demand module does **not** yet emit this table.

## Decision rule

Allocate Crusoe capacity by who takes utilization risk and how fast the MW must be live — not by a single scarcity story.

1. Is the MW signed, reserved, or verbal?
2. Who owns residual utilization if ramp slips?
3. Is power certain on the required date?
4. Is the workload campus-scale training or distributed inference?

Signed + customer-owned utilization + dedicated power → owned.  
Signed + Crusoe-owned utilization + short lead time → Spark or colo.  
Verbal pipeline does not justify a full build.

## Mix

| Buyer segment | Owned campus / full build | Colo / leased MW | Spark modular |
|---|---|---|---|
| **Hyperscaler / campus offtake** (72% of 2026 funding in the public mix; assumed) | **PRIMARY.** Long-tenor offtake (10–15 yr), customer GPUs or dedicated cluster, contracted power. Abilene-class. Build ahead only against signed MW plus a named reserved tranche. | **BRIDGE.** Cover the 18–36 month gap while the campus energizes. Do not make colo the steady-state product for a 200 MW+ training tenant unless the customer wants a landlord, not a factory. | **AVOID as the core.** Wrong primitive for 100 MW+ training. Use only for construction-period inference, remote overflow, or a named edge SKU the contract requires. |
| **Neocloud / reseller / overflow** (16% of 2026 funding; assumed; 100% resale in the public file) | **CONDITIONAL.** Only with a utilization floor or take-or-pay that survives a two-generation GPU slide. Otherwise Crusoe holds residual risk the neocloud will not. | **PRIMARY for speed.** Buy time and location diversity while owned blocks commission. Size colo to contracted GPU-hours, not marketing MW. | **SECONDARY.** Fits multi-site inference POPs. Does not replace a dense training block. |
| **Enterprise / sovereign** (12% of 2026 funding; assumed; self-build treated as outside merchant demand) | **RARE.** Only a sovereign or regulated buyer with a funded campus mandate and visible occupancy. Do not build a full site on an enterprise RFP. | **SECONDARY.** Works when the buyer wants a region, not a factory, and will sign 3–5 years. This is the segment that slips. | **PRIMARY.** Lead time is the product. Matches inference / agentic / on-prem-adjacent demand that dies on a 37–66 month critical path. |

## What flips a cell

- Power late, contract firm → shift the first energization tranche to colo/Spark; do not cancel the campus.
- Contract slips, power firm → stop build-ahead; keep the site option.
- Inference share rises and training offtake is full → raise Spark and small colo; do not add another owned training hall on speculation.
- Neocloud-growth path (to 30% by 2033) raises merchant tightness → more colo + Spark, not more uncontracted owned MW.
- Enterprise/sovereign-growth path (to 26%) looks large in funding terms and small in merchant terms, because that path is mostly self-build.

## Do not do from the public model

Do not put a GW number in these cells yet. Interconnection (60 mo), large-frame generation (66 mo), and transformers (37 mo) are why Spark is a different product, not a cheaper campus. Rebuild on signed MW, reserved MW, and slip by segment before this goes to a CFO.
