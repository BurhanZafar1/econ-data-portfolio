# High blood pressure in US adults, 1999 to 2018: is it getting worse?

**For:** health officials and programme planners. **Data:** national examination survey (NHANES), where trained staff measured the blood pressure of about 4,000 to 5,700 adults in every two year round.

## The short answer

More adults have high blood pressure today mainly because the population is older, not because people of the same age are at higher risk.

| Adults aged 20 and over | 1999-2000 | 2017-2018 | Change (95% range) |
|---|---|---|---|
| Share with high blood pressure, as counted | 28.5% | 34.9% | +6.5 points (+1.7 to +11.2) |
| Same, removing the effect of ageing | 25.9% | 27.5% | +1.6 points (−2.4 to +5.6) |

"High blood pressure" means a reading of 140/90 mmHg or above, or taking medicine to lower it. Under the stricter 2017 US guideline (130/80) about half of adults qualify.

## What this means

* **Plan services for the counted number.** About one adult in three needs diagnosis, treatment or monitoring, and this rises as the population ages, whatever happens to risk.
* **Track risk with the age adjusted number.** It shows no detectable change over two decades (+1.6 points, 95% range −2.4 to +5.6), so there is no sign that risk at a given age has fallen.
* **Average blood pressure** at a given age was stable: about 124 mmHg in men and 119 to 120 mmHg in women.

## Can I trust these numbers?

* The same code reproduces 30 official figures published by the US National Center for Health Statistics to within 0.1 percentage point.
* Re-estimating the same figures from the same data with R's survey package gives the same answers.
* Every figure carries a 95% range that reflects the survey's sampling design.

## Caveats

* Blood pressure was measured at one visit; a doctor would confirm hypertension over several visits, so these figures run somewhat high.
* "Removing the effect of ageing" uses the WHO world standard population, so the adjusted figures compare with other countries' WHO standardized figures, not with US figures adjusted another way.
* Rounds after 2018 used a different measuring device and are not included yet.
