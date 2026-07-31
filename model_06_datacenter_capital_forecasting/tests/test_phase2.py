
from __future__ import annotations

import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from src.io import load_config, load_inputs, load_phase2_inputs
from src.monte_carlo import monte_carlo_summary, run_monte_carlo
from src.scenarios import run_scenario, scenario_comparison


class ScenarioRiskEngineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_config(BASE_DIR / "config" / "model_config.yml")
        cls.tables = load_inputs(BASE_DIR / "data" / "inputs")
        cls.phase2 = load_phase2_inputs(BASE_DIR / "data" / "inputs")
        cls.results = {str(r["scenario"]): run_scenario(cls.tables, cls.config, r) for _, r in cls.phase2["scenarios"].iterrows()}
        cls.comparison = scenario_comparison(cls.results)
        cls.mc, cls.mc_sites = run_monte_carlo(cls.tables, cls.config, cls.phase2["risk_assumptions"], simulations=50, seed=7)

    def test_four_deterministic_scenarios(self):
        self.assertEqual(set(self.comparison["scenario"]), {"base", "upside", "downside", "severe_downside"})

    def test_downside_capex_and_funding_exceed_base(self):
        x = self.comparison.set_index("scenario")
        self.assertGreater(x.loc["downside", "total_capex_usd"], x.loc["base", "total_capex_usd"])
        self.assertGreater(x.loc["downside", "incremental_funding_required_usd"], x.loc["base", "incremental_funding_required_usd"])

    def test_downside_npv_below_base(self):
        x = self.comparison.set_index("scenario")
        self.assertLess(x.loc["downside", "portfolio_unlevered_npv_usd"], x.loc["base", "portfolio_unlevered_npv_usd"])

    def test_schedule_delay_moves_rfs(self):
        x = self.comparison.set_index("scenario")
        self.assertGreater(x.loc["downside", "latest_ready_for_service"], x.loc["base", "latest_ready_for_service"])

    def test_monte_carlo_is_seeded_and_complete(self):
        mc2, _ = run_monte_carlo(self.tables, self.config, self.phase2["risk_assumptions"], simulations=50, seed=7)
        self.assertEqual(len(self.mc), 50)
        self.assertTrue(self.mc["total_capex_usd"].equals(mc2["total_capex_usd"]))

    def test_monte_carlo_outputs_vary(self):
        self.assertGreater(self.mc["total_capex_usd"].nunique(), 10)
        self.assertGreater(self.mc["portfolio_unlevered_npv_usd"].std(), 0)

    def test_probability_summary(self):
        summary = monte_carlo_summary(self.mc).set_index("metric")
        probability = summary.loc["probability_npv_positive", "mean"]
        self.assertGreaterEqual(probability, 0)
        self.assertLessEqual(probability, 1)


if __name__ == "__main__":
    unittest.main()
