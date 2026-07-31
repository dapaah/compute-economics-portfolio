from __future__ import annotations

from pathlib import Path

from .forecast import build_site_forecast, summarize_portfolio, summarize_sites
from .io import load_config, load_inputs


def run(base_dir: Path) -> dict:
    config = load_config(base_dir / "config" / "model_config.yml")
    tables = load_inputs(base_dir / "data" / "inputs")

    site_monthly = build_site_forecast(tables, config)
    site_summary = summarize_sites(site_monthly, config)
    portfolio_monthly = summarize_portfolio(site_monthly, config)

    output_dir = base_dir / "data" / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    site_monthly.to_csv(output_dir / "site_monthly_forecast.csv", index=False)
    portfolio_monthly.to_csv(output_dir / "portfolio_monthly_forecast.csv", index=False)
    site_summary.to_csv(output_dir / "site_summary.csv", index=False)

    return {
        "config": config,
        "site_monthly": site_monthly,
        "portfolio_monthly": portfolio_monthly,
        "site_summary": site_summary,
    }
