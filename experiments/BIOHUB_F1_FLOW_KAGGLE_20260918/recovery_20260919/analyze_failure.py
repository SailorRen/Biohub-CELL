"""Read saved small evidence and reproduce schema error on one synthetic row only."""
import ast,json,re,hashlib,warnings
from pathlib import Path
from decimal import Decimal
P=Path(__file__).resolve().parent.parent;R=P.parents[1];E=P/'recovery_20260919'
platform=json.loads((P/'diagnostic/platform_20260919T130712Z.json').read_text())
assert platform['worker_status']=='ERROR' and platform['version']==1 and platform['script_version_id']==351058693
log=''.join(x['data'] for x in json.loads((P/'diagnostic/log_20260919T130712Z.txt').read_text()))
assert "KeyError: 'edge_tp'" in log
rows=[]
for stem,b,f in re.findall(r'F1_SAMPLE_COMPLETE (\S+) ([0-9.e+-]+) ([0-9.e+-]+)',log):rows.append({'stem':stem,'B0':b,'F1':f,'delta':str(Decimal(f)-Decimal(b)),'provenance':'cloud log F1_SAMPLE_COMPLETE; not reconstructed aggregate'})
c=json.loads((P/'contract.json').read_text());assert [x['stem'] for x in rows]==c['samples']
runtime=json.loads((P/'diagnostic/runtime_start.json').read_text());assert runtime['config']==c['configuration'] and runtime['flow_config']==c['flow']
old=json.loads((P.parent/'BIOHUB_SPRINT01_20260916/output_v1/bidirectional_production_runtime_integrity.json').read_text());assert runtime['weight_sha256']==old['checkpoint_sha256']
assert runtime['division_sha256']=='0a1f9b93bb529e70f4f7c2ba0907eea8b4cecd2befccc8ba1fb75e569edf77a0'
manifest=json.loads((P.parent/'BIOHUB_SPRINT01_20260916/replay_cache_manifest.json').read_text())['files'];expected=[{k:x[k] for k in ['name','sha256']} for x in manifest if x['source_ref']=='sailorren/biohub-division-train-20260914' and x['name'].startswith('tracking_repo/predictions/')]
assert json.loads((P/'diagnostic/input_hashes.json').read_text())==expected and len(expected)==264
source=R/'experiments/TARGET950_20260914/vendor/official_075fc5/metrics.py';assert hashlib.sha256(source.read_bytes()).hexdigest()==runtime['scorer_hashes']['metrics.py']
tree=ast.parse(source.read_text());keep=[]
for n in tree.body:
 if isinstance(n,ast.FunctionDef) and n.name in ['summarise','_jaccard']:keep.append(n)
 if isinstance(n,ast.AnnAssign) and isinstance(n.target,ast.Name) and n.target.id in ['COUNT_COLUMNS','SCORE_DIVISION_WEIGHT']:keep.append(n)
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ['COUNT_COLUMNS','SCORE_DIVISION_WEIGHT'] for t in n.targets):keep.append(n)
scope={'warnings':warnings};exec(compile(ast.Module(body=keep,type_ignores=[]),'synthetic_schema_only','exec'),scope)
row=dict(edge_tp=8,edge_fp=1,edge_fn=1,division_tp=1,division_fp=0,division_fn=0,num_pred_nodes=10,node_recall=.8,adj_edge_jaccard=.8)
summary=scope['summarise']([row]);assert all(k not in summary for k in ['edge_tp','edge_fp','edge_fn'])
try:summary['edge_tp']
except KeyError:reproduced=True
else:raise AssertionError('NOT_REPRODUCED')
result={'status':'DIAGNOSTIC_ERROR_SUMMARY_SCHEMA','ref':platform['ref'],'version':1,'script_version_id':351058693,'platform_status':'ERROR','wall_seconds_ui':2231.9,'root_cause':"F1 runtime expects edge_tp/edge_fp/edge_fn in aggregate; official summarise does not return those keys",'synthetic_schema_error_reproduced':reproduced,'official_summary_keys':sorted(summary),'completed_views':8,'arms_per_view':4,'graph_files_listed':sum(x.endswith('_graph.json') for x in platform['output_names']),'graphs_downloaded':0,'small_output_files':[x for x in platform['output_names'] if x.startswith('f1_small/')],'missing_outputs':['results.json','stages.json','per_view.csv','edge_changes.csv','flow_usage.csv'],'input_hashes_verified':264,'weights_config_scorer_hash_verified':True,'per_view_log_scores':rows,'official_overall_score':None,'official_embryo_scores':None,'production_allowed':False,'formal_submission':'NOT_RUN','second_issue':'All result tables saved only after summary; exception prevented their export','proposed_single_engineering_change':'Repair schema mapping by explicitly summing official per-view edge counts; checkpoint small per-view rows/stages/events/flow before final summary. Do not alter metric, weights, algorithm or thresholds.','repair_implemented':False,'new_cloud_writes':0}
(E/'failure_analysis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
