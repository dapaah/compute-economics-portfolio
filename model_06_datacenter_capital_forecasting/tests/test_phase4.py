from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.dashboard import build_dashboard_html, executive_kpis, load_dashboard_data, write_executive_summary  # noqa: E402


def test_dashboard_inputs_load():
    data = load_dashboard_data(ROOT / "data" / "outputs")
    assert len(data.portfolio) == 60
    assert len(data.sites) == 3
    assert set(data.scenarios["scenario"]) >= {"base", "upside", "downside", "severe_downside"}


def test_executive_kpis_reconcile():
    data = load_dashboard_data(ROOT / "data" / "outputs")
    kpis = executive_kpis(data)
    assert kpis["peak_gpu_online"] == 39000
    assert kpis["base_total_capex_usd"] > 4_000_000_000
    assert 0 <= kpis["mc_positive_npv_probability"] <= 1


def test_static_assets_generate(tmp_path):
    data = load_dashboard_data(ROOT / "data" / "outputs")
    html = tmp_path / "dashboard.html"
    brief = tmp_path / "brief.md"
    build_dashboard_html(data, html)
    write_executive_summary(data, brief)
    assert html.exists() and html.stat().st_size > 10_000
    assert "Executive Dashboard" in html.read_text(encoding="utf-8")
    assert "Decision summary" in brief.read_text(encoding="utf-8")
