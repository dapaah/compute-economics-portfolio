from __future__ import annotations

from copy import deepcopy

import numpy as np
import pandas as pd

from .forecast import build_site_forecast, summarize_portfolio, summarize_sites


def _funding_mix(row: pd.Series) -> tuple[float, float, float]:
    grant = float(row.grant_pct_capex)
    prepay = float(row.customer_prepay_pct_capex)
    equipment = float(row.equipment_finance_pct_capex)
    non_sponsor = grant + prepay
    residual = max(1.0 - non_sponsor, 0.0)
    project_debt = residual * float(row.project_debt_pct_residual)
    total_debt = min(project_debt + equipment, residual)
    sponsor_equity = max(1.0 - non_sponsor - total_debt, 0.0)
    return sponsor_equity, total_debt, non_sponsor


def _prepare_tables(tables: dict[str, pd.DataFrame], option: pd.Series) -> dict[str, pd.DataFrame]:
    adjusted = {name: frame.copy() for name, frame in tables.items()}
    sponsor_equity_pct, debt_pct, non_sponsor_pct = _funding_mix(option)
    financing = adjusted["financing_plan"]
    financing["equity_pct"] = sponsor_equity_pct + non_sponsor_pct
    financing["debt_pct"] = debt_pct
    financing["debt_rate_annual"] = float(option.project_debt_rate_annual)
    financing["debt_tenor_years"] = float(option.debt_tenor_years)
    financing["minimum_equity_first_pct"] = float(option.minimum_equity_first_pct)
    adjusted["financing_plan"] = financing
    return adjusted


def _allocate_non_dilutive(site_monthly: pd.DataFrame, option: pd.Series) -> pd.DataFrame:
    frame = site_monthly.copy()
    grant_pct = float(option.grant_pct_capex)
    prepay_pct = float(option.customer_prepay_pct_capex)
    equipment_pct = float(option.equipment_finance_pct_capex)
    frame["grant_funding_usd"] = frame["capex_usd"] * grant_pct
    frame["customer_prepayment_usd"] = frame["capex_usd"] * prepay_pct
    frame["equipment_finance_usd"] = frame["capex_usd"] * equipment_pct
    non_dilutive = frame["grant_funding_usd"] + frame["customer_prepayment_usd"]
    frame["sponsor_equity_draw_usd"] = (frame["equity_draw_usd"] - non_dilutive).clip(lower=0)
    frame["maintenance_capex_usd"] = frame["revenue_usd"] * float(option.maintenance_capex_pct_revenue)
    frame["cads_usd"] = (
        frame["ebitda_usd"] - frame["cash_tax_usd"] - frame["maintenance_capex_usd"]
    )
    frame["dscr"] = np.where(
        frame["debt_service_usd"] > 0,
        frame["cads_usd"] / frame["debt_service_usd"],
        np.nan,
    )
    frame = frame.sort_values(["site_id", "month"]).copy()
    frame["rolling_12m_cads_usd"] = frame.groupby("site_id")["cads_usd"].transform(
        lambda values: values.rolling(12, min_periods=12).sum()
    )
    frame["rolling_12m_debt_service_usd"] = frame.groupby("site_id")["debt_service_usd"].transform(
        lambda values: values.rolling(12, min_periods=12).sum()
    )
    frame["rolling_12m_dscr"] = np.where(
        frame["rolling_12m_debt_service_usd"] > 0,
        frame["rolling_12m_cads_usd"] / frame["rolling_12m_debt_service_usd"],
        np.nan,
    )
    frame["adjusted_equity_cash_flow_usd"] = (
        frame["operating_cash_flow_usd"]
        - frame["maintenance_capex_usd"]
        - frame["capex_usd"]
        + frame["debt_draw_usd"]
        + frame["grant_funding_usd"]
        + frame["customer_prepayment_usd"]
        - frame["debt_service_usd"]
    )
    frame["capital_stack"] = str(option.structure)
    return frame


def _annualized_irr(values: pd.Series) -> float:
    import numpy_financial as npf
    array = values.to_numpy(dtype=float)
    if not ((array < 0).any() and (array > 0).any()):
        return np.nan
    monthly = npf.irr(array)
    return float((1 + monthly) ** 12 - 1) if monthly is not None and np.isfinite(monthly) else np.nan


