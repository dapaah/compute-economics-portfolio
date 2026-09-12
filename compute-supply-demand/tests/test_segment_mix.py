"""Scenario behavior and regression against the captured pre-extension model."""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
from model_core import Params
from demand_model import DemandModel
from supply_model import SupplyModel


class SegmentMixTests(unittest.TestCase):
    def setUp(self):
        self.p=json.loads((HERE/'demand_parameters.json').read_text(encoding='utf-8'))
        self.scenarios=[*self.p['customer_segment_mix']['terminal_shares']['value'],'static-control']
        s=SupplyModel.from_json(HERE/'parameters.json')
        self.supply=s.summarise(s.run()).set_index('year').energized_gw.to_dict()

    def model(self,scenario='base',**kw):
        return DemandModel(Params(self.p),mix_scenario=scenario,**kw)

    def test_annual_simplex_and_endpoints(self):
        for scenario in self.scenarios:
            m=self.model(scenario)
            shares=np.array([m.shares_for_year(y) for y in range(2026,2034)])
            np.testing.assert_allclose(shares.sum(axis=1),1,atol=1e-12)
            self.assertTrue(((shares>=0)&(shares<=1)).all())
            np.testing.assert_allclose(shares[0],[.72,.16,.12])
            target=[.72,.16,.12] if scenario=='static-control' else self.p['customer_segment_mix']['terminal_shares']['value'][scenario]
            np.testing.assert_allclose(shares[-1],target)
            # Each segment follows a monotone path toward its own endpoint.
            delta=np.diff(shares,axis=0)
            self.assertTrue((delta*(np.array(target)-shares[0])>=-1e-12).all())

    def test_named_scenario_behavior_and_constant_total(self):
        order=['enterprise-sovereign-growth','hyperscaler-heavy','static-control','base','neocloud-growth']
        for y in range(2027,2034):
            totals=[self.model(s).capital_by_buyer(y).capital_usd_bn.sum() for s in order]
            np.testing.assert_allclose(totals,totals[0])
            merchant=[self.model(s).merchant_addressable_gw(y) for s in order]
            self.assertTrue(all(a<b for a,b in zip(merchant,merchant[1:])))
        self.assertGreater(self.model('hyperscaler-heavy').shares_for_year(2033)[0],.72)
        self.assertGreater(self.model('neocloud-growth').shares_for_year(2033)[1],.16)
        self.assertGreater(self.model('enterprise-sovereign-growth').shares_for_year(2033)[2],.12)

    def test_static_control_reproduces_pre_extension_output(self):
        prior=pd.read_csv(HERE/'tests/fixtures/static_mix_serviceable.csv')
        pd.testing.assert_frame_equal(self.model('static-control').serviceable(self.supply),prior,
                                      check_exact=False,rtol=1e-12,atol=1e-12)

    def test_all_flat_paths_reduce_to_control(self):
        for key in self.p['customer_segment_mix']['terminal_shares']['value']:
            self.p['customer_segment_mix']['terminal_shares']['value'][key]=[.72,.16,.12]
        control=self.model('static-control').serviceable(self.supply)
        for scenario in self.scenarios:
            pd.testing.assert_frame_equal(self.model(scenario).serviceable(self.supply),control)

    def test_service_lags_capital_spend_revenue_and_conservation(self):
        for scenario in self.scenarios:
            m=self.model(scenario); impact=m.segment_mix_impact(self.supply)
            cohorts=m.capital_cohorts().groupby('requested_service_year').requested_gw.sum()
            np.testing.assert_allclose(impact.merchant_requested_service_gw,impact.year.map(cohorts))
            np.testing.assert_allclose(impact.us_merchant_provider_capital_spend_usd_bn,
                                       impact.us_merchant_capital_implied_gw*35)
            np.testing.assert_allclose(impact.annualized_revenue_opportunity_usd_bn,impact.cumulative_occupied_gw*8.5)
            np.testing.assert_allclose(impact.demand_backlog_start_gw+impact.merchant_requested_service_gw,
                                       impact.occupied_additions_gw+impact.deferred_gw)
            np.testing.assert_allclose(impact.available_ready_start_gw+impact.ready_for_occupancy_additions_gw,
                                       impact.occupied_additions_gw+impact.available_ready_end_gw)
            self.assertTrue(impact.ready_capacity_occupancy_ratio.between(0,1).all())
        low=self.model('enterprise-sovereign-growth').segment_mix_impact(self.supply).iloc[-1]
        high=self.model('neocloud-growth').segment_mix_impact(self.supply).iloc[-1]
        self.assertGreater(high.annualized_revenue_opportunity_usd_bn,low.annualized_revenue_opportunity_usd_bn)
        self.assertGreater(high.ready_capacity_occupancy_ratio,low.ready_capacity_occupancy_ratio)
        self.assertLess(high.available_ready_end_gw,low.available_ready_end_gw)

    def test_reporting_slice_and_growth_override(self):
        for scenario in self.scenarios:
            full=self.model(scenario).segment_mix_impact(self.supply)
            later=self.model(scenario,start_year=2029,horizon_years=5).segment_mix_impact(self.supply)
            pd.testing.assert_frame_equal(full.query('year>=2029').reset_index(drop=True),later,check_dtype=False)
        before=self.model().serviceable(self.supply,demand_growth=1.2)
        self.p['model']['demand_growth']['value']=1.2
        pd.testing.assert_frame_equal(before,self.model().serviceable(self.supply))

    def test_zero_supply_and_opening_ready_denominator(self):
        zero={y:0 for y in self.supply}
        f=self.model().segment_mix_impact(zero)
        self.assertTrue(f.ready_capacity_occupancy_ratio.isna().all())
        self.assertEqual(f.annualized_revenue_opportunity_usd_bn.sum(),0)
        self.p['model']['opening_ready_capacity_gw']['value']=100
        f=self.model().segment_mix_impact(zero)
        np.testing.assert_allclose(f.ready_capacity_occupancy_ratio,f.cumulative_occupied_gw/100)

    def test_invalid_paths_fail_in_python_and_js(self):
        invalid=[]
        for bad in ([.8,.2,.1],[-.1,.6,.5],[True,0,0],[float('nan'),.5,.5],[.5,.5]):
            p=copy.deepcopy(self.p)
            p['customer_segment_mix']['terminal_shares']['value']['base']=bad
            invalid.append((p,'base'))
        invalid.append((self.p,'invented'))
        missing=copy.deepcopy(self.p)
        del missing['customer_segment_mix']['terminal_shares']['value']['base']
        invalid.append((missing,'base'))
        node=os.environ.get('NODE_BINARY') or shutil.which('node')
        self.assertTrue(node,'Node required for validation parity')
        # JSON cannot carry NaN; null remains invalid in both runtimes.
        script="const m=require('./model.js'),fs=require('fs');let c=JSON.parse(fs.readFileSync(0,'utf8'));try{m.segmentShares(c[0],2026,c[1]);process.exit(1)}catch(e){process.exit(0)}"
        for p,scenario in invalid:
            with self.assertRaises(ValueError): DemandModel(Params(p),mix_scenario=scenario)
            result=subprocess.run([node,'-e',script],input=json.dumps([p,scenario]).replace('NaN','null'),text=True,cwd=HERE,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
        with self.assertRaises(ValueError):self.model(horizon_years=9)
        for bad in (2025,2034,2026.5,True):
            with self.assertRaises(ValueError):self.model().shares_for_year(bad)

    def test_generated_reports_match_models(self):
        mix=pd.read_csv(HERE/'outputs/customer_segment_mix.csv')
        impact=pd.read_csv(HERE/'outputs/segment_mix_impact.csv')
        self.assertEqual(len(mix),5*8*3)
        self.assertEqual(len(impact),5*8)
        self.assertEqual(set(mix.path_evidence),{'assumption'})
        for scenario in self.scenarios:
            expected=self.model(scenario).segment_mix_impact(self.supply)
            actual=impact[impact.scenario==scenario][expected.columns].reset_index(drop=True)
            pd.testing.assert_frame_equal(expected,actual,check_exact=False,rtol=1e-12,atol=1e-12)

if __name__=='__main__':unittest.main()
