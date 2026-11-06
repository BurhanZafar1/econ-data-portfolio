# Linking two files with no shared ID: summary

**Question.** We have two lists of people with no common ID number, and the names, addresses and birth dates contain typos and gaps. How do we decide which records are the same person, and how sure can we be?

**What we did.** We tested methods on a standard benchmark of 5,000 synthetic people, each appearing once in each file with deliberate errors in the second copy. Because the true pairs are known, every method can be graded.

1. Narrow 25 million possible pairs down to 33,263 that share something simple, such as a postcode or a birth date. This keeps 99.6% of the true pairs.
2. Score how closely each field agrees, allowing for small typos.
3. Let a statistical model (Fellegi-Sunter, the method used by census bureaus) learn from the data alone how much each kind of agreement is worth, and give every pair a probability of being the same person.

**Results.**

| Approach | True pairs found (of 5,000) | Wrong links |
|---|---|---|
| Exact match on name and birth date | 2,079 (42%) | 0 |
| Probabilistic model, all fields | 4,974 (99.5%) | 0 |
| Probabilistic model, no address information | 4,101 (82.0%) | 0 |

The last two rows allow each record at most one partner. Without that rule, the model without addresses makes 15 wrong links.

**What it means.**

* Exact matching is safe but throws away more than half the data, and the records it drops are the ones with errors, which may not be random.
* The probabilistic approach finds almost every true pair. The model itself learns without labeled examples, though one of the five shortcuts in step 1 was added after seeing which true pairs the others missed.
* With all fields available, the model's own estimate of its accuracy was right (99.97% predicted, 99.98% actual). Without addresses its estimate was off (93.3% predicted, 99.6% actual). Before relying on a linkage, check a random sample of links by hand.
* 21 pairs were genuinely uncertain. These should go to a person for review rather than be decided by a cutoff.

**Caveat.** The benchmark is cleaner than most real files, so real results will be somewhat worse. The method and the checks carry over unchanged.
