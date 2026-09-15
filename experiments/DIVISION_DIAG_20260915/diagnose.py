"""Reproduce evidence checks and static A/B diff; never execute/import Notebook code.

The real paired run fails closed if required cached inputs are unavailable.
No synthetic candidates, substitute model, proxy score, or optimizer call.
"""
import ast,csv,difflib,hashlib,json,math,subprocess
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
RAW=ROOT/'downloads/DIVISION_DIAG_20260915/platform';BASE='a123f0ad7f8808b44909d4c5fab48caf5147b50c'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_bytes())
def save(name,x):(HERE/name).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def finite(x):
 if isinstance(x,dict):return all(finite(v) for v in x.values())
 if isinstance(x,list):return all(finite(v) for v in x)
 return not isinstance(x,float) or math.isfinite(x)
now=datetime.now(timezone.utc).isoformat();inputs=[]
def fixed(path):
 b=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
 assert b==(ROOT/path).read_bytes(),path
 inputs.append({'path':path,'commit':BASE,'bytes':len(b),'sha256':sha(b),'read_at_utc':now})
 return b
paths=['reports/20260915_训练版正式评分核验.md','experiments/SCORE_RECOVERY_20260915/formal_results.json','experiments/SCORE_RECOVERY_20260915/source_review.json','experiments/SCORE_RECOVERY_20260915/division_remote_source.ipynb','experiments/TARGET950_20260914/candidate.ipynb','experiments/TARGET950_20260914/baseline/candidate.ipynb']
for p in paths[:3]:fixed(p)
books={};cells=[]
for tag,p in zip(['division','selector','forge'],paths[3:]):
 book=json.loads(fixed(p));books[tag]=[''.join(c['source']) for c in book['cells'] if c['cell_type']=='code']
 for i,s in enumerate(books[tag]):
  t=ast.parse(s)
  cells.append({'object':tag,'cell_index_0based':i,'bytes':len(s.encode()),'sha256':sha(s.encode()),'ast_parse':True,'functions':[n.name for n in t.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))],'review_scope':'full bytes and AST inventory; only changed division logic, dependencies, configuration and scorer wiring semantically inspected'})
div=books['division'];sel=books['selector']
module=next(ast.literal_eval(n.value) for n in ast.walk(ast.parse(div[4])) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='DIVISION_SOURCE' for t in n.targets))
ast.parse(module)
diff=''.join(difflib.unified_diff(sel[5].splitlines(True),div[6].splitlines(True),fromfile='Official Selector cell5',tofile='Division Train cell6'))
(HERE/'safe_div_static.diff').write_text('\n'.join(line.rstrip() for line in diff.splitlines())+'\n') # presentation whitespace only; original hashes in manifest
assert sum(s in sel for s in div)==12
save('source_read_manifest.json',{'inputs':inputs,'cells':cells,'division_module_sha256':sha(module.encode()),'notebook_code_executed':False,'semantic_review':'division embedded module; changed safe-div and common topology/filter order; cache/DeepCenter dependencies; validation model routing; final audit; original scorer adapter. Not a new full semantic review of all inference cells.'})
recs=[read(HERE/x) for x in ['recovery_receipt.json','supplemental_receipt.json']]
artifacts=[f for r in recs for f in r['files']]
for r in recs:
 assert r['status']=='EXISTING_ORDINARY_OUTPUT_RECOVERED' and r['inventory_complete'] and r['identity_before']==r['identity_after']
for f in artifacts:
 b=(ROOT/f['path']).read_bytes();assert sha(b)==f['sha256'] and len(b)==f['bytes']
