"""仅本次本地接入修复验收，不调用Kaggle、不运行模型。"""
import ast,hashlib,inspect,importlib.metadata,json,subprocess,sys,zipfile
from pathlib import Path
P=Path(__file__).resolve().parent;B=P.parent;R=B.parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
    assert sha((P/'fix_contract.json').read_bytes())=='b206425e9255bd0a5de27f2e4c303ac0d03f6192abcd45415edb3be78a9c651e'
    assert importlib.metadata.version('tracksdata')=='0.1.0rc6.dev3+g980c2d30a'
    for file,digest in json.loads((P/'initial_state.json').read_text())['historical_hashes'].items():assert sha((R/file).read_bytes())==digest,file
    for name in ['test_observer.py','test_guard.py']:
        subprocess.run([sys.executable,str(B/name)],check=True)
    nb=json.loads((P/'diagnostic_fixed.ipynb').read_text());old=json.loads((B/'diagnostic/candidate.ipynb').read_text())
    for i,c in enumerate(nb['cells']):
        assert not c['outputs'] and c['execution_count'] is None
        ast.parse(''.join(c['source']))
        if i not in [5,7]:assert c==old['cells'][i]
    embedded={}
    for n in ast.parse(nb['cells'][5]['source']).body:
        if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and n.value.func.attr=='write_text':
            embedded[Path(ast.literal_eval(n.value.func.value.args[0])).name]=ast.literal_eval(n.value.args[0])
    for name in ['hoct_guard.py','hoct_observer.py','hoct_worker.py']:assert embedded[name]==(B/name).read_text()
    assert nb['cells'][7]['source']==(B/'diagnostic_runtime.py').read_text()
    r=json.loads((P/'build_receipt.json').read_text());assert r['source_sha256']==sha((P/'diagnostic_fixed.ipynb').read_bytes()) and r['cloud_status']=='NOT_RUN'
    import tracksdata as td
    package_root=Path(inspect.getfile(td)).parent
    wheels=list((R/'downloads/BIOHUB_SPRINT02_HOCT_20260917/support').rglob('tracksdata-*.whl'));assert len(wheels)==1
    with zipfile.ZipFile(wheels[0]) as z:
        files=['graph/_rustworkx_graph.py','graph/_base_graph.py','nodes/_mask.py']
        hashes={}
        for f in files:
            data=(package_root/f).read_bytes();assert data==z.read('tracksdata/'+f);hashes[f]=sha(data)
    result=dict(status='FIXED_LOCAL_VERIFIED',cloud_status='NOT_RUN',original_experiment='PARTIAL_BLOCKED',hoct_effect='UNKNOWN',new_public_score=None,
      tests=dict(observer=7,guard=4,old_error_reproduced=True,real_backend=True,synthetic_selection=True,fast_stop_remaining_calls=0,wrappers_restored=True),
      package_version=importlib.metadata.version('tracksdata'),backend=str(td.graph.InMemoryGraph),source_wheel=str(wheels[0].relative_to(R)),wheel_sha256=sha(wheels[0].read_bytes()),package_source_sha256=hashes,
      source_hashes={str(p.relative_to(R)):sha(p.read_bytes()) for p in [B/'hoct_observer.py',B/'hoct_worker.py',B/'diagnostic_runtime.py',B/'test_observer.py',P/'build_fixed.py',P/'diagnostic_fixed.ipynb']},
      budgets_used={k:0 for k in ['kaggle_write','save_run','submission','dataset_write','training','model_inference','final_selection']},
      limitations=['No HOCT model inference, solver execution or cloud rerun. Synthetic selected graph; real frozen graph interfaces. NumPy local 2.4.2 vs historical cloud 2.0.2; graph backend source matches wheel bytewise.'])
    if '--record' in sys.argv:(P/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__':main()
