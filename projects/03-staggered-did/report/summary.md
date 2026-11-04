# Summary: did state minimum wage increases reduce teen employment?

**Question.** States raised their minimum wages in different years. The standard
regression for this design can give a misleading answer when effects change over
time. We rebuilt the estimate with a method designed for staggered rollouts and
checked how far the evidence can be pushed.

**Data.** 500 US counties in 29 states, 2003 to 2007, from the public sample
that accompanies the Callaway and Sant'Anna paper. It is a teaching subset, so
treat the numbers as an illustration, not a policy finding.

**Headline.** The preferred estimate is a teen employment decline of about
3.1 percent in treated counties. Using all earlier
years as the baseline instead of only the last one gives
4.3 percent. The standard regression gives
3.7 percent, so here it was not badly wrong. Only
5 percent of its weight comes from the
problem comparison, where already treated states act as controls.

**What to be careful about.**

- The large event study average (7.7 percent)
  leans on years 2 and 3 after treatment, and only Illinois is observed that long.
  Using the same cohorts in years 0 and 1, the average is
  2.9 percent.
- Illinois alone cannot carry the claim. 5 of
  16 untreated states show a gap as large as its
  average change, for a placebo p value of 0.35.
- Statistical support is borderline. Reassigning the policy at random across states
  gives a p value of 0.05 for the preferred estimate. With
  errors clustered by state, the level at which policy changed, the standard
  regression has a t statistic of only 1.6.
- Treated states dipped in the year before their increase, by
  2.4 percent on average. The formal pre test does
  not reject parallel trends, but a test on so few years has limited power. That dip
  is why the choice of baseline moves the estimate.

**Bottom line.** The data lean toward a small negative effect of about 3 to 4 percent,
with borderline statistical support. They cannot say whether losses keep growing past
the first year after a wage increase, because only one state is observed that long.
Any decision should rest on the full county sample and more years of data.
