# Market-Trend-Predictor-idc-409
Python pipeline that pairs financial market prices with news headline sentiment analysis. It stores structured daily records in an SQLite database and trains machine learning models to forecast next-day market
What it does:
Gathers Market Data: Scrapes stock, gold, oil, and currency prices using yfinance.

Analyzes News: Pulls financial headlines and calculates daily sentiment scores with NLTK.

Stores Everything: Keeps organized records in a local SQLite database.

Predicts Directions: Runs ML models (Random Forest, SVM) to guess next-day UP/DOWN movements.
