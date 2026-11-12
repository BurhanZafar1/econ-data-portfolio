"""Numbers reported in Moskowitz, Ooi and Pedersen (2012), Journal of Financial Economics 104(2).

Page numbers refer to the published article. Minus signs in the tables are read from the
article's text layer; see output/authentication.md.
"""

SAMPLE = ("1985-01", "2009-12")  # section 3 and 4 results use 1985 to 2009
N_INSTRUMENTS = 58  # 24 commodities, 12 currency pairs, 9 equity indices, 13 bond futures
TARGET_VOL = 0.40  # section 4.1, p. 237
FACTOR_VOL = 0.12  # "an annualized volatility of 12% per year over the sample period 1985-2009"
CENTER_OF_MASS_DAYS = 60  # section 2.4, eq. (1)

# Table 3 Panel A (p. 238): TSMOM on MSCI World (key MKT), SMB, HML, UMD
TABLE3_MONTHLY = {
    "coef": {"MKT": 0.09, "SMB": -0.05, "HML": -0.01, "UMD": 0.28, "const": 0.0158},
    "t": {"MKT": 1.89, "SMB": -0.84, "HML": -0.21, "UMD": 6.78, "const": 7.99},
    "r2": 0.14,
}
TABLE3_QUARTERLY = {
    "coef": {"MKT": 0.07, "SMB": -0.18, "HML": 0.01, "UMD": 0.32, "const": 0.0475},
    "t": {"MKT": 1.00, "SMB": -1.44, "HML": 0.11, "UMD": 4.44, "const": 7.73},
    "r2": 0.23,
}
# Table 3 Panel C, first row (quarterly): TSMOM on MSCI World and its square
TABLE3_STRADDLE = {"coef": {"MKT": -0.01, "MKT2": 1.99}, "t": {"MKT": -0.17, "MKT2": 3.88}}
# Table 2 Panel A (p. 235): t-statistic of the alpha, 12 month look back, 1 month holding
TABLE2_T_12_1 = 6.61
# Section 4.1 (p. 236): all 58 instruments have positive 12 month TSMOM returns, 52 significant at 5%
N_POSITIVE, N_SIGNIFICANT = 58, 52
