# AI Infrastructure Finance Portfolio

Demand, deliverable capacity, deployment mix, and the financial case behind build-ahead.

This repository is a public practice ground for the planning problem a vertically integrated AI infrastructure company actually faces:

**how much demand is signed → how much capacity can be energized, made ready, and occupied → which mix of colo / owned / modular to fund → what price and capital case finance can defend.**

> **Data standard.** Models 1–6 use seeded synthetic data. The compute supply-demand module mixes inherited public reporting with explicit assumptions. No confidential company information is used. Modeled outputs are not operating results and are not a Crusoe forecast.

## Start here

Planning pages first. Token notebooks last.

1. **[Deployment mix](portfolio/deployment_mix_recommendation.md)** — colo vs. owned campus vs. modular (Spark-class) by buyer segment. What funds, what waits.
2. **[Build-ahead vs. build-to-order](portfolio/build_ahead_vs_build_to_order.md)** — signed / reserved / verbal × the same three modes. Verbal is a forecast line, not a capital object.
3. **[Pricing forecast method](portfolio/pricing_forecast_method_stub.md)** — four price units; tightness, ramp, and constraint as named signals; MAPE and bias with a driver split. No invented rate card.
4. **[Compute supply and requested-service demand](compute-supply-demand/README.md)** — announced MW versus deliverable IT capacity; bookings vs. merchant-capital lenses; segment mix. Open `compute-supply-demand/deliverable_capacity.html` locally.
5. **[Demand-planning brief](portfolio/demand_planning_brief.md)** — what the public model will and will not claim.
6. **[Datacenter capital engine (Model 6)](model_06_datacenter_capital_forecasting/README.md)** — site pipeline → power and construction gates → GPU deployment → CapEx, liquidity, scenarios.
7. **[Static executive dashboard](https://dapaah.github.io/compute-economics-portfolio/)** — GitHub Pages view of Model 6.
8. **Models 1–5** — token, inference, cache, usage-to-GPU, and allocation economics. Product-margin machinery. Not the primary planning artifact.

## What maps to a demand-planning and market-economics seat

| Planning question | Where it lives | What is not claimed |
|---|---|---|
| Which deployment mix should we fund by segment? | `portfolio/deployment_mix_recommendation.md` | A Crusoe site list |
| When is build-ahead justified vs. wait for a signature? | `portfolio/build_ahead_vs_build_to_order.md` | A live bookings file |
| How is the canonical price set and scored? | `portfolio/pricing_forecast_method_stub.md` | A 2027 $/GPU-hr |
| Who is buying compute, and how is the mix shifting? | `compute-supply-demand/` segment-mix paths | Observed customer contracts |
| Is announced data-center and power supply actually deliverable? | `compute-supply-demand/` announcement → energized / ready / occupied | A measured industry shortage |
| What financial case sits behind a site? | Model 6 | A live campus portfolio |

## How to run

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

## Evidence standard

Every public claim should trace to executed code, a labeled input, an output table, a chart, or an executive brief. Parameters are classified as observed, derived, calibrated, or assumed. Contrary outputs are retained. No parameter is optimized to force a shortage thesis. The three planning pages are methods. They are not Crusoe operating results.
