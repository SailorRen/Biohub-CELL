"""只构建 Notebook，不执行其中代码。拒绝覆盖已冻结合同。"""
import ast
import hashlib
import json
from pathlib import Path

P=Path(__file__).resolve().parent; R=P.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sources(p):return [''.join(c['source']) for c in json.loads(p.read_text())['cells']]

def build():
    contract=json.loads((P/'contract.json').read_text())
    g1=R/'experiments/BIOHUB_SPRINT01_20260916/own/candidate.ipynb'
    assert sha(g1)==contract['G1_source_sha256']
    base=sources(g1)
    source=R/'downloads/PUBLIC_OPT_REVIEW_20260917/sjlee101.ipynb'
    assert sha(source)==contract['HOCT_source_sha256']
    module=sources(source)[6]
    sphere=next(ast.get_source_segment(module,n) for n in ast.parse(module).body if isinstance(n,ast.FunctionDef) and n.name=='_hv_rasterize_spheres')
    helper='import numpy as _hv_np\nimport math as _hv_math\n_HV_SCALE_ZYX=(1.625,.40625,.40625)\n_HV_RADIUS_UM=3.0\n'+sphere+'\n'
    codefiles={n:(P/n).read_text() for n in ['hoct_guard.py','hoct_observer.py','hoct_worker.py']}
    codefiles['source_helpers.py']=helper
    # Use the prior unchanged, embedded official source and scoring adapter.
    scoring=sources(R/'experiments/BIOHUB_SPRINT01_20260916/diagnostic.ipynb')[5]
    pure=next(ast.get_source_segment(base[5],n) for n in ast.parse(base[5]).body if isinstance(n,ast.FunctionDef) and n.name=='graph_from_geff')
    setup='import time\nS02_START=time.monotonic()\n'
    inject='import sys, json, math\nfrom pathlib import Path\nimport numpy as np\nimport tracksdata as td\nVOXEL_SCALE_UM=(1.625,.40625,.40625)\n'+pure+'\n'
    inject+='CONTRACT=json.loads('+repr(json.dumps(contract))+')\n'
    inject+="Path('/kaggle/working/s02_code').mkdir(exist_ok=True)\n"
    for name,code in codefiles.items():
        ast.parse(code)
        inject+=f"Path('/kaggle/working/s02_code/{name}').write_text({code!r})\n"
    inject+="sys.path.insert(0,'/kaggle/working/s02_code')\n"
    cells=[setup,*base[:4],inject,scoring,(P/'diagnostic_runtime.py').read_text()]
    for code in cells:ast.parse(code)
    forbidden=['train_from_mount(','.fit(','torch.optim.']
    assert all(not any(t in s for t in forbidden) for s in cells)
    nb=dict(cells=[dict(cell_type='code',execution_count=None,metadata={},outputs=[],source=s) for s in cells],metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}},nbformat=4,nbformat_minor=5)
    dest=P/'diagnostic';dest.mkdir(exist_ok=True)
    (dest/'candidate.ipynb').write_text(json.dumps(nb,ensure_ascii=False,indent=1)+'\n')
    meta=json.loads((R/'experiments/BIOHUB_SPRINT01_20260916/own/kernel-metadata.json').read_text())
    meta.update(id='sailorren/biohub-s02-h1-diagnostic-20260917',title='Biohub S02 H1 Diagnostic 20260917',code_file='candidate.ipynb')
    meta['dataset_sources']+=['sjlee101/biohub-hoct-020-wheels/1','musculer/biohub-hoct-general-v0-official/1']
    meta['kernel_sources']=['sailorren/biohub-sprint01-diagnostic-20260916/1']
    (dest/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    receipt=dict(source_sha256=sha(dest/'candidate.ipynb'),cells=len(cells),G1_setup_cells=[0,1,2,3],
        G1_detector_and_postprocessor_not_executed=True,scorer_cell_sha256=hashlib.sha256(scoring.encode()).hexdigest(),
        sphere_function_sha256=hashlib.sha256(sphere.encode()).hexdigest(),training_calls=0)
    (dest/'build_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))

if __name__=='__main__':build()