training=read(RAW/'division_training_receipt.json');weights=read(RAW/'division_gate_weights.json');runtime=read(RAW/'division_runtime_audit.json');audit=read(RAW/'official_selector_audit.json');selected=read(RAW/'ppsweep_selected.json')
assert training['weights_sha256']==runtime['weights_sha256']==sha((RAW/'division_gate_weights.json').read_bytes())
assert runtime['training_receipt_sha256']==sha((RAW/'division_training_receipt.json').read_bytes())
assert runtime['module_sha256']==sha(module.encode())
assert audit['run_stats_sha256']==sha((RAW/'run_stats.csv').read_bytes())
assert audit['ppsweep_selected_sha256']==sha((RAW/'ppsweep_selected.json').read_bytes())
assert runtime['submission_sha256']==audit['submission_csv_sha256'] # CSV itself intentionally not downloaded
assert selected['selected']==runtime['selected_label']==audit['selected_label']=='tight55'
assert selected['overrides']==runtime['selected_config']==audit['selected_config']
assert weights['threshold']==training['threshold']==0.95
inv=training['gt_inventory'];groups=sorted({r['embryo'] for r in inv});totals={g:{'files':sum(r['embryo']==g for r in inv),'positive':sum(r['positives'] for r in inv if r['embryo']==g),'negative':sum(r['negatives'] for r in inv if r['embryo']==g)} for g in groups}
assert sum(r['positives'] for r in inv)==training['final_fit']['n_positive']
assert sum(r['negatives'] for r in inv)==training['final_fit']['n_negative']
assert set(weights['held_out'])==set(groups)==set(training['embryo_groups'])
models=[]
for label,m in [('final',weights['final']),*weights['held_out'].items()]:
 assert finite(m) and len(m['mean'])==len(m['scale'])==10 and len(m['coefficients'])==21 and min(m['scale'])>=0.1
 a=training['final_fit'] if label=='final' else next(f['fit'] for f in training['folds'] if f['held_out_embryo']==label)
 assert a['converged'] and finite(a) and a['final_loss']<a['initial_loss'] and 0<a['optimizer_steps']<=250
 assert abs(math.sqrt(sum(x*x for x in m['coefficients']))-a['coefficient_norm'])<1e-10
 assert a['augmented_rows']==4*(a['n_positive']+a['n_negative'])
 models.append({'model':label,'finite':True,'mean_count':10,'scale_count':10,'coefficient_count':21,'fit':a})
for f in training['folds']:
 g=f['held_out_embryo'];others=set(groups)-{g};assert set(f['training_embryos'])==others
 assert f['fit']['n_positive']==sum(totals[k]['positive'] for k in others)
 assert f['fit']['n_negative']==sum(totals[k]['negative'] for k in others)
 m=f['pair_metrics'];assert m['tp']+m['fn']==totals[g]['positive'] and m['fp']+m['tn']==totals[g]['negative']
rows=list(csv.DictReader((RAW/'run_stats.csv').open()));counts={k:sum(int(float(r.get(k) or 0)) for r in rows) for k in runtime['counts']}
assert counts==runtime['counts'];assert counts['learned_division_scored']==counts['learned_division_accepted']+counts['learned_division_rejected']
log=read(RAW/'ordinary.log');events=[]
for e in log:
 data=e.get('data','')
 for marker,expected in [('DIVISION_TRAINING_COMPLETED ',None),('DIVISION_RUNTIME_AUDIT ',runtime)]:
  if marker in data:
   x=json.loads(data.split(marker,1)[1]);assert x['weights_sha256']==training['weights_sha256']
   if expected:assert x==expected
   else:assert x['final_fit']==training['final_fit'] and x['folds']==training['folds']
   events.append({'marker':marker.strip(),'elapsed_seconds':e.get('time'),'data':x})
assert len(events)==2
save('log_evidence.json',{'source_sha256':sha((RAW/'ordinary.log').read_bytes()),'events':events,'scope':'ordinary session only'})
# Small receipts contain metadata and counts, never parameter vectors or raw graphs.
for name in ['division_training_receipt.json','division_runtime_audit.json','ppsweep_selected.json','run_stats.csv']:
 (HERE/('ordinary_'+name)).write_bytes((RAW/name).read_bytes())
rule_path='research/20260903_BIOHUB_CELL_PUBLIC_RECON_V01/staging/official_kaggle/evidence/browser_official_routes.json'
rule=fixed(rule_path).decode();assert 'first segment identifies' in rule and 'embryo' in rule
selector_summary=json.loads(fixed('experiments/TARGET950_RUN_20260914/ordinary_summary.json'))
selector_audit=json.loads(fixed('experiments/TARGET950_RUN_20260914/official_selector_audit.json'))
assert selector_summary['actual_postprocess']['resolved']==audit['resolved_postprocess']
for n,h in audit['official_source_file_sha256'].items():
 if n=='__init__.py':
  assert h==sha(b'') and '__init__.py' in div[9] # empty package file generated by source, not vendored
  continue
 b=fixed('experiments/TARGET950_20260914/vendor/official_075fc5/'+n);assert sha(b)==h
