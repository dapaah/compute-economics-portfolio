
from __future__ import annotations

from pathlib import Path

from src.io import load_config, load_inputs, load_phase2_inputs
from src.monte_carlo import monte_carlo_summary, risk_sensitivity, run_monte_carlo
from src.scenarios import run_scenario, scenario_comparison


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    config = load_config(base_dir / "config" / "model_config.yml")
    tables = load_inputs(base_dir / "data" / "inputs")
    phase2 = load_phase2_inputs(base_dir / "data" / "inputs")
    outputs = base_dir / "data" / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)

    deterministic = {}
    for _, row in phase2["scenarios"].iterrows():
        result = run_scenario(tables, config, row)
        name = str(row["scenario"])
        deterministic[name] = result
        result["site_summary"].to_csv(outputs / f"site_summary_{name}.csv", index=False)
        result["portfolio_monthly"].to_csv(outputs / f"portfolio_monthly_{name}.csv", index=False)
    comparison = scenario_comparison(deterministic)
    comparison.to_csv(outputs / "scenario_comparison.csv", index=False)

    simulations = int(config.get("risk", {}).get("monte_carlo_simulations", 500))
    seed = int(config.get("risk", {}).get("random_seed", 42))
    mc, mc_sites = run_monte_carlo(tables, config, phase2["risk_assumptions"], simulations=simulations, seed=seed)
    mc.to_csv(outputs / "monte_carlo_simulations.csv", index=False)
    mc_sites.to_csv(outputs / "monte_carlo_site_results.csv", index=False)
    monte_carlo_summary(mc).to_csv(outputs / "monte_carlo_summary.csv", index=False)
    risk_sensitivity(mc).to_csv(outputs / "risk_sensitivity.csv", index=False)

    print(comparison.to_string(index=False))
    print(f"\nCompleted {simulations} seeded Monte Carlo simulations.")


if __name__ == "__main__":
    main()
