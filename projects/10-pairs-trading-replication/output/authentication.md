# Authentication of the paper and the claims checked

Checked 9 to 10 November 2026.

## The paper

| Item | Evidence | Result |
| --- | --- | --- |
| Bibliographic record | RePEc / EconPapers record `RePEc:oup:rfinst:v:19:y:2006:i:3:p:797-827` ([link](https://econpapers.repec.org/RePEc:oup:rfinst:v:19:y:2006:i:3:p:797-827)) | Title "Pairs Trading: Performance of a Relative-Value Arbitrage Rule"; Evan Gatev, William N. Goetzmann, K. Geert Rouwenhorst; *Review of Financial Studies* 19(3), 797 to 827, 2006; DOI 10.1093/rfs/hhj020. Matches the citation. |
| Article text | University of Pennsylvania (Wharton) course copy of the published article ([link](http://stat.wharton.upenn.edu/~steele/Courses/434/434Context/PairsTrading/PairsTradingGGR.pdf)) | Header "The Review of Financial Studies v 19 n 3 2006", "doi:10.1093/rfs/hhj020, Advance Access publication February 13, 2006". Affiliations: Boston College (Gatev), Yale (Goetzmann, Rouwenhorst). |
| Earlier version | NBER Working Paper 7032, March 1999 ([link](https://www.nber.org/papers/w7032)) | Same authors. The 1999 abstract covers 1962 to 1997 and "up to 12 percent"; the 2006 article covers 1962 to 2002 and "up to 11%". All numbers used here come from the 2006 article. |
| Peer review | Published in the *Review of Financial Studies* (Society for Financial Studies) | **Peer reviewed journal article.** |

## Numbers taken from the paper (stored in `src/pairs/paper.py`)

Table 1 (p. 807, 474 months, July 1963 to December 2002) and Table 2 (p. 809), plus the transaction cost argument in section 3.3 (p. 810): the top 20 return falls from 1.44% to 0.90% a month when trades wait one day, which the authors read as 162 bp per pair per round trip.

## Independent checks of the paper's claims

| Claim | Independent source | Result |
| --- | --- | --- |
| Top 20 committed capital return with a one day wait is 0.52% a month | Zhu, X. (2024), "Examining Pairs Trading Profitability", Yale Economics senior essay, quotes "the 0.52% originally reported in Panel B of Table 1 in Gatev et al. (2006)" ([link](https://economics.yale.edu/sites/default/files/2024-05/Zhu_Pairs_Trading.pdf)) | Matches Table 1 Panel B (0.00520). |
| Profits fell after the sample | Zhu (2024) re-runs the rule on CRSP, January 2003 to December 2023: top 20 pairs 0.46% a month. Do, B. and Faff, R. (2010), "Does Simple Pairs Trading Still Work?", *Financial Analysts Journal* 66(4), 83 to 95, DOI 10.2469/faj.v66.n4.1 (record at [Strathprints](https://strathprints.strath.ac.uk/41067)); its abstract reports a continuing downward trend in profitability. | Consistent with the decline we find. The Do and Faff full text was not available to us, so we cite only its abstract. |
| Table 1 is internally consistent | Mean divided by Newey-West SE reproduces every printed t statistic within 0.05 (test `test_paper_table1_internally_consistent`) | Passes. |
| 162 bp implied round trip cost | (1.44% minus 0.90%) times 6 months divided by 2 round trips (test `test_paper_implied_cost_known_answer`) | Reproduced exactly. |

## What could not be verified or obtained

* The paper uses CRSP daily stock files, which are licensed. We could not reproduce the paper's own sample, so no Table 1 cell is reproduced from data; see the README for the substitutes and why each one differs.
* We could not read sections 3.4 onward of the article in full, so the README does not quote the paper's sub-period or industry tables.

## Data sources

| Source | Status |
| --- | --- |
| Kenneth R. French Data Library (Dartmouth), 49 industry portfolios daily and monthly factors, file built from the 202609 CRSP database | Official academic data library |
| Yahoo Finance chart endpoint, adjusted closes | Public, unofficial API; returns may be revised by the vendor |
| fja05680/sp500 on GitHub (MIT license), commit a2430f2, S&P 500 membership intervals | Community compilation, not an official S&P file; used only to define who was a member at each date |
