"""Bounded research artifact checks; does not certify external performance claims."""
import hashlib, json
from pathlib import Path
P = Path(__file__).resolve().parent
R = P.parents[1]
def read(name):
    return json.loads((P / name).read_text())
notebooks = read('notebook_sources.json')
assert len(notebooks) >= 2
for n in notebooks:
    assert n['script_version_id'] and n['version'] and n['read_ranges']
    assert n['full_notebook_review'] is False and n['executed'] is False
    assert hashlib.sha256((R/n['path']).read_bytes()).hexdigest() == n['source_sha256']
discussions = read('discussions.json')
assert len({d['id'] for d in discussions}) >= 4
assert all(d['coverage'] and d['url'] and d['evidence_class']=='AUTHOR_CLAIM' for d in discussions)
gh = read('github_sources.json')
assert len({g['repo'] for g in gh}) >= 3
raw = json.loads((R/'downloads/PUBLIC_OPT_REVIEW_20260917/github_sources.json').read_text())
for a,b in zip(gh,raw,strict=True):
    assert a['commit']==b['commit'] and len(a['commit'])==40
    assert a['sha256']==hashlib.sha256(b['content'].encode()).hexdigest()
obs = read('platform_observations.json')
assert all(v==0 for v in obs['writes'].values())
receipt = json.loads((R/'experiments/BIOHUB_SPRINT01_20260916/formal_terminal_crosscheck.json').read_text())
assert receipt['submission_id']==56270217 and receipt['public_score']=='0.948' and receipt['status']=='COMPLETE'
g1=(R/'reports/20260916_BIOHUB_SPRINT01_RESULTS.md').read_text()
assert '分数歧义已解决' in g1
for file in ['20260917_公开方案与G1对照.md','20260917_交给Chat的Biohub分析材料.md']:
    text=(R/'reports'/file).read_text()
    for term in ['0.948','350197436','UNKNOWN','NOT_RUN']:
        assert term in text, (file,term)
print(json.dumps({'status':'PASS','notebooks':len(notebooks),'discussions':len(discussions),
                  'github_repositories':len({g['repo'] for g in gh}),'github_files':len(gh),
                  'scope':'artifact integrity and scope only; external methods not rerun'},ensure_ascii=False))
