# How the paper was authenticated (checked 8 Nov 2026)

| Check | Evidence | Result |
| --- | --- | --- |
| Listed by the course | Stanford CS230 past projects list (cs230-stanford/website-2019-fall, past-projects.md): "Predicting stock prices with LSTM networks", David Manuel Duemig, Winter 2019, report 15624789 | Match |
| Hosted report | cs230.stanford.edu/projects_winter_2019/reports/15624789.pdf, opened in a browser: a 6 page scanned PDF whose Table 1 has the same 42 numbers as the text PDF in the author's repository | Match |
| Author's code | github.com/duemig/Stanford-Project-Predicting-stock-prices-using-a-LSTM-Network: notebook outputs (row counts, label shares, hyperparameters, accuracies) agree with Table 1 | Match |
| Report metadata | Text PDF created 21 Mar 2019, the end of Stanford's Winter 2019 quarter | Consistent |
| Peer review | Course project report; not published in a journal or conference | Not peer reviewed |

Discrepancies found while replicating, all explained in the README: the data window is one trading day earlier than the dates the code requests; the validation uses 8 folds, not the 9 the code appears to intend; the report's reference list numbers two papers in the wrong order relative to the text.
