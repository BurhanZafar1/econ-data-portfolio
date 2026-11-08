# Paper replication queue

Status: TODO, IN PROGRESS, DONE (date), SKIP (reason). "Verified" means the official page was opened and title, authors, venue and date matched.

## Done

- DONE 2026-11-08: Duemig, D. (2019). Predicting stock prices with LSTM networks. Stanford CS230 course report (not peer reviewed). Verified on cs230.stanford.edu past projects list and the author's repository. Project 08.

## Queue (verify again at build time; build only what passes)

1. TODO. Gatev, E., Goetzmann, W. N., and Rouwenhorst, K. G. (2006). Pairs Trading: Performance of a Relative-Value Arbitrage Rule. Review of Financial Studies 19(3), 797 to 827. Peer reviewed. Public data substitute: liquid US stocks or sector ETFs; must avoid the look ahead in common tutorials (pairs chosen on the same window they are traded).
2. TODO. Moskowitz, T. J., Ooi, Y. H., and Pedersen, L. H. (2012). Time Series Momentum. Journal of Financial Economics 104(2), 228 to 250. Peer reviewed. Public futures or ETF proxies; volatility scaling; out of sample after 2009.
3. TODO. Avellaneda, M., and Stoikov, S. (2008). High-frequency trading in a limit order book. Quantitative Finance 8(3), 217 to 224. Peer reviewed. Theoretical: simulate the model and verify the closed form reservation price and spread.
4. TODO. Almgren, R., and Chriss, N. (2001). Optimal execution of portfolio transactions. Journal of Risk 3(2), 5 to 39. Peer reviewed. Closed form efficient frontier of execution; known answer tests from the paper.
5. TODO. Bailey, D. H., and Lopez de Prado, M. (2014). The Deflated Sharpe Ratio. Journal of Portfolio Management 40(5), 94 to 107. Peer reviewed. Tool for every later backtest.
6. TODO. Black Scholes pricing, Greeks and delta hedging P&L, following Haugh, M. (2016), The Black-Scholes Model, Columbia University IEOR E4706 lecture notes (verified as provided by Burhan); check against Hull, Options, Futures and Other Derivatives. Implied volatility surface from public option chains if reachable.
7. TODO. Kelly, B., and Xiu, D. (2023). Financial Machine Learning. Foundations and Trends in Finance 13(3-4); NBER Working Paper 31502; SSRN 4501707. Verified. Use as the methods reference; build a small Gu, Kelly and Xiu (2020, Review of Financial Studies 33(5)) style return prediction exercise on public data with proper out of sample evaluation.
8. TODO. Amaral, L. R. (2026). Optimal Trading of Microstructure Mean Reversion. arXiv 2608.00885 (q-fin.TR), preprint, single author, not peer reviewed. Verified on arXiv. Build only as a simulation that checks the paper's stated theorems; label as preprint.
9. TODO. Ledoit, O., and Wolf, M. (2004). Honey, I Shrunk the Sample Covariance Matrix. Journal of Portfolio Management 30(4), 110 to 119. Peer reviewed. Minimum variance portfolios with shrinkage versus sample covariance, out of sample.

## Reviewed and not built

- SKIP. Yartseva, A. (2025). The Alchemy of Multibagger Stocks. Birmingham City University CAFE Working Paper 33. Verified (BCU repository, RePEc). Needs survivorship free fundamentals (Compustat style); revisit if a free point in time source is found.
- SKIP. Huang, A. Y., and Fan, Z. (2026). Beyond Prompting: An Autonomous Framework for Systematic Factor Investing via Agentic AI. arXiv 2603.14288. Verified. Needs a paid language model API and point in time fundamentals.
- SKIP. Xiao, Y., Sun, E., Luo, D., and Wang, W. (2024). TradingAgents: Multi-Agents LLM Financial Trading Framework. arXiv 2412.20138. Verified. Needs a paid language model API; short backtest window.
- REFERENCE ONLY. Quant Bible, MIT Sloan Business Club (interview preparation guide, no named author). Sullivan, B. W. (2013), Everything You Always Wanted To Know About Mathematics, Carnegie Mellon University (Doctor of Arts thesis). Study material, not replication targets.
