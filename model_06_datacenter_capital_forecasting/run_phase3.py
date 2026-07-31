from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.capital_stack import compare_capital_stacks
from src.io import load_config, load_inputs


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    config = load_config(base_dir / "config" / "model_config.yml")
    tables = load_inputs(base_dir / "data" / "inputs")
    options = pd.read_csv(base_dir / "data" / "inputs" / "capital_stack_options.csv")
    outputs = base_dir / "data" / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)

    comparison, results = compare_capital_stacks(tables, config, options)
    comparison.to_csv(outputs / "capital_stack_comparison.csv", index=False)
    for name, result in results.items():
        result["site_monthly"].to_csv(outputs / f"site_monthly_capital_stack_{name}.csv", index=False)
    print(comparison.to_string(index=False))


if __name__ == "__main__":
    main()
