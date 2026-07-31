from __future__ import annotations

import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from src.model import run  # noqa: E402


class DeterministicForecastTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.results = run(BASE_DIR)
        cls.site = cls.results["site_monthly"]
        cls.portfolio = cls.results["portfolio_monthly"]
        cls.summary = cls.results["site_summary"]

    def test_three_sites_and_sixty_months(self) -> None:
        self.assertEqual(self.summary["site_id"].nunique(), 3)
        self.assertEqual(self.portfolio["month"].nunique(), 60)

    def test_capex_reconciles_to_input_plan(self) -> None:
        self.assertAlmostEqual(self.summary["total_capex_usd"].sum(), 4_345_000_000, delta=10)

    def test_power_and_rfs_gates(self) -> None:
        pre_rfs = self.site[self.site["month"] < self.site["rfs_month"]]
        self.assertEqual(int(pre_rfs["gpu_online"].max()), 0)
        self.assertEqual(float(pre_rfs["revenue_usd"].max()), 0.0)

    def test_gpu_deployment_is_phased(self) -> None:
        post_rfs = self.site[self.site["rfs_gate_open"]]
        first_online = post_rfs.groupby("site_id").first()
        self.assertTrue((first_online["gpu_online"] < first_online["target_gpu_count"]).all())
        self.assertEqual(int(self.summary["peak_gpu_online"].sum()), 39_000)

    def test_financing_funds_capex(self) -> None:
        funded = self.site["equity_draw_usd"] + self.site["debt_draw_usd"]
        self.assertLess(float((funded - self.site["capex_usd"]).abs().max()), 1.0)

    def test_return_metrics_exist(self) -> None:
        self.assertTrue(self.summary["unlevered_npv_usd"].notna().all())
        self.assertTrue((self.summary["terminal_value_usd"] > 0).all())

    def test_liquidity_floor_is_preserved_after_support(self) -> None:
        minimum = float(self.results["config"]["model"]["minimum_cash_usd"])
        self.assertGreaterEqual(float(self.portfolio["cash_balance_usd"].min()), minimum - 1.0)


if __name__ == "__main__":
    unittest.main()
