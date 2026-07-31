# Notebook Roadmap

Phase 1 will add transparent notebooks in dependency order:

1. `01_site_pipeline_and_capacity.ipynb`
2. `02_milestone_schedule_and_capex.ipynb`
3. `03_financing_and_liquidity.ipynb`
4. `04_operating_ramp_and_returns.ipynb`
5. `05_scenarios_and_monte_carlo.ipynb`
6. `06_executive_dashboard.ipynb`

The production calculation logic should remain in `src/`; notebooks should expose assumptions, analysis, charts, and written decisions rather than duplicate hidden logic.
