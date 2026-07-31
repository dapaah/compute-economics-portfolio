from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy_financial as npf
import pandas as pd


MILESTONE_ORDER = [
    "site_control",
    "design_complete",
    "construction_start",
    "power_ready",
    "commissioning",
    "ready_for_service",
]

CATEGORY_MILESTONE = {
    "land_and_site": "site_control",
    "professional_fees_and_contingency": "design_complete",
    "shell_and_construction": "construction_start",
    "utility_interconnection": "power_ready",
    "electrical_and_mechanical": "power_ready",
    "networking_and_storage": "commissioning",
    "gpu_and_compute": "ready_for_service",
}


@dataclass(frozen=True)
class Scenario:
    name: str
    capex_multiplier: float
    schedule_delay_months: int
    utilization_multiplier: float
    power_cost_multiplier: float
    price_multiplier: float


def month_grid(start_month: str, horizon_months: int, site_ids: list[str]) -> pd.DataFrame:
    months = pd.date_range(pd.Timestamp(start_month), periods=horizon_months, freq="MS")
    index = pd.MultiIndex.from_product([site_ids, months], names=["site_id", "month"])
    return index.to_frame(index=False)


def _months_between(later: pd.Series, earlier: pd.Series) -> pd.Series:
    return (later.dt.year - earlier.dt.year) * 12 + later.dt.month - earlier.dt.month


def _linear_ramp(months_since_start: pd.Series, start: pd.Series, mature: pd.Series, months_to_mature: pd.Series) -> np.ndarray:
    denominator = months_to_mature.clip(lower=1)
    progress = (months_since_start.clip(lower=0) / denominator).clip(upper=1)
    return np.where(months_since_start < 0, 0.0, start + (mature - start) * progress)


def _milestone_table(milestones: pd.DataFrame, delay_months: int) -> pd.DataFrame:
    table = milestones.copy()
    table["adjusted_date"] = table["planned_date"] + pd.offsets.MonthBegin(delay_months)
    pivot = table.pivot(index="site_id", columns="milestone", values="adjusted_date").reset_index()
    missing = set(MILESTONE_ORDER) - set(pivot.columns)
    if missing:
        raise ValueError(f"Missing required milestones: {sorted(missing)}")
    return pivot


def _triangular_weights(length: int, peak: float = 0.65) -> np.ndarray:
    if length <= 1:
        return np.ones(1)
    x = np.linspace(0, 1, length)
    weights = np.where(x <= peak, x / max(peak, 1e-9), (1 - x) / max(1 - peak, 1e-9))
    weights = np.maximum(weights, 0.08)
    return weights / weights.sum()


def _category_spend_schedule(
    months: pd.DatetimeIndex,
    amount: float,
    category: str,
    dates: dict[str, pd.Timestamp],
) -> np.ndarray:
    anchor = CATEGORY_MILESTONE.get(category, "construction_start")
    if anchor == "site_control":
        start = dates["site_control"]
        end = dates["design_complete"]
        peak = 0.30
    elif anchor == "design_complete":
        start = dates["site_control"]
        end = dates["commissioning"]
        peak = 0.65
    elif anchor == "construction_start":
        start = dates["construction_start"]
        end = dates["power_ready"]
        peak = 0.55
    elif anchor == "power_ready":
        start = dates["construction_start"]
        end = dates["power_ready"]
        peak = 0.75
    elif anchor == "commissioning":
        start = dates["power_ready"]
        end = dates["commissioning"]
        peak = 0.70
    else:  # ready_for_service / compute
        start = dates["power_ready"]
        end = dates["ready_for_service"]
        peak = 0.70

    active = (months >= pd.Timestamp(start)) & (months <= pd.Timestamp(end))
    schedule = np.zeros(len(months))
    count = int(active.sum())
    if count == 0:
        return schedule
    schedule[active] = _triangular_weights(count, peak=peak) * amount
    return schedule


