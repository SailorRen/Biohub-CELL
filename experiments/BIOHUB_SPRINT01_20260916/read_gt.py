"""Read downloaded GEFF arrays with original IndexedRXGraph ordering.
Missing structural groups are generated in a temporary copy only; source bytes stay intact.
"""
import json,shutil,tempfile
from pathlib import Path
import tracksdata as td
ROOT=Path(__file__).resolve().parents[2]
def read_gt(stem):
 src=ROOT/'downloads/BIOHUB_SPRINT01_20260916/gt'/(stem+'.geff')
 with tempfile.TemporaryDirectory(prefix='biohub-sprint-gt-') as tmp:
  d=Path(tmp)/src.name;shutil.copytree(src,d)
  for name in ['nodes','edges','nodes/props',*['nodes/props/'+k for k in ['t','z','y','x']]]:
   (d/name/'zarr.json').write_text(json.dumps({'zarr_format':3,'node_type':'group','attributes':{}}))
  graph=td.graph.IndexedRXGraph.from_geff(d)[0]
  nodes={int(r['node_id']):(int(r['t']),float(r['z']),float(r['y']),float(r['x'])) for r in graph.node_attrs().iter_rows(named=True)}
  edges=[(int(r['source_id']),int(r['target_id'])) for r in graph.edge_attrs().iter_rows(named=True)]
 return nodes,edges
if __name__=='__main__':
 import hashlib
 P=Path(__file__).resolve().parent;old=json.loads((ROOT/'downloads/DIVISION_DIAG_20260915/platform/official_selector_audit.json').read_text());out=[]
 for stem in json.loads((P/'selection_rules.json').read_text())['samples']:
  n,e=read_gt(stem);v={'nodes':[[i,*vs] for i,vs in n.items()],'edges':e};h=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest();expected={r['input_gt_graph_sha256'] for r in old['per_sample_same_graph_metrics'] if r['stem']==stem};out.append({'sample':stem,'nodes':len(n),'edges':len(e),'hash':h,'historical_hash_match':h in expected})
 (P/'gt_reader_integrity.json').write_text(json.dumps({'scope':'Original IndexedRXGraph reader ordering, compared with historical exact-version GT input hashes; raw array order was different and is not used','rows':out},indent=2)+'\n');assert all(r['historical_hash_match'] for r in out);print('GT_ORDERED_HASH_PASS',len(out))
