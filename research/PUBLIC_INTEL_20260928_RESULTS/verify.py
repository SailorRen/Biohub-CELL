"""Verify bounded collection identities and recorded exact official results, not author claims."""
from pathlib import Path
import json,hashlib,ast
P=Path(__file__).resolve().parent;R=P.parents[1];checks={}
def check(k,v):checks[k]=bool(v);assert v,k
def flatten(rows):
 for x in rows:yield x;yield from flatten(x.get('replies',[]))
manifest=json.loads((P/'github_file_manifest.json').read_text())
check('eight_fixed_github_repos',len({x['repo'] for x in manifest})==8)
check('twenty_one_fixed_files',len(manifest)==21)
for x in manifest:
 b=(P/x['local_path']).read_bytes();check('blob_'+x['repo']+'/'+x['path'],hashlib.sha256(b).hexdigest()==x['sha256'] and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==x['blob'])
 d=P/'github'/x['repo'].replace('/','__');check('commit_'+x['repo'],json.loads((d/'commit.json').read_text())['sha']==x['commit'])
check('catalog_three_hundred',all(len(json.loads((P/f'catalog_{s}.json').read_text()))==100 for s in ['scoreDescending','dateRun','dateCreated']))
check('github_three_queries',all('items' in json.loads((P/f'github_search_{i}.json').read_text()) for i in range(3)))
check('readonly_research',json.loads((P/'observation.json').read_text())['platform_writes']==0)
disc={}
for f in (P/'discussions').glob('*.json'):
 rows=list(flatten(json.loads(f.read_text())['messages']));check('unique_messages_'+f.stem,len(rows)==len({x['id'] for x in rows}));disc[f.stem]=len(rows)
check('six_discussions',len(disc)==6)
comp=json.loads((P/'sources/kunaldesale2408/biohub-cell-tracking/comparison.json').read_text());check('twelve_cells_equal',comp['all_nonempty_code_ast_equal'] and comp['code_cells']==12)
ids={'DIV04':(56626811,'0.956',353458610),'READMIT940':(56627073,'0.957',353461671),'DIV04_READMIT940':(56626891,'0.958',353458552)}
e=R/'experiments/BIOHUB_FINAL_ILP_READMIT_20260928_V01'
for arm,(sid,score,sv) in ids.items():
 r=json.loads((e/arm/'formal_last_observed.json').read_text());s=r['submission'];check('exact_score_'+arm,s['ref']==sid and s['status']=='COMPLETE' and s['publicScore']==score and r['sv']==sv and r['version']==1 and not s.get('errorDescription'))
old=R/'experiments/BIOHUB_XRL9_TWO_WAVE_20260927_V01/platform_ledger.json';check('old_ledger_unchanged',hashlib.sha256(old.read_bytes()).hexdigest()=='ebc9f1f0f7e8306d3d532fcf8e49bf8ec1291d788bde3cf515181bb474519bef')
coverage={'github_repos':8,'github_files':len(manifest),'discussion_messages':disc,'discussion_total_messages':sum(disc.values()),'unique_kernels':len({x['ref'] for s in ['scoreDescending','dateRun','dateCreated'] for x in json.loads((P/f'catalog_{s}.json').read_text())}),'scope':'bounded retrieval and integrity; not full third-party semantic review'}
(P/'coverage.json').write_text(json.dumps(coverage,indent=2)+'\n');(P/'verification.json').write_text(json.dumps({'passed':True,'checks':checks,'count':len(checks),'coverage':coverage},indent=2)+'\n');print('RESEARCH_CHECK_PASS',len(checks),coverage)
