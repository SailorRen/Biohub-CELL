## Split the score, so you can see which half moved

This is the check I should have been running from the start. It takes your predicted node count and the reference estimate, and tells you how much of your score is the Jaccard and how much is the node-count multiplier.

If a change moves the multiplier while `J` sits still, you are being paid for deleting, and you should assume that money is not in the bank until the leaderboard says so.
