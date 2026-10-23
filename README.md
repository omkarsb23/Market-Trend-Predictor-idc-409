# IDC409 · Web Scraping I: Finance + News

Collect Indian share prices, gold, petrol/crude and currency data together with daily news headlines, store
everything in SQLite, explore it, and test — modestly and honestly — whether **news keywords help predict the
next trading day's Nifty 50 move**.

> **Read this first — what is real and what is demo.**
> The repository ships with a **synthetic demo dataset** (`data/demo/`, `outputs/demo/`) so that every script and
> notebook can be run and checked without internet. *Nothing in the demo outputs is a finding about real markets.*
> To get real results, run the collector once on a machine with internet (Quick start, step 3), then re-run the
> notebooks. They automatically switch to live data when `data/daily_clean.csv` exists, and every figure/table
> prints a `[SYNTHETIC DEMO DATA]` tag otherwise.

## Deliverables checklist

| Required | Where |
|---|---|
| Scraper / API collection script with clear source notes | `src/collect_prices.py`, `src/collect_news.py` (sources in docstrings + table below), driver `run_pipeline.py` |
| SQLite database | `data/finance_news.db` (live) · `data/demo/finance_news.db` (demo) — tables `prices`, `news`, `news_fetch_log`, `daily`, `meta` |
| Cleaned CSV export | `data/daily_clean.csv` (live) · `data/demo/daily_clean.csv` (demo) |
| EDA notebook | `notebooks/01_eda.ipynb` |
| Model notebook | `notebooks/02_models.ipynb` |
| GitHub with setup instructions + sample output | this README · `outputs/demo/*.png|csv` |
| numpy/pandas storage; DB read/write/modify | `src/db.py` (upsert, insert, update, delete, read) — demonstrated live in EDA §1 |
| Feature understanding & reduction | EDA §7 (correlation pairs, PCA) · model notebook §5 (permutation importance, top-k, PCA) |
| Models + metrics | Linear/Ridge/Tree/RandomForest/SVR; Logistic/Tree/RandomForest/SVM · MAE, RMSE, R², F1, confusion matrix |
| Time-based split + naive baseline | 80/20 chronological split with 1-day gap; "tomorrow = today", majority and persistence baselines; walk-forward check |

## Quick start

```bash
git clone <your-repo-url> && cd idc409-finance-news
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 1) Offline smoke test with synthetic data (no internet, ~3 s)
python run_pipeline.py --demo
python tests/test_pipeline.py                            # 8 offline tests

# 2) Real data (needs internet; prices ~1 min, news ~15-30 min for a year, resumable)
python run_pipeline.py                                   # 2 yrs prices + 365 days news
python run_pipeline.py --news-days 120 --delay 0.7       # quicker, shorter news history
python run_pipeline.py --steps build                     # rebuild features/CSV from what is already stored

# 3) Open the notebooks and "Run All"
jupyter lab notebooks/
```

If a news run stops (network/rate limit), just run it again — finished days are skipped.
Optional keys (environment variables, never commit them): `ALPHAVANTAGE_KEY`, `NEWSAPI_KEY`.
Optional better sentiment: `pip install vaderSentiment` and `export SENTIMENT_BACKEND=vader`.

## Data sources

| Data | Source | Notes |
|---|---|---|
| Nifty 50 (`^NSEI`), Sensex (`^BSESN`), Reliance, TCS, HDFC Bank, Infosys | **yfinance** — <https://ranaroussi.github.io/yfinance/> | Unofficial Yahoo Finance wrapper; daily OHLCV, `auto_adjust=False` |
| Gold | yfinance `GC=F` (COMEX gold futures, USD/oz) | |
| Petrol | yfinance `RB=F` (RBOB gasoline futures) + `BZ=F` (Brent crude) | There is no free daily *Indian pump-price* series, so futures are used as the petrol proxy |
| Currency | yfinance `USDINR=X`, `EURINR=X` | **Alpha Vantage** `FX_DAILY` is the optional fallback — <https://www.alphavantage.co/> |
| News | **Google News RSS** search, one query per (day, topic): `.../rss/search?q=<query> after:<day> before:<day+1>` | No key needed; up to ~100 headlines per query-day; two topics: `market`, `macro` (see `config.NEWS_QUERIES`) |
| News (optional) | **NewsAPI** — <https://newsapi.org/> | Free plan reaches back only ~1 month, so it is only a top-up |

Please respect each provider's terms of use; this project is for coursework. Headlines are stored (title, source,
link) only to count keywords and score sentiment.

