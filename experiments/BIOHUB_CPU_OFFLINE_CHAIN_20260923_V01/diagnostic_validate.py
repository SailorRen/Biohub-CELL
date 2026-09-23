"""Structural core extracted from frozen check_actual_csv.py; diagnostic scope only."""
import csv,hashlib,json,re
from collections import Counter
from pathlib import Path
from patch_support import invariant_graph

def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def validate(path,manifest):
 columns=['id','dataset','row_type','node_id','t','z','y','x','source_id','target_id'];groups={};rows=[]
 with Path(path).open(newline='') as f:
  rd=csv.DictReader(f);assert rd.fieldnames==columns
  for count,row in enumerate(rd):
   for k in columns:
    if k not in ['dataset','row_type']:assert re.fullmatch(r'-?\d+',row[k]);row[k]=int(row[k])
   assert row['id']==count;rows.append(row);ns,es=groups.setdefault(row['dataset'],({},[]))
   if row['row_type']=='node':
    assert row['node_id'] not in ns and min(row[k] for k in ['node_id','t','z','y','x'])>=0
    assert row['source_id']==row['target_id']==-1
    assert row['t'] in manifest['frames']
    assert all(row[k]<size for k,size in zip(['z','y','x'],manifest['raw_shape'][1:]))
    ns[row['node_id']]={k:row[k] for k in ['t','z','y','x']}
   else:
    assert row['row_type']=='edge' and all(row[k]==-1 for k in ['node_id','t','z','y','x'])
    es.append({k:row[k] for k in ['source_id','target_id']})
 assert set(groups)=={manifest['video']}
 ns,es=groups[manifest['video']];pairs=[(e['source_id'],e['target_id']) for e in es];assert len(set(pairs))==len(pairs)
 inc=Counter();out=Counter()
 for s,t in pairs:
  assert s in ns and t in ns and ns[t]['t']==ns[s]['t']+1;inc[t]+=1;out[s]+=1
 assert ns and max(inc.values(),default=0)<=1 and max(out.values(),default=0)<=2
 # Actual official reader and round-trip graph equality, with ID/order invariant digest.
 import polars as pl,tracksdata as td
 scope={'pl':pl,'td':td};exec((Path(__file__).parent/'source/official_reader.py').read_text(),scope)
 frame=pl.DataFrame(rows);g=scope['build_graph_from_rows'](frame.filter(pl.col('row_type')=='node'),frame.filter(pl.col('row_type')=='edge'))
 rn={int(r['node_id']):{k:r[k] for k in ['t','z','y','x']} for r in g.node_attrs().iter_rows(named=True)};rebuild=[{'source_id':int(r['source_id']),'target_id':int(r['target_id'])} for r in g.edge_attrs().iter_rows(named=True)]
 inv=digest(invariant_graph(ns,es));assert inv==digest(invariant_graph(rn,rebuild))
 return {'status':'DIAGNOSTIC_STRUCTURE_PASS','rows':len(rows),'nodes':len(ns),'edges':len(es),'id_independent_sha256':inv,'csv_sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),'official_reader_roundtrip':'PASS','scope':'fixed real short segment only','has_effect_and_archive_dedup':'NOT_APPLICABLE_DIAGNOSTIC'}
