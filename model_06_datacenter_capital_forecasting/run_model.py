from __future__ import annotations

from pathlib import Path

from src.model import run


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    results = run(base_dir)
    site_summary = results["site_summary"]
    portfolio = results["portfolio_monthly"]

    print("Model 6 Phase 1 deterministic forecast complete")
    print(f"Scenario: {results['config']['scenario']['active']}")
    print(f"Sites: {site_summary['site_id'].nunique()}")
    print(f"Forecast months: {portfolio['month'].nunique()}")
    print(f"Total modeled CapEx: ${site_summary['total_capex_usd'].sum():,.0f}")
    print(f"Peak GPUs online: {portfolio['gpu_online'].max():,.0f}")
    print(f"Peak IT load online: {portfolio['it_load_online_mw'].max():,.1f} MW")
    print(f"Minimum cash balance: ${portfolio['cash_balance_usd'].min():,.0f}")
    print(f"Incremental funding required: ${portfolio['funding_raise_usd'].sum():,.0f}")
    for row in site_summary.itertuples():
        irr = "n/m" if row.unlevered_irr != row.unlevered_irr else f"{row.unlevered_irr:.1%}"
        print(f"  {row.site_name}: NPV ${row.unlevered_npv_usd:,.0f}; unlevered IRR {irr}")
    print("Outputs written to data/outputs/")


if __name__ == "__main__":
    main()
