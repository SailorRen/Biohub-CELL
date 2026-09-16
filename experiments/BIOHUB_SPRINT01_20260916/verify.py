"""Task-scoped fail-closed verification; never equates file delivery with evaluated results."""
import collections,hashlib,json,math,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1]
read=lambda n:json.loads((P/n).read_text())
assert hashlib.sha256((R/'tasks/CODEX_20260916_BIOHUB_SPRINT01.md').read_bytes()).hexdigest()=='cbdbe51f3948b57b7387a101234354d769fe3cbe91eb8959f04f634605dae17c'
rules=read('selection_rules.json');ledger=read('ledger.json');result=read('results.json')
requests=ledger['requests'];count=collections.Counter(r['action'] for r in requests)
assert count['SaveAndRun']<=4 and count['Submission']<=2
assert all(sum(r['action']=='Submission' and r.get('role')==role for r in requests)<=1 for role in ['own','public'])
assert ledger['training_calls']==ledger['final_selection_changes']==0
assert result['required_computations_complete'] is True,'REQUIRED_COMPUTATION_NOT_COMPLETE'
assert result['public']['status']=='NO_VERIFIED_PUBLIC_CANDIDATE' or result['public']['formal_submission_id']
collection=read('collection_v1.json');assert collection['status']=='COMPLETE' and collection['source_before_after_equal']
assert collection['version']==1 and collection['script_version_id']==350191694
for item in collection['files']:
 if 'git_path' in item:assert hashlib.sha256((R/item['git_path']).read_bytes()).hexdigest()==item['sha256']
d=read('output_v1/diagnostic_results.json');assert d['samples']==rules['samples'] and len(set(d['samples']))==8
stages=read('output_v1/stages.json');decisions=read('output_v1/candidate_decisions.json')
assert len(stages)==32
for stem in d['samples']:
 rows={r['arm']:r for r in stages if r['sample']==stem};assert set(rows)=={'A0','A0_repeat','G1','R1'}
 assert len({r['raw_hash'] for r in rows.values()})==1
 assert len({r['safe_div_input_hash'] for r in rows.values()})==1
 assert rows['A0']['final_hash']==rows['A0_repeat']['final_hash']
 assert rows['A0']['safe_div_hash']==rows['A0_repeat']['safe_div_hash']
 sets={a:{(r['frame'],r['parent'],r['child1'],r['child2']) for r in decisions if r['dataset']==stem and r['arm']==a} for a in ['A0','G1','R1']}
 assert sets['A0']==sets['G1']==sets['R1']
for r in decisions:
 s=r['learned_score'];assert s is None or math.isfinite(s)
 if r['arm']=='G1':assert r['accepted_before_sort']==(s is None or s>=.95)
 else:assert r['accepted_before_sort'] is True
variation=abs(d['summary']['A0']['score']-d['summary']['A0_repeat']['score']);assert variation==d['repeat_variation']==0
changes=read('output_v1/changed_edges.json')
passes={a:d['summary'][a]['score']-d['summary']['A0']['score']>variation and all(d['by_embryo'][a][g]['score']>=d['by_embryo']['A0'][g]['score'] for g in ['44b6','6bba']) and any(e['arm']==a for e in changes) for a in ['G1','R1']}
assert passes==d['pass'];q=[a for a in passes if passes[a]];winner=max(q,key=lambda a:(d['summary'][a]['score'],a=='G1')) if q else None
assert winner==d['selected']==result['own']['selected']
if winner:
 assert result['own']['formal_submission_id'],'QUALIFIED_CANDIDATE_NOT_SUBMITTED'
 formal=read('formal_latest.json');ordinary=read('own_ordinary_verified.json')
 assert formal['status']=='COMPLETE' and formal['submission_id']==result['own']['formal_submission_id']
 assert math.isfinite(float(formal['public_score'])) and result['own']['public_score']==formal['public_score']
 assert ordinary['status']=='ORDINARY_VERIFIED' and ordinary['source_before']==ordinary['source_after']
 assert ordinary['binding']['script_version_id']==formal['script_version_id']
 assert ordinary['production_receipt']['weight_sha256']=='0a1f9b93bb529e70f4f7c2ba0907eea8b4cecd2befccc8ba1fb75e569edf77a0'
 for item in ordinary['artifacts']:
  if 'git_path' in item:assert hashlib.sha256((R/item['git_path']).read_bytes()).hexdigest()==item['sha256']
 assert read('own/source_review.json')['byte_identical_cells']==[0,1,2,3,4,6,7,8,9,10,11]
else:assert not any(r['action']=='Submission' and r.get('role')=='own' for r in requests)
assert all(r['historical_hash_match'] for r in read('gt_reader_integrity.json')['rows'])
assert all(r['exit_code']==0 for r in read('local_tests.json')['runs'])
events=read('event_attribution.json');assert events['status']=='VERIFIED_FINAL_STAGE' and len(events['checks'])==24
assert all(r['pred_hash_match'] and r['gt_hash_match'] and r['division_counts_match'] for r in events['checks'])
safe=read('safe_event_attribution.json');assert safe['status']=='VERIFIED_SAFE_DIV_STAGE' and len(safe['checks'])==24
assert all(r['pred_hash_match'] and r['gt_hash_match'] and r['full_metric_recomputed_match'] for r in safe['checks'])
replay=read('reconstructed_stages.json');assert len(replay['checks'])==24
assert all(r['raw_hash_match'] and r['pre_safe_hash_match'] and r['safe_hash_match'] for r in replay['checks'])
assert replay['detector_or_temporal_model_executions']==replay['platform_writes']==0
assert sum(replay['selection_counts']['G1'].values())==154
# Match exact frozen inherited inputs; tests above prove only task-specific behavior.
assert subprocess.check_output(['git','branch','--show-current'],cwd=R,text=True).strip()=='codex/sprint01-20260916'
subprocess.run(['git','merge-base','--is-ancestor','a1c5859a933e2f71269fc225bc9bbc55851cc860','HEAD'],cwd=R,check=True)
print('PASS: fixed cohort, same inputs, original-rule preservation, repeatability, frozen selection, evidence hashes, request budgets; no claim of Public improvement')
