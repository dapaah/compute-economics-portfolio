from pathlib import Path

from src.dashboard import build_dashboard_html, load_dashboard_data, write_executive_summary, write_kpi_json


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    outputs = base_dir / "data" / "outputs"
    dashboard_outputs = outputs / "dashboard"
    data = load_dashboard_data(outputs)
    build_dashboard_html(data, dashboard_outputs / "executive_dashboard.html")
    write_executive_summary(data, dashboard_outputs / "executive_brief.md")
    write_kpi_json(data, dashboard_outputs / "executive_kpis.json")
    print(f"Wrote dashboard assets to {dashboard_outputs}")


if __name__ == "__main__":
    main()
