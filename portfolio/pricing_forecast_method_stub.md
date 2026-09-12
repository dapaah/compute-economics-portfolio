# Canonical pricing forecast — method stub

How a demand-planning seat would set, revise, and score price. Public inputs only. No Crusoe rate card, no live bookings. The $8.5bn/GW-year and $6.16/H100-hr figures in the registry are inherited proxies, not a forecast.

## Price object

One forecast, four units — never blended.

- Owned campus and colo: $/kW-month (or $/MW-year)
- Spark: $/module-month
- Cloud: $/GPU-hr by SKU

A blended “AI compute price” is how misses get hidden.

## Signals

| Signal (from the JD) | What it does to price | Where it comes from internally | Public-file stand-in (weak) |
|---|---|---|---|
| **Demand volatility** — how unstable the booked ramp is | Higher volatility → shorter tenor, higher $/GPU-hr, tighter utilization floors. Lower volatility → campus $/kW and multi-year discounts. | Bookings revisions, slip, churn, reserved→signed conversion by segment. | Segment-mix paths only. No revision history. Do not price from them. |
| **Ramp timing** — when the MW must be live vs. when power and kits arrive | Customer-early vs. power-late: scarcity premium on Spark and colo, not on a hall that cannot energize. Customer-late vs. power-early: discount or take-or-pay, or you eat utilization. | Contract start vs. interconnection / kit / Spark cycle. Pair with the build-ahead page. | Lead times in the supply module (interconnect 60 mo, large-frame 66, transformers 37). No customer start dates. |
| **Supply-chain constraints** — GPUs, transformers, turbines, interconnection | Constraint on the critical path sets the premium. GPU-short → $/GPU-hr up, campus $/kW unchanged. Transformer-short → campus and colo up, Spark less so if it bypasses that kit. | Allocation and vendor OTIF vs. the deployment plan. Constraint flag is binary per quarter, not a vibe. | Turbine ceiling and topology gates. No GPU allocation series. No transformer GW/year. |
| **Contract quality** — signed / reserved / verbal | Signed locks a band. Reserved gets a hold-price, not the contracted price. Verbal gets no price in the forecast — only a scenario. | CRM / deal desk tags with expiry. Verbal must not write into the canonical path. | Does not exist in the public file. |

## Forecast identity

P̂(product, SKU, quarter) = floor(cost + required margin | utilization) × tightness factor × ramp factor × constraint factor.

- Floor is a cost identity.
- Tightness is deliverable ready-MW vs. signed requested-MW, not announced vs. paper demand.
- Ramp and constraint factors are tabulated, not fitted in public.
- Competitor rate cards are a ceiling check, not the forecast.

## CFO dashboard

| Metric | Definition | Good / watch / miss | Driver split on a miss |
|---|---|---|---|
| **Price MAPE** by product, trailing 4 quarters | mean \|P_realized − P_forecast\| / P_realized. Realized = invoiced blended price for that product/SKU, not list. | Set bands after two scored quarters. Until then publish the number unlabeled. Do not invent a 5% target. | Mix · tightness call · ramp slip · constraint call · competitor move · cost/floor error. |
| **Price bias** (forecast − realized), signed $ | Persistent positive bias = talking the market up. Persistent negative = leaving money in or costing deals. | Sign must flip or shrink within two quarters or the canonical path is wrong, not unlucky. | Same six drivers. Bias that is all “mix” is a product-forecast problem. |

## What this page refuses

It will not print a Crusoe 2027 $/GPU-hr. It will not treat CoreWeave’s published $6.16/H100-hr or an $8.5bn/GW-year proxy as Crusoe’s price. It will not score accuracy on synthetic data and call it forecast skill.

First 90 days internally: tag every live deal signed / reserved / verbal, lock four product units, ship MAPE and bias with a driver split, then put the tightness factor on ready-MW vs. signed-MW. Until those three exist, there is no canonical pricing forecast — only a rate card and a story.
