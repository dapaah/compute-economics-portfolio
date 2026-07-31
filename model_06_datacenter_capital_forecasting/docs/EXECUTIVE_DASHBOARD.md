# Executive Dashboard

Phase 4 turns the forecasting, risk and capital-stack outputs into an executive-consumption layer.

## Public artifacts

- `data/outputs/dashboard/executive_dashboard.html`: standalone interactive dashboard
- `data/outputs/dashboard/executive_brief.md`: generated executive decision brief
- `data/outputs/dashboard/executive_kpis.json`: machine-readable KPI set
- `dashboard/app.py`: interactive Streamlit application

## Views

1. Portfolio deployment and liquidity
2. Site-level capital efficiency and returns
3. Deterministic scenario comparison
4. Capital-stack dilution, return and coverage tradeoffs
5. Monte Carlo outcome distribution and risk sensitivity

## Run

```bash
python run_phase4.py
streamlit run dashboard/app.py
```

The dashboard reads only model outputs. It does not duplicate or alter the validated forecasting calculations.
