from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))
from src.dashboard import load_dashboard_data, executive_kpis  # noqa: E402

st.set_page_config(page_title="AI Infrastructure Finance Dashboard", layout="wide")
data = load_dashboard_data(BASE_DIR / "data" / "outputs")
k = executive_kpis(data)

st.title("AI Datacenter Capital Forecasting Engine")
st.caption("Executive dashboard — synthetic, seeded and reproducible")

cols = st.columns(6)
cols[0].metric("Base CapEx", f"${k['base_total_capex_usd']/1e9:.2f}B")
cols[1].metric("Base NPV", f"${k['base_portfolio_npv_usd']/1e9:.2f}B")
cols[2].metric("Funding Need", f"${k['base_incremental_funding_usd']/1e6:.0f}M")
cols[3].metric("Peak GPUs", f"{k['peak_gpu_online']:,}")
cols[4].metric("Peak IT Load", f"{k['peak_it_load_mw']:.0f} MW")
cols[5].metric("MC Positive NPV", f"{k['mc_positive_npv_probability']:.1%}")

tabs = st.tabs(["Portfolio", "Sites", "Scenarios", "Capital Stack", "Risk"])

with tabs[0]:
    p = data.portfolio.copy()
    p["cumulative_capex_usd"] = p["capex_usd"].cumsum()
    st.plotly_chart(px.line(p, x="month", y=["cumulative_capex_usd", "cash_balance_usd", "liquidity_headroom_usd"], title="Capital and Liquidity"), use_container_width=True)
    st.plotly_chart(px.line(p, x="month", y=["gpu_online", "it_load_online_mw"], title="Capacity Online"), use_container_width=True)

with tabs[1]:
    st.dataframe(data.sites, use_container_width=True)
    st.plotly_chart(px.bar(data.sites, x="site_name", y="unlevered_npv_usd", text="unlevered_irr", title="Site-Level NPV and IRR"), use_container_width=True)

with tabs[2]:
    st.dataframe(data.scenarios, use_container_width=True)
    st.plotly_chart(px.scatter(data.scenarios, x="total_capex_usd", y="portfolio_unlevered_npv_usd", size="incremental_funding_required_usd", text="scenario", title="Scenario Tradeoff"), use_container_width=True)

with tabs[3]:
    st.dataframe(data.capital_stacks, use_container_width=True)
    st.plotly_chart(px.scatter(data.capital_stacks, x="estimated_dilution_pct", y="equity_irr", size="sponsor_equity_usd", text="capital_stack", symbol="coverage_pass", title="Capital Structure Tradeoff"), use_container_width=True)

with tabs[4]:
    st.plotly_chart(px.histogram(data.monte_carlo_simulations, x="portfolio_unlevered_npv_usd", nbins=35, title="Monte Carlo NPV Distribution"), use_container_width=True)
    st.dataframe(data.monte_carlo_summary, use_container_width=True)
    s = data.risk_sensitivity[data.risk_sensitivity["outcome"] == "portfolio_unlevered_npv_usd"]
    st.plotly_chart(px.bar(s, x="pearson_correlation", y="risk_driver", orientation="h", title="NPV Risk Sensitivity"), use_container_width=True)
