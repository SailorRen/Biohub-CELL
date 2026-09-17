"""在云端执行：同一 G1 缓存、一次 HOCT、官方最终图配对评分。"""
import copy
import hashlib
import importlib.metadata
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from hoct_guard import apply_guard, digest

OUT = Path('/kaggle/working/s02_small'); OUT.mkdir(exist_ok=True)
CACHE = Path('/kaggle/working/s02_cache'); CACHE.mkdir(exist_ok=True)
def clean(x):
    if isinstance(x, dict): return {str(k):clean(v) for k,v in x.items()}
    if isinstance(x,(tuple,list)): return [clean(v) for v in x]
    if isinstance(x,np.generic): return clean(x.item())
    if isinstance(x,float) and not math.isfinite(x): return None
    return x
def save(name,value):
    (OUT/name).write_text(json.dumps(clean(value),indent=2,allow_nan=False)+'\n')

# Verify assets before installation; --no-deps cannot silently upgrade G1.
package_before = {n:importlib.metadata.version(n) for n in ['torch','numpy','tracksdata','polars','pydantic']}
for name, sha in CONTRACT['offline_files'].items():
    hits = [p for p in Path('/kaggle/input').rglob(name) if hashlib.sha256(p.read_bytes()).hexdigest()==sha]
    assert hits, 'ASSET_HASH_MISSING:'+name
    if name=='general_v0.pt': weights=hits[0]
    if name.startswith('hoct-'): wheels=hits[0].parent
subprocess.run([sys.executable,'-m','pip','install','--no-index','--no-deps','--find-links',str(wheels),
                'hoct==0.2.0','spatial-graph==0.1.1','pooch==1.9.0'],check=True)
assert package_before == {n:importlib.metadata.version(n) for n in package_before}
import tracksdata as td
rows = {'B0':[],'H1':[]}; coverage=[]; deletions=[]; repeats=[]
for sample in CONTRACT['samples']:
    stem = sample['stem']
    hits=[p for p in Path('/kaggle/input').rglob(stem+'_G1_graph.json') if hashlib.sha256(p.read_bytes()).hexdigest()==sample['cache_sha256']]
    assert len(hits)==1, ('FINAL_GRAPH_CACHE_REQUIRED',stem,len(hits))
    v=json.loads(hits[0].read_text()); nodes={int(i):n for i,n in v['nodes']}; edges=v['edges']
    before=digest([stem,list(nodes.items()),edges])
    gt=graph_from_geff(TRAIN_DIR/(stem+'.geff')); gn,ge=graph_to_plain(gt)
    total=read_estimated_true_node_count(TRAIN_DIR/(stem+'.geff'))
    def evaluate(n,e):
        return score_sample(nodes_by_id_to_plain(n),[(int(x['source_id']),int(x['target_id'])) for x in e],gn,ge,total)
    b0=evaluate(copy.deepcopy(nodes),copy.deepcopy(edges)); repeat=evaluate(copy.deepcopy(nodes),copy.deepcopy(edges))
    assert clean(b0)==clean(repeat), 'NONREPEATABLE_B0_SCORE'
    assert b0['input_pred_graph_sha256']==sample['scorer_input_hash']
    assert b0['input_gt_graph_sha256']==sample['gt_input_hash']
    job=dict(video=stem,input_hash=before,graph=str(hits[0]),train_dir=str(TRAIN_DIR),weights=str(weights),
             result=str(CACHE/(stem+'_evidence.json')),start_monotonic=S02_START,deadline_s=CONTRACT['deadline_s'])
    jp=CACHE/(stem+'_job.json');jp.write_text(json.dumps(job))
    remain=CONTRACT['deadline_s']-(time.monotonic()-S02_START)
    if remain<=0 or 9*len(nodes)/1000+10>min(900,remain):
        evidence=dict(video=stem,input_hash=before,complete=False,reason='BUDGET_ESTIMATE')
    else:
        with (CACHE/(stem+'.log')).open('w') as log:
            proc=subprocess.Popen([sys.executable,'/kaggle/working/s02_code/hoct_worker.py',str(jp)],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            try:
                code=proc.wait(timeout=remain)
                evidence=json.loads(Path(job['result']).read_text()) if code==0 else dict(video=stem,input_hash=before,complete=False,reason='WORKER_ERROR')
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGKILL);proc.wait()
                evidence=dict(video=stem,input_hash=before,complete=False,reason='HARD_GLOBAL_TIMEOUT')
    hn,he,r,deleted=apply_guard(stem,copy.deepcopy(nodes),copy.deepcopy(edges),evidence)
    assert digest([stem,list(nodes.items()),edges])==before
    h1=evaluate(hn,he)
    for arm,row in [('B0',b0),('H1',h1)]:
        row.update(stem=stem,embryo=sample['embryo']);rows[arm].append(row)
    r.update(evidence_summary={k:v for k,v in evidence.items() if k not in ['covered','selected']})
    coverage.append(r);repeats.append(dict(stem=stem,exact_repeat=True))
    for u,v in deleted:
        deletions.append(dict(video=stem,embryo=sample['embryo'],source=u,target=v,frame=nodes[u]['t'],
                              attribution='UNKNOWN',note='Pending unchanged official edge-matching readback; never treat unmatched as negative'))
    (CACHE/(stem+'_H1_graph.json')).write_text(json.dumps(dict(nodes=list(hn.items()),edges=he),allow_nan=False))
    save('progress.json',dict(completed=len(coverage),samples=len(CONTRACT['samples']),latest=stem))
    print('S02_FOV',stem,r,flush=True)
