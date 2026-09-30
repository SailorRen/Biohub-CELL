## Why the offline check couldn't catch it

This part generalises past this competition, so it's the bit worth keeping.

Training label coverage is low, and wildly uneven between the two embryo types. When you delete a track, the validator only notices if that track happened to be labelled. On the sparse type it usually wasn't. So deletion showed up as pure bonus with no cost attached.

A metric term that rewards absence is the hardest kind to validate on sparse labels. The labels can confirm the reward. They cannot confirm the price.

If you're testing anything that reduces output volume, check what fraction of what you removed was even labelled, before you believe the score.
