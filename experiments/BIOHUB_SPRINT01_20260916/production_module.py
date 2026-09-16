"""Frozen-model inference and ordinary runtime evidence; inserted into Forge cell 5.
SPRINT_ARM, VALIDATION_EMBRYO_MAP and original/patched functions supplied by builder.
"""
import copy as _sprint_copy
import hashlib as _sprint_hashlib
import json as _sprint_json
_SPRINT_WEIGHT_SHA='0a1f9b93bb529e70f4f7c2ba0907eea8b4cecd2befccc8ba1fb75e569edf77a0'
_sprint_paths=[p for p in Path('/kaggle/input').rglob('division_gate_weights.json') if _sprint_hashlib.sha256(p.read_bytes()).hexdigest()==_SPRINT_WEIGHT_SHA]
assert len(_sprint_paths)==1,'SPRINT_EXACT_WEIGHT_REQUIRED'
_SPRINT_WEIGHTS=_sprint_json.loads(_sprint_paths[0].read_text())
assert set(_SPRINT_WEIGHTS['held_out'])=={'44b6','6bba'}
_SPRINT_TRAIN_RECEIPT=_sprint_json.loads((_sprint_paths[0].parent/'division_training_receipt.json').read_text())
assert _SPRINT_TRAIN_RECEIPT['weights_sha256']==_SPRINT_WEIGHT_SHA
for _fold in _SPRINT_TRAIN_RECEIPT['folds']:assert _fold['held_out_embryo'] not in _fold['training_embryos']
SPRINT_CALLS=[]
def _sprint_model_key(dataset):
 # Original validator switches the actual source directory; embryo comes only from the explicit frozen map.
 if Path(TEST_DIR).resolve()==(Path(COMP_DIR)/'train').resolve():
  assert dataset in VALIDATION_EMBRYO_MAP,'UNMAPPED_VALIDATION_EMBRYO'
  return VALIDATION_EMBRYO_MAP[dataset]
 return 'final'
def _sprint_score(snapshot,parent,c1,c2,dataset):
 nodes,out_edges=snapshot;out={u:[int(e['target_id']) for e in es] for u,es in out_edges.items() if u in (c1,c2)}
 coords=context(nodes,out,parent,c1,c2)
 if coords is None:return None
 key=_sprint_model_key(dataset);model=_SPRINT_WEIGHTS['final'] if key=='final' else _SPRINT_WEIGHTS['held_out'][key]
 return float(predict(model,pair_features(coords)))
def _sprint_graph_hash(nodes,edges):
 return _sprint_hashlib.sha256(_sprint_json.dumps([list(nodes.items()),edges],allow_nan=False,separators=(',',':')).encode()).hexdigest()
def sprint_audited_safe_div(nodes,edges,stats,**kw):
 global SPRINT_POLICY
 dataset=kw['dataset'];SPRINT_POLICY=ProposalPolicy(SPRINT_ARM,_sprint_score)
 before=_sprint_graph_hash(nodes,edges)
 shadow_nodes=_sprint_copy.deepcopy(nodes);shadow_edges=_sprint_copy.deepcopy(edges);shadow_stats=dict(stats)
 result=_sprint_patched_safe_div(nodes,edges,stats,**kw)
 # Same snapshot original rule replay is evidence only; it never supplies output.
 old=_sprint_original_safe_div(shadow_nodes,shadow_edges,shadow_stats,**kw)
 assert _sprint_graph_hash(shadow_nodes,shadow_edges)==before,'SPRINT_SHADOW_INPUT_MUTATED'
 old_es={(int(e['source_id']),int(e['target_id'])) for e in old};new_es={(int(e['source_id']),int(e['target_id'])) for e in result}
 record={'dataset':dataset,'arm':SPRINT_ARM,'model':_sprint_model_key(dataset),'input_hash':before,'old_safe_hash':_sprint_graph_hash(shadow_nodes,old),'new_safe_hash':_sprint_graph_hash(nodes,result),'added_edges':sorted(new_es-old_es),'lost_edges':sorted(old_es-new_es),'classifier_calls':sum(r['learned_score'] is not None for r in SPRINT_POLICY.rows),'filtered':sum(not r['accepted_before_sort'] for r in SPRINT_POLICY.rows),'abstain':sum(r['abstain'] for r in SPRINT_POLICY.rows),'fallback_frames':SPRINT_POLICY.frame_fallbacks,'candidates':SPRINT_POLICY.rows,'resolved_config':{k:globals()[k] for k in SPRINT_PP_KEYS}}
 SPRINT_CALLS.append(record)
 with (WORKING_DIR/'sprint_production_calls.jsonl').open('a') as f:f.write(_sprint_json.dumps(record,allow_nan=False)+'\n')
 print('SPRINT_PRODUCTION_SAFE_DIV',dataset,record['model'],record['classifier_calls'],len(record['added_edges']),len(record['lost_edges']),flush=True)
 return result
add_safe_divisions_postlink=sprint_audited_safe_div
