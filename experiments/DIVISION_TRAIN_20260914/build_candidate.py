"""Build the single trained division-gate candidate from fixed local source."""
import ast
import hashlib
import json
from pathlib import Path

P=Path(__file__).resolve().parent
ROOT=P.parents[1]
BASE=ROOT/'experiments/TARGET950_20260914/candidate.ipynb'
BASE_SHA='c38460def079f45749a8a3d85d6549dada0ec0343e2eed66bee3c7c40db4ae43'
sha=lambda b:hashlib.sha256(b).hexdigest()


def build():
    assert sha(BASE.read_bytes())==BASE_SHA
    nb=json.loads(BASE.read_text()); original=json.loads(BASE.read_text())
    code=''.join(nb['cells'][5]['source'])
    fn=next(x for x in ast.parse(code).body if isinstance(x,ast.FunctionDef) and x.name=='add_safe_divisions_postlink')
    old=ast.get_source_segment(code,fn);lines=old.splitlines(keepends=True)
    replacements=[]
    for node in ast.walk(ast.parse(old)):
        if not isinstance(node,ast.If):continue
        test=ast.unparse(node.test)
        if test in ('SAFE_DIV_REQUIRE_DIVERGENCE','SAFE_DIV_SISTER_SYMMETRY_TAU > 0.0') or test.startswith('SAFE_DIV_REQUIRE_MUTUAL_NN and'):
            replacements.append((node.lineno-1,node.end_lineno))
    assert len(replacements)==3
    for start,end in sorted(replacements,reverse=True):
        lines[start:end]=[]
    new=''.join(lines)
    anchor='                stats["safe_division_geometric_candidates"] += 1\n'
    gate='''                learned_score = DIVISION_MODULE.runtime_pair_score(
                    DIVISION_PAYLOAD, nodes_by_id, out_by_source, source_id,
                    existing_child_id, candidate_id, dataset,
                    Path(TEST_DIR).resolve() == (Path(COMP_DIR) / "train").resolve(),
                )
                stats["learned_division_context_checked"] = stats.get("learned_division_context_checked", 0) + 1
                if learned_score is None:
                    stats["learned_division_missing_context"] = stats.get("learned_division_missing_context", 0) + 1
                    continue
                stats["learned_division_scored"] = stats.get("learned_division_scored", 0) + 1
                if not math.isfinite(learned_score):
                    raise RuntimeError("NONFINITE_LEARNED_DIVISION_SCORE")
                if learned_score < DIVISION_MODULE.THRESHOLD:
                    stats["learned_division_rejected"] = stats.get("learned_division_rejected", 0) + 1
                    continue
                stats["learned_division_accepted"] = stats.get("learned_division_accepted", 0) + 1
'''
    assert new.count(anchor)==1
    new=new.replace(anchor,gate+anchor)
    assert new.count('score = parent_dist + 0.15 * sister_dist')==1
    new=new.replace('score = parent_dist + 0.15 * sister_dist','score = -learned_score + 1e-6 * (parent_dist + 0.15 * sister_dist)')
    nb['cells'][5]['source']=code.replace(old,new).splitlines(keepends=True)
    module=(P/'division_model.py').read_text()
    training='''# Train only from the labeled competition train mount before any test prediction.
import types as _division_types
import tracksdata as _division_td
DIVISION_MODULE = _division_types.ModuleType("biohub_trained_division")
exec(compile(DIVISION_SOURCE, "division_model.py", "exec"), DIVISION_MODULE.__dict__)
def _division_read_graph(path):
    graph = _division_td.graph.IndexedRXGraph.from_geff(path)
    return graph[0] if isinstance(graph, tuple) else graph
DIVISION_PAYLOAD, DIVISION_TRAINING_RECEIPT = DIVISION_MODULE.train_from_mount(
    COMP_DIR / "train", WORKING_DIR, _division_read_graph,
)
'''
    training='DIVISION_SOURCE = '+repr(module)+'\n'+training
    def cell(source):
        return {'cell_type':'code','execution_count':None,'metadata':{},'outputs':[],'source':source.splitlines(keepends=True)}
    nb['cells'].insert(4,cell(training))
    audit='''# Final run evidence: trained weights and the actual chosen postprocess.
_division_stats = pd.read_csv(RUN_STATS_PATH)
_division_totals = {k: int(_division_stats[k].fillna(0).sum()) for k in _division_stats.columns
                    if k.startswith("learned_division_") or k == "safe_divisions_added"}
if _division_totals.get("learned_division_scored", 0) <= 0:
    raise RuntimeError("TRAINED_GATE_NOT_INVOKED_ON_TEST_PREDICTIONS")
_division_audit = {
    "task_id": "DIVISION_TRAIN_20260914", "training_completed": True,
    "weights_sha256": DIVISION_MODULE.digest(WORKING_DIR / "division_gate_weights.json"),
    "training_receipt_sha256": DIVISION_MODULE.digest(WORKING_DIR / "division_training_receipt.json"),
    "module_sha256": __import__("hashlib").sha256(DIVISION_SOURCE.encode()).hexdigest(),
    "selected_label": selected_label, "selected_config": selected_config,
    "counts": _division_totals, "source_models_retrained": False,
    "formal_score": None, "score_read": False,
    "submission_sha256": DIVISION_MODULE.digest(SUBMISSION_PATH),
}
(WORKING_DIR / "division_runtime_audit.json").write_text(json.dumps(_division_audit, indent=2)+"\\n")
print("DIVISION_RUNTIME_AUDIT", json.dumps(_division_audit), flush=True)
'''
    nb['cells'].append(cell(audit))
    for c in nb['cells']:
        c['outputs']=[];c['execution_count']=None
        compile(''.join(c['source']),'candidate-cell','exec')
    for i,c in enumerate(original['cells']):
        if i==5:continue
        assert c['source']==nb['cells'][i+(i>=4)]['source']
    (P/'candidate.ipynb').write_text(json.dumps(nb,ensure_ascii=False,indent=1)+'\n')
    meta=json.loads((ROOT/'experiments/TARGET950_20260914/kernel-metadata.json').read_text())
    meta.update(id='sailorren/biohub-division-train-20260914',title='Biohub Division Train 20260914')
    (P/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    (P/'source_identity.json').write_text(json.dumps({'task_id':'DIVISION_TRAIN_20260914',
        'development_base_sha256':BASE_SHA,'own_reference':{'version':1,'script_version_id':348960877,'submission_id':56160258,'historical_public_score':'0.947','score_refreshed':False},
        'public_ancestor':'flexonafft/biohub-lineage-forge-precision-tracking','public_ancestor_script_version_id':348830165,
        'candidate_sha256':sha((P/'candidate.ipynb').read_bytes()),'module_sha256':sha(module.encode()),
        'changed_original_cells':[5],'added_cells':['training before detection','final runtime audit'],
        'unchanged_original_cells':[i for i in range(len(original['cells'])) if i!=5]},indent=2)+'\n')
    print('BUILD_OK',sha((P/'candidate.ipynb').read_bytes()))

if __name__=='__main__':build()
