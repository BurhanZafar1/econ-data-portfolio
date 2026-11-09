# Can a neural network call the S&P 500's next month? A replication

**For:** a portfolio manager deciding whether a published "LSTM predicts the market" result is worth building on.

**What was tested.** A 2019 Stanford CS230 student project trained LSTM neural networks and logistic regressions to predict whether the S&P 500 will be up over the next 21 trading days, using past returns, volatility and trading volume. It reported test accuracies of 60% to 66%.

**What we found.**

1. **The paper's numbers reproduce.** The logistic baselines match the paper's table to the reported digit (after uncovering two hidden details in the original code), and the LSTMs land in the same range.
2. **The accuracy is the market's drift, not a forecast.** The market rose in 64% of the test months. That is what "always predict up" scores, and it is what the models score: the original LSTMs predict "up" on 84% to 100% of days.
3. **There is no reliable ranking skill.** For every one of the 7 models, the 95% interval for test AUC (the chance the model ranks an up month above a down month) includes 0.5, which is a coin flip. This holds for the paper's own test period (Apr 2015 to Jan 2019) and for seven new years it never saw (Mar 2019 to Oct 2026).
4. **The validation scheme flatters the models.** Each label covers the next 21 days, so the original validation lets training labels overlap the validation period. Removing that overlap lowers validation accuracy for 6 of the 7 baselines.
5. **On new data, every model fails to beat "always up"** (68% in 2019 to 2026). Four of the seven LSTMs (scaled inputs) flip to predicting "down" on most days and fall to 39% to 48% accuracy.

**Bottom line.** This feature set does not forecast the monthly direction of the S&P 500. The paper's own conclusion (AUC near 0.5) was right; its accuracy figures should not be read as skill. Anything built on this needs features with real information, a purged validation design, and an always-up benchmark in every table.
