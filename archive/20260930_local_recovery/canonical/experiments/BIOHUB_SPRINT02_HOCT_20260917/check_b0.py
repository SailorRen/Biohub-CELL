"""本地纯缓存评分：使用既有官方适配器，无模型导入或推理。"""
import hashlib,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1]
sys.path.insert(0,str(R/'experiments/TARGET950_20260914'))
from test_official_selector import load_official,load_scope
sys.path.insert(0,str(R/'experiments/BIOHUB_SPRINT01_20260916'))
from read_gt import read_gt
metrics=load_official();scope,_,_=load_scope(R/'experiments/TARGET950_20260914/baseline/candidate.ipynb',metrics)
contract=json.loads((P/'contract.json').read_text());rows=[];checks=[]
for s in contract['samples']:
    p=R/s['cache_path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==s['cache_sha256']
    v=json.loads(p.read_text());pn={int(i):tuple(n[k] for k in ['t','z','y','x']) for i,n in v['nodes']};pe=[(e['source_id'],e['target_id']) for e in v['edges']]
    gn,ge=read_gt(s['stem'])
    r=scope['score_sample'](pn,pe,gn,ge,s['n_total']);repeat=scope['score_sample'](pn,pe,gn,ge,s['n_total'])
    assert r['input_pred_graph_sha256']==s['scorer_input_hash'] and r['input_gt_graph_sha256']==s['gt_input_hash']
    for k in ['edge_tp','edge_fp','edge_fn','div_tp','div_fp','div_fn','adj_edge_jaccard','node_recall']:assert r[k]==repeat[k]
    rows.append(r);checks.append(dict(stem=s['stem'],input_hashes_match=True,repeat_exact=True))
result=dict(status='B0_INPUT_AND_SCORER_VERIFIED',checks=checks,summary=metrics.summarise(rows),model_executions=0,training_calls=0,scope='B0 cache only; H1 NOT_RUN')
(P/'b0_preflight.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
