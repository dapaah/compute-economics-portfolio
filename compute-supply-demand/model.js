/* Browser and Node model. Parameters come from the JSON registries, never UI constants. */
"use strict";
function value(p,path) {
  const n=path.split('.').reduce((o,k)=>o[k],p);
  if(n.formula) {
    const a=n.formula.inputs.map(k=>value(p,k));
    if(n.formula.operation==='product') return a.reduce((s,v)=>s*v,1);
    if(n.formula.operation==='mean') return a.reduce((s,v)=>s+v,0)/a.length;
    throw Error('Unsupported formula');
  }
  return n.value;
}
function finite(n,name,min=0,max=Infinity) {
  if(typeof n!=='number'||!Number.isFinite(n)||n<min||n>max) throw Error('Invalid '+name);
  return n;
}
function distribution(a,name) {
  if(!Array.isArray(a)||!a.length||Math.abs(a.reduce((s,v)=>s+finite(v,name,0,1),0)-1)>1e-9) throw Error('Invalid '+name);
  return a;
}
function runSupply(p,options={}) {
  const v=k=>value(p,k), n=(k,max=Infinity)=>finite(v(k),k,0,max);
  const ref=v('model.reference_year'), start=options.start_year??ref, horizon=options.horizon_years??v('model.horizon_years'), end=start+horizon;
  if(!Number.isInteger(ref)||ref<1||!Number.isInteger(start)||start<ref||!Number.isInteger(horizon)||horizon<1) throw Error('Invalid reporting window');
  if(v('model.landing_rule')!=='linear_calendar_interpolation'||v('model.opening_equipment_backlog_gw')!==0) throw Error('Unsupported opening or landing rule');
  const shares=v('model.pathway_shares'), names=['grid_queue','btm_large_frame','btm_aeroderivative','colo_lease'];
  if(Object.keys(shares).sort().join()!==[...names].sort().join()) throw Error('Invalid pathway names');
  distribution(Object.values(shares),'pathway shares');
  const low=n('turbine_supply.industry_annual_capacity_gw_low'), high=n('turbine_supply.industry_annual_capacity_gw_high');
  const ratio=n('conversion_ratios.generation_nameplate_per_gw_it_load');
  if(high<low||!ratio) throw Error('Invalid turbine capacity');
  const dc=finite(options.dc_turbine_share??v('turbine_supply.data_center_share_of_us_turbine_output'),'DC turbine share',0,1);
  const aero=finite(options.aero_turbine_share??v('model.aero_turbine_share'),'aero share',0,1);
  const cap=(low+high)/2*n('turbine_supply.us_share_of_turbine_output',1)*dc/ratio;
  const dev=n('pipeline.share_under_active_development',1), proxy=n('model.grid_lifetime_conversion_proxy',1);
  const common={site_permitting:n('model.site_permitting_months'),shell_fitout:n('equipment_lead_times_months.site_build_shell_and_fitout'),transformer:n('equipment_lead_times_months.power_substation_transformer'),switchgear:n('equipment_lead_times_months.mv_switchgear_38kv'),commissioning_ready:n('model.commissioning_ready_months')};
  const topologies=v("model.supply_topologies"), topology=options.scenario??"base";
  if(!topologies||JSON.stringify(topologies.base)!=="{}"||!Object.hasOwn(topologies,topology)) throw Error("Invalid supply topology");
  const exclusions=topologies[topology];
  if(!exclusions||Array.isArray(exclusions)||typeof exclusions!=="object"||Object.keys(exclusions).some(k=>!names.includes(k))) throw Error("Unknown topology pathway");
  const routes=[
    [names[0],{interconnection:n('grid_interconnection.median_ir_to_cod_years')*12},dev,dev?Math.min(1,proxy/dev):0,null],
    [names[1],{generation:n('equipment_lead_times_months.large_frame_gas_turbine'),gsu:n('equipment_lead_times_months.gsu_transformer')},dev,n('model.large_frame_power_gate',1),cap*(1-aero)],
    [names[2],{generation:n('equipment_lead_times_months.aeroderivative_gas_turbine'),gsu:n('equipment_lead_times_months.gsu_transformer')},dev,n('model.aero_power_gate',1),cap*aero],
    [names[3],{},n('model.colo_development_gate',1),n('model.colo_power_gate',1),null]
  ].map(([name,extra,d,power,ceiling])=>{
    const components={...common,...extra},omitted=exclusions[name]??[];
    if(!Array.isArray(omitted)||omitted.some(k=>!Object.hasOwn(components,k))) throw Error('Unknown topology component');
    omitted.forEach(k=>delete components[k]);
    if(!Object.keys(components).length) throw Error('Topology must retain readiness components');
    const lead=Math.max(...Object.values(components));
    return {name,components,lead,conversion:d*power,share:shares[name],ceiling};
  });
  let announced={};
  if(options.announced_gw_by_year!==undefined) announced={...options.announced_gw_by_year};
  else {
    for(let y=ref;y<end;y++) announced[y]=n('pipeline.annual_announcement_flow_gw');
    if(options.include_in_flight!==undefined&&typeof options.include_in_flight!=='boolean') throw Error('Invalid opening flag');
    if(options.include_in_flight!==false) {
      const scale=finite(options.opening_scale??1,'opening scale');
      for(const [y,gw] of Object.entries(v('model.opening_announcements_gw'))) {
        if(+y>=ref) throw Error('Invalid opening year');
        announced[y]=finite(gw,'opening volume')*scale;
      }
    }
  }
  for(const [y,gw] of Object.entries(announced)) {
    if(!/^\d+$/.test(y)||+y<1) throw Error('Invalid cohort year');
    finite(gw,'announcement');
  }
  const detail=[];
  let beyond=0;
  for(const pw of routes) {
    const arrivals={};
    for(const [cy,gw] of Object.entries(announced).sort((a,b)=>+a[0]-b[0])) {
      const exact=+cy+pw.lead/12,lo=Math.floor(exact),frac=exact-lo;
      for(const [y,w] of [[lo,1-frac],[lo+1,frac]]) {
        const volume=gw*pw.share*pw.conversion*w;
        if(volume&&y>=ref) {
          (arrivals[y]??=[]).push([+cy,volume]);
          if(y>=end) beyond+=volume;
        }
      }
    }
    const queue=[];
    for(let y=ref;y<end;y++) {
      const carry=queue.reduce((s,a)=>s+a[1],0), incoming=arrivals[y]??[], fresh=incoming.reduce((s,a)=>s+a[1],0);
      queue.push(...incoming.map(a=>[...a]));
      const available=carry+fresh,delivered=pw.ceiling===null?available:Math.min(available,pw.ceiling);
      let remaining=delivered,opening=0,current=0;
      while(queue.length&&remaining>1e-12) {
        const [cy,volume]=queue[0],taken=Math.min(remaining,volume);
        if(cy<ref) opening+=taken; else current+=taken;
        remaining-=taken;
        if(taken>=volume) queue.shift(); else queue[0][1]-=taken;
      }
      if(y>=start) detail.push({year:y,pathway:pw.name,uncapped_gw:fresh,backlog_start_gw:carry,equipment_ceiling_gw:pw.ceiling,energized_gw:delivered,equipment_backlog_gw:Math.max(0,available-delivered),opening_cohort_energized_gw:opening,forecast_cohort_energized_gw:current,lead_time_months:pw.lead,binding_constraints:Object.keys(pw.components).filter(k=>pw.components[k]===pw.lead).join(';'),project_conversion:pw.conversion});
    }
  }
  const summary=[];
  let cum=0;
  for(let y=start;y<end;y++) {
    const row={year:y};
    for(const k of ['energized_gw','uncapped_gw','backlog_start_gw','equipment_backlog_gw','opening_cohort_energized_gw','forecast_cohort_energized_gw']) row[k]=detail.filter(r=>r.year===y).reduce((s,r)=>s+r[k],0);
    cum+=row.energized_gw; row.cumulative_energized_gw=cum; summary.push(row);
  }
  const lags=distribution(v('model.booking_delivery_weights'),'booking weights'),opening=v('model.opening_bookings_us_gw');
  for(const [y,gw] of Object.entries(opening)) { if(!/^\d+$/.test(y)||+y>=ref||+y<1) throw Error('Invalid opening booking'); finite(gw,'opening booking'); }
  const base=n('demand.na_absorption_h1_2026_gw')*n('model.h1_annualization_factor')*n('model.bookings_us_share',1);
  const growth=v('model.booking_growth');
  if(Object.keys(growth).sort().join()!=='base,high,low') throw Error('Invalid growth labels');
  const demand=summary.map(r=>({year:r.year,energized_gw:r.energized_gw}));
  for(const [label,g] of Object.entries(growth)) {
    if(!finite(g,'growth')) throw Error('Invalid growth');
    const signed={...opening};
    for(let y=ref;y<end;y++) signed[y]=base*g**(y-ref);
    for(const row of demand) {
      row['signed_us_bookings_'+label+'_gw']=signed[row.year];
      row['required_service_'+label+'_gw']=lags.reduce((s,w,lag)=>s+(signed[row.year-lag]??0)*w,0);
    }
  }
  for(const row of demand) { row.gap_vs_base_gw=row.energized_gw-row.required_service_base_gw; row.coverage_ratio=row.required_service_base_gw?row.energized_gw/row.required_service_base_gw:null; }
  return {routes,detail,summary,demand,scheduled_after_horizon_gw:beyond};
}
function segmentShares(p,y,scenario='base') {
  const ref=value(p,'model.reference_year'),last=value(p,'customer_segment_mix.end_year');
  if(!Number.isInteger(y)||!Number.isInteger(last)||last<=ref||y<ref||y>last) throw Error('Year outside supported segment path');
  const opening=['hyperscaler_share','neocloud_share','enterprise_and_sovereign_share'].map(k=>value(p,'buyer_segments.'+k));
  distribution(opening,'buyer shares');
  const targets=value(p,'customer_segment_mix.terminal_shares');
  if(Object.keys(targets).sort().join()!=='base,enterprise-sovereign-growth,hyperscaler-heavy,neocloud-growth') throw Error('Invalid scenario labels');
  for(const v of Object.values(targets)) {if(!Array.isArray(v)||v.length!==3) throw Error('Three shares required');distribution(v,'terminal shares');}
  if(scenario!=='static-control'&&!Object.hasOwn(targets,scenario)) throw Error('Unknown segment scenario');
  const target=scenario==='static-control'?opening:targets[scenario],t=(y-ref)/(last-ref);
  return distribution(opening.map((a,i)=>a+(target[i]-a)*t),'annual shares');
}
function runDemand(p,supply,scenario='base') {
  const v=k=>value(p,k),n=(k,max=Infinity)=>finite(v(k),k,0,max),ref=v('model.reference_year');
  const shares=['hyperscaler_share','neocloud_share','enterprise_and_sovereign_share'].map(k=>n('buyer_segments.'+k,1));
  distribution(shares,'buyer shares');
  const cost=n('unit_economics.capex_per_gw_usd_bn'),growth=n('model.demand_growth');
  if(!cost||!shares[0]||!growth) throw Error('Invalid cost, share or growth');
  const total=n('capital_deployed.hyperscaler_capex_2026_usd_bn')*n('capital_deployed.hyperscaler_ai_tied_share',1)/shares[0]/cost;
  const merchant=s=>s[0]*(1-n('deployment_mode.hyperscaler_self_consumed_share',1))+s[1]*n('deployment_mode.neocloud_resold_share',1)+s[2]*n('deployment_mode.enterprise_merchant_share',1);
  const capital={...v('model.opening_merchant_capex_gw')};
  for(const [y,gw] of Object.entries(capital)) { if(!/^\d+$/.test(y)||+y<1||+y>=ref) throw Error('Invalid opening capital'); finite(gw,'capital'); }
  const share=n('model.merchant_supply_share',1),ramp=distribution(v('model.live_load_weights'),'ramp'),lags=distribution(v('model.capacity_required_weights'),'capital weights');
  const end=ref+v('model.horizon_years'),byYear=Object.fromEntries(supply.map(r=>[r.year,r.energized_gw]));
  for(let y=ref;y<end;y++) { finite(byYear[y],'supply'); capital[y]=total*merchant(segmentShares(p,y,scenario))*n('model.us_capacity_share',1)*growth**(y-ref); }
  for(const k of ['cancellation_rate','retirement_rate','existing_occupied_capacity_gw']) if(n('model.'+k)!==0) throw Error('Unsupported '+k);
  let backlog=n('model.opening_demand_backlog_gw'),spare=n('model.opening_ready_capacity_gw'),cumServed=0,cumEnergized=0,cumReady=0;
  const rows=[];
  for(let y=ref;y<end;y++) {
    const demand=lags.reduce((s,w,lag)=>s+(capital[y-lag]??0)*w,0),energized=byYear[y]*share;
    const ready=ramp.reduce((s,w,lag)=>s+(y-lag>=ref?(byYear[y-lag]??0)*share*w:0),0);
    const oldBacklog=backlog,oldSpare=spare,served=Math.min(backlog+demand,spare+ready);
    backlog=Math.max(0,backlog+demand-served); spare=Math.max(0,spare+ready-served);
    cumServed+=served; cumEnergized+=energized; cumReady+=ready;
    rows.push({year:y,merchant_requested_service_gw:demand,total_energized_gw:byYear[y],merchant_energized_gw:energized,ready_for_occupancy_additions_gw:ready,demand_backlog_start_gw:oldBacklog,available_ready_start_gw:oldSpare,occupied_additions_gw:served,deferred_gw:backlog,available_ready_end_gw:spare,energized_not_ready_gw:Math.max(0,cumEnergized-cumReady),coverage:demand+oldBacklog?served/(demand+oldBacklog):null,cumulative_occupied_gw:cumServed,annualized_revenue_opportunity_usd_bn:cumServed*n('unit_economics.revenue_per_gw_year_usd_bn')});
  }
  return rows;
}
if(typeof module!=='undefined') module.exports={value,runSupply,runDemand,segmentShares};
