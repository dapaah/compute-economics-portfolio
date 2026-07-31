# Phase 3 — Capital Stack Optimizer

Phase 3 extends the deterministic forecasting and risk engine into financing architecture. It compares alternative funding structures across dilution, liquidity, debt service, coverage, and equity returns.

## Run

```bash
python run_phase3.py
pytest -q
```

## Structures compared

1. All equity
2. Balanced corporate financing
3. Project finance
4. Strategic customer prepayment
5. Government-supported financing

## Base-case findings from synthetic assumptions

- All-equity funding eliminates coverage and liquidity risk but requires $4.345B of sponsor equity and implies the highest estimated dilution.
- Government-supported financing reduces sponsor equity to approximately $1.33B and produces the highest modeled equity IRR, aided by grants and equipment financing.
- Strategic-customer and project-finance structures also reduce equity needs, but increase debt service and liquidity pressure.
- None of the leveraged structures meets its illustrative rolling DSCR threshold during the modeled ramp, indicating that the base operating profile would require delayed amortization, sculpted debt service, additional reserves, stronger utilization/pricing, or lower leverage.

These results are illustrative and generated from synthetic assumptions. They demonstrate how financing architecture changes stakeholder outcomes without changing the underlying physical deployment plan.
