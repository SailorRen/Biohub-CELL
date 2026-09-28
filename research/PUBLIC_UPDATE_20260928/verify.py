"""Check bounded read-only report evidence, without executing downloaded source."""
import ast,hashlib,json
from pathlib import Path
from IPython.core.inputtransformer2 import TransformerManager
P=Path(__file__).resolve().parent
R=P.parents[1]
def read(f):return json.loads(f.read_text())
contract=read(R/'tasks/CODEX_20260928_PUBLIC_UPDATE_ACCEPTANCE.json')
checks={};req=contract['required'];subs=list(P.glob('submission_*.json'))
checks['eleven_exact_complete_scores']=len(subs)==req['submissions'] and all(read(f)['status']=='COMPLETE' and read(f).get('publicScore') and str(read(f)['ref']) in f.stem for f in subs)
checks['two_wave2_scores']=read(P/'submission_56615584.json')['publicScore']=='0.955' and read(P/'submission_56615617.json')['publicScore']=='0.956'
cats=list(P.glob('catalog_*.json'));refs={x['ref'] for f in cats for x in read(f)}
checks['catalog_coverage']=len(cats)==3 and all(len(read(f))==100 for f in cats) and len(refs)==162
checks['discussion_coverage']=len(list(P.glob('topics_*.json')))==2 and len(list((P/'discussions').glob('*.json')))>=req['discussion_bodies']
c=read(P/'coverage.json');tm=TransformerManager();n=0
for f in (P/'sources').rglob('source.ipynb'):
 for cell in read(f)['cells']:
  if cell['cell_type']=='code':ast.parse(tm.transform_cell(''.join(cell['source'])));n+=1
checks['notebook_static_syntax']=n==90
checks['four_sources_unchanged']=sum(x['same_as_previous'] for x in c['sources'])==4
lb=read(P/'leaderboard.json')['submissions'];checks['team_rank']=lb[188]['teamName']=='Sailor Ren' and lb[188]['score']=='0.956'
checks['author_team_rank']=lb[102]['teamName']=='John Taylor (AI)' and lb[102]['score']=='0.959'
report=(R/'reports/20260928_BIOHUB_PUBLIC_UPDATE_AND_RESULTS.md').read_text()
checks['all_ids_in_report']=all(str(read(f)['ref']) in report for f in subs)
checks['limitations_and_sources']=all(s in report for s in ['AUTHOR_CLAIM','INFERENCE','UNKNOWN','353423030','0.882','743929','不标记 FULL_NOTEBOOK_SOURCE_REVIEWED'])
checks['no_forbidden_artifacts']=not any(f.suffix in ['.csv','.pt','.pth','.geff'] for f in P.rglob('*') if f.is_file())
result={'checks':checks,'passed':all(checks.values()),'status':'LOCAL_EVIDENCE_CHECKED','semantic_review':'manual; author claims not independently reproduced','remote_readback':'separate delivery receipt','contract_sha256':hashlib.sha256((R/'tasks/CODEX_20260928_PUBLIC_UPDATE_ACCEPTANCE.json').read_bytes()).hexdigest()}
(P/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False));assert all(checks.values())
