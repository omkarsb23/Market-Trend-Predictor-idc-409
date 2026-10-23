"""Central configuration: what to collect, where to store it, which keywords to count."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "outputs"

# ---------------------------------------------------------------------------
# Market data. name -> (Yahoo Finance ticker, category, note)
# `name` is the short column prefix used everywhere downstream.
# ---------------------------------------------------------------------------
SYMBOLS = {
    "NSEI":     ("^NSEI",      "index",     "Nifty 50 index  (PREDICTION TARGET)"),
    "BSESN":    ("^BSESN",     "index",     "BSE Sensex index"),
    "RELIANCE": ("RELIANCE.NS", "share",    "Reliance Industries, NSE"),
    "TCS":      ("TCS.NS",      "share",    "Tata Consultancy Services, NSE"),
    "HDFCBANK": ("HDFCBANK.NS", "share",    "HDFC Bank, NSE"),
    "INFY":     ("INFY.NS",     "share",    "Infosys, NSE"),
    "GOLD":     ("GC=F",        "gold",     "COMEX gold futures, USD/oz"),
    "PETROL":   ("RB=F",        "petrol",   "NYMEX RBOB gasoline futures, USD/gal (petrol proxy)"),
    "BRENT":    ("BZ=F",        "petrol",   "Brent crude futures, USD/bbl"),
    "USDINR":   ("USDINR=X",    "currency", "US Dollar -> Indian Rupee"),
    "EURINR":   ("EURINR=X",    "currency", "Euro -> Indian Rupee"),
}
TARGET = "NSEI"          # asset whose next-day move we try to predict
MACRO = ["GOLD", "PETROL", "BRENT", "USDINR", "EURINR"]
PEERS = ["BSESN", "RELIANCE", "TCS", "HDFCBANK", "INFY"]

# ---------------------------------------------------------------------------
# News. One Google-News-RSS query per (day, query); headlines are then scanned
# for the keywords below.
# ---------------------------------------------------------------------------
NEWS_QUERIES = {
    "market": "Sensex OR Nifty OR \"stock market\" India",
    "macro": "RBI OR inflation OR \"crude oil\" OR gold OR rupee OR tariff OR budget India",
}

# keyword name -> regex (case-insensitive) matched against each headline
KEYWORDS = {
    "rbi":       r"\brbi\b|reserve bank",
    "inflation": r"inflation|\bcpi\b|\bwpi\b|price rise",
    "rates":     r"repo rate|interest rate|rate cut|rate hike|\bmpc\b",
    "crude":     r"crude|\bbrent\b|opec",
    "petrol":    r"petrol|diesel|\bfuel\b",
    "gold":      r"\bgold\b|bullion",
    "rupee":     r"rupee|\binr\b",
    "dollar":    r"dollar|\busd\b",
    "fed":       r"\bfed\b|federal reserve|powell",
    "tariff":    r"tariff|trade war|trade deal|\btrump\b",
    "budget":    r"budget|fiscal",
    "election":  r"election|\bpolls?\b",
    "war":       r"\bwar\b|conflict|geopolit|ukraine|gaza|israel|\biran\b",
    "ipo":       r"\bipo\b",
    "earnings":  r"earnings|quarterly|\bq[1-4]\b|results",
    "profit":    r"profit",
    "loss":      r"\bloss\b|losses",
    "rally":     r"rally|surge|soar|jump|record high|\bgains?\b",
    "crash":     r"crash|plunge|tumble|sell-?off|slump|slide|\bfalls?\b|\bdrops?\b|sink",
    "fii":       r"\bfii\b|\bfpi\b|foreign investor|foreign portfolio",
    "gdp":       r"\bgdp\b|economic growth",
    "recession": r"recession|slowdown",
    "banks":     r"\bbanks?\b|banking",
    "it_sector": r"\bit stocks\b|infosys|\btcs\b|wipro|software",
}

# ---------------------------------------------------------------------------
# Paths. "live" = real collected data, "demo" = synthetic offline data.
# ---------------------------------------------------------------------------

def get_paths(mode: str) -> dict:
    if mode not in ("live", "demo"):
        raise ValueError("mode must be 'live' or 'demo'")
    d = DATA_DIR if mode == "live" else DATA_DIR / "demo"
    o = OUT_DIR if mode == "live" else OUT_DIR / "demo"
    d.mkdir(parents=True, exist_ok=True)
    o.mkdir(parents=True, exist_ok=True)
    return {"mode": mode, "db": d / "finance_news.db", "csv": d / "daily_clean.csv", "out": o}


def resolve_mode() -> str:
    """Notebooks call this. IDC409_MODE=live|demo forces a mode; otherwise use
    live data if it has been collected, else fall back to the bundled demo data."""
    forced = os.environ.get("IDC409_MODE", "").lower()
    if forced in ("live", "demo"):
        return forced
    return "live" if get_paths("live")["csv"].exists() else "demo"


# Optional API keys (read from environment, never hard-coded)
ALPHAVANTAGE_KEY = os.environ.get("ALPHAVANTAGE_KEY", "")
NEWSAPI_KEY = os.environ.get("NEWSAPI_KEY", "")
