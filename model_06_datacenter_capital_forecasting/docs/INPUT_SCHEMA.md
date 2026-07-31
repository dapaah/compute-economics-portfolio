# Phase 1 Input Schema

## sites.csv
Site identity, region, IT load, PUE, total facility MW, target dates, and target GPU count.

## milestones.csv
Six physical-development milestones per site. `spend_weight` remains as a control total and future scenario parameter; Phase 1 uses milestone dates and category-specific spend curves.

## capex_plan.csv
Total CapEx by site and category. Categories map to engineering intervals in `src/forecast.py`.

## financing_plan.csv
Target debt/equity mix, debt cost and tenor, and the minimum portion of project CapEx that must be funded with equity first.

## operating_assumptions.csv
Price per GPU-hour, power cost, fixed and variable OpEx, utilization ramp, and GPU deployment ramp.

## model_config.yml
Forecast horizon, discount rate, starting and minimum cash, tax rate, terminal multiple, and active deterministic scenario.
