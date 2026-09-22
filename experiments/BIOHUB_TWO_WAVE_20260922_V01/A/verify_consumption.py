"""CPU-only verify actual final consumption; no platform writes."""
import json,hashlib,re
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;D=Path('/private/tmp/biohub-a351739212-output')
r=json.loads((D/'two_wave/production_receipt.json').read_text());proof=json.loads((P/'formal_precheck.json').read_text());binding=json.loads((P/'output_binding.json').read_text())
for a in binding['artifacts']:assert hashlib.sha256((D/a['name']).read_bytes()).hexdigest()==a['sha256']
assert r['engineering_status']=='PASS' and r['training_calls']==0 and r['original_selector_unchanged']
assert r['worker_detection_weight']==.8 and r['worker_test_records']>0 and len(r['worker_harmonic_records'])>0
calls=[json.loads(x) for x in (D/'two_wave/postprocess_calls.jsonl').read_text().splitlines()]
assert hashlib.sha256((D/'two_wave/postprocess_calls.jsonl').read_bytes()).hexdigest()==r['postprocess_calls_sha256']
assert set(r['velocity_consumed'])==set(r['expected_samples'])
for stem,v in r['velocity_consumed'].items():
 assert v['wave_velocity_consumed']==.25 and v['wave_velocity_calls']>0 and v['wave_leaf']['threshold'] is None and v['wave_leaf']['deleted']==0
 last=[c for c in calls if c['stem']==stem][-1]
 assert last['stats']['wave_velocity_consumed']==.25 and last['stats']['wave_velocity_calls']==v['wave_velocity_calls']
 assert last['config']==r['final_resolved_config'] and last['final_hash']==proof['graphs'][stem]['canonical_sha256']
 assert last['raw_input_unchanged'] and last['stats']['deepcenter_safe_div_missing']==0
 assert last['candidate_invariant_sha256']==proof['graphs'][stem]['id_independent_sha256']
 assert last['actual_effect']==(last['baseline_invariant_sha256']!=last['candidate_invariant_sha256'])
i=json.loads((D/'bidirectional_production_runtime_integrity.json').read_text());s=json.loads((D/'sprint_production_receipt.json').read_text());chosen=json.loads((D/'ppsweep_selected.json').read_text())
assert i['checkpoint_sha256']==r['weights'] and s['weight_sha256']==r['gate_weight_sha256'] and s['training_calls']==0
assert chosen['selected']==r['selected_label'] and chosen['overrides']==r['selected_config']
log=(D/'ordinary.log').read_text();assert re.search(r'Dual-seed ensemble:\s+requested=True\s+weights_found=True',log) and re.search(r'DeepCenter veto:\s+requested=True\s+loaded=True',log)
summary={'status':'PASS','observed_at_utc':datetime.now(timezone.utc).isoformat(),'version':1,'sv':351739212,'kernel_id':binding['after']['kernel_id'],'csv_sha256':proof['sha256'],'velocity_consumed':r['velocity_consumed'],'det':r['worker_det_threshold'],'harmonic':r['worker_bidirectional_weight'],'division':r['final_resolved_config']['DEEPCENTER_SAFE_DIV_THRESHOLD'],'weights':r['weights'],'gate_sha256':r['gate_weight_sha256'],'models_loaded':True,'selected_label':r['selected_label'],'same_run_comparison':r['same_run_comparison'],'public':None,'platform_writes':0}
(P/'consumption_precheck.json').write_text(json.dumps(summary,indent=2)+'\n');print('FINAL_CONSUMPTION_PASS',sum(v['wave_velocity_calls'] for v in r['velocity_consumed'].values()))
