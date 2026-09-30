## The leaderboard

| submission | validator | public LB |
|---|---|---|
| baseline fork | 0.9368 | **0.938** |
| min length 10 + det 0.98 + per-type | 0.9495 | **0.934** |
| my own pipeline, same policy | 0.9523 | **0.865** |

Offline said plus 0.013. The leaderboard said minus 0.004.

I can't see the scorer, so I won't pretend to know which explanation is right. The multiplier might be clipped at 1 on the real thing. `N_est` might be computed differently. Or the hidden ground truth is dense enough that the tracks I deleted were mostly real, and `J` fell by as much as the bonus gained.

What I can say is narrower and more useful. The training-film validator does not rank configurations the way the hidden test does, at least along this axis.
