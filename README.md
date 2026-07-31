# AI Infrastructure Finance Portfolio

A synthetic, end-to-end body of work exploring the financial architecture required to deploy AI infrastructure at scale—from product demand and GPU economics through datacenter delivery, capital allocation, financing, liquidity, risk, and executive decision support.

> **Portfolio thesis:** AI infrastructure finance is a connected operating system linking product demand → token demand → GPU capacity → power and datacenter requirements → deployment milestones → CapEx and OpEx → financing and liquidity → returns and executive decisions.
>
> **Data:** 100% synthetic, seeded, and reproducible. No confidential company information is used.

## Start here

- **[Open the executive dashboard](https://dapaah.github.io/compute-economics-portfolio/)** — static, zero-install CFO view published through GitHub Pages after deployment.
- **[Run the interactive Streamlit dashboard](model_06_datacenter_capital_forecasting/dashboard/app.py)** — scenario, site, capital-stack, liquidity, and risk exploration.
- **[Read the executive brief](model_06_datacenter_capital_forecasting/data/outputs/dashboard/executive_brief.md)** — concise decision narrative.
- **[Review Model 6](model_06_datacenter_capital_forecasting/README.md)** — assumptions, calculation architecture, tests, and outputs.
- **[Review the original compute capstone](portfolio/executive_brief.pdf)** — one-page Board-ready brief for Models 1–5.

## Portfolio architecture

### Layer 1 — Compute Economics

Five linked models connect product behavior to compute cost, capacity, and margin:

| # | Model | Question answered | Headline insight |
|---|---|---|---|
| 1 | **Token Economics** | How throughput and token mix drive cost per token and margin | ProductC runs ~17% above blended cost per 1K output tokens; cost is ~75% compute / 15% overhead / 10% power. |
| 2 | **Inference Economics** | Where latency, throughput, and margin optimize | Raising interactive batch 3 → 14 cuts cost/inference ~39% but adds ~72 ms latency; the margin-optimal batch under a 150 ms SLO is 16. |
| 3 | **Cache Modeling** | What cache optimization is worth | Each +10 points of cache-hit rate cuts effective cost/inference ~11.8%—≈ $2.3M/yr at a representative 1B inferences/day. |
| 4 | **Demand Forecasting** | How usage growth becomes GPU and capital requirements | Demand compounds ~2.4×/yr; fleet scales ~1,260 → ~1,985 GPUs by Q4 (base), requiring ≈ $22M of CapEx. |
| 5 | **Capacity Allocation** | How workload mix and utilization affect margin | Interactive earns ~47% more margin per GPU-second; the binding lever is utilization toward ~85%. |

**Compute capstone:** cost → cache → demand → allocation → margin.

### Layer 2 — Datacenter Capital Forecasting

`model_06_datacenter_capital_forecasting/` extends the portfolio from GPU operating economics into physical infrastructure deployment and capital architecture.

It connects:

**Site pipeline → power and construction milestones → GPU deployment → monthly CapEx and OpEx → funding and liquidity → scenario risk → capital structure → NPV / IRR / ROIC → executive decisions.**

The current prototype includes:

- three synthetic datacenter sites and a 60-month monthly forecast;
- milestone-driven construction and commissioning logic;
- power-ready and ready-for-service gates;
- phased GPU deployment and utilization ramps;
- revenue, OpEx, cash flow, liquidity, NPV, IRR, and ROIC;
- base, upside, downside, and severe-downside scenarios;
- seeded Monte Carlo completion, cost, liquidity, and return risk;
- five capital-stack alternatives with dilution, CADS, DSCR, debt service, and equity-return tradeoffs;
- a static executive dashboard, Streamlit app, KPI export, and executive brief;
- 14 automated validation tests.

## Executive findings from Model 6

The illustrative base case deploys **39,000 GPUs** and **195 MW** of IT load against **$4.345B** of CapEx, producing approximately **$1.00B of unlevered NPV** while requiring **$248M of incremental liquidity support**.

The risk-adjusted picture is more demanding:

- Monte Carlo median NPV: **$(101)M**
- Probability of positive NPV: **40.6%**
- Downside incremental funding need: **$634M**
- Severe-downside incremental funding need: **$969M**

The model identifies **utilization ramp** and **installed cost** as the most material value and liquidity drivers. It also shows why leverage must be sized to stabilized operating cash flow rather than construction-period equity-return optimization alone.

## How to run

### Models 1–5

```bash
python -m pip install -r requirements.txt
python data/generate_data.py
python pipeline/ingest.py
jupyter lab models/
```

Pre-rendered notebooks are available in [`exports/`](exports).

### Model 6 — full pipeline

```bash
cd model_06_datacenter_capital_forecasting
python -m pip install -r requirements.txt
python run_model.py
python run_phase2.py
python run_phase3.py
python run_phase4.py
python -m unittest discover -s tests -p 'test_*.py'
```

### Streamlit dashboard

```bash
streamlit run model_06_datacenter_capital_forecasting/dashboard/app.py
```

## Repository structure

```text
compute-economics-portfolio/
├── README.md
├── requirements.txt
├── data/                         # synthetic inference-event generator
├── pipeline/                     # SQLite ingestion and named SQL queries
├── models/                       # Models 1–5 notebooks
├── portfolio/                    # compute-economics capstone and brief
├── exports/                      # pre-rendered notebook HTML/PDF
├── model_06_datacenter_capital_forecasting/
│   ├── config/
│   ├── data/inputs/
│   ├── data/outputs/
│   ├── dashboard/
│   ├── docs/
│   ├── src/
│   ├── tests/
│   └── run_phase*.py
└── docs/                         # GitHub Pages static executive dashboard
```

## Evidence and confidentiality standard

Every public claim is traceable to executed code, a visible synthetic input, an output table, a chart, or an executive brief. Modeled decisions are not represented as realized operating outcomes. Synthetic assumptions are labeled throughout.

## Deployment

- **GitHub Pages:** publish the `/docs` folder from the `main` branch. The generated dashboard is already copied to `docs/index.html`.
- **Streamlit Community Cloud:** select this repository and use `model_06_datacenter_capital_forecasting/dashboard/app.py` as the entry point.

The GitHub Pages URL in this README assumes the repository remains named `compute-economics-portfolio` under the `dapaah` account. Update the link if the repository owner or name changes.
