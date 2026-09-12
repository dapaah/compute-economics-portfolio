# Local build and review

From `compute-supply-demand`:

```sh
python run_scenarios.py
python run_demand.py
python build_dashboard.py
python -m unittest discover -s tests -v
git diff --check
git diff --stat
git diff -- compute-supply-demand README.md
```

Use Python 3.10+ with NumPy and pandas, plus Node for parity. `NODE_BINARY` can name
an absolute executable when Node is not on PATH. Open `deliverable_capacity.html`
locally; no server or external scripts/fonts are needed. Edit registries, Python,
JS or the template; regenerate artifacts before review.

The dashboard is not hosted on Pages. Existing Pages hosting uses `docs/`, so this
module does not automatically make the HTML live. Moving it there is a separate
publication decision.
