"""Numbers printed in Gatev, Goetzmann and Rouwenhorst (2006), Review of Financial Studies 19(3).

Table 1 (p. 807): monthly excess returns of pairs portfolios, July 1963 to December 2002,
474 months; t statistics use Newey-West errors with six lags. Table 2 (p. 809): trading
statistics. Section 3.3 (p. 810): implied transaction cost. Values copied from the
published article; nothing here is computed.
"""

TABLE1 = {
    # panel: {portfolio: (fully invested mean, Newey-West SE, t, committed capital mean)}
    "no_wait": {
        "Top 5": (0.01308, 0.00148, 8.84, 0.00784),
        "Top 20": (0.01436, 0.00124, 11.56, 0.00805),
        "101-120": (0.01081, 0.00094, 11.54, 0.00679),
        "All": (0.01104, 0.00099, 11.16, 0.00614),
    },
    "wait_one_day": {
        "Top 5": (0.00745, 0.00119, 6.26, 0.00463),
        "Top 20": (0.00895, 0.00096, 9.29, 0.00520),
        "101-120": (0.00795, 0.00085, 9.40, 0.00503),
        "All": (0.00715, 0.00090, 7.92, 0.00396),
    },
}
TABLE2 = {
    # portfolio: (pairs traded per six months, round trips per pair, months open)
    "Top 5": (4.81, 2.02, 3.75),
    "Top 20": (19.30, 1.96, 3.76),
    "101-120": (19.41, 1.78, 3.98),
    "All": (1944.22, 1.62, 3.97),
}
N_MONTHS = 474
SAMPLE = ("1963-07", "2002-12")
IMPLIED_COST_BP_PER_ROUND_TRIP = 162  # section 3.3, from the top 20 drop of 1.44% to 0.90%


def implied_round_trip_cost(monthly_no_wait: float, monthly_wait: float, round_trips: float,
                            months: int = 6) -> float:
    """GGR's argument: the return lost by waiting a day over a six month period, divided by
    the number of round trips, is the bid ask cost of one round trip (as a fraction)."""
    return (monthly_no_wait - monthly_wait) * months / round_trips
