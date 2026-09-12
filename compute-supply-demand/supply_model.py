"""US capacity scenarios: critical paths, opening cohorts and turbine queues.

Transformer scarcity is a lead-time constraint; only turbines have a throughput
ceiling. Annual landing interpolation is not a project-level COD forecast.
Inherited public inputs have not been independently reverified.
"""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass, field, replace
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
from model_core import Params, cohorts, number, weights, year, service_cohorts


@dataclass(frozen=True)
class Pathway:
    name: str
    components: dict
    development_gate: float
    power_gate: float
    share_of_announcements: float
    equipment_ceiling_gw_yr: float | None = None

    @property
    def lead_time_months(self):
        return max(self.components.values())

    @property
    def lead_time_years(self):
        return self.lead_time_months / 12

    @property
    def project_conversion(self):
        return self.development_gate * self.power_gate


@dataclass
class SupplyModel:
    p: Params
    start_year: int | None = None
    horizon_years: int | None = None
    pathways: dict = field(default_factory=dict)

    def __post_init__(self):
        self.start_year = self.reference_year if self.start_year is None else self.start_year
        self.horizon_years = self.p.get("model.horizon_years") if self.horizon_years is None else self.horizon_years
        year(self.start_year, "start_year")
        year(self.horizon_years, "horizon_years")
        if self.start_year < self.reference_year:
            raise ValueError("start_year must be at or after reference_year")
        self._build_pathways()

    @property
    def reference_year(self):
        return year(self.p.get("model.reference_year"), "reference_year")

    @classmethod
    def from_json(cls, path, **kwargs):
        return cls(Params(json.loads(Path(path).read_text(encoding="utf-8"))), **kwargs)

    def _turbine_ceiling_gw_yr(self, dc_share):
        p = self.p
        low = p.numeric("turbine_supply.industry_annual_capacity_gw_low")
        high = p.numeric("turbine_supply.industry_annual_capacity_gw_high")
        if high < low:
            raise ValueError("Turbine capacity range is reversed")
        return ((low+high)/2 * p.numeric("turbine_supply.us_share_of_turbine_output", maximum=1)
                * number(dc_share, "dc_turbine_share", maximum=1)
                / p.numeric("conversion_ratios.generation_nameplate_per_gw_it_load", positive=True))

    def _build_pathways(self, dc_turbine_share=None, aero_turbine_share=None):
        p = self.p
        dc = p.numeric("turbine_supply.data_center_share_of_us_turbine_output", maximum=1) if dc_turbine_share is None else dc_turbine_share
        aero = p.numeric("model.aero_turbine_share", maximum=1) if aero_turbine_share is None else number(aero_turbine_share, "aero_turbine_share", maximum=1)
        cap = self._turbine_ceiling_gw_yr(dc)
        dev = p.numeric("pipeline.share_under_active_development", maximum=1)
        queue = p.numeric("model.grid_lifetime_conversion_proxy", maximum=1)
        shares = weights(p.get("model.pathway_shares"), "pathway_shares")
        if set(shares) != {"grid_queue", "btm_large_frame", "btm_aeroderivative", "colo_lease"}:
            raise ValueError("pathway_shares must name exactly the four supported routes")
        common = {
            "site_permitting": p.numeric("model.site_permitting_months"),
            "shell_fitout": p.numeric("equipment_lead_times_months.site_build_shell_and_fitout"),
            "transformer": p.numeric("equipment_lead_times_months.power_substation_transformer"),
            "switchgear": p.numeric("equipment_lead_times_months.mv_switchgear_38kv"),
            "commissioning_ready": p.numeric("model.commissioning_ready_months"),
        }
        def route(name, extras, gate, power, ceiling=None):
            return Pathway(name, {**common, **extras}, gate, power, shares[name], ceiling)
        self.pathways = {"base": [
            route("grid_queue", {"interconnection": p.numeric("grid_interconnection.median_ir_to_cod_years")*12}, dev, min(1,queue/dev) if dev else 0),
            route("btm_large_frame", {"generation": p.numeric("equipment_lead_times_months.large_frame_gas_turbine"), "gsu": p.numeric("equipment_lead_times_months.gsu_transformer")}, dev, p.numeric("model.large_frame_power_gate", maximum=1), cap*(1-aero)),
            route("btm_aeroderivative", {"generation": p.numeric("equipment_lead_times_months.aeroderivative_gas_turbine"), "gsu": p.numeric("equipment_lead_times_months.gsu_transformer")}, dev, p.numeric("model.aero_power_gate", maximum=1), cap*aero),
            route("colo_lease", {}, p.numeric("model.colo_development_gate", maximum=1), p.numeric("model.colo_power_gate", maximum=1)),
        ]}

        base = self.pathways["base"]
        topologies = p.get("model.supply_topologies")
        if not isinstance(topologies, dict) or topologies.get("base") != {}:
            raise ValueError("Supply topologies require an unchanged base")
        for label, exclusions in topologies.items():
            if not isinstance(exclusions, dict) or set(exclusions) - {pw.name for pw in base}:
                raise ValueError("Unknown topology pathway")
            routes = []
            for pw in base:
                omitted = exclusions.get(pw.name, [])
                if not isinstance(omitted, list) or any(k not in pw.components for k in omitted):
                    raise ValueError("Unknown topology component")
                components = {k: v for k, v in pw.components.items() if k not in omitted}
                if not components:
                    raise ValueError("Topology must retain readiness components")
                routes.append(replace(pw, components=components))
            self.pathways[label] = routes

    def run(self, announced_gw_by_year=None, scenario="base", dc_turbine_share=None,
            include_in_flight=True, aero_turbine_share=None, opening_scale=1.0):
        """Annual arrivals, deliveries and ending backlog, simulated from 2026.

        Default opening announcements are illustrative, replacing the old
        construction stock entirely. include_in_flight=False excludes them.
        An explicit mapping is the complete ledger, never supplemented. No
        pre-reference rationing or equipment backlog is inferred.
        """
        if scenario not in self.p.get("model.supply_topologies"):
            raise ValueError(f"Unsupported supply scenario: {scenario}")
        if not isinstance(include_in_flight, bool):
            raise ValueError("include_in_flight must be boolean")
        scale = number(opening_scale, "opening_scale")
        self._build_pathways(dc_turbine_share, aero_turbine_share)
        if self.p.get("model.landing_rule") != "linear_calendar_interpolation":
            raise ValueError("Unsupported landing_rule")
        if self.p.numeric("model.opening_equipment_backlog_gw") != 0:
            raise ValueError("A nonzero opening backlog requires a cohort ledger")
        end = self.start_year+self.horizon_years
        if announced_gw_by_year is None:
            flow = self.p.numeric("pipeline.annual_announcement_flow_gw")
            announced = {y:flow for y in range(self.reference_year,end)}
            if include_in_flight:
                opening = cohorts(self.p.get("model.opening_announcements_gw"), json_keys=True)
                if any(y >= self.reference_year for y in opening):
                    raise ValueError("Opening announcements must precede reference_year")
                announced.update({y:gw*scale for y,gw in opening.items()})
        else:
            announced = cohorts(announced_gw_by_year, "announced_gw_by_year")
        rows = []
        cohort_ledger = []
        beyond = 0.0
        for pw in self.pathways[scenario]:
            arrivals = {}
            for cy, gw in sorted(announced.items()):
                exact = cy+pw.lead_time_years
                low = math.floor(exact)
                fraction = exact-low
                for y,w in ((low,1-fraction),(low+1,fraction)):
                    volume = gw*pw.share_of_announcements*pw.project_conversion*w
                    if volume:
                        cohort_ledger.append(dict(announcement_year=cy,pathway=pw.name,
                            scheduled_year=y,scheduled_gw=volume,
                            cohort="opening" if cy < self.reference_year else "forecast",
                            window="before_reference" if y < self.reference_year else "after_horizon" if y >= end else "within_simulation"))
                    if volume and y >= self.reference_year:
                        arrivals.setdefault(y,[]).append([cy,volume])
                        if y >= end:
                            beyond += volume
            queue = deque()
            for y in range(self.reference_year,end):
                carry = sum(v for _,v in queue)
                incoming = arrivals.get(y,[])
                new = sum(v for _,v in incoming)
                queue.extend([cy,v] for cy,v in incoming)
                available = carry+new
                capacity = pw.equipment_ceiling_gw_yr
                delivered = min(available,capacity) if capacity is not None else available
                remaining = delivered
                opening_delivered = current_delivered = 0.0
                while queue and remaining > 1e-12:
                    cy,volume = queue[0]
                    taken = min(remaining,volume)
                    if cy < self.reference_year:
                        opening_delivered += taken
                    else:
                        current_delivered += taken
                    remaining -= taken
                    if taken >= volume:
                        queue.popleft()
                    else:
                        queue[0][1] -= taken
                if y >= self.start_year:
                    rows.append(dict(year=y,pathway=pw.name,uncapped_gw=new,
                        backlog_start_gw=carry,equipment_ceiling_gw=capacity,
                        energized_gw=delivered,equipment_backlog_gw=max(0,available-delivered),
                        opening_cohort_energized_gw=opening_delivered,
                        forecast_cohort_energized_gw=current_delivered,
                        lead_time_months=pw.lead_time_months,
                        binding_constraints=";".join(k for k,v in pw.components.items() if v == pw.lead_time_months),
                        project_conversion=pw.project_conversion))
        df = pd.DataFrame(rows)
        df.attrs["announced_total_gw"] = sum(v for y,v in announced.items() if y >= self.reference_year)
        df.attrs["scheduled_after_horizon_gw"] = beyond
        df.attrs["cohort_ledger"] = cohort_ledger
        return df

    def summarise(self,df):
        cols = ["energized_gw","uncapped_gw","backlog_start_gw","equipment_backlog_gw","opening_cohort_energized_gw","forecast_cohort_energized_gw"]
        result = df.groupby("year",as_index=False)[cols].sum()
        result["cumulative_energized_gw"] = result.energized_gw.cumsum()
        return result

    def headline_conversion(self,df):
        """Censored window delivery / supplied post-reference announcements.

        Uses this run's metadata, never mutable model state. Not a lifetime
        conversion probability; later deliveries are outside the numerator.
        """
        if "announced_total_gw" not in df.attrs:
            raise ValueError("Conversion requires the original run metadata")
        denominator = df.attrs["announced_total_gw"]
        return df.forecast_cohort_energized_gw.sum()/denominator if denominator else np.nan

    def validate(self,df):
        """Explicitly reject the former stock-as-flow calibration benchmark."""
        first = float(df.groupby("year").energized_gw.sum().get(self.start_year,np.nan))
        benchmark = self.p.get("validation.cbre_primary_inventory_2025_gw")
        return pd.DataFrame([dict(model_year=self.start_year, modelled_energized_additions_gw=first,
            rejected_benchmark_gw=benchmark,
            status="No compatible annual US delivery observation; no historical accuracy claim",
            reason=f"{benchmark} GW is CBRE primary-market inventory stock, not annual US delivery")])

    def backtest(self, df, observations, *, snapshot_as_of, observation_scope):
        """Score same-year frozen predictions against a compatible realized series.

        The caller must supply an archived parameter/announcement snapshot made
        before the first scored year. This API cannot authenticate that archive.
        Current parameters are not a historical backtest dataset.
        """
        from datetime import date
        cutoff = date.fromisoformat(snapshot_as_of)
        if observation_scope != "US_all_new_energized_IT_GW":
            raise ValueError("Backtest requires US all-market annual energized IT additions")
        obs = cohorts(observations, "observations")
        if not obs or cutoff.year >= min(obs):
            raise ValueError("Snapshot must precede every scored year")
        modelled = self.summarise(df).set_index("year").energized_gw.to_dict()
        if any(y not in modelled for y in obs):
            raise ValueError("Every observed year must exist in model output")
        return pd.DataFrame([dict(year=y, observed_gw=v, predicted_gw=modelled[y],
            error_gw=modelled[y]-v, absolute_error_gw=abs(modelled[y]-v),
            percentage_error=(modelled[y]-v)/v if v else np.nan,
            snapshot_as_of=snapshot_as_of, scope=observation_scope)
            for y,v in sorted(obs.items())])

    def booking_cohorts(self):
        p = self.p
        end = self.start_year+self.horizon_years
        opening = cohorts(p.get("model.opening_bookings_us_gw"),json_keys=True)
        if any(y >= self.reference_year for y in opening):
            raise ValueError("Opening bookings must precede reference_year")
        base = p.numeric("demand.na_absorption_h1_2026_gw")*p.numeric("model.h1_annualization_factor")*p.numeric("model.bookings_us_share",maximum=1)
        growth = p.get("model.booking_growth")
        if set(growth) != {"low","base","high"}:
            raise ValueError("booking_growth must contain low, base, high")
        rows = []
        for label,g in growth.items():
            g = number(g,"booking_growth",positive=True)
            signed = {**opening, **{y:base*g**(y-self.reference_year) for y in range(self.reference_year,end)}}
            for row in service_cohorts(signed,p.get("model.booking_delivery_weights"),self.reference_year,end):
                rows.append(dict(scenario=label, geography="US", **row))
        return pd.DataFrame(rows)

    def demand_vs_supply(self,df):
        """US requested-service cohorts versus US energized additions.

        Signed bookings are retained separately. This aggregate comparison
        cannot establish customer matching, cancellation or utilization.
        """
        out = self.summarise(df)[["year","energized_gw"]].copy()
        ledger = self.booking_cohorts()
        for label in ("low", "base", "high"):
            subset = ledger[ledger.scenario == label]
            signed = subset.groupby("booking_year").signed_gw.first()
            required = subset.groupby("requested_service_year").requested_gw.sum()
            out[f"signed_us_bookings_{label}_gw"] = out.year.map(signed)
            out[f"required_service_{label}_gw"] = out.year.map(required).fillna(0)
        out["gap_vs_base_gw"] = out.energized_gw-out.required_service_base_gw
        out["coverage_ratio"] = out.energized_gw/out.required_service_base_gw.replace(0,np.nan)
        return out


@dataclass
class ErcotFunnel:
    p: Params

    def observed(self):
        """Dated snapshots, not a matched-cohort conversion funnel."""
        entries = [("Large-load queue","ercot.large_load_queue_gw"),
            ("Approval to energize","ercot.approval_to_energize_gw"),
            ("Observed peak consumption","ercot.observed_peak_large_load_gw")]
        return pd.DataFrame([dict(stage=label,gw=self.p.numeric(path),
            date=self.p._node(path)["date"],source=self.p.cite(path),
            note="Different dates and populations; not a conversion rate") for label,path in entries])

    def audit_shock(self):
        return {key:self.p.get("ercot."+key) for key in ("audit_start","audit_target_completion","batch_zero_study_slip")}

    def sub_threshold_capacity_gw(self):
        return self.p.numeric("ercot.medium_load_pipeline_mw")/1000
