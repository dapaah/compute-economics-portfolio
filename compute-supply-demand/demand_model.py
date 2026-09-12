"""Capital-based AI capacity scenarios. Buyer shares describe funding, not chip
shipments. Workload mix is not consumer segmentation. Energized, ready and
occupied capacity are reported separately; revenue is an illustrative annual
run-rate opportunity, not recognized revenue or a contracted sales forecast.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from model_core import Params, cohorts, number, weights, year, service_cohorts


@dataclass
class DemandModel:
    p: Params
    start_year: int | None = None
    horizon_years: int | None = None
    mix_scenario: str = "base"

    def __post_init__(self):
        self.start_year = self.reference_year if self.start_year is None else self.start_year
        self.horizon_years = self.p.get("model.horizon_years") if self.horizon_years is None else self.horizon_years
        year(self.start_year, "start_year")
        year(self.horizon_years, "horizon_years")
        if self.start_year < self.reference_year:
            raise ValueError("start_year must be at or after reference_year")
        weights({k: self.p.numeric("buyer_segments."+k, maximum=1)
                 for k in ("hyperscaler_share", "neocloud_share", "enterprise_and_sovereign_share")}, "buyer shares")
        self.p.numeric("buyer_segments.hyperscaler_share", positive=True)
        self.p.numeric("unit_economics.capex_per_gw_usd_bn", positive=True)
        self.p.numeric("capital_deployed.hyperscaler_ai_tied_share", maximum=1)
        self.p.numeric("deployment_mode.hyperscaler_self_consumed_share", maximum=1)
        self.p.numeric("deployment_mode.neocloud_resold_share", maximum=1)
        self.p.numeric("deployment_mode.enterprise_merchant_share", maximum=1)

        terminal = self.p.get("customer_segment_mix.terminal_shares")
        expected = {"base", "hyperscaler-heavy", "neocloud-growth", "enterprise-sovereign-growth"}
        if not isinstance(terminal, dict) or set(terminal) != expected:
            raise ValueError("Invalid segment scenario labels")
        for label, values in terminal.items():
            if not isinstance(values, list) or len(values) != 3:
                raise ValueError("Segment paths need exactly three shares")
            weights(values, label)
        if self.mix_scenario not in expected | {"static-control"}:
            raise ValueError("Unknown customer segment scenario")
        last = year(self.p.get("customer_segment_mix.end_year"), "mix end year")
        if last <= self.reference_year or self.start_year+self.horizon_years-1 > last:
            raise ValueError("Reporting horizon outside supported segment path")

    def shares_for_year(self, calendar_year):
        """Derived linear interpolation of assumed funding-share endpoints."""
        y = year(calendar_year)
        last = self.p.get("customer_segment_mix.end_year")
        if not self.reference_year <= y <= last:
            raise ValueError("Year outside supported segment path")
        opening = [self.p.get("buyer_segments."+k) for k in
                   ("hyperscaler_share", "neocloud_share", "enterprise_and_sovereign_share")]
        target = opening if self.mix_scenario == "static-control" else self.p.get(
            "customer_segment_mix.terminal_shares")[self.mix_scenario]
        t = (y-self.reference_year)/(last-self.reference_year)
        result = [a+(b-a)*t for a,b in zip(opening,target)]
        return weights(result, "annual segment shares")

    @property
    def reference_year(self):
        return year(self.p.get("model.reference_year"), "reference_year")

    @classmethod
    def from_json(cls, path: str | Path, **kw) -> "DemandModel":
        return cls(p=Params(json.loads(Path(path).read_text(encoding="utf-8"))), **kw)

    # ------------------------------------------------------------- level 1-4

    def ai_tied_capital_usd_bn(self) -> float:
        """Estimated AI allocation of company-wide capex guidance."""
        return (
            self.p.numeric("capital_deployed.hyperscaler_capex_2026_usd_bn")
            * self.p.get("capital_deployed.hyperscaler_ai_tied_share")
        )

    def capital_by_buyer(self, calendar_year=None, demand_growth=None) -> pd.DataFrame:
        """Illustrative funding shares; not observed chip purchasing shares."""
        hs_capital = self.ai_tied_capital_usd_bn()
        y = self.reference_year if calendar_year is None else calendar_year
        shares = self.shares_for_year(y)
        # Hold aggregate growth fixed to isolate mix, rather than dividing each
        # year's hyperscaler capital by a changing share (which would change TAM).
        total = hs_capital / self.p.get("buyer_segments.hyperscaler_share")
        growth = self.p.numeric("model.demand_growth", positive=True) if demand_growth is None else number(demand_growth,"demand_growth",positive=True)
        total *= growth**(y-self.reference_year)
        rows = [
            ("Hyperscalers", shares[0], "Fund capacity for internal use and resale"),
            ("Neoclouds", shares[1], "Fund capacity for assumed resale; consumers unidentified"),
            ("Enterprise and sovereign", shares[2], "Fund self-build; consumers not separately measured"),
        ]
        df = pd.DataFrame(rows, columns=["segment", "share", "role"])
        df["capital_usd_bn"] = df["share"] * total
        df["implied_gw"] = df["capital_usd_bn"] / self.p.get("unit_economics.capex_per_gw_usd_bn")
        return df

    def capacity_demand_gw(self) -> float:
        """Level 3: total capacity implied by capital deployed."""
        return self.capital_by_buyer()["implied_gw"].sum()

    def consumption_split(self) -> pd.DataFrame:
        """Contextual workload mix on distinct denominators, not consumer shares.

        Reported separately rather than blended. The spend measure and the
        cycles measure are not interchangeable, and averaging them would
        manufacture a number that no source supports.
        """
        spend_share = self.p.numeric("consumption.inference_share_of_infra_spend_2026", maximum=1)
        cycle_share = self.p.numeric("consumption.inference_share_of_compute_cycles_2026", maximum=1)
        life_share = self.p.numeric("consumption.inference_share_of_lifecycle_dollars", maximum=1)

        return pd.DataFrame([
            {"measure": "Infrastructure spending", "denominator": "dollars",
             "inference_share": spend_share, "training_share": 1 - spend_share,
             "inference_gw_equiv": np.nan},
            {"measure": "Compute cycles", "denominator": "cycles",
             "inference_share": cycle_share, "training_share": 1 - cycle_share,
             "inference_gw_equiv": np.nan},
            {"measure": "Model lifecycle dollars", "denominator": "dollars over model life",
             "inference_share": life_share, "training_share": 1 - life_share,
             "inference_gw_equiv": np.nan},
        ])

    # ------------------------------------------------------------- the ladder

    def tam_ladder(self) -> pd.DataFrame:
        """Company-wide capital arithmetic before US and service-year allocation."""
        p = self.p
        hs_capex = p.get("capital_deployed.hyperscaler_capex_2026_usd_bn")
        ai_tied = self.ai_tied_capital_usd_bn()
        total_capital = self.capital_by_buyer()["capital_usd_bn"].sum()
        gw = self.capacity_demand_gw()
        rev_per_gw = p.get("unit_economics.revenue_per_gw_year_usd_bn")
        merchant_gw = self.merchant_addressable_gw()

        rungs = [
            ("Hyperscaler capex, all purposes", hs_capex, "$bn", "Starting point most TAM work uses"),
            ("AI-tied capital only", ai_tied, "$bn", "Strip general cloud"),
            ("All buyers, all segments", total_capital, "$bn", "Add neocloud, enterprise, sovereign"),
            ("Capacity implied", gw, "GW", "Divide by all-in cost per GW"),
            ("Merchant-addressable", merchant_gw, "GW", "Exclude self-consumed hyperscaler capacity"),
            ("Hypothetical merchant annual revenue at full occupation", merchant_gw * rev_per_gw, "$bn/year", "Illustrative capacity times revenue proxy; not a sales forecast"),
        ]
        df = pd.DataFrame(rungs, columns=["rung", "value", "unit", "narrowing"])
        df["step_ratio"] = [np.nan] + [
            df.value.iloc[i] / df.value.iloc[i - 1] if df.unit.iloc[i] == df.unit.iloc[i - 1] else np.nan
            for i in range(1, len(df))
        ]
        return df

    def merchant_addressable_gw(self, calendar_year=None, demand_growth=None) -> float:
        """Illustrative merchant allocation; enterprise share explicit in registry."""
        by_buyer = self.capital_by_buyer(calendar_year, demand_growth).set_index("segment")["implied_gw"]
        self_share = self.p.get("deployment_mode.hyperscaler_self_consumed_share")
        hs_merchant = by_buyer["Hyperscalers"] * (1 - self_share)
        return (hs_merchant + by_buyer["Neoclouds"] * self.p.numeric("deployment_mode.neocloud_resold_share", maximum=1)
                + by_buyer["Enterprise and sovereign"] * self.p.numeric("deployment_mode.enterprise_merchant_share",maximum=1))

    # ------------------------------------------------------------ the trend

    def agentic_pressure(self) -> pd.DataFrame:
        """Inherited contextual ratios; no causal pricing inference."""
        p = self.p
        lo = p.get("consumption.agentic_token_multiplier_low")
        hi = p.get("consumption.agentic_token_multiplier_high")
        linear = p.get("consumption.cost_per_interaction_linear_usd")
        agentic = p.get("consumption.cost_per_interaction_agentic_usd")
        price_fall = p.get("consumption.token_price_decline_2yr_factor")
        spend_rise = p.get("consumption.enterprise_spend_growth_same_period")

        return pd.DataFrame([
            {"metric": "Agentic tokens per task vs chatbot", "low": lo, "high": hi, "unit": "x"},
            {"metric": "Cost per interaction, linear to agentic",
             "low": linear, "high": agentic, "unit": "$"},
            {"metric": "Realised cost multiple per interaction",
             "low": agentic / linear, "high": agentic / linear, "unit": "x"},
            {"metric": "Token price decline, 2 years", "low": price_fall, "high": price_fall, "unit": "x cheaper"},
            {"metric": "Enterprise spend growth, same window",
             "low": spend_rise, "high": spend_rise, "unit": "x"},
        ])

    # ----------------------------------------------------------- the join

    def demand_measure_reconciliation(self, supply_params=None):
        """Keep geography and economic events explicit; no cross-scope ratio."""
        p = supply_params or Params(json.loads(Path(__file__).with_name("parameters.json").read_text(encoding="utf-8")))
        return pd.DataFrame([
            dict(measure="Signed bookings, annualized", gw=p.numeric("demand.na_absorption_h1_2026_gw")*p.numeric("model.h1_annualization_factor"),
                 geography="North America", event="Signing year, includes forward delivery", source=p.cite("demand.na_absorption_h1_2026_gw")),
            dict(measure="Capex-implied capacity", gw=self.capacity_demand_gw(),
                 geography="Company-wide; US share not yet applied", event="Capital cohort, not service date", source="Capital / calibrated cost per GW"),
            dict(measure="Occupancy change, annualized", gw=p.numeric("demand.cbre_net_absorption_h1_2026_mw")*p.numeric("model.h1_annualization_factor")/1000,
                 geography="CBRE primary colocation markets", event="Occupancy change", source=p.cite("demand.cbre_net_absorption_h1_2026_mw")),
        ])

    def serviceable(self, supply_by_year, demand_growth=None, merchant_share_of_supply=None):
        """Annual US merchant additions, including occupancy readiness and backlog.

        Assumes capacity is fungible across customers/regions. No retirement,
        cancellation or existing live base is inferred. Unmatched live capacity
        and unmet requested service both carry forward. Readiness is not live IT
        electricity consumption. Served capacity is an occupied-capacity proxy.
        Missing years fail
        explicitly, since they cannot be silently treated as zero supply.
        """
        p = self.p
        growth = p.numeric("model.demand_growth", positive=True) if demand_growth is None else number(demand_growth,"demand_growth",positive=True)
        share = p.numeric("model.merchant_supply_share",maximum=1) if merchant_share_of_supply is None else number(merchant_share_of_supply,"merchant_share_of_supply",maximum=1)
        us_share = p.numeric("model.us_capacity_share",maximum=1)
        ramp = weights(p.get("model.live_load_weights"),"live_load_weights")
        required_lags = weights(p.get("model.capacity_required_weights"),"capacity_required_weights")
        if not isinstance(ramp,list) or not isinstance(required_lags,list):
            raise ValueError("Readiness and service lag weights must be lists")
        supply = cohorts(supply_by_year,"supply_by_year")
        end = self.start_year+self.horizon_years
        if any(y not in supply for y in range(self.reference_year,end)):
            raise ValueError("Supply must include every year from reference_year through reporting horizon")
        capital = cohorts(p.get("model.opening_merchant_capex_gw"),json_keys=True)
        if any(y >= self.reference_year for y in capital):
            raise ValueError("Opening merchant capital must precede reference_year")
        capital.update({y:self.merchant_addressable_gw(y, growth)*us_share
                        for y in range(self.reference_year,end)})
        for key in ("cancellation_rate", "retirement_rate", "existing_occupied_capacity_gw"):
            if p.numeric("model."+key) != 0:
                raise ValueError(f"Nonzero {key} is not supported by the incremental model")
        backlog = p.numeric("model.opening_demand_backlog_gw")
        spare = p.numeric("model.opening_ready_capacity_gw")
        cumulative_served = cumulative_energized = cumulative_live = 0.0
        rows=[]
        for y in range(self.reference_year,end):
            demand = sum(capital.get(y-lag,0)*w for lag,w in enumerate(required_lags))
            energized = supply[y]*share
            live = sum(supply.get(y-lag,0)*share*w for lag,w in enumerate(ramp) if y-lag >= self.reference_year)
            opening_backlog, opening_spare = backlog, spare
            served = min(backlog+demand, spare+live)
            backlog = max(0,backlog+demand-served)
            spare = max(0,spare+live-served)
            cumulative_served += served
            cumulative_energized += energized
            cumulative_live += live
            if y >= self.start_year:
                rows.append(dict(year=y,merchant_requested_service_gw=demand,total_energized_gw=supply[y],
                    merchant_energized_gw=energized,ready_for_occupancy_additions_gw=live,
                    demand_backlog_start_gw=opening_backlog,available_ready_start_gw=opening_spare,
                    occupied_additions_gw=served,deferred_gw=backlog,available_ready_end_gw=spare,
                    energized_not_ready_gw=max(0,cumulative_energized-cumulative_live),
                    coverage=served/(demand+opening_backlog) if demand+opening_backlog else np.nan,
                    cumulative_occupied_gw=cumulative_served,
                    annualized_revenue_opportunity_usd_bn=cumulative_served*p.numeric("unit_economics.revenue_per_gw_year_usd_bn")))
        return pd.DataFrame(rows)

    def capital_cohorts(self):
        p = self.p
        end = self.start_year+self.horizon_years
        capital = cohorts(p.get("model.opening_merchant_capex_gw"),json_keys=True)
        if any(y >= self.reference_year for y in capital):
            raise ValueError("Opening merchant capital must precede reference_year")
        capital.update({y:self.merchant_addressable_gw(y)*p.numeric("model.us_capacity_share",maximum=1)
                        for y in range(self.reference_year,end)})
        return pd.DataFrame(service_cohorts(capital,p.get("model.capacity_required_weights"),self.reference_year,end)).rename(columns={"booking_year":"capital_year", "signed_gw":"us_merchant_capital_implied_gw"})

    def cross_check(self,supply_2026_gw):
        """Scope-aligned arithmetic comparison, not independent validation."""
        supply = number(supply_2026_gw,"supply_2026_gw")
        capex = self.capacity_demand_gw()*self.p.numeric("model.us_capacity_share",maximum=1)
        return dict(us_all_buyer_capex_implied_gw_2026=capex,
            supply_model_energized_gw_2026=supply,divergence_gw=capex-supply,
            divergence_pct=capex/supply-1 if supply else np.nan,
            note="Consistency diagnostic only: capex is calibrated, geographic share assumed, and capital year differs from delivery year.")


    def customer_segment_mix(self):
        """Annual funding allocation; derived results retain assumed provenance."""
        rows = []
        merchant = [1-self.p.numeric("deployment_mode.hyperscaler_self_consumed_share",maximum=1),
                    self.p.numeric("deployment_mode.neocloud_resold_share",maximum=1),
                    self.p.numeric("deployment_mode.enterprise_merchant_share",maximum=1)]
        us = self.p.numeric("model.us_capacity_share",maximum=1)
        for y in range(self.start_year,self.start_year+self.horizon_years):
            for i,r in enumerate(self.capital_by_buyer(y).to_dict("records")):
                rows.append(dict(scenario=self.mix_scenario,year=y,**r,
                    merchant_fraction=merchant[i],merchant_capital_usd_bn=r["capital_usd_bn"]*merchant[i],
                    merchant_addressable_gw=r["implied_gw"]*merchant[i],
                    us_merchant_capital_implied_gw=r["implied_gw"]*merchant[i]*us,
                    path_evidence="assumption",calculation_evidence="derived",
                    capacity_cost_evidence=self.p.kind("unit_economics.capex_per_gw_usd_bn")))
        return pd.DataFrame(rows)

    def segment_mix_impact(self, supply_by_year):
        """Funding spend and occupancy economics, not consumer utilization."""
        frame = self.serviceable(supply_by_year)
        mix = self.customer_segment_mix().groupby("year").sum(numeric_only=True)
        frame.insert(0,"scenario",self.mix_scenario)
        for key in ("capital_usd_bn", "merchant_capital_usd_bn", "merchant_addressable_gw",
                    "us_merchant_capital_implied_gw"):
            frame[key] = frame.year.map(mix[key])
        frame["us_merchant_provider_capital_spend_usd_bn"] = frame.merchant_capital_usd_bn*self.p.get("model.us_capacity_share")
        # Include any opening ready stock in the utilization denominator, as in
        # the matching ledger. This is occupancy of modeled incremental capacity.
        cumulative_ready = frame.cumulative_occupied_gw+frame.available_ready_end_gw
        frame["ready_capacity_occupancy_ratio"] = frame.cumulative_occupied_gw/cumulative_ready.replace(0,np.nan)
        frame["ready_additions_minus_requested_gw"] = frame.ready_for_occupancy_additions_gw-frame.merchant_requested_service_gw
        frame["requested_additions_annual_spend_opportunity_usd_bn"] = frame.merchant_requested_service_gw*self.p.get("unit_economics.revenue_per_gw_year_usd_bn")
        return frame
