## The term

The adjusted edge Jaccard is roughly:

```
adj = max(0,  J * (1 - 0.1 * (N_pred - N_est) / N_est))
```

`J` is the edge Jaccard. The bracket penalises predicting more nodes than the organisers' estimate.

Now read it again. It's clipped at zero from below. Nothing clips it from above. Predict *fewer* nodes than `N_est` and the difference goes negative, the multiplier goes above 1, and your score goes up for producing less.

You get paid for deleting. And nothing checks whether what you deleted was wrong.
