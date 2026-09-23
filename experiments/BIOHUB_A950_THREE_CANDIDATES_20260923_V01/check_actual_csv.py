"""Independent stdlib-only check of actual downloaded candidate output; no launch/submit."""
import argparse,csv,hashlib,json,re
from collections import Counter
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'BIOHUB_TWO_WAVE_20260922_V01'))
from patch_support import invariant_graph
p=argparse.ArgumentParser();p.add_argument('csv');p.add_argument('receipt');p.add_argument('--arm',choices=['V0375', 'V025-L020P', 'V025-L030P'],required=True);p.add_argument('--output',required=True);p.add_argument('--other-check',action='append',default=[]);a=p.parse_args()
receipt=json.loads(Path(a.receipt).read_text(encoding='utf-8'))
assert receipt['task_id']=='BIOHUB_A950_THREE_CANDIDATES_20260923_V01' and receipt['arm']==a.arm
assert receipt['csv_roundtrip']=='PASS' and receipt['worker_config_verified'] is True
assert receipt['velocity']==({'V0375': 0.375, 'V025-L020P': 0.25, 'V025-L030P': 0.25}[a.arm])
assert receipt['leaf_threshold']==({'V0375': None, 'V025-L020P': 0.2, 'V025-L030P': 0.3}[a.arm])
assert receipt['worker_det_threshold']==.960 and receipt['worker_bidirectional_weight']==.15
assert receipt['gate_weight_sha256']=='0a1f9b93bb529e70f4f7c2ba0907eea8b4cecd2befccc8ba1fb75e569edf77a0'
assert receipt['weights']=={'primary':'12f6881ee3620a831697ca098ff8f48e687a24225f4e048b538deec3562fe771', 'secondary':'9bac2fa0dadc4a6fc1899e0caf187f4b553e0a7cd90ba1261a68b35ffe9e305f', 'deepcenter':'8040999a92f6b7bbd98fa8cf458141e045c0f9ad7c936bdb3b18e1f7edafe2a0'}
assert receipt['final_resolved_config']['DEEPCENTER_SAFE_DIV_THRESHOLD']==.20
columns=['id','dataset','row_type','node_id','t','z','y','x','source_id','target_id']
groups={};count=0
with Path(a.csv).open(newline='',encoding='utf-8') as f:
    rd=csv.DictReader(f);assert rd.fieldnames==columns
    for row in rd:
        for k in columns:
            if k not in ['dataset','row_type']:
                assert re.fullmatch(r'-?\d+',row[k]);row[k]=int(row[k])
        assert row['id']==count;count+=1
        ns,es=groups.setdefault(row['dataset'],({},[]))
        if row['row_type']=='node':
            assert row['node_id'] not in ns and min(row[k] for k in ['node_id','t','z','y','x'])>=0
            assert row['source_id']==row['target_id']==-1
            ns[row['node_id']]={k:row[k] for k in ['t','z','y','x']}
        else:
            assert row['row_type']=='edge' and all(row[k]==-1 for k in ['node_id','t','z','y','x'])
            es.append({k:row[k] for k in ['source_id','target_id']})
assert set(groups)==set(receipt['expected_samples'])
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
result={}
for stem,(ns,es) in groups.items():
    pairs=[(e['source_id'],e['target_id']) for e in es];assert len(set(pairs))==len(pairs)
    inc=Counter();out=Counter()
    for s,t in pairs:
        assert s in ns and t in ns and ns[t]['t']==ns[s]['t']+1
        inc[t]+=1;out[s]+=1
    assert ns and max(inc.values(),default=0)<=1 and max(out.values(),default=0)<=2
    canon=[[[i,n['t'],float(n['z']),float(n['y']),float(n['x'])] for i,n in sorted(ns.items())],sorted([s,t] for s,t in pairs)]
    oldhash=digest(canon);invhash=digest(invariant_graph(ns,es))
    assert oldhash==receipt['final_graphs'][stem]['canonical_sha256']
    assert invhash==receipt['same_run_comparison'][stem]['candidate_invariant_sha256']
    result[stem]={'nodes':len(ns),'edges':len(es),'canonical_sha256':oldhash,'id_independent_sha256':invhash}
filehash=hashlib.sha256(Path(a.csv).read_bytes()).hexdigest()
assert filehash==receipt['final_csv_sha256']
canonical=digest({s:r['canonical_sha256'] for s,r in result.items()})
assert canonical==receipt['final_canonical_sha256']
known=json.loads((Path(__file__).parent.parent/'BIOHUB_TWO_WAVE_20260922_V01/known_output_hashes.json').read_text())
assert all(filehash!=r['csv_sha256'] and canonical!=r['canonical_sha256'] for r in known['outputs']),'DUPLICATE_ARCHIVED_OUTPUT'
invariant=digest({s:r['id_independent_sha256'] for s,r in result.items()})
for other in [str(Path(__file__).parent.parent/'BIOHUB_TWO_WAVE_20260922_V01/A/formal_precheck.json'),*a.other_check]:
    prior=json.loads(Path(other).read_text())
    assert invariant!=prior['id_independent_sha256'],'DUPLICATE_BATCH_OUTPUT'
assert receipt['has_effect'] and any(r['actual_effect'] for r in receipt['same_run_comparison'].values()),'NO_EFFECT_DO_NOT_SUBMIT'
summary={'arm':a.arm,'status':'CSV_AND_RECEIPT_PASS','sha256':filehash,'canonical_sha256':canonical,'id_independent_sha256':invariant,'rows':count,'graphs':result,'archived_deduplication':'PASS','other_batch_checks':a.other_check,'scope':'Actual CSV downloaded from exact ordinary version; independent stdlib check plus same-run official reader receipt. Formal score not implied.'}
Path(a.output).write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8');print(json.dumps(summary,indent=2))
