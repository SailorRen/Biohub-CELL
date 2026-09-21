"""Minimum production evidence; derived from frozen prior CSV/audit helpers. No diagnostic scoring."""
import copy,csv,hashlib,json,math,os
from collections import Counter
from pathlib import Path
COLUMNS=['id', 'dataset', 'row_type', 'node_id', 't', 'z', 'y', 'x', 'source_id', 'target_id']

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

def file_manifest(root):
    return {str(p.relative_to(root)):sha(p) for p in sorted(Path(root).rglob('*')) if p.is_file()}

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

def resolved_config(base,selected,arm):
    config=copy.deepcopy(base);config.update(copy.deepcopy(selected))
    config['SHORT_TRACK_RESCUE_TRIGGER_REMOVED_FRAC']=.10
    before=copy.deepcopy(config)
    assert config['DEEPCENTER_SAFE_DIV_THRESHOLD']==.20
    assert arm in ['D960','H30','R00']
    if arm=='R00':config['SHORT_TRACK_RESCUE_TRIGGER_REMOVED_FRAC']=.0
    return before,config


def install(g,arm,keys):
    root=g['WORKING_DIR']/'score_trio';root.mkdir(exist_ok=True)
    original=g['filter_output_graph'];calls=[];testdir=g['TEST_DIR'];g['_trio_rescue_rows']=[]
    keys=list(keys)+['SHORT_TRACK_RESCUE_TRIGGER_REMOVED_FRAC']
    def audited(nodes,edges,**kw):
        if g['TEST_DIR']!=testdir:return original(nodes,edges,**kw)
        start=len(g['_trio_rescue_rows']);raw=digest([nodes,edges]);result=original(copy.deepcopy(nodes),copy.deepcopy(edges),**kw)
        assert raw==digest([nodes,edges])
        assert not result[2]['deepcenter_safe_div_missing']
        row={'stem':kw['dataset'],'input_hash':raw,'final_hash':digest(graph_content(result[0],result[1],serialized=True)),
             'config':{k:g[k] for k in keys},'stats':result[2],'raw_input_unchanged':True,'rescue_calls':copy.deepcopy(g['_trio_rescue_rows'][start:])}
        calls.append(row);append(root/'postprocess_calls.jsonl',row)
        return result
    g['filter_output_graph']=audited;g['_trio_calls']=calls

