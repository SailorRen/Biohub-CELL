"""Learn a symmetric daughter-pair gate from confirmed annotated topology.

Unannotated nodes and missing outgoing edges are never negative labels.
No image detector, public weight, fusion coefficient or ILP is trained here.
"""
import hashlib
import json
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from scipy.spatial import cKDTree

TASK_ID = "DIVISION_TRAIN_20260914"
SCALE = np.array([1.625, 0.40625, 0.40625], dtype=float)
THRESHOLD = 0.95
SEED = 20260914
FEATURE_NAMES = ["parent_distance_min", "parent_distance_max", "sister_distance",
                 "midpoint_distance", "relative_asymmetry", "daughter_angle_cosine",
                 "granddaughter_distance", "sister_separation_change",
                 "daughter_speed_mean", "daughter_speed_difference"]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def point(row):
    return np.array([row["z"], row["y"], row["x"]], dtype=float) * SCALE


def pair_features(coords):
    """Physical-coordinate input [..., parent/d1/d2/g1/g2, z/y/x]."""
    a = np.asarray(coords, dtype=float)
    if a.shape[-2:] != (5, 3) or not np.isfinite(a).all():
        raise ValueError("INVALID_PAIR_COORDINATES")
    p, c1, c2, g1, g2 = np.moveaxis(a, -2, 0)
    v1, v2 = c1-p, c2-p
    norm = lambda v: np.linalg.norm(v, axis=-1)
    d1, d2 = norm(v1), norm(v2)
    sister, grand = norm(c1-c2), norm(g1-g2)
    speed1, speed2 = norm(g1-c1), norm(g2-c2)
    return np.stack([np.minimum(d1,d2), np.maximum(d1,d2), sister,
                     norm((c1+c2)*0.5-p), np.abs(d1-d2)/np.maximum((d1+d2)*0.5,1e-6),
                     np.sum(v1*v2,axis=-1)/np.maximum(d1*d2,1e-6), grand, grand-sister,
                     (speed1+speed2)*0.5, np.abs(speed1-speed2)], axis=-1)


def maps(nodes, edges):
    out, incoming, frames = defaultdict(list), defaultdict(list), defaultdict(list)
    for node_id, node in nodes.items():
        frames[int(node["t"])].append(node_id)
    for e in edges:
        u,v = int(e["source_id"]),int(e["target_id"])
        if u not in nodes or v not in nodes:
            raise ValueError("DANGLING_GT_EDGE")
        if int(nodes[v]["t"]) == int(nodes[u]["t"])+1:
            out[u].append(v); incoming[v].append(u)
    return out, incoming, frames


def context(nodes, out, parent, c1, c2):
    t = int(nodes[parent]["t"])
    if c1 == c2 or any(int(nodes[c]["t"]) != t+1 for c in (c1,c2)):
        return None
    if any(len(out.get(c,[])) != 1 for c in (c1,c2)):
        return None
    g1,g2 = out[c1][0],out[c2][0]
    if g1 == g2 or any(int(nodes[g]["t"]) != t+2 for g in (g1,g2)):
        return None
    return np.stack([point(nodes[i]) for i in (parent,c1,c2,g1,g2)])