def aggregate(rs):
    answer=aggregate_official(rs)
    answer.update({k:sum(r[k] for r in rs) for k in ['edge_tp','edge_fp','edge_fn']})
    return answer
summary={a:aggregate(rs) for a,rs in rows.items()}
groups={a:{g:aggregate([r for r in rs if r['embryo']==g]) for g in ['44b6','6bba']} for a,rs in rows.items()}
fail=[]
for g in ['ALL','44b6','6bba']:
    a=summary['B0'] if g=='ALL' else groups['B0'][g]
    b=summary['H1'] if g=='ALL' else groups['H1'][g]
    if b['score']<a['score']:fail.append(g+':SCORE_DOWN')
    for key in ['edge_tp','division_tp']:
        if b[key]<a[key]:fail.append(g+':'+key+'_DOWN')
    for key in ['edge_fn','division_fn']:
        if b[key]>a[key]:fail.append(g+':'+key+'_UP')
covered_groups={s['embryo'] for s in CONTRACT['samples'] if any(r['video']==s['stem'] and r['covered']>0 for r in coverage)}
if fail:decision='DIAGNOSTIC_REJECT'
elif not deletions or covered_groups!={'44b6','6bba'}:decision='DIAGNOSTIC_NO_EFFECT'
else:decision='DIAGNOSTIC_GAIN' if summary['H1']['score']>summary['B0']['score'] else 'EXPLORATORY_ALLOWED'
save('diagnostic_metrics.json',dict(status='EVALUATED',decision=decision,failures=fail,summary=summary,by_embryo=groups,per_sample=rows,repeats=repeats,independent_panel_available=False,production_gate='PENDING_LOCAL_OFFICIAL_EDGE_ATTRIBUTION'))
save('coverage.json',coverage);save('deleted_edges.json',deletions)
save('runtime_receipt.json',dict(stage='B',package_versions=package_before,seconds=time.monotonic()-S02_START,training_calls=0,detector_calls=0,complete_samples=len(coverage),hoct_successful_videos=sum(r['evidence_summary'].get('complete') is True for r in coverage)))
print('S02_DIAGNOSTIC_DONE',decision,flush=True)
