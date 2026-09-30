"""Independent gate before local deletion: coverage, source preservation, safe archive, Git and official scores."""
import json,hashlib,subprocess,re
from pathlib import Path
from urllib.parse import unquote
P=Path(__file__).resolve().parent;R=P.parents[1]
h=lambda b:hashlib.sha256(b).hexdigest()
d=json.loads((P/'local_inventory.json').read_text());assert len(d['files'])==d['summary']['files'];assert not d['summary']['sensitive_filename_hits']
tracked=set(subprocess.check_output(['git','ls-files','-z'],cwd=R).decode().split('\0'))
archived=0
for x in d['files']:
 assert x['disposition'].startswith(('ARCHIVED_','EXCLUDED_'))
 if 'archive_path' not in x:continue
 p=R/x['archive_path'];assert p.is_file() and h(p.read_bytes())==x['archive_sha256'],x['path'];assert x['archive_path'] in tracked,x['archive_path'];archived+=1
 if x['disposition']=='ARCHIVED_EXACT':assert x['sha256']==x['archive_sha256']
 else:
  original=Path(d['summary']['roots'][x['root']])/x['path']
  if original.exists():
   a=json.loads(original.read_text());b=json.loads(p.read_text());assert [(z['cell_type'],z['source']) for z in a['cells']]==[(z['cell_type'],z['source']) for z in b['cells']]
report=R/'reports/20260930_Biohub比赛总报告与归档索引.md';s=report.read_text()
for target in re.findall(r'\]\(([^)]+)\)',s):
 if target.startswith(('https:','http:','#')):continue
 assert (report.parent/unquote(target.split('#')[0])).exists(),target
for p in (R/'archive/20260930_local_recovery').rglob('*'):
 if p.is_file():
  if p.suffix=='.csv':assert p.name in {'deleted_edge_attribution.csv','ppsweep_results.csv','validator_results.csv','run_stats.csv'} and p.stat().st_size<1000000
  assert p.suffix not in ['.npy','.npz','.pth','.pt','.bin','.zip','.whl','.so','.dylib','.pyc']
  assert not any(x in p.parts for x in ['s02_cache','replay_cache','sprint_cache','venv','site-packages'])
for x in json.loads((R/'experiments/BIOHUB_LAST_DAY_FIVE_20260929_V01/验收合同.json').read_text())['acceptance']:
 if x['type']=='file':assert h((R/x['path']).read_bytes())==x['sha256']
for name in ['private_leaderboard.json','public_leaderboard.json']:
 b=json.loads((P/name).read_text());assert b['complete'];assert len({x['teamId'] for x in b['rows']})==len(b['rows']);assert len([x for x in b['rows'] if x['teamId']==16578232])==1
subprocess.run(['/opt/anaconda3/envs/ml/bin/python',str(P/'read_private.py')],check=True,cwd=R)
print('ARCHIVE_COVERAGE_PASS',len(d['files']),archived)