def labeled_pairs(nodes, edges):
    """Negatives require the alternate daughter to have a different known parent."""
    out, incoming, frames = maps(nodes, edges)
    records = []
    for t, parents in sorted(frames.items()):
        targets = sorted(i for i in frames.get(t+1,[]) if len(incoming.get(i,[])) == 1)
        if not targets:
            continue
        tree = cKDTree(np.stack([point(nodes[i]) for i in targets]))
        for p in sorted(parents):
            children = out.get(p,[])
            if len(children) not in (1,2):
                continue
            if len(children) == 2 and all(incoming.get(c) == [p] for c in children):
                coords = context(nodes,out,p,*children)
                if coords is not None:
                    records.append((coords,1,(p,*sorted(children))))
            # Only locally plausible, explicitly incompatible annotated pairings.
            local = [targets[i] for i in tree.query_ball_point(point(nodes[p]),10.0)]
            seen = set()
            for c1 in sorted(children):
                if incoming.get(c1) != [p]:
                    continue
                alternatives = sorted((c for c in local if c not in children and incoming[c][0] != p),
                                      key=lambda c: (np.linalg.norm(point(nodes[c])-point(nodes[c1])),c))
                added = 0
                for c2 in alternatives:
                    key = (p,*sorted((c1,c2)))
                    if key in seen or np.linalg.norm(point(nodes[c2])-point(nodes[c1])) > 14.0:
                        continue
                    coords = context(nodes,out,p,c1,c2)
                    if coords is None:
                        continue
                    records.append((coords,0,key));seen.add(key);added+=1
                    if added == 4:
                        break
    return records


def design(x, mean, scale):
    z = np.clip((np.asarray(x)-mean)/scale,-8.0,8.0)
    return np.concatenate([np.ones((*z.shape[:-1],1)), z, z*z],axis=-1)


def fit(coords, labels, seed=SEED):
    coords, y = np.asarray(coords,dtype=float),np.asarray(labels,dtype=float)
    if len(coords) != len(y) or set(y.tolist()) != {0.0,1.0}:
        raise ValueError("TRAINING_REQUIRES_CONFIRMED_POSITIVES_AND_NEGATIVES")
    rng=np.random.default_rng(seed)
    # Augmentation is applied only inside the training partition, in micrometres.
    augmented = np.concatenate([coords]+[coords+rng.normal(0,0.35,coords.shape) for _ in range(3)])
    yy=np.tile(y,4);x=pair_features(augmented)
    mean=x.mean(axis=0);scale=np.maximum(x.std(axis=0),0.1)
    xx=design(x,mean,scale)
    w=np.where(yy==1,0.5/max(1,(yy==1).sum()),0.5/max(1,(yy==0).sum()))
    ridge=0.003
    def objective(beta):
        z=xx@beta
        loss=float(np.sum(w*(np.logaddexp(0,z)-yy*z))+0.5*ridge*np.sum(beta[1:]**2))
        grad=xx.T@(w*(expit(z)-yy));grad[1:]+=ridge*beta[1:]
        return loss,grad
    start=np.zeros(xx.shape[1]);initial=objective(start)[0]
    result=minimize(objective,start,jac=True,method="L-BFGS-B",options={"maxiter":250,"ftol":1e-10,"gtol":1e-6})
    if not result.success or not np.isfinite(result.x).all() or result.fun >= initial:
        raise RuntimeError("TRAINING_OPTIMIZATION_FAILED: "+str(result.message))
    model={"mean":mean.tolist(),"scale":scale.tolist(),"coefficients":result.x.tolist()}
    audit={"n_positive":int(y.sum()),"n_negative":int((y==0).sum()),"augmented_rows":int(len(yy)),
           "initial_loss":initial,"final_loss":float(result.fun),"optimizer_steps":int(result.nit),
           "coefficient_norm":float(np.linalg.norm(result.x)),"converged":bool(result.success)}
    return model,audit


def predict(model, features):
    return expit(design(features,np.asarray(model["mean"]),np.asarray(model["scale"]))@np.asarray(model["coefficients"]))


def binary_metrics(y,scores):
    y=np.asarray(y,dtype=bool);pred=np.asarray(scores)>=THRESHOLD
    tp=int((pred&y).sum());fp=int((pred&~y).sum());fn=int((~pred&y).sum());tn=int((~pred&~y).sum())
    return {"tp":tp,"fp":fp,"fn":fn,"tn":tn,"precision":tp/max(1,tp+fp),"recall":tp/max(1,tp+fn),
            "negative_acceptance_rate":fp/max(1,fp+tn),"threshold":THRESHOLD}