def _build_capex_schedule(
    grid: pd.DataFrame,
    capex_plan: pd.DataFrame,
    milestone_pivot: pd.DataFrame,
    multiplier: float,
) -> pd.DataFrame:
    result = grid[["site_id", "month"]].copy()
    result["capex_usd"] = 0.0
    result["gpu_capex_usd"] = 0.0

    milestone_lookup = milestone_pivot.set_index("site_id").to_dict("index")
    for site_id, site_grid in result.groupby("site_id", sort=False):
        idx = site_grid.index
        months = pd.DatetimeIndex(site_grid["month"])
        dates = milestone_lookup[site_id]
        for row in capex_plan.loc[capex_plan["site_id"] == site_id].itertuples():
            amount = float(row.total_capex_usd) * multiplier
            schedule = _category_spend_schedule(months, amount, row.category, dates)
            result.loc[idx, "capex_usd"] += schedule
            if row.category == "gpu_and_compute":
                result.loc[idx, "gpu_capex_usd"] += schedule
    return result


def _debt_schedule(site_frame: pd.DataFrame) -> pd.DataFrame:
    frame = site_frame.sort_values("month").copy()
    debt_balance = 0.0
    accrued_idc = 0.0
    balances, interest, principal, idc = [], [], [], []
    monthly_rate = float(frame["debt_rate_annual"].iloc[0]) / 12
    tenor_months = max(int(round(float(frame["debt_tenor_years"].iloc[0]) * 12)), 1)
    rfs = pd.Timestamp(frame["rfs_month"].iloc[0])

    for row in frame.itertuples():
        debt_balance += float(row.debt_draw_usd)
        current_interest = debt_balance * monthly_rate
        current_principal = 0.0
        current_idc = 0.0
        if row.month < rfs:
            current_idc = current_interest
            accrued_idc += current_idc
            debt_balance += current_idc
            current_interest = 0.0
        else:
            if accrued_idc > 0:
                accrued_idc = 0.0
            current_principal = min(debt_balance, debt_balance / max(tenor_months, 1))
            debt_balance -= current_principal
            tenor_months = max(tenor_months - 1, 1)
        balances.append(debt_balance)
        interest.append(current_interest)
        principal.append(current_principal)
        idc.append(current_idc)

    frame["interest_during_construction_usd"] = idc
    frame["cash_interest_usd"] = interest
    frame["principal_repayment_usd"] = principal
    frame["ending_debt_balance_usd"] = balances
    frame["debt_service_usd"] = frame["cash_interest_usd"] + frame["principal_repayment_usd"]
    return frame


