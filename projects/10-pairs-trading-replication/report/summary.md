# Pairs trading (Gatev, Goetzmann and Rouwenhorst, 2006): one page summary

**Bottom line.** The distance method's famous profits (0.805% a month on committed capital for the top 20 stock pairs, 1963 to 2002) do not carry over to anything we can trade or test on public data today. After 2002 it earns about 0.13% a month gross on S&P 500 stocks, roughly 0.08% after 5 bp per leg per side, and that number is likely biased upward by survivorship. On industry portfolios and sector ETFs it earns nothing.

**What we did.** Rebuilt the paper's rule faithfully (12 month formation, minimum squared distance pairs, open at 2 standard deviations, close at crossing, six overlapping portfolios, committed and fully invested returns, one day wait). Ran it on three public universes: 49 Fama-French industries (1963 to 2026, survivorship free), nine sector ETFs and current S&P 500 members (2003 to 2026).

**Key numbers** (top 20, wait one day, committed capital, monthly)

| Universe | Period | Gross | Net of 5 bp | Break even cost (per leg per side) |
| --- | --- | --- | --- | --- |
| Paper, CRSP stocks | 1963 to 2002 | 0.52% | not reported | not reported (paper's implied bid ask cost: 162 bp per pair round trip, about 40 bp per leg per side) |
| 49 industries | 1963 to 2002 | -0.08% | | n/a (gross < 0) |
| 49 industries | 2003 to 2026 | 0.00% | -0.04% | 0.1 bp |
| Sector ETFs (top 5) | 2003 to 2026 | 0.03% | 0.00% | 5.2 bp |
| S&P 500 stocks | 2003 to 2026 | 0.13% | 0.08% | 13.3 bp |

**Why industries likely fail.** A pairs trade buys the recent loser and sells the recent winner, so it is short momentum. In industry portfolios the stock specific noise that reverts is diversified away, and industry momentum dominates. Regression on factors, 1963 to 2002: momentum beta -0.07 (t -7.6), reversal beta +0.07 (t 8.5), alpha -0.06% (t -1.6).

**Why the stock result is not tradable evidence.**
* Survivorship: only today's members are in the sample (42% of the January 2002 index).
* Random pairs under the same rule earn 0.087% a month, two thirds of the distance pairs' return; distance pairs beat 91 of 100 draws (p = 0.09). The factor alpha is 0.145% a month (t 3.38), so the return is not just the reversal factor, though survivorship likely inflates it.
* Deflated Sharpe ratio of the pre-specified series, given the 24 variants tried, is 0.92, below 0.95.
* Borrow costs and impact are not included.

**Risk notes.** The strategy carries negative momentum exposure, so it loses when relative trends persist. Capacity was not tested; with a 13 bp break even cost, execution cost is the first constraint to study.

**Recommendation.** Do not allocate to the plain distance rule. If revisited, test it on a point in time stock universe with delisting returns (CRSP) and compare against a pure short term reversal factor before adding any pair selection logic.
