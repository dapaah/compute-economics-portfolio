from __future__ import annotations

from pathlib import Path
from typing import Dict

import pandas as pd
import yaml

REQUIRED_COLUMNS = {
    "sites": {"site_id", "site_name", "it_load_mw", "pue", "target_rfs", "target_gpu_count"},
    "milestones": {"site_id", "milestone", "planned_date", "spend_weight"},
    "capex_plan": {"site_id", "category", "total_capex_usd"},
    "financing_plan": {
        "site_id", "equity_pct", "debt_pct", "debt_rate_annual",
        "debt_tenor_years", "minimum_equity_first_pct",
    },
    "operating_assumptions": {
        "site_id", "price_per_gpu_hour", "power_cost_per_mwh", "fixed_opex_monthly",
        "variable_opex_per_gpu_hour", "utilization_at_rfs", "utilization_mature",
        "months_to_mature", "gpu_ramp_months",
    },
}


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict) or "model" not in config or "scenario" not in config:
        raise ValueError("Configuration must contain 'model' and 'scenario' sections.")
    return config


def load_inputs(input_dir: Path) -> Dict[str, pd.DataFrame]:
    tables: Dict[str, pd.DataFrame] = {}
    for name, required in REQUIRED_COLUMNS.items():
        path = input_dir / f"{name}.csv"
        if not path.exists():
            raise FileNotFoundError(f"Missing required input: {path}")
        frame = pd.read_csv(path)
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"{name}.csv missing columns: {sorted(missing)}")
        tables[name] = frame

    for col in ["target_power_ready", "target_rfs"]:
        if col in tables["sites"].columns:
            tables["sites"][col] = pd.to_datetime(tables["sites"][col])
    tables["milestones"]["planned_date"] = pd.to_datetime(tables["milestones"]["planned_date"])

    site_ids = set(tables["sites"]["site_id"])
    for name, frame in tables.items():
        unknown = set(frame["site_id"]) - site_ids
        if unknown:
            raise ValueError(f"{name}.csv contains unknown site_id values: {sorted(unknown)}")

    weights = tables["milestones"].groupby("site_id")["spend_weight"].sum()
    if not weights.between(0.999, 1.001).all():
        raise ValueError("Milestone spend_weight must sum to 1.0 for each site.")

    financing = tables["financing_plan"]
    mix = financing["equity_pct"] + financing["debt_pct"]
    if not mix.between(0.999, 1.001).all():
        raise ValueError("equity_pct + debt_pct must sum to 1.0 for each site.")
    if not financing["minimum_equity_first_pct"].between(0, 1).all():
        raise ValueError("minimum_equity_first_pct must be between 0 and 1.")

    ops = tables["operating_assumptions"]
    if not ops["utilization_mature"].between(0, 1).all():
        raise ValueError("utilization_mature must be between 0 and 1.")
    if not ops["gpu_ramp_months"].gt(0).all():
        raise ValueError("gpu_ramp_months must be positive.")

    return tables



def load_phase2_inputs(input_dir: Path) -> dict[str, pd.DataFrame]:
    extra = {}
    for name in ["scenarios", "risk_assumptions"]:
        path = input_dir / f"{name}.csv"
        if not path.exists():
            raise FileNotFoundError(f"Missing Phase 2 input: {path}")
        extra[name] = pd.read_csv(path)
    required_scenarios = {"scenario", "capex_multiplier", "schedule_delay_months", "utilization_multiplier", "power_cost_multiplier", "price_multiplier", "debt_rate_shift_bps"}
    missing = required_scenarios.difference(extra["scenarios"].columns)
    if missing:
        raise ValueError(f"scenarios.csv missing columns: {sorted(missing)}")
    required_risk = {"risk_factor", "distribution", "minimum", "mode", "maximum"}
    missing = required_risk.difference(extra["risk_assumptions"].columns)
    if missing:
        raise ValueError(f"risk_assumptions.csv missing columns: {sorted(missing)}")
    if not (extra["risk_assumptions"]["minimum"] <= extra["risk_assumptions"]["mode"]).all() or not (extra["risk_assumptions"]["mode"] <= extra["risk_assumptions"]["maximum"]).all():
        raise ValueError("Risk triangular assumptions must satisfy minimum <= mode <= maximum.")
    return extra
