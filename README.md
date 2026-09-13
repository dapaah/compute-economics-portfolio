# AI Infrastructure Economics & Financial Architecture

Demand, deliverable capacity, deployment strategy, pricing, and the capital case behind build-ahead.

This repository is a public research and decision-systems portfolio focused on the planning problem faced by capital-intensive AI infrastructure operators:

**how much demand is real → how much capacity can actually be energized, made ready, and occupied → which deployment path should be funded → what pricing and capital case finance can defend.**

The models connect:

**AI workload demand → GPU capacity → datacenter and power deliverability → deployment choice → pricing → utilization → capital allocation → returns.**

> **Data standard.** Models 1–6 use seeded synthetic data. The compute supply-demand module uses public industry data, derived values, calibrated parameters, and explicit assumptions. No confidential company information is used. Modeled outputs are not operating results and are not forecasts for any specific company.

## Current findings

- Merchant backlog clears in **2029** in the current base case; spare merchant capacity emerges thereafter.
- An enterprise/sovereign-growth scenario clears backlog in **2028**; other segment-mix scenarios remain at 2029.
- Merchant supply/request crossover occurs in **2027**, while the separate all-market base case remains constrained through **2033**.
- Announced capacity is not treated as usable supply: the model distinguishes energized, ready, and occupied capacity.
- The model does not assume permanent scarcity. Contrary outputs are retained rather than calibrated away.

These are model outputs, not market facts. The purpose of the system is to make the assumptions and physical constraints visible enough to challenge.

## How to read this repository

The default path is AI infrastructure planning. The objects underneath — demand quality, deliverable capacity, utilization, price, cash, and whether to buy ahead of contracted demand — also apply to other owned-compute businesses. The public dataset is GPU/MW. The units are not the claim.

**Path A — AI infrastructure planning** (demand, deliverability, deployment mix, pricing method, capital case)

1. [Demand-planning brief](portfolio/demand_planning_brief.md)
2. [Compute supply and requested-service demand](compute-supply-demand/README.md)
3. [Deployment mix](portfolio/deployment_mix_recommendation.md)
4. [Pricing forecast method](portfolio/pricing_forecast_method_stub.md)
5. [Build-ahead vs. build-to-order](portfolio/build_ahead_vs_build_to_order.md)
6. [Datacenter capital engine (Model 6)](model_06_datacenter_capital_forecasting/README.md)

**Path B — owned-fleet / consumption compute** (when to add machines, what a unit of compute should cost, how the buy is financed)

The repo does not model a CI product, a runner rate card, or any company's live fleet. Read the decision system, not the GPU labels:

1. [Build-ahead vs. build-to-order](portfolio/build_ahead_vs_build_to_order.md) — signed / reserved / verbal demand versus capital commitment
2. [Pricing forecast method](portfolio/pricing_forecast_method_stub.md) — price units, tightness, scoring; no invented rate card
3. [Datacenter capital engine (Model 6)](model_06_datacenter_capital_forecasting/README.md) — capacity → CapEx / cash / financing structure / returns
4. 4. [Models 1–5](models/) — usage, utilization, and unit-cost layer

## Start here

Planning pages first. Token notebooks last.Path A is the default order below.

1. **[Deployment mix](portfolio/deployment_mix_recommendation.md)** — colo vs. owned campus vs. modular infrastructure by buyer segment. What funds, what waits.
2. **[Build-ahead vs. build-to-order](portfolio/build_ahead_vs_build_to_order.md)** — signed / reserved / verbal demand × deployment mode. Verbal demand is a forecast input, not a capital commitment.
3. **[Pricing forecast method](portfolio/pricing_forecast_method_stub.md)** — price units, demand tightness, ramp timing, supply constraints, forecast scoring, MAPE, bias, and driver attribution. No invented rate card.
4. **[Compute supply and requested-service demand](compute-supply-demand/README.md)** — announced MW versus deliverable IT capacity; requested-service cohorts; buyer/consumer mix; energized / ready / occupied capacity.
5. **[Demand-planning brief](portfolio/demand_planning_brief.md)** — what the public model can and cannot claim.
6. **[Datacenter capital engine (Model 6)](model_06_datacenter_capital_forecasting/README.md)** — site pipeline → power and construction gates → GPU deployment → CapEx, liquidity, scenarios, capital stack, and returns.
7. **[Static executive dashboard](https://dapaah.github.io/compute-economics-portfolio/)** — GitHub Pages view of Model 6.
8. **[Models 1–5](models/)** — token, inference, cache, usage-to-GPU, and capacity-allocation economics. These are the product-margin layer, not the primary infrastructure-planning artifact.

## Planning questions the portfolio answers

| Planning question | Where it lives | What is not claimed |
|---|---|---|
| Who funds/buys capacity, who consumes compute, and how is segment mix shifting? | `compute-supply-demand/` | Observed customer contracts |
| Can announced datacenter and power capacity actually be delivered? | `compute-supply-demand/` | A measured industry shortage |
| Which deployment path should be funded by demand profile? | `portfolio/deployment_mix_recommendation.md` | A live site portfolio |
| When is build-ahead justified versus waiting for contracted demand? | `portfolio/build_ahead_vs_build_to_order.md` | A live bookings file |
| How should pricing be forecast and scored? | `portfolio/pricing_forecast_method_stub.md` | A current market rate card |
| What financial case sits behind a site or portfolio? | Model 6 | A live campus portfolio |

## System architecture

The portfolio is organized around three linked questions.

### 1. What is the demand?

The demand side separates the population that funds or buys infrastructure capacity from the population that consumes compute.

It models:

- hyperscaler, neocloud, and enterprise/sovereign funding paths
- workload and token-demand growth
- training vs. inference mix
- changing segment mix over time
- merchant-addressable demand
- provider spend and revenue opportunity
- utilization, backlog, and spare capacity

### 2. Can the infrastructure physically deliver it?

The supply side distinguishes announced capacity from capacity that can actually become revenue-bearing infrastructure:

**announcement → development → interconnection / power → equipment → energized → ready → occupied**

The model treats physical constraints explicitly rather than assuming announced MW become usable capacity on schedule.

### 3. Where should capital be deployed?

The capital layer connects demand and deliverability to:

- deployment mode
- build-ahead vs. build-to-order
- CapEx / OpEx / cash
- liquidity
- financing structure
- project returns
- pricing
- scenario and sensitivity analysis

## Evidence standard

Every material public claim should trace to executed code, a labeled parameter, a source registry, an output table, a chart, or an executive decision brief.

Parameters are classified as **observed · derived · calibrated · assumed**.

Contrary outputs are retained. No parameter is optimized to force a shortage thesis, a particular investment conclusion, or a specific employer narrative.

Methods are separated from operating claims. Public-data models are not presented as substitutes for live customer contracts, proprietary site ledgers, or production fleet data.

## How to run

Install dependencies and generate the original data pipeline:

```bash
python -m pip install -r requirements.txt
python data/generate_data.py
python pipeline/ingest.py
```

Supply-demand module:

```bash
cd compute-supply-demand
python run_scenarios.py
python run_demand.py
python build_dashboard.py
python -m unittest discover -s tests -v
```

Model 6:

```bash
cd model_06_datacenter_capital_forecasting
python -m pip install -r requirements.txt
python run_model.py
python run_phase2.py
python run_phase3.py
python run_phase4.py
python -m unittest discover -s tests -p "test_*.py"
```

## What this repository demonstrates

This is not a claim of prior datacenter operating ownership.

It is a public, executable demonstration of the analytical system used to think about AI infrastructure:

**demand → physical capacity → deployment → pricing → capital allocation → returns.**
