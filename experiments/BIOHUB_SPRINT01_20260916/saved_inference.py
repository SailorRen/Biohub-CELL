import numpy as np
from scipy.special import expit
SCALE = np.array([1.625,0.40625,0.40625])

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

def design(x, mean, scale):
    z = np.clip((np.asarray(x)-mean)/scale,-8.0,8.0)
    return np.concatenate([np.ones((*z.shape[:-1],1)), z, z*z],axis=-1)

def predict(model, features):
    return expit(design(features,np.asarray(model["mean"]),np.asarray(model["scale"]))@np.asarray(model["coefficients"]))
