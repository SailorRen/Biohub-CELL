"""固定真实 InMemoryGraph 接口；HOCT结果为手工合成，无模型推理。"""
import ast,copy,importlib.metadata,inspect,json,types,unittest,time
from pathlib import Path
from unittest.mock import patch
import numpy as np
import polars as pl
import tracksdata as td
from tracksdata.nodes import Mask
from tracksdata.solvers import ILPSolver
import hoct_observer as obs
from hoct_guard import apply_guard,digest
P=Path(__file__).resolve().parent
assert importlib.metadata.version('tracksdata')=='0.1.0rc6.dev3+g980c2d30a'

class ObserverTests(unittest.TestCase):
    def graph(self):
        g=td.graph.InMemoryGraph();g.add_node_attr_key(td.DEFAULT_ATTR_KEYS.MASK,pl.Object,None)
        g.add_edge_attr_key('similarity',pl.Float64,-1.)
        specs={2:(0,0,101),5:(1,0,205),9:(1,1,309),12:(0,1,412),15:(1,2,515),17:(0,2,617),19:(1,3,719)}
        labels=np.zeros((2,1,1,4),dtype=np.int16);ids={10:[],11:[]};raster={}
        for i in range(20):
            t,x,pid=specs.get(i,(0,0,-1))
            g.add_node({'t':t,td.DEFAULT_ATTR_KEYS.MASK:Mask(np.ones((1,1,1),bool),[0,0,x,1,1,x+1])})
            if i in specs:
                ids[t+10].append(pid);labels[t,0,0,x]=len(ids[t+10]);raster[pid]=[t+10,0,0,x]
        g.bulk_remove_nodes([i for i in range(20) if i not in specs])
        for u,v in [(2,5),(2,9),(12,15),(17,19)]:g.add_edge(u,v,{'similarity':.8})
        g.add_edge_attr_key('synthetic_selected',pl.Boolean,False)
        g.update_edge_attrs(edge_ids=[g.edge_id(17,19)],attrs={'synthetic_selected':True})
        sol=g.filter(td.EdgeAttr('synthetic_selected') == True).subgraph()
        return g,sol,labels,ids,raster

    def test_old_error_reproduced(self):
        g,*_=self.graph();row=next(g.node_attrs(attr_keys=['t',td.DEFAULT_ATTR_KEYS.MASK]).iter_rows(named=True))
        with self.assertRaises(KeyError):_ = row['node_id']
        print('OLD_ERROR_REPRODUCED: real InMemoryGraph missing node_id')

    def test_real_mapping_edges_chunk_guard(self):
        g,sol,labels,ids,raster=self.graph()
        self.assertEqual(set(g.node_ids()),{2,5,9,12,15,17,19})
        c,s,r=obs.collect_mapped_edges(g,sol,obs.initial_candidate_ids(g),labels,ids,raster,10,11,True)
        self.assertEqual(c,{(101,205),(101,309),(412,515),(617,719)})
        self.assertEqual(s,{(617,719)})
        copied=td.graph.InMemoryGraph.from_other(sol)
        self.assertNotEqual(set(copied.node_ids()),set(sol.node_ids()))
        self.assertEqual(obs.collect_mapped_edges(g,copied,obs.initial_candidate_ids(g),labels,ids,raster,10,11,True)[1],s)
        print('SOLUTION_IDS',list(sol.node_ids()),'COPY_IDS',list(copied.node_ids()))
        nodes={i:dict(t=v[0],z=v[1],y=v[2],x=v[3]) for i,v in raster.items()}
        edges=[dict(source_id=u,target_id=v) for u,v in sorted(c|{(205,309)})]
        ev=dict(video='synthetic',input_hash=digest(['synthetic',list(nodes.items()),edges]),complete=True,covered=list(c),selected=list(s))
        n,e,receipt,deleted=apply_guard('synthetic',nodes,edges,ev)
        self.assertEqual(deleted,[(412,515)]);self.assertEqual(n,nodes);self.assertEqual(receipt['protected'],2)
        self.assertIn(dict(source_id=205,target_id=309),e)
        self.assertEqual(apply_guard('synthetic',nodes,edges,dict(ev,complete=False))[1],edges)
        print('REAL_INTERFACE_PASS: explicit four reads; sparse graph IDs; chunk_start=10; protected/uncovered unchanged')

    def test_empty_and_incomplete(self):
        g,_,labels,ids,raster=self.graph();g.bulk_remove_edges(g.edge_ids())
        self.assertEqual(obs.collect_mapped_edges(g,g,set(),labels,ids,raster,10,11,True)[:2],(set(),set()))
        g.bulk_remove_nodes(g.node_ids())
        self.assertEqual(obs.collect_mapped_edges(g,g,set(),labels,ids,raster,10,11,True)[:2],(set(),set()))
        with self.assertRaisesRegex(RuntimeError,'INCOMPLETE_SOLVE'):
            obs.collect_mapped_edges(g,g,set(),labels,ids,raster,10,11,False)

    def test_missing_and_ambiguous(self):
        g,sol,labels,ids,raster=self.graph()
        with self.assertRaisesRegex(obs.InterfaceError,'required=.*actual='):
            obs.required_attrs(g,'node',['node_id','missing'],'probe')
        with patch.object(g,'node_attrs',return_value=pl.DataFrame({'t':[0]})):
            with self.assertRaisesRegex(obs.InterfaceError,"actual=\\['t'\\]"):
                obs.required_attrs(g,'node',['node_id','t'],'missing_column')
        labels[0,0,0,1]=0 # unmapped ordinary parent cannot enter C
        c,_,_=obs.collect_mapped_edges(g,sol,obs.initial_candidate_ids(g),labels,ids,raster,10,11,True)
        self.assertNotIn((412,515),c)
        # Exact mask sees two labels: no nearest-node guess.
        g.update_node_attrs(node_ids=[12],attrs={td.DEFAULT_ATTR_KEYS.MASK:[Mask(np.ones((1,1,2),bool),[0,0,0,1,1,2])]})
        labels[0,0,0,1]=2
        c,_,_=obs.collect_mapped_edges(g,sol,obs.initial_candidate_ids(g),labels,ids,raster,10,11,True)
        self.assertNotIn((412,515),c)

    def test_wrapper_restored(self):
        api=types.SimpleNamespace(model_predict=object());old=ILPSolver._solve;before=api.model_predict
        with self.assertRaises(obs.InterfaceError):
            with obs.temporary_observers(ILPSolver,api,object(),object()):raise obs.InterfaceError('injected')
        self.assertIs(ILPSolver._solve,old);self.assertIs(api.model_predict,before)

    def test_interface_no_chunk_retry(self):
        n={9:dict(t=0,z=0,y=0,x=0)};vol=np.ones((2,1,1,1));error=obs.InterfaceError('injected',dict(statuses=['OPTIMAL'],stage='mapping'))
        with patch.object(obs,'observe_chunk',side_effect=error) as call:
            e=obs.observe_video('a',n,[],None,vol,lambda *_:np.ones_like(vol),time.monotonic())
        self.assertEqual(call.call_count,1);self.assertEqual(e['status'],'INTERFACE_ERROR');self.assertFalse(e['complete'])
        self.assertIn('InterfaceError',e['traceback']);self.assertEqual(e['observation']['statuses'],['OPTIMAL'])

    def test_actual_diagnostic_stop_block(self):
        tree=ast.parse((P/'diagnostic_runtime.py').read_text())
        loop=next(n for n in tree.body if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='sample')
        stop=next(n for n in loop.body if isinstance(n,ast.If) and isinstance(n.test,ast.Call) and getattr(n.test.func,'id','')=='stop_on_interface_error')
        calls=[];saved={};ev=dict(status='INTERFACE_ERROR',traceback='injected original stack',observation=dict(statuses=['OPTIMAL']))
        def invoke(sample):calls.append(sample);return ev
        prefix=ast.parse("evidence=invoke(sample)\ncoverage.append({'sample':sample})").body
        actual=ast.Module(body=[ast.For(target=loop.target,iter=loop.iter,body=prefix+[stop],orelse=[])],type_ignores=[])
        scope=dict(CONTRACT={'samples':[{'stem':str(i)} for i in range(8)]},invoke=invoke,coverage=[],rows={},repeats=[],deletions=[],save=lambda n,v:saved.update({n:v}),stop_on_interface_error=obs.stop_on_interface_error)
        with self.assertRaisesRegex(RuntimeError,'INTERFACE_ERROR'):
            exec(compile(ast.fix_missing_locations(actual),'actual_diagnostic_stop_block','exec'),scope)
        self.assertEqual(len(calls),1);self.assertEqual(saved['runtime_receipt.json']['remaining_samples'],7)
        self.assertEqual(saved['interface_error.json']['failure'],ev)
        for reason in ['TIMEOUT','BUDGET_ESTIMATE','INCOMPLETE_SOLVE']:
            self.assertFalse(obs.stop_on_interface_error(dict(reason=reason,complete=False),lambda _:self.fail()))
        print('FAST_STOP_PASS: actual diagnostic stop block; subsequent calls=0; original receipt preserved')

if __name__=='__main__':
    print('ENV',json.dumps({k:importlib.metadata.version(k) for k in ['tracksdata','numpy','polars']}))
    print('BACKEND',inspect.getfile(td.graph.InMemoryGraph),'synthetic HOCT selection; model inference=0')
    unittest.main(verbosity=2)
