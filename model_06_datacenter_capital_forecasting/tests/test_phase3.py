from pathlib import Path

import numpy as np
import pandas as pd

from src.capital_stack import compare_capital_stacks
from src.io import load_config, load_inputs

BASE = Path(__file__).resolve().parents[1]


def _results():
    config = load_config(BASE / "config" / "model_config.yml")
    tables = load_inputs(BASE / "data" / "inputs")
    options = pd.read_csv(BASE / "data" / "inputs" / "capital_stack_options.csv")
    return compare_capital_stacks(tables, config, options)


def test_all_options_run():
    comparison, results = _results()
    assert len(comparison) == 5
    assert set(comparison["capital_stack"]) == set(results)


def test_funding_sources_reconcile_to_capex():
    comparison, _ = _results()
    funded = (
        comparison["sponsor_equity_usd"]
        + comparison["project_debt_draw_usd"]
        + comparison["grant_funding_usd"]
        + comparison["customer_prepayment_usd"]
    )
    assert np.allclose(funded, comparison["total_capex_usd"], rtol=1e-6, atol=1.0)


def test_all_equity_has_no_debt_service():
    comparison, _ = _results()
    row = comparison.loc[comparison["capital_stack"] == "all_equity"].iloc[0]
    assert row["project_debt_draw_usd"] == 0
    assert row["total_debt_service_usd"] == 0


def test_non_dilutive_structures_reduce_sponsor_equity():
    comparison, _ = _results()
    all_equity = comparison.loc[comparison["capital_stack"] == "all_equity", "sponsor_equity_usd"].iloc[0]
    supported = comparison.loc[comparison["capital_stack"] == "government_supported", "sponsor_equity_usd"].iloc[0]
    assert supported < all_equity


def test_dilution_is_bounded():
    comparison, _ = _results()
    assert comparison["estimated_dilution_pct"].between(0, 1).all()


def test_dscr_only_applies_to_debt_structures():
    comparison, _ = _results()
    all_equity = comparison.loc[comparison["capital_stack"] == "all_equity"].iloc[0]
    assert pd.isna(all_equity["minimum_dscr"])
    assert comparison.loc[comparison["capital_stack"] != "all_equity", "weighted_dscr"].notna().all()