fixed('experiments/TARGET950_20260914/official_selector_adapter.py')
# Inventory read includes all 452 output paths, not only a keyword search.
names=[i['name'] for i in recs[0]['inventory']]
val_graphs=sorted({n.split('.geff/')[0]+'.geff' for n in names if '/unet_transformer_val/' in n and '.geff/' in n})
assert len(val_graphs)==8
non_graph=[n for n in names if '.geff/' not in n]
local=subprocess.check_output(['rg','--files','-uu','-g','!.git/**','.'],cwd=ROOT,text=True).splitlines()
local_hits=[p for p in local if any(s in p.lower() for s in ['heatmap','val_raw_graph','deepcenter_cache']) or ('.geff/' in p and '/c/' in p)]
save('cache_audit.json',{'output_inventory_sha256':sha((HERE/'recovery_receipt.json').read_bytes()),'output_files_reviewed':len(names),'validation_graphs_available_on_platform':val_graphs,'graph_payloads_downloaded':False,'reason_not_downloaded':'DeepCenter heatmaps/point decisions and gap image-refinement cache not persisted; full pair forbidden without them. Existing graph URLs not serialized.','non_graph_output_paths':non_graph,'local_search_scope':'all repository file paths including ignored, excluding .git; no external project scan','local_payload_or_heatmap_hits':local_hits,'local_search_count':len(local),'gt_payload_recovered':False,'gt_hash_inventory_available':True,'deepcenter_required':True,'deepcenter_saved_cache_found':False,'source_evidence':['division cell6 deepcenter_heatmap_for_frame:323-378 memory cache; cache miss calls model(tensor)','division cell6 filter_output_graph:1479 onward creates per-run repair_frame_cache and deepcenter_heatmap_cache','division cell10 VAL_RAW_GRAPHS/VAL_GT are in-memory; persisted .geff predictions listed separately'],'upstream_training_lineage':'UNKNOWN; no full-pipeline no-leakage claim'})
plan={'status':'BLOCKED_BEFORE_SAMPLE_FREEZE','reference_config_source':'archived Selector ordinary_summary and official_selector_audit, V1/SV349666428','scope':'controlled diagnostic reference, not hidden formal configuration','selected_label':'tight55','sweep_enabled':False,'classifier_threshold':0.95,'resolved_postprocess':selector_summary['actual_postprocess']['resolved'],'common_non_sweep_source_sha256':sha(sel[2].encode()),'sample_plan':selected['held_out_stems'],'frozen_executable_samples':None,'input_graph_hashes':None,'safe_div_input_copy_required':True,'stages':['safe_div_end','postprocess_end'],'A':'original safe-div and distance sorting','B':'learned gate + replacement of three hard rules + probability sorting','scorer_commit':audit['official_source_commit'],'automatic_parameter_search':False}
save('controlled_config.json',plan)
# Historical ordinary aggregates are NOT an A/B experiment: raw graph identity is unverified.
hist=[]
for name,a,sv in [('Selector',selector_audit,349666428),('Division',audit,349707105)]:
 v=a['official_pp_results']['tight55'];hist.append({'object':name,'sv':sv,'scope':'historical ordinary full-graph validation; not rerun/not paired','n':v['n'],'score':v['score'],'division_tp':v['division_tp'],'division_fp':v['division_fp'],'division_fn':v['division_fn']})
