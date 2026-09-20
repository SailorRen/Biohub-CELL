"""Append-only production audit. Original G1 cells and selector execute first.
No training, network access, submission or platform mutation in this module.
"""
import copy
import csv
import hashlib
import json
import math
import os
from collections import Counter
from pathlib import Path

KEY = 'DEEPCENTER_SAFE_DIV_THRESHOLD'
FIXED_STEMS = ['44b6_12dfb391','44b6_267148e4','44b6_2a2eff9f','44b6_341df25f',
               '6bba_062c8d37','6bba_07e24132','6bba_085bf656','6bba_09961292']
COLUMNS = ['id','dataset','row_type','node_id','t','z','y','x','source_id','target_id']

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,allow_nan=False,separators=(',',':')).encode()).hexdigest()

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def clean(value):
    if isinstance(value,float) and not math.isfinite(value): return None
    if isinstance(value,dict): return {str(k):clean(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)): return [clean(v) for v in value]
    return value

def save(path,value):
    path=Path(path); tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(clean(value),ensure_ascii=False,allow_nan=False,indent=2)+'\n')
    os.replace(tmp,path)

def append(path,value):
    with Path(path).open('a') as f:
        f.write(json.dumps(clean(value),ensure_ascii=False,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())

def resolved_config(base,selected,threshold):
    result=copy.deepcopy(base);result.update(copy.deepcopy(selected))
    assert result[KEY]==0.20,'G1_THRESHOLD_NOT_020'
    baseline=copy.deepcopy(result);result[KEY]=threshold
    assert {k for k in result if result[k]!=baseline[k]} <= {KEY}
    return baseline,result

def graph_content(nodes,edges,serialized=False):
    ns=[]
    for i,n in sorted(nodes.items()):
        xyz=[float(max(0,int(round(float(n[k]))))) if serialized else float(n[k]) for k in ['z','y','x']]
        ns.append([int(i),int(n['t']),*xyz])
    es=sorted([int(e['source_id']),int(e['target_id'])] for e in edges)
    return [ns,es]

def csv_contents(path,expected):
    groups={};rowids=[]
    with Path(path).open(newline='') as f:
        rd=csv.DictReader(f);assert rd.fieldnames==COLUMNS,'CSV_SCHEMA'
        for row in rd:
            for k in COLUMNS:
                if k not in ['dataset','row_type']:row[k]=int(row[k])
            rowids.append(row['id']);g=groups.setdefault(row['dataset'],[{},[]])
            if row['row_type']=='node':
                assert row['node_id'] not in g[0],'DUPLICATE_NODE'
                assert min(row[k] for k in ['node_id','t','z','y','x'])>=0
                assert row['source_id']==row['target_id']==-1
                g[0][row['node_id']]={k:row[k] for k in ['t','z','y','x']}
            else:
                assert row['row_type']=='edge','ROW_TYPE'
                assert all(row[k]==-1 for k in ['node_id','t','z','y','x'])
                g[1].append({k:row[k] for k in ['source_id','target_id']})
    assert rowids==list(range(len(rowids))),'ROW_IDS'
    assert set(groups)==set(expected),'SAMPLE_COVERAGE'
    result={}
    for stem,(nodes,edges) in groups.items():
        assert nodes,'EMPTY_NODES'
        pairs=[(e['source_id'],e['target_id']) for e in edges]
        assert len(set(pairs))==len(pairs),'DUPLICATE_EDGE'
        inc=Counter();out=Counter()
        for s,t in pairs:
            assert s in nodes and t in nodes,'ENDPOINT'
            assert nodes[t]['t']==nodes[s]['t']+1,'TIME_DIRECTION'
            inc[t]+=1;out[s]+=1
        assert max(inc.values(),default=0)<=1 and max(out.values(),default=0)<=2,'DEGREE'
        result[stem]={'content':graph_content(nodes,edges),'nodes':len(nodes),'edges':len(edges),
                      'divisions':sum(v==2 for v in out.values()),'canonical_sha256':digest(graph_content(nodes,edges))}
    return result

def diff_contents(base,candidate):
    assert set(base)==set(candidate)
    rows=[]
    for stem in sorted(base):
        b=base[stem];c=candidate[stem];be=set(map(tuple,b['content'][1]));ce=set(map(tuple,c['content'][1]))
        rows.append({'stem':stem,'g1_hash':b['canonical_sha256'],'candidate_hash':c['canonical_sha256'],
                     'nodes_delta':c['nodes']-b['nodes'],'edges_added':len(ce-be),'edges_removed':len(be-ce),
                     'division_delta':c['divisions']-b['divisions'],'changed':b['content']!=c['content']})
    return rows

def count_totals(rows):
    keys=['edge_tp','edge_fp','edge_fn','division_tp','division_fp','division_fn']
    for r in rows:
        for k in keys:
            assert k in r and r[k] is not None and math.isfinite(r[k]),f'MISSING_METRIC_{k}'
    return {k:sum(r[k] for r in rows) for k in keys}

def file_manifest(root):
    return {str(p.relative_to(root)):sha(p) for p in sorted(Path(root).rglob('*')) if p.is_file()}

def official_modules(sources,hashes):
    import sys,types,polars as pl,tracksdata as td
    for name,s in sources.items():assert hashlib.sha256(s.encode()).hexdigest()==hashes[name]
    pkg=types.ModuleType('_divgate_official');pkg.__path__=[];sys.modules[pkg.__name__]=pkg
    for name in ['division_metrics','metrics']:
        m=types.ModuleType('_divgate_official.'+name);m.__package__='_divgate_official'
        sys.modules[m.__name__]=m;exec(compile(sources[name],name+'.py','exec'),m.__dict__);setattr(pkg,name,m)
    scope={'pl':pl,'td':td};exec(compile(sources['build_graph_from_rows'],'official_csv_reader.py','exec'),scope)
    return pkg.metrics,scope['build_graph_from_rows']

def official_roundtrip(path,expected,build):
    import polars as pl
    df=pl.read_csv(path);graphs={};content=csv_contents(path,expected)
    for stem in sorted(expected):
        group=df.filter(pl.col('dataset')==stem);ns=group.filter(pl.col('row_type')=='node');es=group.filter(pl.col('row_type')=='edge')
        graph=build(ns,es)
        ids=list(graph.node_ids());back=dict(zip(ids,ns['node_id'].to_list(),strict=True))
        nodes={back[int(r['node_id'])]:{k:float(r[k]) if k!='t' else int(r[k]) for k in ['t','z','y','x']} for r in graph.node_attrs().iter_rows(named=True)}
        edges=[{'source_id':back[int(r['source_id'])],'target_id':back[int(r['target_id'])]} for r in graph.edge_attrs().iter_rows(named=True)] if graph.num_edges() else []
        assert graph_content(nodes,edges)==content[stem]['content'],'OFFICIAL_ROUNDTRIP_MISMATCH'
        graphs[stem]=graph
    return graphs

def run(g,arm,threshold,sources,hashes):
    assert (arm,threshold) in [('A18',0.18),('B22',0.22)]
    root=g['WORKING_DIR']/'divgate_pair';root.mkdir(exist_ok=True)
    baseline_cfg,candidate_cfg=resolved_config(g['PP_BASE_CONFIG'],g['selected_config'],threshold)
    assert g['SPRINT_ARM']=='G1' and g['_SPRINT_WEIGHT_SHA']=='0a1f9b93bb529e70f4f7c2ba0907eea8b4cecd2befccc8ba1fb75e569edf77a0'
    assert g['DEEPCENTER_VETO_DETECTOR'] is not None
    assert sha(g['DEEPCENTER_VETO_DETECTOR']['path'])==g['_deepcenter_expected_sha256']
    assert not g['ALLOW_ARTIFACT_FALLBACK']
    final_path=g['SUBMISSION_PATH'];original=final_path.read_bytes();(root/'g1_original.csv').write_bytes(original)
    original_content=csv_contents(final_path,g['test_stems'])
    selection={'selected_label':g['selected_label'],'selected_config':copy.deepcopy(g['selected_config']),
               'g1_config':baseline_cfg,'candidate_config':candidate_cfg,
               'resolved_scalars':{k:v for k,v in g.items() if k.isupper() and isinstance(v,(str,int,float,bool))},
               'biohub_environment':{k:v for k,v in os.environ.items() if k.startswith('BIOHUB_')},'g1_csv_sha256':sha(final_path)}
    save(root/'selection.json',selection)
    raw_before=file_manifest(g['REPO_DIR']/'predictions')
    original_filter=g['filter_output_graph'];calls=[]
    def audited_filter(nodes,edges,**kw):
        raw=digest([nodes,edges]); nc=copy.deepcopy(nodes);ec=copy.deepcopy(edges)
        result=original_filter(nc,ec,**kw)
        assert digest([nodes,edges])==raw,'RAW_GRAPH_MUTATED'
        content=graph_content(result[0],result[1],serialized=True)
        stat=result[2]
        assert not stat['deepcenter_safe_div_missing'],'DEEPCENTER_MISSING'
        row={'stem':kw['dataset'],'threshold':g[KEY],'input_hash':raw,'final_hash':digest(content),
             'config':{k:g[k] for k in baseline_cfg},'stats':stat,'raw_input_unchanged':True}
        calls.append(row);append(root/'postprocess_calls.jsonl',row)
        return result
    g['filter_output_graph']=audited_filter
    def write(config,path,tag):
        saved=g['pp_apply'](config);old_path=g['SUBMISSION_PATH'];old_stats=g['RUN_STATS_PATH']
        g['SUBMISSION_PATH']=path;g['RUN_STATS_PATH']=root/(tag+'_run_stats.csv');start=len(calls)
        try:g['write_test_submission'](tag)
        finally:g['SUBMISSION_PATH']=old_path;g['RUN_STATS_PATH']=old_stats;g['pp_restore'](saved)
        parsed=csv_contents(path,g['test_stems']);current=calls[start:]
        assert len(current)==len(parsed)
        for row in current:assert row['final_hash']==parsed[row['stem']]['canonical_sha256'],'WRITER_CONTENT_MISMATCH'
        return parsed
    # Reconstruct baseline first, then candidate. Every invocation reads raw GEFF again.
    reproduced=write(baseline_cfg,root/'g1_reproduced.csv','g1_reproduced')
    assert all(reproduced[s]['content']==original_content[s]['content'] for s in original_content),'G1_020_NOT_EQUIVALENT'
    candidate=write(candidate_cfg,final_path,arm)
    assert raw_before==file_manifest(g['REPO_DIR']/'predictions'),'RAW_FILES_MUTATED'
    metrics,build=official_modules(sources,hashes)
    official_roundtrip(final_path,g['test_stems'],build)
    changes=diff_contents(original_content,candidate)
    import importlib.metadata as im, tracksdata as td
    deps={name:im.version(name) for name in ['tracksdata','polars','numpy','scipy','geff','zarr','torch']}
    td_root=Path(td.__file__).parent
    dep_hashes={str(p.relative_to(td_root)):sha(p) for p in sorted(td_root.rglob('*.py'))}
    receipt={'arm':arm,'threshold':threshold,'engineering_status':'PASS','g1_off_equivalent':True,
             'raw_inputs_unchanged':True,'original_selector_unchanged':True,'training_calls':0,
             'g1_csv_sha256':hashlib.sha256(original).hexdigest(),'final_csv_sha256':sha(final_path),
             'final_canonical_sha256':digest({s:r['canonical_sha256'] for s,r in candidate.items()}),
             'final_graphs':{s:{k:v for k,v in r.items() if k!='content'} for s,r in candidate.items()},
             'changes':changes,'has_effect':any(r['changed'] for r in changes),'csv_roundtrip':'PASS',
             'selection':selection,'official_source_hashes':hashes,'dependency_versions':deps,
             'tracksdata_python_hashes':dep_hashes,'raw_manifest_sha256':digest(raw_before),
             'weights':g['_runtime_integrity_receipt']['checkpoint_sha256'],
             'gate_weight_sha256':g['_SPRINT_WEIGHT_SHA'],'public':None}
    save(root/'production_receipt.json',receipt)
    # Auxiliary scoring never supplies the production file or selector.
    diag={'status':'NOT_RUN','gaps':[],'rows':0,'coverage':{'primary':'COVERAGE_UNKNOWN','deepcenter':'COVERAGE_UNKNOWN','secondary':'COVERAGE_UNKNOWN','gate':'held_out_embryo; upstream unseen not established'}}
    old_dir=g['TEST_DIR'];old_stems=g['test_stems'];old_method=g['METHOD']
    diag_phase='cache'
    try:
        assert set(g.get('VAL_RAW_GRAPHS',{}))==set(FIXED_STEMS),'FIXED_VALIDATION_CACHE_UNAVAILABLE'
        # Reuse exactly the validator predictions generated in this same run.
        valpaths=sorted((g['REPO_DIR']/'predictions').glob('*/unet_transformer_val/split_0/*.geff'))
        assert {p.stem for p in valpaths}==set(FIXED_STEMS),'VALIDATION_RAW_PATHS'
        for p in valpaths:
            assert all(raw_before[str(f.relative_to(g['REPO_DIR']/'predictions'))]==sha(f) for f in p.rglob('*') if f.is_file())
        g['TEST_DIR']=g['TRAIN_DIR'];g['test_stems']=FIXED_STEMS;g['METHOD']='unet_transformer_val'
        diag_phase='postprocessing'
        val_base=write(baseline_cfg,root/'validation_g1.csv','validation_g1')
        val_arm=write(candidate_cfg,root/'validation_candidate.csv','validation_candidate')
        val_graphs={'G1':official_roundtrip(root/'validation_g1.csv',FIXED_STEMS,build),arm:official_roundtrip(root/'validation_candidate.csv',FIXED_STEMS,build)}
        diag_phase='scoring'
        allrows=[]
        for stem in FIXED_STEMS:
            for label in ['G1',arm]:
                pred=val_graphs[label][stem];gt=g['graph_from_geff'](g['TRAIN_DIR']/(stem+'.geff'))
                # Read scale and estimated total from same competition metadata used by G1.
                meta=json.loads((g['TRAIN_DIR']/(stem+'.zarr')/'zarr.json').read_text())
                attrs=meta.get('attributes',{})
                scales=attrs.get('multiscales',[{}])[0].get('datasets',[{}])[0].get('coordinateTransformations',[{}])[0]
                scale=tuple(scales['scale'][-3:]) if scales.get('type')=='scale' else tuple(g['VOXEL_SCALE_UM'])
                er=metrics.evaluate(pred,gt,scale=scale,max_distance=7.0)
                recall=metrics.node_recall(pred,gt) if pred.num_edges() else 0.0
                total=g['read_estimated_true_node_count'](g['TRAIN_DIR']/(stem+'.geff'));assert total and total>0
                row=metrics.per_sample_metrics(er,total,recall);count_totals([row])
                row.update(stem=stem,embryo=stem.split('_')[0],arm=label,canonical_sha256=(val_base if label=='G1' else val_arm)[stem]['canonical_sha256'])
                append(root/'diagnostic_results.jsonl',row);allrows.append(row)
                diag['rows']=len(allrows);save(root/'diagnostic_checkpoint.json',diag)
        sums={}
        for label in ['G1',arm]:
            rows=[r for r in allrows if r['arm']==label]
            sums[label]={'overall':{**metrics.summarise(rows),**count_totals(rows)},'embryos':{e:{**metrics.summarise([r for r in rows if r['embryo']==e]),**count_totals([r for r in rows if r['embryo']==e])} for e in ['44b6','6bba']}}
        manifest=g['SECONDARY_WEIGHTS_PATH'].parent/'split_manifest.json'
        if manifest.is_file():
            data=json.loads(manifest.read_text());diag['secondary_split_manifest_sha256']=sha(manifest)
            def find_train(o):
                if isinstance(o,dict):
                    for k,v in o.items():
                        if k=='train' and isinstance(v,list):yield from v
                        else:yield from find_train(v)
                elif isinstance(o,list):
                    for v in o:yield from find_train(v)
            seen=set(find_train(data));diag['secondary_sample_coverage']={s:'TRAIN_SEEN_DIAGNOSTIC' if s in seen else 'COVERAGE_UNKNOWN' for s in FIXED_STEMS}
        diag.update(status='MEASURED_SAME_RUN_DIAGNOSTIC',summary=sums,changes=diff_contents(val_base,val_arm))
    except Exception as exc:
        if diag_phase=='postprocessing':
            save(root/'engineering_failure.json',{'phase':diag_phase,'error':type(exc).__name__+': '+str(exc)[:400]})
            raise
        diag['status']='AUXILIARY_EVALUATION_GAP';diag['gaps'].append(type(exc).__name__+': '+str(exc)[:400])
    finally:
        g['TEST_DIR']=old_dir;g['test_stems']=old_stems;g['METHOD']=old_method;g['filter_output_graph']=original_filter
    assert sha(final_path)==receipt['final_csv_sha256'],'FINAL_OUTPUT_OVERWRITTEN'
    save(root/'summary.json',diag)
    # This final receipt follows all writes, including auxiliary evaluation.
    from datetime import datetime,timezone
    from zoneinfo import ZoneInfo
    timestamp=datetime.now(timezone.utc)
    receipt['observed_at_utc']=timestamp.isoformat();receipt['observed_at_shanghai']=timestamp.astimezone(ZoneInfo('Asia/Shanghai')).isoformat()
    receipt['diagnostic_status']=diag['status'];receipt['final_csv_sha256']=sha(final_path)
    receipt['status']='READY_FOR_FORMAL_CHECK' if receipt['has_effect'] else 'MEASURED_NO_EFFECT'
    save(root/'production_receipt.json',receipt)
    print('DIVGATE_PRODUCTION_FINAL',arm,receipt['status'],receipt['final_csv_sha256'],flush=True)
