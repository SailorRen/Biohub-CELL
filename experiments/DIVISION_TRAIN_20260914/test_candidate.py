"""Executed synthetic behavior checks; no competition data or platform writes."""
import ast
import hashlib
import json
import unittest
import math
from collections import defaultdict
from scipy.spatial import cKDTree
from pathlib import Path
import numpy as np
import division_model as m

P=Path(__file__).resolve().parent


class DivisionTests(unittest.TestCase):
    def fixture(self):
        coords=np.array([[0,0,0],[-2,0,0],[2,0,0],[-4,0,0],[4,0,0]],float)
        return coords

    def test_swap_rotation_translation_and_units(self):
        a=self.fixture();ref=m.pair_features(a)
        np.testing.assert_allclose(ref,m.pair_features(a[[0,2,1,4,3]]))
        np.testing.assert_allclose(ref,m.pair_features(a+np.array([300,20,600])))
        np.testing.assert_allclose(ref,m.pair_features(a[:,[2,0,1]]*[-1,1,-1]))
        np.testing.assert_allclose(m.point({'z':1,'y':4,'x':4}),[1.625]*3)
        self.assertEqual(ref[7],4.0)

    def graph(self):
        coords={1:(0,0),2:(1,-4),3:(1,4),4:(2,-8),5:(2,8),6:(0,12),7:(1,10),8:(2,12),9:(1,8),10:(2,9)}
        nodes={i:{'node_id':i,'t':t,'z':0,'y':0,'x':x+20} for i,(t,x) in coords.items()}
        edges=[{'source_id':u,'target_id':v} for u,v in [(1,2),(1,3),(2,4),(3,5),(6,7),(7,8),(9,10)]]
        return nodes,edges

    def test_sparse_negatives_require_different_known_parent(self):
        nodes,edges=self.graph();pairs=m.labeled_pairs(nodes,edges)
        positives=[key for _,y,key in pairs if y];negatives=[key for _,y,key in pairs if not y]
        self.assertIn((1,2,3),positives)
        self.assertTrue(any(7 in key[1:] for key in negatives if key[0]==1))
        self.assertFalse(any(9 in key[1:] for key in negatives))
        self.assertEqual(len(negatives),len(set(negatives)))

    def test_missing_or_merged_granddaughter_rejected(self):
        nodes,edges=self.graph();out,_,_=m.maps(nodes,edges)
        self.assertIsNotNone(m.context(nodes,out,1,2,3))
        out[3]=[4];self.assertIsNone(m.context(nodes,out,1,2,3))
        out[3]=[];self.assertIsNone(m.context(nodes,out,1,2,3))

    def test_fit_changes_weights_and_generalizes_synthetic_geometry(self):
        rng=np.random.default_rng(83);n=100
        positive=np.tile(self.fixture(),(n,1,1))+rng.normal(0,.15,(n,5,3))
        negative=positive.copy();negative[:,2]=negative[:,1]+[.1,.1,.1];negative[:,4]=negative[:,3]+[.1,.1,.1]
        coords=np.concatenate([positive,negative]);labels=np.r_[np.ones(n),np.zeros(n)]
        model,audit=m.fit(coords,labels)
        scores=m.predict(model,m.pair_features(coords))
        self.assertGreater(scores[:n].mean(),scores[n:].mean()+.5)
        self.assertLess(audit['final_loss'],audit['initial_loss'])
        self.assertGreater(audit['coefficient_norm'],0)
        model2,_=m.fit(coords,labels);self.assertEqual(model,model2)
        with self.assertRaises(ValueError):m.fit(positive,np.ones(n))

    def test_validation_uses_held_out_weights_and_fails_unknown_group(self):
        nodes,edges=self.graph();out={}
        for e in edges:out.setdefault(e['source_id'],[]).append(e)
        d=len(m.FEATURE_NAMES)
        constant=lambda b:{'mean':[0]*d,'scale':[1]*d,'coefficients':[b]+[0]*(2*d)}
        payload={'final':constant(10),'held_out':{'A':constant(-10)}}
        self.assertLess(m.runtime_pair_score(payload,nodes,out,1,2,3,'A_001',True),.01)
        self.assertGreater(m.runtime_pair_score(payload,nodes,out,1,2,3,'A_001',False),.99)
        with self.assertRaises(RuntimeError):m.runtime_pair_score(payload,nodes,out,1,2,3,'B_001',True)

    def test_notebook_scope_and_training_order(self):
        base=json.loads((P.parents[1]/'experiments/TARGET950_20260914/candidate.ipynb').read_text())
        nb=json.loads((P/'candidate.ipynb').read_text())
        self.assertEqual(len(nb['cells']),len(base['cells'])+2)
        self.assertIn('train_from_mount',''.join(nb['cells'][4]['source']))
        for i,c in enumerate(base['cells']):
            if i!=5:self.assertEqual(c['source'],nb['cells'][i+(i>=4)]['source'])
        a=ast.parse(''.join(base['cells'][5]['source']));b=ast.parse(''.join(nb['cells'][6]['source']))
        self.assertEqual(len(a.body),len(b.body))
        changes=[]
        for x,y in zip(a.body,b.body):
            if ast.dump(x)!=ast.dump(y):changes.append(getattr(x,'name',None))
        self.assertEqual(changes,['add_safe_divisions_postlink'])
        for c in nb['cells']:compile(''.join(c['source']),'candidate','exec')
        identity=json.loads((P/'source_identity.json').read_text())
        self.assertEqual(identity['candidate_sha256'],hashlib.sha256((P/'candidate.ipynb').read_bytes()).hexdigest())

    def test_integrated_gate_changes_a_fork_and_preserves_deepcenter_veto(self):
        nb=json.loads((P/'candidate.ipynb').read_text())
        code=''.join(nb['cells'][6]['source'])
        names={'node_point','_position_um','edge_distance_um','add_safe_divisions_postlink'}
        defs=[ast.get_source_segment(code,n) for n in ast.parse(code).body if isinstance(n,ast.FunctionDef) and n.name in names]
        d=len(m.FEATURE_NAMES)
        payload={'final':{'mean':[0]*d,'scale':[1]*d,'coefficients':[10]+[0]*(2*d)},'held_out':{}}
        ns={'np':np,'math':math,'Path':Path,'cKDTree':cKDTree,'VOXEL_SCALE_UM':m.SCALE,
            'OUTPUT_SAFE_DIVISIONS':True,'SAFE_DIV_GLOBAL_FRAC_CAP':.004,'SAFE_DIV_FRAME_FRAC_CAP':.008,
            'SAFE_DIV_REQUIRE_MUTUAL_NN':True,'SAFE_DIV_REQUIRE_DIVERGENCE':True,
            'SAFE_DIV_EXISTING_CHILD_MAX_UM':10.,'SAFE_DIV_MAX_UM':9.,'SAFE_DIV_SISTER_MAX_UM':14.,
            'DEEPCENTER_SAFE_DIV_VETO':True,'DEEPCENTER_SAFE_DIV_THRESHOLD':.20,
            'DIVISION_MODULE':m,'DIVISION_PAYLOAD':payload,'TEST_DIR':Path('/test'),'COMP_DIR':Path('/competition'),
            'deepcenter_accept_repair_point':lambda *args:True}
        exec('\n\n'.join(defs),ns)
        nodes,edges=self.graph()
        edges=[e for e in edges if (e['source_id'],e['target_id']) in [(1,2),(2,4),(3,5)]]
        nodes={i:nodes[i] for i in range(1,6)}
        # No divergence: the public hand rule rejects; the trained gate can accept.
        nodes[4]['x']=nodes[2]['x'];nodes[5]['x']=nodes[3]['x']
        stats=defaultdict(int)
        result=ns['add_safe_divisions_postlink'](nodes,edges,stats,dataset='test')
        self.assertEqual(len(result),len(edges)+1)
        self.assertEqual((result[-1]['source_id'],result[-1]['target_id']),(1,3))
        self.assertEqual(stats['learned_division_scored'],1)
        self.assertEqual(len({e['target_id'] for e in result}),len(result))
        ns['deepcenter_accept_repair_point']=lambda *args:False
        self.assertEqual(ns['add_safe_divisions_postlink'](nodes,edges,defaultdict(int),dataset='test'),edges)


if __name__=='__main__':unittest.main(verbosity=2)
