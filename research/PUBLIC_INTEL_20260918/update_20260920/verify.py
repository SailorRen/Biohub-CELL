"""Verify delivered coverage, immutable source bytes, counts and no-write ledger; not scientific truth."""
import json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
load=lambda n:json.loads((P/n).read_text())
s=load('源码阅读覆盖.json')['sources'];assert len(s)==3
assert {(x['version'],x['script_version_id']) for x in s}=={(8,351100540),(7,351100632),(1,351098581)}
for x in s:
 p=P/x['source_path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256']
 assert (p.parent/'LICENSE-Apache-2.0.txt').stat().st_size>10000
 assert x['public_score'] is None and x['dependencies']=='PARTIAL_DEPENDENCIES'
 if p.suffix=='.ipynb':assert len(json.loads(p.read_text())['cells'])==x['cells_read']==8
 else:assert len(p.read_text().splitlines())==x['source_lines']
d=load('讨论阅读覆盖.json');assert len(d['topics'])==4 and d['total_messages']==16 and d['total_replies']==12
assert sum(len(x['messages']) for x in d['topics'])==16
assert len({m['message_id'] for x in d['topics'] for m in x['messages']})==16
g=load('GitHub阅读覆盖.json');assert len(g['repositories'])==3 and sum(len(x['files']) for x in g['repositories'])==10
l=load('操作账本.json');assert all(l[k]==0 for k in ['training','inference','save_and_run','formal_submission','dataset_write','experiment_start'])
assert l['research_status']=='PARTIAL_RESEARCH_BLOCKED'
m=load('公开权重训练覆盖核查.json');assert m['train_unique']==199 and m['test_unique']==m['intersection']==40
for name in ['最新公开情报.md','交给Chat.md']:assert 'PARTIAL_RESEARCH_BLOCKED' in (P/name).read_text()
print('PASS: delivery scope, hashes, exact-version IDs, coverage counts and zero-write ledger; research gaps remain.')
