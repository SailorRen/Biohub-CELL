import numpy as np


def split_score(J, n_pred, n_est, k=0.1):
    """Break the adjusted edge Jaccard into its two parts.

    adj = max(0, J * (1 - k * (n_pred - n_est) / n_est))

    Returns a dict with the raw Jaccard, the node-count multiplier, and the
    final score, so you can see which one a change actually moved.
    """
    mult = 1.0 - k * (n_pred - n_est) / n_est
    return {"J": J, "multiplier": mult, "adj": max(0.0, J * mult),
            "node_delta_pct": 100.0 * (n_pred - n_est) / n_est}


def compare(before, after):
    """before/after are dicts from split_score. Says where the change came from."""
    dJ = after["J"] - before["J"]
    dM = after["multiplier"] - before["multiplier"]
    total = after["adj"] - before["adj"]
    share = abs(dM) / (abs(dJ) + abs(dM) + 1e-12)
    flag = "  <-- almost all multiplier, treat as unproven" if share > 0.7 else ""
    return (f"adj {total:+.4f}   from J {dJ:+.4f}, from multiplier {dM:+.4f}"
            f"   ({share:.0%} multiplier){flag}")


# my own case: raising min track length from 6 to 10
before = split_score(J=0.9368, n_pred=100_000, n_est=100_000)
after  = split_score(J=0.9366, n_pred= 95_000, n_est=100_000)   # J flat, 5% fewer nodes
print("baseline :", {k: round(v, 4) for k, v in before.items()})
print("variant  :", {k: round(v, 4) for k, v in after.items()})
print()
print(compare(before, after))
print()
print("leaderboard said: 0.938 -> 0.934")
