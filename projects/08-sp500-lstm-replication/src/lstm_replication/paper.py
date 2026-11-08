"""Numbers reported in the original project, kept in one place for the comparison table.

Table 1 of the report (accuracies as fractions) and the notebook's printed outputs.
Source: report.pdf and Final Project.ipynb in github.com/duemig/Stanford-Project-Predicting-stock-prices-using-a-LSTM-Network,
checked against the copy hosted at cs230.stanford.edu/projects_winter_2019/reports/15624789.pdf.
"""

from __future__ import annotations

# model: (lstm_dev, lstm_test, base_dev, base_test, lstm_auc, base_auc)
TABLE1: dict[int, tuple[float, float, float, float, float, float]] = {
    1: (0.6102, 0.6438, 0.5448, 0.6501, 0.52, 0.52),
    2: (0.5562, 0.6501, 0.5544, 0.6607, 0.52, 0.54),
    3: (0.5649, 0.6512, 0.5521, 0.6395, 0.54, 0.48),
    4: (0.5442, 0.6332, 0.5206, 0.6004, 0.52, 0.54),
    5: (0.5934, 0.6596, 0.5552, 0.5909, 0.46, 0.53),
    6: (0.4956, 0.6385, 0.5419, 0.6554, 0.55, 0.55),
    7: (0.5313, 0.6554, 0.5228, 0.6617, 0.53, 0.50),
}

# Notebook outputs used as known answers in the tests.
RAW_ROWS = 9875
FEATURE_ROWS = 9454
TRAIN_UP_SHARE = 0.6243535496003761
TEST_UP_SHARE = 0.6437632135306554
