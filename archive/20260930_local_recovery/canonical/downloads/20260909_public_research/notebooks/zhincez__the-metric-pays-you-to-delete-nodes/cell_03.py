## It kept getting better, which should have bothered me

The two embryo types have very different label density. One has 0.2 to 1.3 percent of its nodes labelled. The other has 13 to 15. So throwing away short tracks is nearly free on the sparse one and expensive on the dense one.

| configuration | validator |
|---|---|
| baseline | 0.9368 |
| uniform min length 10 | 0.9420 |
| plus detection threshold 0.98 | 0.9450 |
| **per-type: 44b6 = 20, 6bba = 10** | **0.9495** |

On my own pipeline the same policy went 0.9367 to 0.9523.

Every step consistent. Every step mechanistic. Every step reproducible. That is what a real finding looks like, and it is also exactly what this one looked like.
