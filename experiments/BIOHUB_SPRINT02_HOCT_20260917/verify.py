"""本任务预算、输入和交付证据检查；不把 NOT_RUN 认作实测完成。"""
import ast,hashlib,json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert sha(P/'contract.json')=='6f4d778f64475447632514cf2f1515dfc8f4168af8e7ed5f9756f374c0c9c350'
    c=json.loads((P/'contract.json').read_text())
    assert sha(R/'tasks/CODEX_20260917_BIOHUB_SPRINT02_HOCT.md')==c['task_sha256']
    assert c['budgets']==dict(training=0,save_run=2,diagnostic_save_run=1,production_save_run=1,submission=1,dataset_write=0,final_selection=0)
    assert len(c['samples'])==8 and not c['independent_panel_available']
    m=json.loads((P/'manifest.json').read_text())
    for r in m['inputs']:assert sha(R/r['path'])==r['sha256'],r['path']
    for p in P.glob('*.py'):ast.parse(p.read_text())
    subprocess.run([sys.executable,str(P/'test_guard.py')],check=True)
    events=[json.loads(s) for s in (P/'request_ledger.jsonl').read_text().splitlines() if s.strip()]
    counts={k:sum(e.get('counted',0) for e in events if e['action']==k) for k in ['SaveAndRun','Submission']}
    assert counts['SaveAndRun']<=2 and counts['Submission']<=1
    for stage in ['diagnostic','production']:assert sum(e.get('counted',0) for e in events if e.get('stage')==stage and e['action']=='SaveAndRun')<=1
    d=json.loads((P/'diagnostic_metrics.json').read_text());formal=json.loads((P/'formal_receipt.json').read_text())
    if formal['status']=='NOT_RUN':assert formal['submission_id'] is None and formal['public_score'] is None
    if d['status']=='NOT_RUN':assert d.get('score_H1') is None
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=R,text=True).strip()
    assert branch==c['branch']
    print(json.dumps(dict(status='PASS_SCOPED_LOCAL_CHECKS',budgets_used=counts,diagnostic_status=d['status'],formal_status=formal['status'],claim='not an inference or formal-score completion certificate')))

if __name__=='__main__':main()

# Additional result-integrity checks implement the original Stage B stop gate.
if __name__=='__main__' and (P/'verification.json').exists():
    v=json.loads((P/'verification.json').read_text())
    assert v['status']=='VERIFIED_FALLBACK_NO_EFFECT' and len(v['checks'])==8
    assert v['fallback_videos']==8 and v['covered']==v['deleted']==0
    assert not v['production_allowed'] and not v['formal_allowed']
    platform=json.loads((P/'diagnostic_platform.json').read_text())
    assert (platform['kernel_id'],platform['version'],platform['script_version_id'])==(134683728,1,350471527)
    assert platform['status']=='COMPLETE' and platform['source_cells_match']
    for f in platform['collected']:assert sha(R/f['local_path'])==f['sha256']
    for f in (P/'output_v1').glob('*.json'):
        r=next(x for x in platform['collected'] if x['path']=='s02_small/'+f.name)
        assert sha(f)==r['sha256']
    d=json.loads((P/'diagnostic_metrics.json').read_text())
    assert d['summary']['B0']==d['summary']['H1'] and d['decision']=='DIAGNOSTIC_NO_EFFECT'
    assert d['production_gate']=='BLOCKED_HOCT_COVERAGE_UNOBSERVABLE'
    assert sha(P/'diagnostic/candidate.ipynb')==json.loads((P/'diagnostic/build_receipt.json').read_text())['source_sha256']
    local=json.loads((P/'diagnostic/candidate.ipynb').read_text());remote=json.loads((R/platform['source_local']).read_text())
    assert [(c['cell_type'],''.join(c['source'])) for c in local['cells']]==[(c['cell_type'],''.join(c['source'])) for c in remote['cells']]
    print('PASS_TERMINAL_STOP_GATE_AND_IMMUTABLE_SOURCE')
