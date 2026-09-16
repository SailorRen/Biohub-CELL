import ast,hashlib,json
from pathlib import Path
from division_patch import patch_safe_div
R=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent

def cells(path):return [''.join(c['source']) for c in json.loads((R/path).read_text())['cells'] if c['cell_type']=='code']
f=cells('experiments/TARGET950_20260914/baseline/candidate.ipynb');s=cells('experiments/TARGET950_20260914/candidate.ipynb');d=cells('experiments/SCORE_RECOVERY_20260915/division_remote_source.ipynb')
t=ast.parse(d[4]);module=next(ast.literal_eval(n.value) for n in t.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='DIVISION_SOURCE' for x in n.targets))
allowed={'point','pair_features','context','design','predict'}
pure='import numpy as np\nfrom scipy.special import expit\nSCALE = np.array([1.625,0.40625,0.40625])\n'
for n in ast.parse(module).body:
 if isinstance(n,ast.FunctionDef) and n.name in allowed:pure+='\n'+ast.get_source_segment(module,n)+'\n'
assert all(x not in pure for x in ['def fit','train_from_mount','minimize('])
(P/'saved_inference.py').write_text(pure)
old=next(ast.get_source_segment(f[5],n) for n in ast.parse(f[5]).body if isinstance(n,ast.FunctionDef) and n.name=='add_safe_divisions_postlink')
patched=patch_safe_div(old)
# Forge and Selector common postprocess must be identical before adding independent scorer.
assert f[5]==s[5]
post=f[5];assert post.count('write_test_submission("base")')==1;post=post.replace('write_test_submission("base")','')
# Only required setup, original postprocess, independent scorer, frozen inference module, replayer.
config=json.loads((P/'selection_rules.json').read_text())
bootstrap='TRAIN_DIR=COMP_DIR / "train"\nVALIDATOR_MATCH_RADIUS_UM=7.0\nVALIDATOR_NODE_COUNT_PENALTY_A=0.1\nVALIDATOR_DIVISION_WEIGHT=0.1\n'
constants='FIXED_STEMS='+repr(config['samples'])+'\nFROZEN_CONFIG='+repr(config['configuration'])+'\nEXPECTED_WEIGHT_SHA="0a1f9b93bb529e70f4f7c2ba0907eea8b4cecd2befccc8ba1fb75e569edf77a0"\nPATCHED_SAFE_DIV='+repr(patched)+'\n'
out=f[:4]+[post,bootstrap+s[8],pure,(P/'division_patch.py').read_text(),constants+(P/'replay.py').read_text()]
for code in out:ast.parse(code)
nb={'cells':[{'cell_type':'code','execution_count':None,'metadata':{},'outputs':[],'source':code} for code in out],'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}},'nbformat':4,'nbformat_minor':5}
(P/'diagnostic.ipynb').write_text(json.dumps(nb,ensure_ascii=False,indent=1)+'\n')
metadata=json.loads((R/'experiments/TARGET950_20260914/kernel-metadata.json').read_text());metadata.update(id='sailorren/biohub-sprint01-diagnostic-20260916',title='Biohub Sprint01 Diagnostic 20260916',code_file='diagnostic.ipynb',kernel_sources=['sailorren/biohub-division-train-20260914/1'])
(P/'kernel-metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
receipt={'source_sha256':hashlib.sha256((P/'diagnostic.ipynb').read_bytes()).hexdigest(),'cells':len(out),'training_functions_excluded':True,'original_inference_cells_excluded':[4,7],'cached_prediction_source':'Division V1','original_postprocess_sha256':hashlib.sha256(f[5].encode()).hexdigest(),'pure_function_names':sorted(allowed),'no_auto_pp_search':True}
(P/'build_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