def run_capital_stack(tables: dict[str, pd.DataFrame], config: dict, option: pd.Series) -> dict:
    adjusted_tables = _prepare_tables(tables, option)
    adjusted_config = deepcopy(config)
    adjusted_config["scenario"]["active"] = "base"
    site_monthly = build_site_forecast(adjusted_tables, adjusted_config)
    site_monthly = _allocate_non_dilutive(site_monthly, option)
    site_summary = summarize_sites(site_monthly, adjusted_config)
    portfolio = summarize_portfolio(site_monthly, adjusted_config)
    return {
        "site_monthly": site_monthly,
        "site_summary": site_summary,
        "portfolio_monthly": portfolio,
    }


def compare_capital_stacks(tables: dict[str, pd.DataFrame], config: dict, options: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, dict]]:
    rows: list[dict] = []
    results: dict[str, dict] = {}
    for _, option in options.iterrows():
        name = str(option.structure)
        result = run_capital_stack(tables, config, option)
        results[name] = result
        monthly = result["site_monthly"].sort_values(["site_id", "month"])
        sites = result["site_summary"]
        portfolio = result["portfolio_monthly"]
        sponsor_equity = float(monthly["sponsor_equity_draw_usd"].sum())
        pre_money = float(option.pre_money_equity_value_usd)
        dilution = sponsor_equity / (pre_money + sponsor_equity) if pre_money + sponsor_equity else np.nan
        debt_service_mask = monthly["debt_service_usd"] > 0
        dscr_values = monthly["rolling_12m_dscr"].replace([np.inf, -np.inf], np.nan).dropna()
        min_dscr = float(dscr_values.min()) if not dscr_values.empty else np.nan
        weighted_dscr = (
            float(monthly.loc[debt_service_mask, "cads_usd"].sum())
            / float(monthly.loc[debt_service_mask, "debt_service_usd"].sum())
            if float(monthly.loc[debt_service_mask, "debt_service_usd"].sum()) > 0 else np.nan
        )
        terminal_value = float(sites["terminal_value_usd"].sum())
        ending_debt = float(sites["ending_debt_balance_usd"].sum())
        equity_cf = monthly.groupby("month")["adjusted_equity_cash_flow_usd"].sum().copy()
        equity_cf.iloc[-1] += max(terminal_value - ending_debt, 0.0)
        rows.append({
            "capital_stack": name,
            "description": str(option.description),
            "total_capex_usd": float(monthly["capex_usd"].sum()),
            "sponsor_equity_usd": sponsor_equity,
            "project_debt_draw_usd": float(monthly["debt_draw_usd"].sum()),
            "grant_funding_usd": float(monthly["grant_funding_usd"].sum()),
            "customer_prepayment_usd": float(monthly["customer_prepayment_usd"].sum()),
            "equipment_finance_usd": float(monthly["equipment_finance_usd"].sum()),
            "interest_during_construction_usd": float(monthly["interest_during_construction_usd"].sum()),
            "total_debt_service_usd": float(monthly["debt_service_usd"].sum()),
            "ending_debt_balance_usd": ending_debt,
            "minimum_dscr": min_dscr,
            "weighted_dscr": weighted_dscr,
            "dscr_breach_months": int((monthly["rolling_12m_dscr"] < float(option.minimum_dscr)).sum()),
            "minimum_dscr_threshold": float(option.minimum_dscr),
            "incremental_funding_required_usd": float(portfolio["incremental_funding_required_usd"].max()),
            "minimum_cash_pre_support_usd": float(portfolio["cash_balance_pre_support_usd"].min()),
            "estimated_dilution_pct": dilution,
            "equity_irr": _annualized_irr(equity_cf),
            "portfolio_unlevered_npv_usd": float(sites["unlevered_npv_usd"].sum()),
            "total_ebitda_usd": float(sites["total_ebitda_usd"].sum()),
        })
    comparison = pd.DataFrame(rows)
    comparison["liquidity_rank"] = comparison["incremental_funding_required_usd"].rank(method="min")
    comparison["dilution_rank"] = comparison["estimated_dilution_pct"].rank(method="min")
    comparison["equity_irr_rank"] = comparison["equity_irr"].rank(method="min", ascending=False)
    comparison["coverage_pass"] = comparison["minimum_dscr"].isna() | (
        comparison["minimum_dscr"] >= comparison["minimum_dscr_threshold"]
    )
    return comparison.sort_values("capital_stack").reset_index(drop=True), results
