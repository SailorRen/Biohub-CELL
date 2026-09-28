import ast,contextlib,copy,hashlib,io,json,os,shutil,tempfile,textwrap
from pathlib import Path
import nbformat,numpy as np
from scipy.spatial import cKDTree
P=Path(__file__).resolve().parent;R=P.parents[1];checks=[]
def ck(k,v):
 checks.append({'id':k,'pass':bool(v)});assert v,k
base=json.loads((R/'experiments/BIOHUB_XRL9_TWO_WAVE_20260927_V01/R9D955/candidate.ipynb').read_text());base=[c['source'] for c in base['cells'] if c['cell_type']=='code']
allcodes={}
for arm,ilp,readmit in [('DIV02_READMIT940',.2,.94),('DIV04_READMIT9525',.4,.9525)]:
 nb=nbformat.read(P/arm/'candidate.ipynb',as_version=4);nbformat.validate(nb);s=[c.source for c in nb.cells];allcodes[arm]=s
 ck(arm+'_13_code_cells',len(s)==13)
 for i,c in enumerate(s):ast.parse(c)
 ck(arm+'_unchanged_cells',all(s[i]==base[i] for i in range(12) if i not in [0,1,4,5]))
 for c in s:
  for n in ast.walk(ast.parse(c)):
   if isinstance(n,ast.Constant) and isinstance(n.value,str) and '\n' in n.value and ('def ' in n.value or 'import ' in n.value):
    try:ast.parse(textwrap.dedent(n.value))
    except SyntaxError: pass # partial patch strings are not standalone scripts
 oldenv=dict(os.environ)
 try:
  ns={'os':os};log=io.StringIO()
  with contextlib.redirect_stdout(log):
   exec(s[0],ns);exec(s[1],ns)
   keys=['ILP_DIVISION_WEIGHT','DET_THRESHOLD','MOTION_RELINK_VELOCITY_WEIGHT','MOTION_RELINK_FLOW_MODE','READMIT_MIN_SCORE','DEEPCENTER_SAFE_DIV_THRESHOLD','MOTION_RELINK_RELAXED_UM','MOTION_RELINK_FLOW_RELAXED_UM','MOTION_RELINK_TIGHT_UM','MOTION_RELINK_FLOW_TIGHT_UM','MOTION_RELINK_LEARNED_BONUS']
   nodes=[n for n in ast.parse(s[2]).body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in keys]
   exec(compile(ast.Module(body=nodes,type_ignores=[]),'params','exec'),ns)
   ck(arm+'_actual_config',[ns[k] for k in keys]==[ilp,.955,.5,'seed',readmit,.25,9.,0.,5.5,7.,1.])
   with tempfile.TemporaryDirectory() as td:
    repo=Path(td);(repo/'scripts').mkdir();original=R/'experiments/BIOHUB_XR0_XD960_SCORE_PAIR_20260925_V01/support_predict_original.py'
    ck(arm+'_support_original_hash',hashlib.sha256(original.read_bytes()).hexdigest()=='c44e771ba5980b820f93091e03a303c25dfe8f3232e501f54dc9565731c234b9')
    shutil.copyfile(original,repo/'scripts/predict_unet_transformer.py');ns.update(REPO_DIR=repo,WORKING_DIR=repo,Path=Path,json=json)
    c=s[4];first=c[c.index('_ps = REPO_DIR'):c.index('def list_test_stems()')];second=c[c.index('_cache_dir_env ='):c.index('start_time = time.time()')]
    a=second.index('_myhead =');b=second.index('_trial_source =');second=second[:a]+"os.environ['V1284_MODE']='candidate'\n"+second[b:]
    exec(first,ns);exec(second,ns)
    patched=(repo/'scripts/predict_unet_transformer.py').read_text();ast.parse(patched);ast.parse((repo/'scripts/v1284_coordinate_refinement.py').read_text())
    ck(arm+'_support_dynamic_patch',all(x in patched for x in ['EDGE_TTA_ACTIVE','SECONDARY_EDGE_TTA_ACTIVE','_LOWDET.append','_v1284_refine(ds_path','harmonic_prob = 1.0 / (','retention_guard_']))
    ck(arm+'_ilp_solver_consumption','division_weight=cfg.ilp_division_weight' in patched and 'FINAL_ILP_CONSUMED' in patched and 'ilp_division_weight: float' in patched)
    ck(arm+'_cache_before_head',patched.index('_LOWDET.append')<patched.index('arr = _v1284_refine'))
  ck(arm+'_no_patch_warning','WARNING' not in log.getvalue() and 'SKIPPED' not in log.getvalue())
  (P/arm/'dynamic_patch_check.log').write_text(log.getvalue())
 finally:os.environ.clear();os.environ.update(oldenv)


from build import make
for arm,ilp,readmit in [('DIV02_READMIT940',.2,.94),('DIV04_READMIT9525',.4,.9525)]:
 expected,meta=make(arm,ilp,readmit)
 actual=json.loads((P/arm/'candidate.ipynb').read_text())
 ck(arm+'_exact_allowed_diff',actual==expected)
 ck(arm+'_metadata',json.loads((P/arm/'kernel-metadata.json').read_text())==meta)
 s=allcodes[arm]
 ck(arm+'_readmit_chain',all(x in s[5] for x in ['peaks["score"] >= READMIT_MIN_SCORE','d <= READMIT_RADIUS_UM','d > GAPFILL_EXCLUDE_UM','anchors.setdefault(t + 1','anchors.setdefault(t - 1','readmit_discarded_detections(nodes_by_id, motion_edges']))
 ck(arm+'_ilp_command','"--ilp-division-weight",\n    str(ILP_DIVISION_WEIGHT)' in s[4])
(P/'wave2_build_checks.json').write_text(json.dumps({'passed':True,'count':len(checks),'checks':checks,'scope':'13 code cells AST, config consumption, allowlisted diff, actual support dynamic patch; no inference'},indent=2)+'\n')
print('PASS',len(checks))