def build_site_forecast(tables: dict[str, pd.DataFrame], config: dict) -> pd.DataFrame:
    model_cfg = config["model"]
    scenario_name = config["scenario"]["active"]
    raw = config["scenario"]["definitions"][scenario_name]
    scenario = Scenario(name=scenario_name, **raw)

    sites = tables["sites"].copy()
    ops = tables["operating_assumptions"].copy()
    financing = tables["financing_plan"].copy()
    milestone_pivot = _milestone_table(tables["milestones"], scenario.schedule_delay_months)

    grid = month_grid(model_cfg["start_month"], int(model_cfg["horizon_months"]), sites["site_id"].tolist())
    frame = grid.merge(sites, on="site_id", how="left")
    frame = frame.merge(ops, on="site_id", how="left")
    frame = frame.merge(financing, on="site_id", how="left")
    frame = frame.merge(milestone_pivot, on="site_id", how="left")
    frame["scenario"] = scenario.name
    frame["rfs_month"] = frame["ready_for_service"]
    frame["power_gate_open"] = frame["month"] >= frame["power_ready"]
    frame["commissioning_gate_open"] = frame["month"] >= frame["commissioning"]
    frame["rfs_gate_open"] = frame["month"] >= frame["rfs_month"]

    capex_schedule = _build_capex_schedule(
        grid,
        tables["capex_plan"],
        milestone_pivot,
        scenario.capex_multiplier,
    )
    frame = frame.merge(capex_schedule, on=["site_id", "month"], how="left")

    frame["months_since_rfs"] = _months_between(frame["month"], frame["rfs_month"])
    frame["utilization"] = _linear_ramp(
        frame["months_since_rfs"],
        frame["utilization_at_rfs"],
        frame["utilization_mature"] * scenario.utilization_multiplier,
        frame["months_to_mature"].astype(int),
    )
    frame["utilization"] = frame["utilization"].clip(upper=0.98)

    gpu_progress = ((frame["months_since_rfs"] + 1) / frame["gpu_ramp_months"].clip(lower=1)).clip(0, 1)
    frame["gpu_online"] = np.where(
        frame["rfs_gate_open"],
        np.floor(frame["target_gpu_count"] * gpu_progress),
        0,
    ).astype(int)
    frame["it_load_online_mw"] = frame["it_load_mw"] * np.where(
        frame["target_gpu_count"] > 0,
        frame["gpu_online"] / frame["target_gpu_count"],
        0,
    )
    frame["facility_load_online_mw"] = frame["it_load_online_mw"] * frame["pue"]

    hours = 24 * frame["month"].dt.days_in_month
    frame["gpu_hours_available"] = frame["gpu_online"] * hours
    frame["gpu_hours_sold"] = frame["gpu_hours_available"] * frame["utilization"]
    frame["price_per_gpu_hour_scenario"] = frame["price_per_gpu_hour"] * scenario.price_multiplier
    frame["revenue_usd"] = frame["gpu_hours_sold"] * frame["price_per_gpu_hour_scenario"]

    frame["power_mwh"] = frame["facility_load_online_mw"] * hours * frame["utilization"]
    frame["power_cost_usd"] = frame["power_mwh"] * frame["power_cost_per_mwh"] * scenario.power_cost_multiplier
    frame["fixed_opex_usd"] = np.where(frame["rfs_gate_open"], frame["fixed_opex_monthly"], 0.0)
    frame["variable_opex_usd"] = frame["gpu_hours_sold"] * frame["variable_opex_per_gpu_hour"]
    frame["opex_usd"] = frame["power_cost_usd"] + frame["fixed_opex_usd"] + frame["variable_opex_usd"]
    frame["ebitda_usd"] = frame["revenue_usd"] - frame["opex_usd"]

    # Equity is contributed first up to the configured minimum; thereafter the target mix funds CapEx.
    total_capex = frame.groupby("site_id")["capex_usd"].transform("sum")
    cumulative_capex_before = frame.groupby("site_id")["capex_usd"].cumsum() - frame["capex_usd"]
    equity_first_threshold = total_capex * frame["minimum_equity_first_pct"]
    equity_first_draw = np.minimum(frame["capex_usd"], (equity_first_threshold - cumulative_capex_before).clip(lower=0))
    remaining_capex = frame["capex_usd"] - equity_first_draw
    frame["equity_draw_usd"] = equity_first_draw + remaining_capex * frame["equity_pct"]
    frame["debt_draw_usd"] = remaining_capex * frame["debt_pct"]
    # Any residual caused by equity-first mechanics is funded with equity.
    residual = frame["capex_usd"] - frame["equity_draw_usd"] - frame["debt_draw_usd"]
    frame["equity_draw_usd"] += residual

    frame = pd.concat([_debt_schedule(group) for _, group in frame.groupby("site_id", sort=False)], ignore_index=True)
    frame["taxable_income_proxy_usd"] = (frame["ebitda_usd"] - frame["cash_interest_usd"]).clip(lower=0)
    frame["cash_tax_usd"] = frame["taxable_income_proxy_usd"] * float(model_cfg["default_tax_rate"])
    frame["operating_cash_flow_usd"] = frame["ebitda_usd"] - frame["cash_tax_usd"]
    frame["unlevered_free_cash_flow_usd"] = frame["operating_cash_flow_usd"] - frame["capex_usd"]
    frame["equity_cash_flow_usd"] = (
        frame["operating_cash_flow_usd"]
        - frame["capex_usd"]
        + frame["debt_draw_usd"]
        - frame["debt_service_usd"]
    )
    frame["net_cash_flow_post_financing_usd"] = (
        frame["operating_cash_flow_usd"]
        - frame["capex_usd"]
        + frame["equity_draw_usd"]
        + frame["debt_draw_usd"]
        - frame["debt_service_usd"]
    )
    return frame.sort_values(["site_id", "month"]).reset_index(drop=True)


def _annualized_irr(monthly_cash_flows: pd.Series) -> float:
    values = monthly_cash_flows.to_numpy(dtype=float)
    if not ((values < 0).any() and (values > 0).any()):
        return np.nan
    monthly_irr = npf.irr(values)
    if monthly_irr is None or not np.isfinite(monthly_irr):
        return np.nan
    return float((1 + monthly_irr) ** 12 - 1)


def _npv(monthly_cash_flows: pd.Series, annual_rate: float) -> float:
    monthly_rate = (1 + annual_rate) ** (1 / 12) - 1
    return float(npf.npv(monthly_rate, monthly_cash_flows.to_numpy(dtype=float)))


