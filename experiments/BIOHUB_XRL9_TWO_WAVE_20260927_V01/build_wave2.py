"""Build only frozen wave-2 configurations directly from scored R9D955 bytes."""
import ast,copy,difflib,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];OLD=R/'experiments/BIOHUB_XR0_LAST_TWO_20260926_V01'
base=json.loads((P/'R9D955/candidate.ipynb').read_text());assert len(base['cells'])==13
config={'R9D950':(.950,9.),'R8D955':(.955,8.)}
for arm,(det,relaxed) in config.items():
 d=P/arm;d.mkdir(exist_ok=True);nb=copy.deepcopy(base);s=[c['source'] for c in nb['cells']]
 if det!=.955:
  for i,a,b in [(0,'os.environ["BIOHUB_DET_THRESHOLD"] = "0.955"',f'os.environ["BIOHUB_DET_THRESHOLD"] = "{det:.3f}"'),(1,'"BIOHUB_DET_THRESHOLD": 0.955',f'"BIOHUB_DET_THRESHOLD": {det:.3f}')]:
   assert s[i].count(a)==1;s[i]=s[i].replace(a,b)
 if relaxed!=9.:
  a='os.environ["BIOHUB_MOTION_RELINK_RELAXED_UM"] = "9.0"';assert s[0].count(a)==1;s[0]=s[0].replace(a,f'os.environ["BIOHUB_MOTION_RELINK_RELAXED_UM"] = "{relaxed:.1f}"')
 s[12]=s[12].replace("_TRIO_ARM = 'R9D955'",f'_TRIO_ARM = {arm!r}').replace('DET_THRESHOLD == 0.955',f'DET_THRESHOLD == {det}').replace('MOTION_RELINK_RELAXED_UM == 9.0',f'MOTION_RELINK_RELAXED_UM == {relaxed}').replace('BIOHUB_XR0_LAST_TWO_20260926_V01','BIOHUB_XRL9_TWO_WAVE_20260927_V01').replace('last_two_receipt.json','two_wave_receipt.json')
 for i,c in enumerate(nb['cells']):ast.parse(s[i]);c.update(source=s[i],execution_count=None,outputs=[],id=f'two-wave-{i:02}')
 (d/'candidate.ipynb').write_text(json.dumps(nb,ensure_ascii=False,indent=1)+'\n')
 (d/'source.diff').write_text(''.join(''.join(difflib.unified_diff(base['cells'][i]['source'].splitlines(True),s[i].splitlines(True),fromfile=f'R9D955/cell{i+1}',tofile=f'{arm}/cell{i+1}')) for i in range(13)))
 m=json.loads((P/'R9D955/kernel-metadata.json').read_text());slug='biohub-xrl9-'+arm.lower()+'-20260927';m.update(id='sailorren/'+slug,title=slug);(d/'kernel-metadata.json').write_text(json.dumps(m,indent=2)+'\n')
 (d/'build_receipt.json').write_text(json.dumps({'arm':arm,'det':det,'relaxed':relaxed,'readmit':.965,'flow_relaxed':0.,'velocity':.5,'g1':False,'source_sha256':hashlib.sha256((d/'candidate.ipynb').read_bytes()).hexdigest(),'parent_source_sha256':hashlib.sha256((P/'R9D955/candidate.ipynb').read_bytes()).hexdigest(),'task_commit':'74ffadea8e7ac750a2bdb837207f3fa5a7aa48f5'},indent=2)+'\n')
 print('BUILT',arm)
