# Authentication of the paper and the claims checked

Checked 11 and 12 November 2026.

## The paper

| Item | Evidence | Result |
| --- | --- | --- |
| Bibliographic record | RePEc / EconPapers record `RePEc:eee:jfinec:v:104:y:2012:i:2:p:228-250` ([link](https://econpapers.repec.org/RePEc:eee:jfinec:v:104:y:2012:i:2:p:228-250)) | Title "Time series momentum"; Tobias J. Moskowitz, Yao Hua Ooi, Lasse Heje Pedersen; *Journal of Financial Economics* 104(2), 228 to 250, 2012. Abstract (58 liquid instruments, persistence for one to 12 months, partial reversal) matches. |
| DOI | [doi:10.1016/j.jfineco.2011.11.003](https://doi.org/10.1016/j.jfineco.2011.11.003) resolves to the Elsevier article page | Matches. |
| Article text | Published version posted by the third author ([NYU Stern page](https://pages.stern.nyu.edu/~lpederse/papers/TimeSeriesMomentum.pdf)) | Journal header "Journal of Financial Economics 104 (2012) 228–250"; received 16 August 2010, accepted 12 August 2011. Affiliations: University of Chicago Booth School of Business and NBER (Moskowitz); AQR Capital Management (Ooi, Pedersen); New York University, Copenhagen Business School, NBER, CEPR (Pedersen). |
| Peer review | Published in the *Journal of Financial Economics* (Elsevier) | **Peer reviewed journal article.** |
| Authors' data | AQR data sets "Time Series Momentum: Original Paper Data" (1985 to 2009) and "Time Series Momentum: Factors, Monthly" (updated), copyright 2012 Moskowitz, Ooi and Pedersen ([data set page](https://www.aqr.com/Insights/Datasets/Time-Series-Momentum-Original-Paper-Data)) | The original file says it "contains the TSMOM factors used in" the paper. The updated file says it is "an updated and extended version" and that AQR "reconstructs the full history each time the returns are updated". Neither file is redistributed here; `get_data.py` downloads them and `output/aqr_checksums_used.json` records the vintage. |

## Numbers taken from the paper (stored in `src/tsmom/paper.py`)

* Section 2.4, eq. (1): ex ante variance is 261 times an exponentially weighted average of squared demeaned daily returns, center of mass 60 days; the estimate at t-1 scales returns at t.
* Section 4.1, eq. (5): position sign(past 12 month excess return) times 40% / sigma; the factor is the equal weighted average over available instruments; "an annualized volatility of 12% per year over the sample period 1985–2009".
* Introduction: the diversified portfolio has "a Sharpe ratio greater than one on an annual basis".
* Table 3 Panel A (monthly and quarterly regressions on MSCI World, SMB, HML, UMD) and the first row of Panel C (quarterly regression on MSCI World and its square).
* Table 2 Panel A, 12 month look back and 1 month holding: alpha t-statistic 6.61.
* Section 4.1: all 58 instruments have positive 12 month TSMOM returns and 52 are significant at 5%.

The PDF text layer drops some minus signs. Signs were assigned from the spacing left by the missing glyph (for example "( 0.84)" for SMB) and from the text, which says the strategy "does not exhibit significant betas on the market, SMB, or HML". Table 2 cells beyond 12 months may carry lost minus signs, so only the 12 by 1 cell is used.

## Independent checks of the paper's claims

| Claim | Independent source | Result |
| --- | --- | --- |
| Factor volatility of 12% and a Sharpe ratio above one, 1985 to 2009 | The authors' own published factor file (AQR original paper data) | Volatility 12.3%, Sharpe 1.38 on that file (test `test_volatility_is_the_papers_12_percent`). Confirmed. |
| Table 3: alpha 1.58% a month (t 7.99), UMD loading 0.28 | Same file, our regression (US market in place of MSCI World) | Loadings match within 0.03, but the alpha is 1.22% (t 6.13). Applying the paper's own printed loadings to this file's factor means implies an alpha of 1.20%, so the printed 1.58% is not consistent with this exact series; the table likely used a different vintage of the returns. Reported as a gap; see README. |
| Pooled regression t-statistics are large | Huang, D., Li, J., Wang, L., and Zhou, G. (2020). Time series momentum: Is it there? *Journal of Financial Economics* 135(3), 774 to 794 (RePEc record `RePEc:eee:jfinec:v:135:y:2020:i:3:p:774-794`, opened) | Abstract: asset by asset regressions show "little evidence" of TSM and the pooled t-statistic "is less than the critical values of parametric and nonparametric bootstraps". We test the asset by asset version on our data. |
| The alpha comes from time series predictability | Kim, A. Y., Tse, Y., and Wald, J. K. (2016). Time series momentum and volatility scaling. *Journal of Financial Markets* 30, 103 to 124 (RePEc record `RePEc:eee:finmar:v:30:y:2016:i:c:p:103-124`, opened) | Abstract: results are "largely driven by volatility-scaling"; without scaling, TSMOM and buy and hold have similar returns. We run the same decomposition. |
| Profits continued after the sample | AQR updated factor file, 2010 to May 2026 | Reported in the README out of sample section. |

## What could not be obtained

* The paper's 58 futures series (Bloomberg, Datastream and exchange data) are not public. We rebuild 23 public substitutes; see the README for each one and its gap.
* MSCI World excess returns before 1997 are not available from MSCI's public endpoint, so the market factor in every regression is the US market excess return from the French library. The Yahoo chart endpoint, which carries MSCI and country index history, rate limited every long history request during this build, so it is not used anywhere.
* The Barclays Aggregate and S&P GSCI indices used in Table 2 are licensed; Table 2 style regressions use our own passive bond and commodity portfolios instead.

## Data sources

| Source | Status |
| --- | --- |
| AQR Capital Management data sets (Moskowitz, Ooi and Pedersen) | Authors' data, downloaded at run time, not redistributed |
| Federal Reserve Board H.15 (Data Download Program) and H.10 historical rates | Official statistics |
| Deutsche Bundesbank, yields on listed Federal securities (Svensson method) | Official statistics |
| Ministry of Finance Japan, JGB constant maturity yields | Official statistics |
| US EIA, NYMEX futures prices contracts 1 and 2 (ended April 2024) | Official statistics |
| Kenneth R. French Data Library (monthly factors; daily US, Europe, Japan and Asia Pacific ex Japan market returns, files built from the 202609 CRSP and Bloomberg databases) | Academic data library |
