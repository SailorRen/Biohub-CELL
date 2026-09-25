"""Bounded checks of all cells and actual support-source rewriting. Never run models."""
import ast,contextlib,hashlib,io,json,os,shutil,tempfile,textwrap
from pathlib import Path
import nbformat
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
orig=json.loads((ROOT/'research/PUBLIC_0950_20260924/sources/x138/biohub-x138.ipynb').read_text());texts=[''.join(c['source']) for c in orig['cells'] if c['cell_type']=='code' and ''.join(c['source']).strip()]
actual=P/'support_predict_original.py'
checks=[]
def check(k,v):
 checks.append({'id':k,'pass':bool(v)});assert v,k
check('actual_support_sha256',hashlib.sha256(actual.read_bytes()).hexdigest()=='c44e771ba5980b820f93091e03a303c25dfe8f3232e501f54dc9565731c234b9')
embedded=[]
for ci,s in enumerate(texts):
 for n in ast.walk(ast.parse(s)):
  if isinstance(n,ast.Constant) and isinstance(n.value,str) and '\n' in n.value and ('def ' in n.value or 'import ' in n.value):
   try:ast.parse(textwrap.dedent(n.value))
   except SyntaxError:continue
   embedded.append({'cell':ci+1,'line':n.lineno,'sha256':hashlib.sha256(n.value.encode()).hexdigest()})
for arm,threshold in [('XR0',.965),('XD960',.960)]:
 nb=nbformat.read(P/arm/'candidate.ipynb',as_version=4);nbformat.validate(nb);s=[c.source for c in nb.cells if c.cell_type=='code'];check(arm+'_12_cells',len(s)==12)
 for i,c in enumerate(s):ast.parse(c);check(arm+f'_cell_{i+1}_ast',True)
 expected=texts.copy()
 if arm=='XD960':expected[0]=expected[0].replace('os.environ["BIOHUB_DET_THRESHOLD"] = "0.965"','os.environ["BIOHUB_DET_THRESHOLD"] = "0.960"',1);expected[1]=expected[1].replace('"BIOHUB_DET_THRESHOLD": 0.965,','"BIOHUB_DET_THRESHOLD": 0.960,',1)
 check(arm+'_exact_allowed_code_diff',s==expected)
 check(arm+'_no_outputs',all(not c.get('outputs') and c.get('execution_count') is None for c in nb.cells))
 env_before=dict(os.environ)
 try:
  for k in list(os.environ):
   if k.startswith('BIOHUB_') or k.startswith('V1284_'):del os.environ[k]
  ns={'os':os};log=io.StringIO()
  with contextlib.redirect_stdout(log):
   exec(compile(s[0],'<cell1>','exec'),ns);exec(compile(s[1],'<cell2>','exec'),ns)
   selected=[n for n in ast.parse(s[2]).body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ['DET_THRESHOLD','MOTION_RELINK_VELOCITY_WEIGHT','MOTION_RELINK_FLOW_MODE','READMIT_MIN_SCORE','DEEPCENTER_SAFE_DIV_THRESHOLD']]
   exec(compile(ast.Module(body=selected,type_ignores=[]),'<parameter-consumption>','exec'),ns)
   check(arm+'_effective_parameters',ns['DET_THRESHOLD']==threshold and ns['MOTION_RELINK_VELOCITY_WEIGHT']==.5 and ns['MOTION_RELINK_FLOW_MODE']=='seed' and ns['READMIT_MIN_SCORE']==.965 and ns['DEEPCENTER_SAFE_DIV_THRESHOLD']==.25 and os.environ['BIOHUB_VALIDATOR_ENABLE']=='0')
   with tempfile.TemporaryDirectory(prefix='x138-patch-check-') as temp:
    repo=Path(temp);(repo/'scripts').mkdir();shutil.copyfile(actual,repo/'scripts/predict_unet_transformer.py');ns.update(REPO_DIR=repo,WORKING_DIR=repo,Path=Path,json=json)
    c=s[4];first=c[c.index('_ps = REPO_DIR'):c.index('def list_test_stems()')];second=c[c.index('_cache_dir_env ='):c.index('start_time = time.time()')]
    # Exclude only head-mount resolution: no model/weights loaded in source rewriting test.
    a=second.index('_myhead =');b=second.index('_trial_source =');second=second[:a]+"os.environ['V1284_MODE']='candidate'\n"+second[b:]
    exec(compile(first,'<actual-source-patches>','exec'),ns);exec(compile(second,'<actual-cache-then-head>','exec'),ns)
    patched=(repo/'scripts/predict_unet_transformer.py').read_text();ast.parse(patched);ast.parse((repo/'scripts/v1284_coordinate_refinement.py').read_text())
    check(arm+'_dynamic_patches_actual_support',all(x in patched for x in ['EDGE_TTA_ACTIVE','SECONDARY_EDGE_TTA_ACTIVE','_LOWDET.append','_v1284_refine(ds_path','harmonic_prob = 1.0 / (','retention_guard_']))
    check(arm+'_cache_before_head',patched.index('_LOWDET.append')<patched.index('arr = _v1284_refine'))
    check(arm+'_threshold_real_cli_path','"--det-threshold",\n    str(DET_THRESHOLD)' in c and 'det_threshold=args.det_threshold' in patched)
    (P/arm/'patched_source.sha256').write_text(hashlib.sha256(patched.encode()).hexdigest()+'\n')
  (P/arm/'source_patch_check.log').write_text(log.getvalue());check(arm+'_patch_no_skip_warning','WARNING' not in log.getvalue() and 'SKIPPED' not in log.getvalue())
 finally:os.environ.clear();os.environ.update(env_before)
(P/'checks.json').write_text(json.dumps({'status':'PASS','count':len(checks),'checks':checks,'embedded_complete_python_strings':embedded,'scope':'All-cell syntax and exact diff, config ordering/consumption, actual original support prediction source dynamic patch application and compiled result. No GPU/model execution, offline package compatibility, head load or actual CSV validation. Those remain required in teammate full GPU run.','model_runs':0},indent=2)+'\n')
print('PASS',len(checks),'checks;',len(embedded),'embedded complete Python strings')
