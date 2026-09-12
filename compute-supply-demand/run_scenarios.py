"""Generate supply reports from the canonical parameters, from any directory."""
from pathlib import Path
import pandas as pd
from supply_model import SupplyModel, ErcotFunnel

HERE = Path(__file__).resolve().parent


def main():
    out = HERE / "outputs"
    out.mkdir(exist_ok=True)
    m = SupplyModel.from_json(HERE / "parameters.json")
    detail = m.run()
    reports = {
        "national_deliverable_capacity": m.summarise(detail),
        "pathway_detail": detail,
        "demand_vs_supply": m.demand_vs_supply(detail),
        "booking_service_cohorts": m.booking_cohorts(),
        "announcement_delivery_cohorts": pd.DataFrame(detail.attrs["cohort_ledger"]),
        "validation_diagnostic": m.validate(detail),
        "ercot_funnel": ErcotFunnel(m.p).observed(),
        "pathway_critical_paths": pd.DataFrame([
            dict(pathway=pw.name,component=k,months=v,binding=v==pw.lead_time_months)
            for pw in m.pathways["base"] for k,v in pw.components.items()]),
    }
    for name, param, override in (
        ("turbine_sensitivity","model.turbine_sensitivity","dc_turbine_share"),
        ("aero_sensitivity","model.aero_sensitivity","aero_turbine_share"),
        ("opening_cohort_sensitivity","model.opening_sensitivity","opening_scale"),
    ):
        rows=[]
        for value in m.p.get(param):
            run = m.run(**{override:value})
            summary = m.summarise(run)
            rows.append(dict(parameter=override,value=value,
                cumulative_energized_gw=summary.energized_gw.sum(),
                ending_equipment_backlog_gw=summary.equipment_backlog_gw.iloc[-1],
                scheduled_after_horizon_gw=run.attrs["scheduled_after_horizon_gw"]))
        reports[name] = pd.DataFrame(rows)
    topology_rows, component_rows = [], []
    for topology in m.p.get("model.supply_topologies"):
        run = m.run(scenario=topology)
        topology_rows.append(m.summarise(run).assign(topology=topology))
        for pw in m.pathways[topology]:
            for component, months in pw.components.items():
                component_rows.append(dict(topology=topology, pathway=pw.name,
                    component=component, months=months, binding=months==pw.lead_time_months))
    reports['topology_supply_comparison'] = pd.concat(topology_rows, ignore_index=True)
    reports['topology_components'] = pd.DataFrame(component_rows)
    reports['supply_parameter_registry'] = pd.DataFrame(m.p.registry())
    for name,frame in reports.items():
        frame.to_csv(out / f"{name}.csv",index=False)
    print(reports["national_deliverable_capacity"].to_string(index=False))
    print("\nIllustrative opening cohorts; most inherited sources not reverified; see parameter registries.")
    print("Censored forecast-cohort delivery ratio:",m.headline_conversion(detail))
    print(reports["validation_diagnostic"].to_string(index=False))


if __name__ == "__main__":
    main()
