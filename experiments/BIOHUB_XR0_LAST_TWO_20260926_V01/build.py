import ast,copy,difflib,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];T=R/'experiments/BIOHUB_XR0_TRANSFER_TRIO_20260926_V01'
baseline=json.loads((R/'experiments/BIOHUB_XR0_XD960_SCORE_PAIR_20260925_V01/XR0/candidate.ipynb').read_text())
base=[c['source'] for c in baseline['cells'] if c['cell_type']=='code'];assert len(base)==12
for arm,det,relaxed in [('XD960',.960,10.),('XRL9',.965,9.)]:
 d=P/arm;d.mkdir(exist_ok=True);s=base.copy()
 if arm=='XD960':
  for i,a,b in [(0,'os.environ["BIOHUB_DET_THRESHOLD"] = "0.965"','os.environ["BIOHUB_DET_THRESHOLD"] = "0.960"'),(1,'"BIOHUB_DET_THRESHOLD": 0.965','"BIOHUB_DET_THRESHOLD": 0.960')]:
   assert s[i].count(a)==1;s[i]=s[i].replace(a,b)
 else:s[0]+='\nos.environ["BIOHUB_MOTION_RELINK_RELAXED_UM"] = "9.0"\n'
 idx=s[4].index('_trial_source =')
 s[4]=s[4][:idx]+'''import hashlib as _last_hh
assert _myhead[0].stat().st_size == 33913, 'LAST_TWO_HEAD_SIZE'
assert _last_hh.sha256(_myhead[0].read_bytes()).hexdigest() == '625a0d9340f48193f2ec294fc2d81c5bb3c03087eab78ef0ae998a9c4c7da00c', 'LAST_TWO_HEAD_HASH'
print('LAST_TWO_HEAD_VERIFIED', str(_myhead[0]), flush=True)
'''+s[4][idx:]
 # Read-only counters at actual assignment call, preserving every original expression.
 a='                matches = assign_pass(pass_sources, pass_targets, gate_um, flow, flow_exclude_um)';assert s[5].count(a)==1
 s[5]=s[5].replace(a,'''                if pass_name == "relaxed":
                    _last_mode = "flow" if flow is not None else "no_flow"
                    stats["last_two_" + _last_mode + "_relaxed_calls"] = stats.get("last_two_" + _last_mode + "_relaxed_calls", 0) + 1
                    stats["last_two_" + _last_mode + "_relaxed_gate"] = gate_um
'''+a)
 fn=next(n for n in ast.parse(s[5]).body if isinstance(n,ast.FunctionDef) and n.name=='motion_relink_edges')
 lines=s[5].splitlines(True);lines[fn.body[0].lineno-1:fn.body[0].lineno-1]=['    stats["last_two_relaxed_config"] = MOTION_RELINK_RELAXED_UM\n','    stats["last_two_flow_relaxed_config"] = MOTION_RELINK_FLOW_RELAXED_UM\n','    stats.setdefault("last_two_flow_relaxed_calls", 0)\n','    stats.setdefault("last_two_no_flow_relaxed_calls", 0)\n'];s[5]=''.join(lines)
 end=(T/'runtime_receipt.py').read_text().replace('__ARM__',repr(arm)).replace('__VEL__','0.5').replace('__GATE__','False').replace('DET_THRESHOLD == 0.965',f'DET_THRESHOLD == {det}').replace('BIOHUB_XR0_TRANSFER_TRIO_20260926_V01','BIOHUB_XR0_LAST_TWO_20260926_V01').replace('trio_receipt.json','last_two_receipt.json')
 end=end.replace('_TRIO_ARM = '+repr(arm),'_TRIO_ARM = '+repr(arm)+f'\nassert MOTION_RELINK_RELAXED_UM == {relaxed} and MOTION_RELINK_FLOW_RELAXED_UM == 0\nassert MOTION_RELINK_LEARNED_BONUS == 1.0 and MOTION_RELINK_TIGHT_UM == 5.5 and MOTION_RELINK_FLOW_TIGHT_UM == 7.0')
 end=end.replace('velocity=MOTION_RELINK_VELOCITY_WEIGHT,','det=DET_THRESHOLD,relaxed=MOTION_RELINK_RELAXED_UM,flow_relaxed=MOTION_RELINK_FLOW_RELAXED_UM,velocity=MOTION_RELINK_VELOCITY_WEIGHT,')
 nb={'nbformat':4,'nbformat_minor':5,'metadata':copy.deepcopy(baseline['metadata']),'cells':[]}
 for i,code in enumerate(s+[end]):
  ast.parse(code);nb['cells'].append(dict(cell_type='code',source=code,metadata={},execution_count=None,outputs=[],id=f'last-two-{i:02}'))
 (d/'candidate.ipynb').write_text(json.dumps(nb,ensure_ascii=False,indent=1)+'\n')
 (d/'source.diff').write_text(''.join(''.join(difflib.unified_diff(base[i].splitlines(True),s[i].splitlines(True),fromfile=f'XR0/cell{i+1}',tofile=f'{arm}/cell{i+1}')) for i in range(12)))
 m=json.loads((T/'XV25/kernel-metadata.json').read_text());slug='biohub-xr0-'+arm.lower()+'-last-two-20260926';m.update(id='sailorren/'+slug,title=slug,kernel_sources=[]);(d/'kernel-metadata.json').write_text(json.dumps(m,indent=2)+'\n')
 (d/'build_receipt.json').write_text(json.dumps({'arm':arm,'det':det,'relaxed':relaxed,'velocity':.5,'g1':False,'source_sha256':hashlib.sha256((d/'candidate.ipynb').read_bytes()).hexdigest(),'algorithm_changes':['DET_THRESHOLD_AND_GUARD'] if arm=='XD960' else ['RELAXED_UM'],'runtime_additions':'head hash, read-only assignment counters and existing lightweight output checks'},indent=2)+'\n')
 print('BUILT',arm)
