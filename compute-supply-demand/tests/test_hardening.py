"""Conservation, causality, input validation and independent-runtime parity."""
import copy
import json
import math
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import unittest
import pandas as pd

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
from model_core import Params, service_cohorts
from supply_model import SupplyModel
from demand_model import DemandModel
from build_dashboard import build


def blob(name="parameters.json"):
    return json.loads((HERE/name).read_text(encoding="utf-8"))


def put(p,path,v):
    parts=path.split('.')
    for key in parts[:-1]: p=p[key]
    p[parts[-1]]["value"]=v


class ModelTests(unittest.TestCase):
    def test_critical_paths_and_nonbinding_changes(self):
        p=blob(); m=SupplyModel(Params(p))
        self.assertEqual([pw.lead_time_months for pw in m.pathways['base']],[60,66,37,37])
        for pw in m.pathways['base']:
            self.assertEqual(pw.lead_time_months,max(pw.components.values()))
        base=m.run()
        put(p,'equipment_lead_times_months.aeroderivative_gas_turbine',30)
        self.assertTrue(base.equals(SupplyModel(Params(p)).run()))
        put(p,'equipment_lead_times_months.power_substation_transformer',80)
        changed=SupplyModel(Params(p))
        self.assertTrue(all(pw.lead_time_months==80 for pw in changed.pathways['base']))
        self.assertFalse(changed.run().equals(base))

    def test_single_cohort_conservation_and_tail(self):
        m=SupplyModel(Params(blob()),horizon_years=30)
        df=m.run({2026:100})
        expected=sum(100*pw.share_of_announcements*pw.project_conversion for pw in m.pathways['base'])
        self.assertAlmostEqual(df.energized_gw.sum(),expected)
        self.assertAlmostEqual(df.groupby('pathway').tail(1).equipment_backlog_gw.sum(),0)
        short=SupplyModel(Params(blob()),horizon_years=4)
        run=short.run({2026:100})
        self.assertAlmostEqual(run.energized_gw.sum()+run.groupby('pathway').tail(1).equipment_backlog_gw.sum()+run.attrs['scheduled_after_horizon_gw'],expected)

    def test_queue_balance_and_zero_turbine_capacity(self):
        m=SupplyModel(Params(blob()))
        df=m.run(dc_turbine_share=0)
        for row in df.itertuples():
            self.assertAlmostEqual(row.backlog_start_gw+row.uncapped_gw,row.energized_gw+row.equipment_backlog_gw)
        gas=df[df.pathway.str.startswith('btm_')]
        self.assertEqual(gas.energized_gw.sum(),0)
        self.assertGreater(gas.equipment_backlog_gw.sum(),0)

    def test_opening_replaces_stock_no_automatic_seed_for_explicit_ledger(self):
        p=blob(); m=SupplyModel(Params(p));base=m.run()
        put(p,'demand.na_under_construction_gw',100000)
        put(p,'pipeline.us_disclosed_pipeline_gw',100000)
        self.assertTrue(base.equals(SupplyModel(Params(p)).run()))
        self.assertEqual(m.run({}).energized_gw.sum(),0)
        self.assertEqual(m.run(include_in_flight=False).query('year < 2029').energized_gw.sum(),0)
        totals=m.summarise(base).set_index('year').energized_gw
        self.assertGreater(totals[2030],totals[2029])
        ledger={int(y):gw for y,gw in p['model']['opening_announcements_gw']['value'].items()}
        ledger.update({y:100 for y in range(2026,2034)})
        self.assertTrue(base.equals(m.run(ledger)))

    def test_reporting_slice_retains_queue_history(self):
        p=blob()
        full=SupplyModel(Params(p)).run()
        later=SupplyModel(Params(p),start_year=2029,horizon_years=5).run()
        pd.testing.assert_frame_equal(full.query('year >= 2029').reset_index(drop=True),later)

    def test_booking_timing_and_geography(self):
        ledger=service_cohorts({2025:10},[0,.25,.75],2026,2027)
        self.assertEqual(sum(r['requested_gw'] for r in ledger),10)
        self.assertEqual([r['requested_service_year'] for r in ledger],[2026,2027])
        self.assertEqual([r['window'] for r in ledger],['within','after'])
        p=blob();m=SupplyModel(Params(p));df=m.demand_vs_supply(m.run())
        self.assertAlmostEqual(df.required_service_base_gw.iloc[0],9+20+9)
        self.assertAlmostEqual(df.signed_us_bookings_base_gw.iloc[0],45)
        put(p,'model.bookings_us_share',0)
        put(p,'model.opening_bookings_us_gw',{})
        zero=SupplyModel(Params(p));result=zero.demand_vs_supply(zero.run())
        self.assertEqual(result.required_service_base_gw.sum(),0)
        self.assertTrue(result.coverage_ratio.isna().all())
        self.assertTrue((result.gap_vs_base_gw>0).all())

    def test_demand_occupancy_and_backlog_conservation(self):
        s=SupplyModel(Params(blob()));supply=s.summarise(s.run()).set_index('year').energized_gw.to_dict()
        d=DemandModel(Params(blob('demand_parameters.json')));frame=d.serviceable(supply)
        for r in frame.itertuples():
            self.assertAlmostEqual(r.demand_backlog_start_gw+r.merchant_requested_service_gw,r.occupied_additions_gw+r.deferred_gw)
            self.assertAlmostEqual(r.available_ready_start_gw+r.ready_for_occupancy_additions_gw,r.occupied_additions_gw+r.available_ready_end_gw)
        self.assertLess(frame.occupied_additions_gw.iloc[0],frame.merchant_energized_gw.iloc[0])
        self.assertEqual(frame.deferred_gw.iloc[-1],0)
        self.assertGreater(frame.available_ready_end_gw.iloc[-1],0)
        no_supply=d.serviceable({y:0 for y in supply})
        self.assertEqual(no_supply.occupied_additions_gw.sum(),0)
        self.assertAlmostEqual(no_supply.deferred_gw.iloc[-1],no_supply.merchant_requested_service_gw.sum())
        ledger=d.capital_cohorts()
        required=ledger.groupby('requested_service_year').requested_gw.sum()
        for r in frame.itertuples():self.assertAlmostEqual(required[r.year],r.merchant_requested_service_gw)

    def test_ramp_shifts_occupancy_without_changing_energization(self):
        p=blob('demand_parameters.json');put(p,'model.live_load_weights',[0,0,1])
        d=DemandModel(Params(p));frame=d.serviceable({y:10 for y in range(2026,2034)})
        self.assertEqual(frame.ready_for_occupancy_additions_gw.iloc[:2].sum(),0)
        self.assertGreater(frame.energized_not_ready_gw.iloc[0],0)
        self.assertGreater(frame.ready_for_occupancy_additions_gw.iloc[2],0)

    def test_registry_classification_derivation_and_isolation(self):
        p=blob();params=Params(p)
        put(p,'pipeline.quarterly_pipeline_additions_q4_2025_gw',35)
        self.assertEqual(params.get('pipeline.annual_announcement_flow_gw'),100)
        self.assertEqual(Params(p).get('pipeline.annual_announcement_flow_gw'),140)
        for name in ('parameters.json','demand_parameters.json'):
            for path,n in Params(blob(name)).entries():
                self.assertIn(n['kind'],{'observed','derived','calibrated','assumption'},path)
                self.assertTrue(n['source'],path)
                self.assertTrue(n['date'],path)
        self.assertEqual(Params(blob('demand_parameters.json')).kind('unit_economics.capex_per_gw_usd_bn'),'calibrated')

    def test_invalid_inputs_fail(self):
        for key,bad in [('model.pathway_shares',{'grid_queue':1}),('equipment_lead_times_months.gsu_transformer',float('nan')),('model.aero_turbine_share',1.1)]:
            p=blob();put(p,key,bad)
            with self.assertRaises(ValueError):SupplyModel(Params(p)).run()
        m=SupplyModel(Params(blob()))
        for ledger in ({True:2},{2026:-1},{2026:float('inf')}):
            with self.assertRaises(ValueError):m.run(ledger)
        d=DemandModel(Params(blob('demand_parameters.json')))
        with self.assertRaises(ValueError):d.serviceable({2026:1})

    def test_backtest_refuses_stock_wrong_year_and_lookahead(self):
        m=SupplyModel(Params(blob()));df=m.run()
        status=m.validate(df)
        self.assertNotIn('implied_growth_vs_2025',status)
        with self.assertRaises(ValueError):m.backtest(df,{2026:9},snapshot_as_of='2025-12-31',observation_scope='inventory')
        with self.assertRaises(ValueError):m.backtest(df,{2026:9},snapshot_as_of='2026-12-31',observation_scope='US_all_new_energized_IT_GW')
        with self.assertRaises(ValueError):m.backtest(df,{2025:9},snapshot_as_of='2024-12-31',observation_scope='US_all_new_energized_IT_GW')
        # Synthetic fixture exercises scoring only, never a historical accuracy claim.
        scored=m.backtest(df,{2026:10},snapshot_as_of='2025-12-31',observation_scope='US_all_new_energized_IT_GW')
        self.assertAlmostEqual(scored.error_gw.iloc[0],1.2875)

    def test_dashboard_is_current_and_contains_tested_js(self):
        self.assertEqual((HERE/'deliverable_capacity.html').read_text(encoding='utf-8'),build())
        self.assertIn((HERE/'model.js').read_text(encoding='utf-8'),build())

    def test_alternative_topology_isolated_and_component_driven(self):
        p=blob(); m=SupplyModel(Params(p))
        base=m.run(); alt=m.run(scenario='alternative-btm')
        self.assertEqual([pw.lead_time_months for pw in m.pathways['base']],[60,66,37,37])
        self.assertEqual([pw.lead_time_months for pw in m.pathways['alternative-btm']],[60,66,27,37])
        for original, changed in zip(m.pathways['base'],m.pathways['alternative-btm']):
            self.assertEqual(original.share_of_announcements,changed.share_of_announcements)
            self.assertEqual(original.equipment_ceiling_gw_yr,changed.equipment_ceiling_gw_yr)
            self.assertEqual(original.project_conversion,changed.project_conversion)
        pd.testing.assert_frame_equal(base[base.pathway!='btm_aeroderivative'],
                                      alt[alt.pathway!='btm_aeroderivative'])
        for row in alt.itertuples():
            self.assertAlmostEqual(row.backlog_start_gw+row.uncapped_gw,row.energized_gw+row.equipment_backlog_gw)
        put(p,'model.commissioning_ready_months',50)
        changed=SupplyModel(Params(p))
        self.assertEqual(changed.pathways['alternative-btm'][2].lead_time_months,50)
        pd.testing.assert_frame_equal(m.run(),base)

    def test_python_js_parity(self):
        node=os.environ.get('NODE_BINARY') or shutil.which('node')
        if not node:self.fail('Node required: set NODE_BINARY to run parity')
        cases=[dict(p=blob(),d=blob('demand_parameters.json'),options={}),
               dict(p=blob(),d=blob('demand_parameters.json'),options={'dc_turbine_share':0}),
               dict(p=blob(),d=blob('demand_parameters.json'),options={'include_in_flight':False}),
               dict(p=blob(),d=blob('demand_parameters.json'),options={'announced_gw_by_year':{}}),
               dict(p=blob(),d=blob('demand_parameters.json'),options={'announced_gw_by_year':{2023:30,2026:40,2029:100}})]
        for scenario in [*blob('demand_parameters.json')['customer_segment_mix']['terminal_shares']['value'], 'static-control']:
            for no_supply in (False, True):
                cases.append(dict(p=blob(),d=blob('demand_parameters.json'),scenario=scenario,
                                  options={'announced_gw_by_year':{}} if no_supply else {}))
        for options in ({'scenario':'alternative-btm'},
                        {'scenario':'alternative-btm','include_in_flight':False},
                        {'scenario':'alternative-btm','dc_turbine_share':0}):
            cases.append(dict(p=blob(),d=blob('demand_parameters.json'),options=options))
        rng=random.Random(17)
        for _ in range(15):
            p=blob();d=blob('demand_parameters.json')
            for path,lo,hi in [('equipment_lead_times_months.power_substation_transformer',20,90),('equipment_lead_times_months.aeroderivative_gas_turbine',18,60),('pipeline.quarterly_pipeline_additions_q4_2025_gw',0,60),('model.bookings_us_share',0,1),('pipeline.share_under_active_development',0,1)]:put(p,path,rng.uniform(lo,hi))
            put(d,'model.us_capacity_share',rng.random());put(d,'model.merchant_supply_share',rng.random());put(d,'unit_economics.capex_per_gw_usd_bn',rng.uniform(20,60))
            put(d,'deployment_mode.enterprise_merchant_share',rng.random())
            cases.append(dict(p=p,d=d,scenario=rng.choice(['base','hyperscaler-heavy','neocloud-growth','enterprise-sovereign-growth','static-control']),options={'dc_turbine_share':rng.random(),'aero_turbine_share':rng.random(),'opening_scale':rng.uniform(0,2)}))
        script="const fs=require('fs'),m=require('./model.js'); const cases=JSON.parse(fs.readFileSync(0,'utf8')); console.log(JSON.stringify(cases.map(c=>{const r=m.runSupply(c.p,c.options);return {...r,merchant:m.runDemand(c.d,r.summary,c.scenario),mix:r.summary.map(r=>m.segmentShares(c.d,r.year,c.scenario))}})));"
        result=subprocess.run([node,'-e',script],input=json.dumps(cases),text=True,capture_output=True,cwd=HERE,check=True)
        js=json.loads(result.stdout)
        def compare(a,b,path=''):
            if isinstance(a,dict):
                self.assertEqual(set(a),set(b),path)
                for k in a:compare(a[k],b[k],path+'.'+k)
            elif isinstance(a,list):
                self.assertEqual(len(a),len(b),path)
                for i,(x,y) in enumerate(zip(a,b)):compare(x,y,path+f'[{i}]')
            elif isinstance(a,(float,int)):
                if math.isnan(a):self.assertIsNone(b,path)
                else:self.assertTrue(math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-9),f'{path}: {a} != {b}')
            else:self.assertEqual(a,b,path)
        for i,(case,j) in enumerate(zip(cases,js)):
            m=SupplyModel(Params(case['p']));df=m.run(**case['options']);summary=m.summarise(df)
            compare(df.to_dict('records'),j['detail'],f'case {i} detail')
            compare(summary.to_dict('records'),j['summary'],f'case {i} summary')
            compare(m.demand_vs_supply(df).to_dict('records'),j['demand'],f'case {i} bookings')
            compare(df.attrs['scheduled_after_horizon_gw'],j['scheduled_after_horizon_gw'])
            dm=DemandModel(Params(case['d']),mix_scenario=case.get('scenario','base'))
            demand=dm.serviceable(summary.set_index('year').energized_gw.to_dict())
            compare([dm.shares_for_year(int(y)) for y in summary.year],j['mix'],f'case {i} mix')
            compare(demand.to_dict('records'),j['merchant'],f'case {i} merchant')


if __name__=='__main__':unittest.main()
