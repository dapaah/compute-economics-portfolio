
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict

import pandas as pd

from .forecast import build_site_forecast, summarize_portfolio, summarize_sites

SCENARIO_FIELDS = [
    "capex_multiplier", "schedule_delay_months", "utilization_multiplier",
    "power_cost_multiplier", "price_multiplier",
]


def scenario_config(base_config: dict, row: pd.Series) -> dict:
    config = deepcopy(base_config)
    name = str(row["scenario"])
    definition = {field: float(row[field]) for field in SCENARIO_FIELDS}
    definition["schedule_delay_months"] = int(round(definition["schedule_delay_months"]))
    config["scenario"]["active"] = name
    config["scenario"]["definitions"][name] = definition
    return config


def apply_financing_shift(tables: dict[str, pd.DataFrame], debt_rate_shift_bps: float) -> dict[str, pd.DataFrame]:
    shifted = {name: frame.copy() for name, frame in tables.items()}
    shifted["financing_plan"]["debt_rate_annual"] += float(debt_rate_shift_bps) / 10_000
    return shifted


def run_scenario(tables: dict[str, pd.DataFrame], base_config: dict, row: pd.Series) -> dict:
    config = scenario_config(base_config, row)
    scenario_tables = apply_financing_shift(tables, float(row.get("debt_rate_shift_bps", 0.0)))
    site_monthly = build_site_forecast(scenario_tables, config)
    return {
        "config": config,
        "site_monthly": site_monthly,
        "site_summary": summarize_sites(site_monthly, config),
        "portfolio_monthly": summarize_portfolio(site_monthly, config),
    }


def scenario_comparison(results: dict[str, dict]) -> pd.DataFrame:
    rows = []
    for name, result in results.items():
        site = result["site_summary"]
        portfolio = result["portfolio_monthly"].sort_values("month")
        rows.append({
            "scenario": name,
            "total_capex_usd": site["total_capex_usd"].sum(),
            "total_revenue_usd": site["total_revenue_usd"].sum(),
            "total_ebitda_usd": site["total_ebitda_usd"].sum(),
            "portfolio_unlevered_npv_usd": site["unlevered_npv_usd"].sum(),
            "weighted_unlevered_irr": (site["unlevered_irr"] * site["total_capex_usd"]).sum() / site["total_capex_usd"].sum(),
            "incremental_funding_required_usd": portfolio["incremental_funding_required_usd"].max(),
            "minimum_cash_pre_support_usd": portfolio["cash_balance_pre_support_usd"].min(),
            "peak_gpu_online": site["peak_gpu_online"].sum(),
            "latest_ready_for_service": site["ready_for_service"].max(),
            "total_interest_during_construction_usd": site["interest_during_construction_usd"].sum(),
        })
    comparison = pd.DataFrame(rows).sort_values("scenario").reset_index(drop=True)
    base = comparison.loc[comparison["scenario"] == "base"].iloc[0]
    for col in ["total_capex_usd", "portfolio_unlevered_npv_usd", "incremental_funding_required_usd", "total_ebitda_usd"]:
        comparison[f"delta_vs_base_{col}"] = comparison[col] - base[col]
    return comparison
