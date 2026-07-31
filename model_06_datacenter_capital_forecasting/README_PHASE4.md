# Phase 4 — CFO Executive Dashboard

Phase 4 adds the presentation and decision layer to the AI Datacenter Capital Forecasting Engine.

The dashboard connects physical deployment, capital consumption, liquidity, risk, financing structure and returns in one executive view.

## Deliverables

- standalone interactive HTML dashboard
- Streamlit application
- generated executive brief
- machine-readable executive KPI file
- dashboard tests and documentation

## Key views

- cumulative CapEx, GPUs and MW online
- monthly CapEx, cash balance and liquidity headroom
- site-level NPV and IRR
- base/upside/downside scenario tradeoffs
- capital-stack dilution, equity IRR and coverage
- Monte Carlo NPV and funding distributions
- sensitivity of value to utilization, installed cost, pricing and financing

## Run

```bash
pip install -r requirements.txt
python run_phase4.py
streamlit run dashboard/app.py
pytest -q
```

## Design principle

The dashboard is downstream of the model engine. It consumes validated CSV outputs and therefore remains auditable: every displayed number can be traced to a generated model table.
