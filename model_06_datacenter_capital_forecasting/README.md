# Model 6 — AI Datacenter Capital Forecasting Engine

A synthetic, driver-based prototype connecting datacenter delivery milestones to CapEx, financing, liquidity, operating ramp, returns, infrastructure risk, capital structure, and executive decisions.

## Architecture

### Phase 1 — Deterministic forecasting core
- milestone-driven monthly CapEx;
- power, commissioning, and ready-for-service gates;
- phased GPU deployment and utilization ramp;
- revenue, OpEx, project cash flow, debt, liquidity, NPV, IRR, and ROIC.

### Phase 2 — Scenario and risk engine
- base, upside, downside, and severe-downside cases;
- schedule, CapEx, utilization, power, price, and debt-rate stresses;
- seeded Monte Carlo completion, cost, liquidity, and return distributions;
- scenario comparison and risk-sensitivity outputs.

### Phase 3 — Capital-stack optimizer
- all-equity, corporate, project-finance, customer-prepayment, and government-supported structures;
- sponsor equity, grants, project debt, equipment financing, and customer capital;
- dilution, CADS, DSCR, debt service, minimum cash, incremental funding, and levered equity IRR.

### Phase 4 — Executive decision layer
- standalone interactive HTML dashboard;
- Streamlit dashboard application;
- machine-readable KPI export;
- executive decision brief;
- portfolio, site, scenario, liquidity, capital-stack, and risk views.

## Run the complete model

```bash
python -m pip install -r requirements.txt
python run_model.py
python run_phase2.py
python run_phase3.py
python run_phase4.py
python -m unittest discover -s tests -p 'test_*.py'
```

## Open the outputs

- Static dashboard: `data/outputs/dashboard/executive_dashboard.html`
- Streamlit app: `dashboard/app.py`
- Executive brief: `data/outputs/dashboard/executive_brief.md`
- KPI export: `data/outputs/dashboard/executive_kpis.json`
- Scenario comparison: `data/outputs/scenario_comparison.csv`
- Capital-stack comparison: `data/outputs/capital_stack_comparison.csv`
- Monte Carlo results: `data/outputs/monte_carlo_summary.csv`

All data and assumptions are synthetic, seeded, and explicitly documented.
