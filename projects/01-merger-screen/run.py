"""Run the full merger screen: python run.py [--shares FILE --mergers FILE]."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402

from merger_screen.data import load_inputs  # noqa: E402
from merger_screen.report import (  # noqa: E402
    plot_guppi_by_margin,
    plot_hhi_screen,
    screen_table_markdown,
    write_summary,
)
from merger_screen.screen import compare_with_court, diversion_screen, screen_all  # noqa: E402

EFFICIENCY_CREDIT = 0.10  # Farrell and Shapiro's illustrative standard deduction
MARGINS = (0.3, 0.5, 0.7)  # assumed margins for the diversion table
SUMMARY_MARGIN = 0.5  # margin quoted in the manager summary (must be in MARGINS)
DEFAULT_SHARES = ROOT / "data" / "market_shares.csv"
DEFAULT_OUT = ROOT / "output"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shares", type=Path, default=DEFAULT_SHARES)
    parser.add_argument("--mergers", type=Path, default=ROOT / "data" / "mergers.csv")
    parser.add_argument("--court", type=Path, default=ROOT / "data" / "court_reported.csv")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    shares, mergers = load_inputs(args.shares, args.mergers)

    screen = screen_all(shares, mergers)
    diversion = diversion_screen(shares, mergers, MARGINS, efficiency_credit=EFFICIENCY_CREDIT)
    screen.round(2).to_csv(args.out / "screen_results.csv", index=False)
    diversion.round(4).to_csv(args.out / "diversion_screen.csv", index=False)
    (args.out / "screen_results.md").write_text(screen_table_markdown(screen), encoding="utf-8")
    plot_hhi_screen(screen, args.out / "hhi_screen.png")
    plot_guppi_by_margin(shares, mergers, EFFICIENCY_CREDIT, args.out / "guppi_by_margin.png")

    # The court check and the manager summary describe the bundled court data only.
    using_default_data = args.shares.resolve() == DEFAULT_SHARES.resolve()
    if using_default_data and args.court.exists():
        court = compare_with_court(screen, pd.read_csv(args.court))
        court.round(2).to_csv(args.out / "court_check.csv", index=False)
        # Only the default run refreshes the committed report; other runs keep it with their outputs.
        report_dir = ROOT / "report" if args.out.resolve() == DEFAULT_OUT.resolve() else args.out
        write_summary(screen, court, diversion, report_dir / "summary.md", SUMMARY_MARGIN, EFFICIENCY_CREDIT)
        print("Computed vs court reported figures:")
        print(court.drop(columns="citation").round(1).to_string(index=False))

    print("\nScreen results:")
    print(screen_table_markdown(screen))
    print(f"Outputs written to {args.out}")


if __name__ == "__main__":
    main()
