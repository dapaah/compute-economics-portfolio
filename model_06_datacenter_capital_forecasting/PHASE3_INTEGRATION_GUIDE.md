# Phase 3 Integration Guide

Copy the Phase 3 files into the existing `model_06_datacenter_capital_forecasting` directory after integrating Phases 0–2.

## New files

- `data/inputs/capital_stack_options.csv`
- `src/capital_stack.py`
- `run_phase3.py`
- `tests/test_phase3.py`
- `docs/CAPITAL_STACK_OPTIMIZER.md`

## New generated outputs

- `data/outputs/capital_stack_comparison.csv`
- `data/outputs/site_monthly_capital_stack_<structure>.csv`

## Validation

```bash
python run_phase3.py
pytest -q
```

The full suite should report 20 passing tests.