save('historical_ordinary_summary.json',{'rows':hist,'raw_prediction_byte_identity_between_sessions':'UNKNOWN','paired_delta':None,'no_causal_attribution':True})
summary={'fact_class':'MEASURED','training_completed_evidence':True,'ordinary_classifier_used_evidence':True,'models':models,'groups':totals,'gt_inventory_count':len(inv),'nonempty_pair_source_files':sum(r['positives']+r['negatives']>0 for r in inv),'zero_pair_source_files':sum(r['positives']+r['negatives']==0 for r in inv),'original_pairs':training['final_fit']['n_positive']+training['final_fit']['n_negative'],'folds':training['folds'],'seconds':training['seconds'],'ordinary_counts':counts,'ordinary_per_dataset':[{'dataset':r['dataset'],**{k:int(float(r.get(k) or 0)) for k in counts}} for r in rows],'model_parameters_uploaded':False,'optimizer_message':'UNKNOWN: success and iterations saved, raw scipy message/status code absent','optimizer_trajectory':'UNKNOWN: per-iteration loss/gradient not persisted','candidate_training_rows':'UNKNOWN: receipt has per-GT counts/hashes, not original per-candidate coordinates/labels','grouping_rule_evidence':rule_path,'group_separation':'recorded group sets and counts verified against official naming definition; GT payload not independently recomputed','upstream_model_data_lineage':'UNKNOWN','hidden_training_and_runtime':'UNKNOWN'}
save('training_runtime_summary.json',summary)
fields=['sample','embryo','frame','parent_id','child1_id','child2_id','old_accept','old_reason','new_accept','new_reason','classifier_score','held_out_model','context_complete','mutual_nn','separation_growth','distance_symmetry','old_rank','new_rank','deepcenter_gate','topology_conflict','cap_effect','safe_div_added_or_lost','postprocess_added_or_lost','annotation_support','change_category','direct_rule_difference','cascade_difference']
with (HERE/'candidate_diff.csv').open('w',newline='') as f:csv.writer(f,lineterminator='\n').writerow(fields)
d={'task_id':'DIVISION_DIAG_20260915','status':'PARTIAL_BLOCKED','observed_at_utc':now,'object':recs[0]['identity_before'],'evidence_commit':BASE,'evidence_recovery':'TRAINING_AND_ORDINARY_RUNTIME_RECOVERED; diagnostic caches incomplete','input_manifest':'source_read_manifest.json','artifact_manifest':artifacts,'training_summary':'training_runtime_summary.json','frozen_configuration':'controlled_config.json','paired':{'executed':False,'status':'NOT_RUN_MISSING_REQUIRED_CACHES','candidate_rows':0,'executed_samples':[],'prospective_samples':selected['held_out_stems'],'prospective_sample_count':8,'effective_samples':0,'excluded_from_run':8,'unknown_events':None,'per_embryo_metrics':None,'safe_div_stage_metrics':None,'postprocess_stage_metrics':None,'division_tp_fp_fn_A':None,'division_tp_fp_fn_B':None,'official_score_A':None,'official_score_B':None,'paired_delta':None,'added_correct':None,'added_wrong':None,'lost_correct':None,'removed_wrong':None,'unreliably_labeled':None},'gaps':['No persisted DeepCenter heatmaps/point decisions for required candidate union; cannot run detector or bypass gate.','No cached image refinement inputs for single-frame/gap2 recovery; raw .geff is before earlier postprocessing, not exact safe-div input.','Ground-truth bytes and estimated node metadata not recovered; per-file hash/count receipts are not annotations.','Original training candidate rows and per-iteration optimizer trace absent.','Upstream pretraining embryo lineage and hidden formal runtime unknown.'],'hidden_formal_runtime':'UNKNOWN','next_modification':'尚不能确定下一修改点','public_archived':{'Forge':{'submission':56160258,'version':1,'sv':348960877,'score':'0.947'},'Selector':{'submission':56222238,'version':1,'sv':349666428,'score':'0.947'},'Division':{'submission':56226396,'version':1,'sv':349707105,'score':'0.945'},'live_score_read_this_task':False,'new_formal_score':None,'baseline_retained':'Forge 0.947'},'execution':{'notebook_executed':False,'training_calls':0,'classifier_prediction_calls_this_task':0,'detector_runs':0,'kaggle_writes':0,'submissions':0,'selection_changes':0},'github_delivery':'PENDING_SEPARATE_FIXED_COMMIT_READBACK'}
save('diagnosis.json',d);save('source_read_manifest.json',{'inputs':inputs,'cells':cells,'division_module_sha256':sha(module.encode()),'notebook_code_executed':False,'semantic_review':'Full changed module/safe-div and relevant dependencies inspected; all other cells byte/AST comparison only.'})
print(json.dumps({'status':d['status'],'training_artifacts_verified':True,'ordinary_runtime_verified':True,'original_pairs':summary['original_pairs'],'groups':totals,'paired_executed':False,'candidate_rows':0,'historical_ordinary':hist},ensure_ascii=False))
