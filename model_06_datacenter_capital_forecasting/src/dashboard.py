from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


@dataclass
class DashboardData:
    portfolio: pd.DataFrame
    sites: pd.DataFrame
    scenarios: pd.DataFrame
    capital_stacks: pd.DataFrame
    monte_carlo_summary: pd.DataFrame
    monte_carlo_simulations: pd.DataFrame
    risk_sensitivity: pd.DataFrame


def load_dashboard_data(outputs_dir: Path) -> DashboardData:
    portfolio = pd.read_csv(outputs_dir / "portfolio_monthly_forecast.csv", parse_dates=["month"])
    sites = pd.read_csv(outputs_dir / "site_summary.csv", parse_dates=["power_ready", "ready_for_service"])
    scenarios = pd.read_csv(outputs_dir / "scenario_comparison.csv", parse_dates=["latest_ready_for_service"])
    capital_stacks = pd.read_csv(outputs_dir / "capital_stack_comparison.csv")
    monte_carlo_summary = pd.read_csv(outputs_dir / "monte_carlo_summary.csv")
    monte_carlo_simulations = pd.read_csv(outputs_dir / "monte_carlo_simulations.csv")
    risk_sensitivity = pd.read_csv(outputs_dir / "risk_sensitivity.csv")
    return DashboardData(portfolio, sites, scenarios, capital_stacks, monte_carlo_summary, monte_carlo_simulations, risk_sensitivity)


def _money(v: float) -> str:
    sign = "-" if v < 0 else ""
    n = abs(float(v))
    if n >= 1e9:
        return f"{sign}${n/1e9:.2f}B"
    if n >= 1e6:
        return f"{sign}${n/1e6:.0f}M"
    return f"{sign}${n:,.0f}"


def executive_kpis(data: DashboardData) -> Dict[str, object]:
    base = data.scenarios.loc[data.scenarios["scenario"] == "base"].iloc[0]
    mc = data.monte_carlo_summary.set_index("metric")
    best_stack = data.capital_stacks.sort_values(["coverage_pass", "equity_irr"], ascending=[False, False]).iloc[0]
    return {
        "base_total_capex_usd": float(base["total_capex_usd"]),
        "base_portfolio_npv_usd": float(base["portfolio_unlevered_npv_usd"]),
        "base_incremental_funding_usd": float(base["incremental_funding_required_usd"]),
        "peak_gpu_online": int(base["peak_gpu_online"]),
        "peak_it_load_mw": float(data.portfolio["it_load_online_mw"].max()),
        "mc_p50_npv_usd": float(mc.loc["portfolio_unlevered_npv_usd", "p50"]),
        "mc_positive_npv_probability": float((data.monte_carlo_simulations["portfolio_unlevered_npv_usd"] > 0).mean()),
        "best_coverage_stack": str(best_stack["capital_stack"]),
    }


