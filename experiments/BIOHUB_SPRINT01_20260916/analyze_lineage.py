"""Summarize actual inherited split manifests without claiming full pipeline independence."""
import json
from pathlib import Path
P=Path(__file__).resolve().parent
m=json.loads((P/'output_v1/upstream_split_manifests.json').read_text());stems=json.loads((P/'selection_rules.json').read_text())['samples'];rows=[]
def occurrences(value,stem,path=()):
 if isinstance(value,dict):return [p for k,v in value.items() for p in occurrences(v,stem,(*path,str(k)))]
 if isinstance(value,list):return [p for i,v in enumerate(value) for p in occurrences(v,stem,(*path,str(i)))]
 if isinstance(value,str) and stem in value:return ['/'.join(path)]
 return []
for f in m:
 rows.append({'path':f['path'],'sha256':f['sha256'],'top_level_keys':list(f['metadata']) if isinstance(f['metadata'],dict) else None,'sample_occurrences':{s:occurrences(f['metadata'],s) for s in stems}})
(P/'lineage_summary.json').write_text(json.dumps({'scope':'Actual mounted split-manifest contents; matching occurrence is not independently proof of every model training history','manifests':rows,'full_pipeline_independent_validation':False,'classifier_models':'Explicit held_out[44b6] / held_out[6bba]; runtime asserts embryo excluded from training_embryos; final never used for this diagnostic'},ensure_ascii=False,indent=2)+'\n')
print(json.dumps(rows,ensure_ascii=False))