> **Verification status.** The sandbox this repo was built in could not reach Yahoo, Google News or Alpha Vantage.
> The *parsers* for Google RSS, NewsAPI and Alpha Vantage are unit-tested on sample payloads, and the whole
> pipeline is tested end-to-end on synthetic data, but the **live network calls (yfinance, RSS fetch) have not been
> run by me**. If a ticker returns nothing, the collector prints a warning and continues; check the symbol in
> `config.SYMBOLS`.

## Pipeline

```
yfinance ──► prices ─┐                         ┌─► daily_clean.csv
                     ├─► features.build_daily ─┤
Google RSS ─► news ──┘   (SQLite → pandas)     └─► daily table in SQLite
                                                   │
                                  01_eda.ipynb ◄───┤───► 02_models.ipynb
```

`daily` has one row per NSE trading day: price/technical features, cross-asset returns, news volume, mean
sentiment, per-keyword counts (`kw_*`) and rates (`kwr_*`, share of that day's headlines), and the targets
(`target_ret` %, `target_dir`, `next_abs_ret`, `next_close`).

### Leakage rules (why the evaluation can be trusted)

* Row *t* represents what is known **before the next NSE open**. Targets always look one trading day ahead.
* Gold / petrol / FX are joined *as-of*: latest close dated ≤ *t*. Their returns are computed over the same
  window as the Nifty return, so holidays give 0, not a stale double count.
* Headlines are assigned to the first trading day ≥ their date (Saturday news → Monday's row, never Friday's).
* Train/test split is chronological with a 1-day gap; scalers and hyper-parameter search live inside
  `Pipeline` + `TimeSeriesSplit` on the training period only; the High/Low threshold is the *training* median.
* These rules are asserted in `tests/test_pipeline.py` (e.g. corrupting all future prices leaves row-*t* features unchanged).

## Modelling summary

* **Regression** of next-day return (%), with implied next-day price — Linear, Ridge, Decision Tree, Random Forest, SVR.
  Metrics: MAE, RMSE, R². R² on *price* is ≈ 1 for everything (tomorrow ≈ today), so judge skill on return metrics and
  on MAE versus the **naive "tomorrow = today"** baseline.
* **Classification** — Up/Down and High/Low move — Logistic, Decision Tree, Random Forest, SVM. Metrics: accuracy, F1
  (class and macro), confusion matrix; baselines: majority class and persistence; binomial test vs. majority accuracy,
  **Bonferroni-corrected** for the number of models tried.
* **Robustness**: 5-fold walk-forward validation, plus an **ablation** (tech → +cross-asset → +news → news only).
* The final cell prints an automatic verdict from these numbers — it only claims skill if the model beats the
  baselines on the hold-out *and* walk-forward *and* survives the multiple-testing correction.

## Sample output (SYNTHETIC demo data)

Generated by `python run_pipeline.py --demo` + `python tools/build_notebooks.py demo`:
`outputs/demo/*.png` (trends, moving averages, return distribution, keyword frequency, news-vs-return
correlations, PCA, confusion matrices, ablation, feature importance) and `outputs/demo/*.csv` (metrics tables).
The demo generator makes news react to *the same day's* market moves and plants **no** next-day signal, so the
expected — and observed — verdict is "no reliable skill". That is the pipeline behaving correctly, not a result.

## What to write in your report once you have live data

1. Same-day vs next-day news correlations (EDA §6): news usually *describes* the day; does it *predict* the next?
2. Whether any model beats "tomorrow = today" and the majority baseline (model notebook §1–2, §6).
3. Whether adding news features improves walk-forward scores (§4) — report it even if the answer is "no".
4. Limitations: ~1 year of daily data ⇒ ~100 test days ⇒ wide uncertainty; lexicon sentiment is crude; Google News
   queries are a biased sample; many hypotheses tested ⇒ some "hits" occur by chance; not trading advice.

## Repo layout

```
config.py            symbols, news queries, keyword regexes, paths
run_pipeline.py      collect → store → features → CSV  (--demo for offline synthetic data)
src/                 db.py · collect_prices.py · collect_news.py · sentiment.py · features.py · demo_data.py
notebooks/           01_eda.ipynb · 02_models.ipynb   (shipped with executed demo outputs)
data/                finance_news.db, daily_clean.csv (live, after you run) · demo/ (synthetic)
outputs/             figures + metrics CSVs (live) · demo/ (synthetic)
tests/               offline tests
tools/               regenerates the notebooks with outputs (developer helper)
```

## Push to GitHub

```bash
git remote add origin https://github.com/<you>/idc409-finance-news.git
git push -u origin main
```