def summarize_sites(site_monthly: pd.DataFrame, config: dict) -> pd.DataFrame:
    rate = float(config["model"]["discount_rate_annual"])
    terminal_multiple = float(config["model"]["terminal_value_multiple"])
    rows = []
    for (site_id, site_name, scenario), group in site_monthly.groupby(["site_id", "site_name", "scenario"]):
        group = group.sort_values("month").copy()
        terminal_value = max(float(group["ebitda_usd"].tail(12).sum()), 0.0) * terminal_multiple
        unlevered_cf = group["unlevered_free_cash_flow_usd"].copy()
        equity_cf = group["equity_cash_flow_usd"].copy()
        unlevered_cf.iloc[-1] += terminal_value
        equity_cf.iloc[-1] += max(terminal_value - float(group["ending_debt_balance_usd"].iloc[-1]), 0.0)
        total_capex = float(group["capex_usd"].sum())
        total_equity = float(group["equity_draw_usd"].sum())
        total_ebitda = float(group["ebitda_usd"].sum())
        rows.append({
            "site_id": site_id,
            "site_name": site_name,
            "scenario": scenario,
            "power_ready": group["power_ready"].iloc[0],
            "ready_for_service": group["rfs_month"].iloc[0],
            "total_capex_usd": total_capex,
            "gpu_capex_usd": float(group["gpu_capex_usd"].sum()),
            "total_revenue_usd": float(group["revenue_usd"].sum()),
            "total_opex_usd": float(group["opex_usd"].sum()),
            "total_ebitda_usd": total_ebitda,
            "total_equity_draw_usd": total_equity,
            "total_debt_draw_usd": float(group["debt_draw_usd"].sum()),
            "interest_during_construction_usd": float(group["interest_during_construction_usd"].sum()),
            "ending_debt_balance_usd": float(group["ending_debt_balance_usd"].iloc[-1]),
            "peak_gpu_online": int(group["gpu_online"].max()),
            "mature_utilization": float(group["utilization"].max()),
            "unlevered_npv_usd": _npv(unlevered_cf, rate),
            "unlevered_irr": _annualized_irr(unlevered_cf),
            "equity_irr": _annualized_irr(equity_cf),
            "roic_horizon": total_ebitda / total_capex if total_capex else np.nan,
            "revenue_to_capex": float(group["revenue_usd"].sum()) / total_capex if total_capex else np.nan,
            "terminal_value_usd": terminal_value,
        })
    return pd.DataFrame(rows)


def summarize_portfolio(site_monthly: pd.DataFrame, config: dict) -> pd.DataFrame:
    model_cfg = config["model"]
    cols = [
        "capex_usd", "gpu_capex_usd", "revenue_usd", "opex_usd", "ebitda_usd",
        "operating_cash_flow_usd", "equity_draw_usd", "debt_draw_usd", "debt_service_usd",
        "interest_during_construction_usd", "unlevered_free_cash_flow_usd",
        "net_cash_flow_post_financing_usd", "gpu_online", "it_load_online_mw",
        "facility_load_online_mw", "power_mwh",
    ]
    portfolio = site_monthly.groupby(["month", "scenario"], as_index=False)[cols].sum()
    starting_cash = float(model_cfg["starting_cash_usd"])
    minimum_cash = float(model_cfg["minimum_cash_usd"])
    portfolio["cumulative_cash_change_usd"] = portfolio["net_cash_flow_post_financing_usd"].cumsum()
    portfolio["cash_balance_pre_support_usd"] = starting_cash + portfolio["cumulative_cash_change_usd"]
    portfolio["incremental_funding_required_usd"] = (
        minimum_cash - portfolio["cash_balance_pre_support_usd"]
    ).clip(lower=0)
    portfolio["funding_raise_usd"] = portfolio["incremental_funding_required_usd"].diff().fillna(
        portfolio["incremental_funding_required_usd"]
    ).clip(lower=0)
    portfolio["cash_balance_usd"] = portfolio["cash_balance_pre_support_usd"] + portfolio["funding_raise_usd"].cumsum()
    portfolio["liquidity_headroom_usd"] = portfolio["cash_balance_usd"] - minimum_cash
    return portfolio
