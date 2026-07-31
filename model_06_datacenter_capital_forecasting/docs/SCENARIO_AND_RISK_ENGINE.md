
# Scenario and Risk Engine

Phase 2 adds two layers above the deterministic forecasting core.

## Deterministic scenarios
`scenarios.csv` defines management cases using common drivers: schedule delay, installed-cost multiplier, utilization, power cost, pricing, and financing spread. Every case reruns the same Phase 1 engine, preserving an apples-to-apples comparison.

## Monte Carlo simulation
`risk_assumptions.csv` defines seeded triangular distributions. The engine samples six drivers, reruns the integrated model, and records completion dates, total CapEx, liquidity support, EBITDA, and NPV.

## Executive outputs
- `scenario_comparison.csv`
- `monte_carlo_summary.csv`
- `risk_sensitivity.csv`
- full simulation and site-level audit trails

The simulation is illustrative and synthetic. Distribution parameters are transparent inputs, not claims about Fluidstack or any real project.
