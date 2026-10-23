#!/usr/bin/env python3
"""One-command pipeline: collect -> store (SQLite) -> engineer features -> export cleaned CSV.

  python run_pipeline.py --demo                 # offline, SYNTHETIC data (tests the whole pipeline)
  python run_pipeline.py                        # live: 2 years of prices + 365 days of news
  python run_pipeline.py --steps prices,build   # only some stages
  python run_pipeline.py --news-days 120        # shorter news history (faster)
"""
from __future__ import annotations

import argparse

import config
from src import db, features


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--demo", action="store_true", help="use synthetic offline data (no internet)")
    ap.add_argument("--steps", default="prices,news,build", help="comma list of: prices,news,build")
    ap.add_argument("--years", type=float, default=2.0, help="years of price history (live)")
    ap.add_argument("--news-days", type=int, default=365, help="days of news history (live)")
    ap.add_argument("--delay", type=float, default=1.0, help="seconds between news requests")
    a = ap.parse_args()

    paths = config.get_paths("demo" if a.demo else "live")
    if a.demo and paths["db"].exists():
        paths["db"].unlink()                      # demo data is regenerated from scratch every run
    conn = db.connect(paths["db"])
    steps = set(a.steps.split(","))
    print(f"mode={paths['mode']}  db={paths['db']}")

    if a.demo:
        from src import demo_data
        print("[demo] generating SYNTHETIC prices + headlines (not real data!)")
        demo_data.populate(conn)
    else:
        if "prices" in steps:
            from src import collect_prices
            print("[1/3] prices (yfinance)")
            collect_prices.collect_prices(conn, years=a.years)
            db.set_meta(conn, "data_source", "live")
        if "news" in steps:
            from src import collect_news
            print("[2/3] news (Google News RSS)")
            n = collect_news.collect_news(conn, days=a.news_days, delay=a.delay)
            print(f"  {n} new headlines stored")

    if "build" in steps or a.demo:
        print("[3/3] features + export")
        features.build_and_export(conn, paths["csv"], paths["out"] / "cleaning_report.txt")
        print(f"  cleaned CSV  -> {paths['csv']}")
    print("tables:", {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                      for t in ("prices", "news", "news_fetch_log", "daily")
                      if conn.execute("SELECT 1 FROM sqlite_master WHERE name=?", (t,)).fetchone()})
    conn.close()


if __name__ == "__main__":
    main()