def build_dashboard_html(data: DashboardData, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    kpis = executive_kpis(data)

    portfolio = data.portfolio.copy()
    portfolio["cumulative_capex_usd"] = portfolio["capex_usd"].cumsum()

    fig1 = make_subplots(specs=[[{"secondary_y": True}]])
    fig1.add_trace(go.Scatter(x=portfolio["month"], y=portfolio["cumulative_capex_usd"], name="Cumulative CapEx"), secondary_y=False)
    fig1.add_trace(go.Scatter(x=portfolio["month"], y=portfolio["gpu_online"], name="GPUs Online"), secondary_y=True)
    fig1.update_layout(title="Deployment and Capital Build")
    fig1.update_yaxes(title_text="Cumulative CapEx (USD)", secondary_y=False)
    fig1.update_yaxes(title_text="GPUs Online", secondary_y=True)

    fig2 = make_subplots(specs=[[{"secondary_y": True}]])
    fig2.add_trace(go.Bar(x=portfolio["month"], y=portfolio["capex_usd"], name="Monthly CapEx"), secondary_y=False)
    fig2.add_trace(go.Scatter(x=portfolio["month"], y=portfolio["cash_balance_usd"], name="Cash Balance"), secondary_y=True)
    fig2.add_trace(go.Scatter(x=portfolio["month"], y=portfolio["liquidity_headroom_usd"], name="Liquidity Headroom"), secondary_y=True)
    fig2.update_layout(title="Monthly Capital Deployment and Liquidity")

    scen = data.scenarios.copy()
    fig3 = px.scatter(
        scen,
        x="total_capex_usd",
        y="portfolio_unlevered_npv_usd",
        size="incremental_funding_required_usd",
        text="scenario",
        hover_data=["weighted_unlevered_irr", "latest_ready_for_service"],
        title="Scenario Tradeoff: Installed Cost, NPV, and Funding Need",
    )
    fig3.update_traces(textposition="top center")

    stacks = data.capital_stacks.copy()
    fig4 = px.scatter(
        stacks,
        x="estimated_dilution_pct",
        y="equity_irr",
        size="sponsor_equity_usd",
        text="capital_stack",
        symbol="coverage_pass",
        hover_data=["minimum_dscr", "incremental_funding_required_usd", "weighted_dscr"],
        title="Capital Stack Tradeoff: Dilution, Equity IRR, and Coverage",
    )
    fig4.update_traces(textposition="top center")

    sims = data.monte_carlo_simulations.copy()
    fig5 = px.histogram(sims, x="portfolio_unlevered_npv_usd", nbins=35, title="Monte Carlo Portfolio NPV Distribution")
    fig5.add_vline(x=0)

    sens = data.risk_sensitivity[data.risk_sensitivity["outcome"] == "portfolio_unlevered_npv_usd"].copy()
    sens = sens.reindex(sens["pearson_correlation"].abs().sort_values().index)
    fig6 = px.bar(sens, x="pearson_correlation", y="risk_driver", orientation="h", title="Risk Sensitivity: Drivers of Portfolio NPV")

    site = data.sites.copy()
    fig7 = px.bar(site, x="site_name", y="unlevered_npv_usd", text="unlevered_irr", hover_data=["total_capex_usd", "peak_gpu_online", "ready_for_service"], title="Site-Level Returns")
    fig7.update_traces(texttemplate="IRR %{text:.1%}", textposition="outside")

    cards = f"""
    <div class='cards'>
      <div class='card'><span>Base CapEx</span><strong>{_money(kpis['base_total_capex_usd'])}</strong></div>
      <div class='card'><span>Base NPV</span><strong>{_money(kpis['base_portfolio_npv_usd'])}</strong></div>
      <div class='card'><span>Funding Need</span><strong>{_money(kpis['base_incremental_funding_usd'])}</strong></div>
      <div class='card'><span>Peak GPUs</span><strong>{kpis['peak_gpu_online']:,}</strong></div>
      <div class='card'><span>Peak IT Load</span><strong>{kpis['peak_it_load_mw']:.0f} MW</strong></div>
      <div class='card'><span>MC Positive NPV</span><strong>{kpis['mc_positive_npv_probability']:.1%}</strong></div>
    </div>
    """

    figures = [fig1, fig2, fig3, fig4, fig5, fig6, fig7]
    divs = []
    for i, fig in enumerate(figures):
        divs.append(fig.to_html(full_html=False, include_plotlyjs="cdn" if i == 0 else False, config={"displaylogo": False}))

    html = f"""<!doctype html>
<html><head><meta charset='utf-8'><title>AI Datacenter Capital Forecasting — Executive Dashboard</title>
<style>
body{{font-family:Arial,sans-serif;margin:0;background:#f6f7f9;color:#1d2530}} header{{padding:28px 42px;background:#111827;color:white}}
main{{max-width:1400px;margin:auto;padding:24px}} .cards{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:22px}}
.card{{background:white;border:1px solid #dfe3e8;border-radius:10px;padding:16px;box-shadow:0 1px 3px rgba(0,0,0,.06)}}
.card span{{display:block;font-size:12px;text-transform:uppercase;color:#667085}} .card strong{{display:block;font-size:27px;margin-top:8px}}
.panel{{background:white;border:1px solid #dfe3e8;border-radius:10px;padding:8px;margin:16px 0;box-shadow:0 1px 3px rgba(0,0,0,.05)}}
.note{{font-size:13px;color:#667085}} @media(max-width:800px){{.cards{{grid-template-columns:1fr 1fr}}}}
</style></head><body>
<header><h1>AI Datacenter Capital Forecasting Engine</h1><p>Executive dashboard — deployment, liquidity, risk, capital structure, and returns</p></header>
<main>{cards}<p class='note'>Illustrative, synthetic and seeded data. All results are generated by the repository model.</p>
{''.join(f"<div class='panel'>{d}</div>" for d in divs)}
</main></body></html>"""
    output_path.write_text(html, encoding="utf-8")


def write_executive_summary(data: DashboardData, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    k = executive_kpis(data)
    scenarios = data.scenarios.set_index("scenario")
    base = scenarios.loc["base"]
    downside = scenarios.loc["downside"]
    severe = scenarios.loc["severe_downside"]
    sensitivity = data.risk_sensitivity[data.risk_sensitivity["outcome"] == "portfolio_unlevered_npv_usd"].copy()
    sensitivity["abs_corr"] = sensitivity["pearson_correlation"].abs()
    top_risks = sensitivity.sort_values("abs_corr", ascending=False).head(3)["risk_driver"].tolist()
    lines = [
        "# AI Datacenter Capital Forecasting — Executive Brief",
        "",
        "## Decision summary",
        f"The deterministic base case deploys **{k['peak_gpu_online']:,} GPUs** and **{k['peak_it_load_mw']:.0f} MW** of IT load against **{_money(k['base_total_capex_usd'])}** of CapEx, producing **{_money(k['base_portfolio_npv_usd'])}** of unlevered NPV.",
        f"The same plan requires **{_money(k['base_incremental_funding_usd'])}** of incremental liquidity support under the configured minimum-cash policy.",
        "",
        "## Risk view",
        f"The Monte Carlo median NPV is **{_money(k['mc_p50_npv_usd'])}**, with only **{k['mc_positive_npv_probability']:.1%}** of simulations producing a positive NPV.",
        f"The downside case reduces NPV to **{_money(downside['portfolio_unlevered_npv_usd'])}** and increases funding need to **{_money(downside['incremental_funding_required_usd'])}**; severe downside reaches **{_money(severe['portfolio_unlevered_npv_usd'])}** of NPV and **{_money(severe['incremental_funding_required_usd'])}** of funding need.",
        f"The most material modeled NPV drivers are **{', '.join(top_risks)}**.",
        "",
        "## Capital structure view",
        "Non-dilutive support and customer capital improve sponsor returns and reduce dilution, but leveraged structures fail the illustrative DSCR thresholds during ramp. Financing should therefore be sequenced to operating stabilization, sculpted to cash generation, or supported by reserves and additional non-dilutive capital.",
        "",
        "## Recommended executive actions",
        "1. Treat utilization ramp and installed cost as board-level value drivers, not operating details.",
        "2. Stage debt conversion or amortization after site stabilization rather than maximizing construction leverage.",
        "3. Maintain explicit liquidity triggers tied to power-ready, commissioning, and revenue-ramp milestones.",
        "4. Use the scenario and Monte Carlo outputs to sequence sites and capital raises before committing the full portfolio.",
        "",
        "*Illustrative, synthetic and seeded data. This brief is generated from the repository outputs.*",
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")


def write_kpi_json(data: DashboardData, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(executive_kpis(data), indent=2), encoding="utf-8")