def finish(g,arm,reader_source,reader_hash):
    root=g['WORKING_DIR']/'score_trio';final=g['SUBMISSION_PATH'];expected=sorted(g['test_stems'])
    assert g['SPRINT_ARM']=='G1' and not g['ALLOW_ARTIFACT_FALLBACK']
    assert g['DEEPCENTER_VETO_DETECTOR'] is not None
    assert sha(g['DEEPCENTER_VETO_DETECTOR']['path'])==g['_deepcenter_expected_sha256']
    before,config=resolved_config(g['PP_BASE_CONFIG'],g['selected_config'],arm)
    weight=.8
    det=.960 if arm=='D960' else .965
    bi=.30 if arm=='H30' else .15
    assert float(os.environ['BIOHUB_SECONDARY_DETECTION_WEIGHT'])==weight
    assert float(os.environ['BIOHUB_SECONDARY_EDGE_WEIGHT'])==.15
    assert float(os.environ['BIOHUB_BIDIRECTIONAL_EDGE_WEIGHT'])==bi
    assert float(os.environ['BIOHUB_DUAL_SEED_MIN_CANDIDATE_RETENTION'])==.9
    assert g['DET_THRESHOLD']==det
    worker=g['_guard_records'];assert worker and {r['dataset'] for r in worker}==set(expected)
    assert all(r['secondary_detection_weight']==weight and r['det_threshold']==det for r in worker),'WORKER_CONFIG_MISMATCH'
    harmonic=[json.loads(p.read_text()) for p in g['WORKING_DIR'].glob('trio_harmonic_*.json')]
    assert harmonic and all(r['weight']==bi and r['mode']=='harmonic_probability' for r in harmonic)
    for key,value in {'ADAPTIVE_SHORT_TRACK_RESCUE':True,'SHORT_TRACK_RESCUE_MIN_LEN':4,'SHORT_TRACK_RESCUE_MIN_MEAN_EDGE_PROB':.88,'SHORT_TRACK_RESCUE_MAX_MEAN_EDGE_DIST_UM':3.,'SHORT_TRACK_RESCUE_MAX_NODES_FRAC':.012,'SHORT_TRACK_RESCUE_MAX_NODES_ABS':120,'OUTPUT_MIN_TRACK_LEN':6}.items():assert g[key]==value
    base=None;raw_before=None
    if arm=='R00':
        (root/'g1_original.csv').write_bytes(final.read_bytes());base=csv_contents(final,expected)
        raw_before=file_manifest(g['REPO_DIR']/'predictions')
        saved=g['pp_apply']({k:v for k,v in config.items() if k in g['PP_SWEEP_KEYS']})
        saved_trigger=g['SHORT_TRACK_RESCUE_TRIGGER_REMOVED_FRAC']
        g['SHORT_TRACK_RESCUE_TRIGGER_REMOVED_FRAC']=config['SHORT_TRACK_RESCUE_TRIGGER_REMOVED_FRAC']
        try:g['write_test_submission']('R00')
        finally:
            g['pp_restore'](saved)
            g['SHORT_TRACK_RESCUE_TRIGGER_REMOVED_FRAC']=saved_trigger
        assert raw_before==file_manifest(g['REPO_DIR']/'predictions'),'RAW_FILES_CHANGED'
    content=csv_contents(final,expected)
    latest={r['stem']:r for r in g['_trio_calls']}
    assert set(latest)==set(expected)
    for stem,row in latest.items():
        assert row['config']==config and row['final_hash']==content[stem]['canonical_sha256']
    if arm=='R00':
        for stem in expected:
            rows=[r for r in g['_trio_calls'] if r['stem']==stem]
            assert len({r['input_hash'] for r in rows})==1
    assert hashlib.sha256(reader_source.encode()).hexdigest()==reader_hash
    import polars as pl,tracksdata as td
    scope={'pl':pl,'td':td};exec(compile(reader_source,'official_csv_reader.py','exec'),scope)
    official_roundtrip(final,expected,scope['build_graph_from_rows'])
    changes=diff_contents(base,content) if base else None
    from datetime import datetime,timezone
    from zoneinfo import ZoneInfo
    import importlib.metadata as im
    now=datetime.now(timezone.utc)
    receipt={'arm':arm,'status':'READY_FOR_FORMAL_CHECK','engineering_status':'PASS','observed_at_utc':now.isoformat(),'observed_at_shanghai':now.astimezone(ZoneInfo('Asia/Shanghai')).isoformat(),
        'expected_samples':expected,'final_csv_sha256':sha(final),'final_canonical_sha256':digest({s:r['canonical_sha256'] for s,r in content.items()}),
        'final_graphs':{s:{k:v for k,v in r.items() if k!='content'} for s,r in content.items()},'selected_label':g['selected_label'],
        'selected_config':g['selected_config'],'original_resolved_config':before,'final_resolved_config':config,
        'worker_detection_weight':weight,'worker_det_threshold':det,'worker_bidirectional_weight':bi,'worker_harmonic_records':harmonic,'worker_test_records':len(worker),'worker_config_verified':True,
        'worker_retention_summary':g['_guard_by_movie'],'original_selector_unchanged':True,'training_calls':0,
        'weights':g['_runtime_integrity_receipt']['checkpoint_sha256'],'gate_weight_sha256':g['_SPRINT_WEIGHT_SHA'],
        'official_reader_sha256':reader_hash,'csv_roundtrip':'PASS','raw_input_copy_isolation':True,
        'dependency_versions':{n:im.version(n) for n in ['tracksdata','polars','numpy','scipy','geff','zarr','torch']},
        'changes_vs_same_run_g1':changes,'has_effect':any(r['changed'] for r in changes) if changes is not None else None,
        'comparison_limit':None if base else 'Upstream arm has no same-run G1 comparator; compare archived G1 externally with input identity limits.',
        'legacy_guard_report_note':'Inherited historical literal configuration is not authoritative; use this resolved receipt and worker records.',
        'postprocess_calls_sha256':sha(root/'postprocess_calls.jsonl'),'public':None}
    save(root/'production_receipt.json',receipt)
    print('SCORE_TRIO_FINAL',arm,receipt['final_csv_sha256'],flush=True)
