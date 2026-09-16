"""Independent pre-production gate on actual diagnostic outputs and frozen rules."""
import hashlib,json,math
from pathlib import Path
P=Path(__file__).resolve().parent;O=P/'output_v1';load=lambda p:json.loads(p.read_text())
d=load(O/'diagnostic_results.json');rules=load(P/'selection_rules.json');stages=load(O/'stages.json');rows=load(O/'candidate_decisions.json');v=load(P/'verified_metrics.json')
assert d['samples']==rules['samples'] and len(stages)==32
for stem in rules['samples']:
 rr={r['arm']:r for r in stages if r['sample']==stem};assert len(rr)==4
 assert len({r['raw_hash'] for r in rr.values()})==len({r['safe_div_input_hash'] for r in rr.values()})==1
 assert rr['A0']['final_hash']==rr['A0_repeat']['final_hash'] and rr['A0']['safe_div_hash']==rr['A0_repeat']['safe_div_hash']
 cs={a:{(r['frame'],r['parent'],r['child1'],r['child2']) for r in rows if r['dataset']==stem and r['arm']==a} for a in ['A0','G1','R1']};assert cs['A0']==cs['G1']==cs['R1']
for r in rows:
 s=r['learned_score'];assert s is None or math.isfinite(s)
 if r['arm']=='G1':assert r['accepted_before_sort']==(s is None or s>=.95)
 else:assert r['accepted_before_sort']
variation=abs(v['A0']['final']['overall']['score']-v['A0_repeat']['final']['overall']['score']);assert variation==0
passes={};detail={}
for arm in ['G1','R1']:
 delta=v[arm]['final']['overall']['score']-v['A0']['final']['overall']['score'];group_delta={g:v[arm]['final']['by_embryo'][g]['score']-v['A0']['final']['by_embryo'][g]['score'] for g in ['44b6','6bba']};changed=any(r['final_hash']!=next(q['final_hash'] for q in stages if q['sample']==r['sample'] and q['arm']=='A0') for r in stages if r['arm']==arm)
 passes[arm]=changed and delta>variation and all(x>=0 for x in group_delta.values());detail[arm]={'delta':delta,'group_delta':group_delta,'actual_final_graph_change':changed,'passes':passes[arm]}
q=[a for a in passes if passes[a]];selected=max(q,key=lambda a:(v[a]['final']['overall']['score'],a=='G1')) if q else None
assert passes==d['pass'] and selected==d['selected']
e=load(P/'event_attribution.json');assert len(e['checks'])==24 and all(r['full_metric_recomputed_match'] for r in e['checks'])
r={'status':'PASS','selected':selected,'repeat_variation':variation,'arms':detail,'rules_sha256':hashlib.sha256((P/'selection_rules.json').read_bytes()).hexdigest(),'scope':'controlled eight-field/two-embryo diagnostic, not Public score or generalization guarantee'};(P/'selection_verified.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