def train_from_mount(train_dir, output_dir, graph_reader):
    started=time.time();train_dir=Path(train_dir);output_dir=Path(output_dir)
    sources=sorted(train_dir.glob("*.geff"))
    if not sources:
        raise RuntimeError("LABELED_TRAIN_MOUNT_MISSING")
    coords=[];labels=[];groups=[];inventory=[]
    for path in sources:
        graph=graph_reader(path)
        nodes={int(r["node_id"]):r for r in graph.node_attrs().iter_rows(named=True)}
        edges=list(graph.edge_attrs().iter_rows(named=True));records=labeled_pairs(nodes,edges)
        group=path.stem.split("_")[0]
        for a,y,_ in records:
            coords.append(a);labels.append(y);groups.append(group)
        h=hashlib.sha256()
        for f in sorted(p for p in path.rglob("*") if p.is_file()):
            h.update(str(f.relative_to(path)).encode());h.update(f.read_bytes())
        inventory.append({"stem":path.stem,"embryo":group,"gt_sha256":h.hexdigest(),
                          "positives":sum(y for _,y,_ in records),"negatives":sum(1-y for _,y,_ in records)})
        if time.time()-started > 1200:
            raise RuntimeError("TRAINING_20_MINUTE_BUDGET_EXCEEDED")
    coords=np.asarray(coords);labels=np.asarray(labels);groups=np.asarray(groups)
    unique=sorted(set(groups.tolist()))
    if len(unique)<2:
        raise RuntimeError("EMBRYO_HOLDOUT_UNAVAILABLE")
    models={};folds=[]
    for held in unique:
        train=groups!=held;val=~train
        model,audit=fit(coords[train],labels[train]);models[held]=model
        scores=predict(model,pair_features(coords[val]))
        folds.append({"held_out_embryo":held,"training_embryos":sorted(set(groups[train].tolist())),
                      "embryo_overlap":False,"fit":audit,"pair_metrics":binary_metrics(labels[val],scores)})
    final,final_audit=fit(coords,labels)
    payload={"task_id":TASK_ID,"feature_names":FEATURE_NAMES,"threshold":THRESHOLD,
             "final":final,"held_out":models}
    weights=output_dir/"division_gate_weights.json"
    weights.write_text(json.dumps(payload,sort_keys=True,allow_nan=False)+"\n")
    receipt={"task_id":TASK_ID,"training_completed":True,"weights_sha256":digest(weights),
             "model_type":"L2 logistic regression with squared standardized features",
             "embryo_overlap":False,"embryo_groups":unique,"folds":folds,"final_fit":final_audit,
             "gt_inventory":inventory,"seconds":time.time()-started,"threshold":THRESHOLD,
             "negative_rule":"candidate has exactly one annotated parent different from the proposed parent",
             "sparse_unannotated_as_negative":False,"feature_names":FEATURE_NAMES,
             "diagnostic_scope":"embryo-held-out pair classification; not full tracking CV or formal Kaggle score",
             "final_model_training_scope":"all labeled training embryos; held-out models used for PP validation",
             "no_test_labels":True,"formal_score":None}
    (output_dir/"division_training_receipt.json").write_text(json.dumps(receipt,indent=2,allow_nan=False)+"\n")
    print("DIVISION_TRAINING_COMPLETED",json.dumps({"weights_sha256":receipt["weights_sha256"],"final_fit":final_audit,"folds":folds}),flush=True)
    return payload,receipt


def runtime_pair_score(payload,nodes,out_edges,parent,c1,c2,dataset,is_validation):
    out={u:[int(e["target_id"]) for e in es] for u,es in out_edges.items() if u in (c1,c2)}
    coords=context(nodes,out,parent,c1,c2)
    if coords is None:
        return None
    if is_validation:
        group=str(dataset).split("_")[0]
        if group not in payload["held_out"]:
            raise RuntimeError("UNKNOWN_VALIDATION_EMBRYO")
        model=payload["held_out"][group]
    else:
        model=payload["final"]
    return float(predict(model,pair_features(coords)))
