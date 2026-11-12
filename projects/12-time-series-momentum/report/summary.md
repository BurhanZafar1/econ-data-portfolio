# Time series momentum: what replicates and what to expect now

**For:** a portfolio manager deciding whether a 12 month trend sleeve earns its place.

**The claim.** Moskowitz, Ooi and Pedersen (2012, *Journal of Financial Economics*) show that across 58 futures from 1985 to 2009, going long assets that rose over the past year and short those that fell, each at 40% volatility, earned a Sharpe ratio above one, an alpha of 1.58% a month, and its best returns in extreme markets.

**What replicates.**

* On the authors' own factor file the volatility (12.3%), the Sharpe ratio (1.38), the factor loadings (UMD 0.26 against 0.28) and the straddle shape (convex in the market, t 3.57) all match.
* The printed alpha does not: the file gives 1.22% a month (t 6.13), and the paper's own loadings applied to it imply 1.20%, not 1.58%.
* A rebuild from 23 public markets (equity regions, government bonds, currencies, energy) correlates 0.74 with the authors' factor and earns a 0.94 Sharpe ratio, alpha 1.28% a month (t 4.24).

**What weakens it.**

* Only 10 of 22 instruments are significant on their own; the strength is in the diversified portfolio.
* Volatility timing does much of the work: with a slow (expanding window) volatility, trend has a Sharpe ratio of 0.67 against 0.62 for buy and hold, versus 0.94 with the paper's scaling. Scaled trend still adds 1.19% a month over scaled buy and hold (t 4.05).
* After 64 correlated variants the deflated Sharpe ratio of the headline is 0.75, below the 0.95 bar, though its t of 5.40 clears the Harvey, Liu and Zhu hurdle of 3.

**What happened next.** From 2010 the authors' updated factor earns 0.44% a month (Sharpe 0.40, alpha t 1.20) and our rebuild 0.36% (Sharpe 0.23) with a 44% drawdown. Bonds kept working; our currencies did not, partly because the rebuild omits carry, while AQR's stayed slightly positive. Costs are not the issue: break even is about 96 bp per unit of notional traded.

**Recommendation.** Treat trend as a diversifier with crisis convexity, sized for a Sharpe ratio near 0.3 to 0.4, not the 1.0 plus of the original sample. Watch its UMD loading, which on the authors' updated file rose from 0.26 (1985 to 2009) to 0.51 after 2009.

Figures: `output/cumulative_returns.png`, `output/lag_tstats_paper_fig1.png`. Numbers: `output/headline.json`.
