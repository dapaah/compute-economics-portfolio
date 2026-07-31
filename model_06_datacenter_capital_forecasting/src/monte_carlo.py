
from __future__ import annotations

from copy import deepcopy

import numpy as np
import pandas as pd

from .scenarios import run_scenario


def _sample(rng: np.random.Generator, row: pd.Series) -> float:
    dist = str(row["distribution"]).lower()
    if dist != "triangular":
        raise ValueError(f"Unsupported distribution: {dist}")
    return float(rng.triangular(float(row["minimum"]), float(row["mode"]), float(row["maximum"])))


def run_monte_carlo(
    tables: dict[str, pd.DataFrame],
    config: dict,
    risk_assumptions: pd.DataFrame,
    simulations: int = 500,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    assumptions = risk_assumptions.set_index("risk_factor")
    rows = []
    site_rows = []
    for simulation_id in range(1, simulations + 1):
        draws = {factor: _sample(rng, assumptions.loc[factor]) for factor in assumptions.index}
        scenario_row = pd.Series({
            "scenario": f"mc_{simulation_id:04d}",
            "capex_multiplier": draws["capex_multiplier"],
            "schedule_delay_months": int(round(draws["schedule_delay_months"])),
            "utilization_multiplier": draws["utilization_multiplier"],
            "power_cost_multiplier": draws["power_cost_multiplier"],
            "price_multiplier": draws["price_multiplier"],
            "debt_rate_shift_bps": draws["debt_rate_shift_bps"],
        })
        result = run_scenario(tables, config, scenario_row)
        site = result["site_summary"].copy()
        portfolio = result["portfolio_monthly"].sort_values("month")
        total_capex = float(site["total_capex_usd"].sum())
        total_npv = float(site["unlevered_npv_usd"].sum())
        rows.append({
            "simulation_id": simulation_id,
            **draws,
            "total_capex_usd": total_capex,
            "portfolio_unlevered_npv_usd": total_npv,
            "total_ebitda_usd": float(site["total_ebitda_usd"].sum()),
            "incremental_funding_required_usd": float(portfolio["incremental_funding_required_usd"].max()),
            "minimum_cash_pre_support_usd": float(portfolio["cash_balance_pre_support_usd"].min()),
            "latest_ready_for_service": site["ready_for_service"].max(),
            "npv_positive": total_npv > 0,
        })
        site["simulation_id"] = simulation_id
        site_rows.append(site[["simulation_id", "site_id", "site_name", "ready_for_service", "total_capex_usd", "unlevered_npv_usd", "unlevered_irr"]])
    return pd.DataFrame(rows), pd.concat(site_rows, ignore_index=True)


def monte_carlo_summary(simulations: pd.DataFrame) -> pd.DataFrame:
    metrics = [
        "total_capex_usd", "portfolio_unlevered_npv_usd", "total_ebitda_usd",
        "incremental_funding_required_usd", "minimum_cash_pre_support_usd",
    ]
    rows = []
    for metric in metrics:
        s = simulations[metric]
        rows.append({
            "metric": metric,
            "mean": s.mean(), "p10": s.quantile(0.10), "p50": s.quantile(0.50),
            "p90": s.quantile(0.90), "minimum": s.min(), "maximum": s.max(),
        })
    rows.append({
        "metric": "probability_npv_positive", "mean": simulations["npv_positive"].mean(),
        "p10": np.nan, "p50": np.nan, "p90": np.nan, "minimum": np.nan, "maximum": np.nan,
    })
    return pd.DataFrame(rows)


def risk_sensitivity(simulations: pd.DataFrame) -> pd.DataFrame:
    drivers = [
        "schedule_delay_months", "capex_multiplier", "utilization_multiplier",
        "power_cost_multiplier", "price_multiplier", "debt_rate_shift_bps",
    ]
    outcomes = ["portfolio_unlevered_npv_usd", "incremental_funding_required_usd", "total_capex_usd"]
    rows = []
    for outcome in outcomes:
        for driver in drivers:
            rows.append({"outcome": outcome, "risk_driver": driver, "pearson_correlation": simulations[[driver, outcome]].corr().iloc[0, 1]})
    return pd.DataFrame(rows).sort_values(["outcome", "pearson_correlation"], key=lambda s: s.abs() if s.name == "pearson_correlation" else s, ascending=[True, False])
