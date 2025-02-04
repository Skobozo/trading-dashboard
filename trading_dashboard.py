import streamlit as st
import logging
import yfinance as yf
import pandas as pd
import numpy as np
import ta  # Technische Analyse Indikatoren
import requests
from textblob import TextBlob
import time

import streamlit as st
import logging

# Debugging aktivieren
logging.basicConfig(level=logging.DEBUG)

st.title("📊 KI Trading-Signale")
st.write("🚀 Debug-Modus aktiv!")

st.write("Prüfung: Wird dieser Text angezeigt?")
try:
    st.write("Streamlit läuft ohne Fehler! ✅")
except Exception as e:
    st.error(f"Fehler: {e}")


# === KONFIGURATION ===
ASSETS = {
    "EUR/USD": "EURUSD=X",
    "Gold": "GC=F",
    "Öl": "CL=F"
}
NEWS_API_KEY = "0d90c5634d7c448cbb72ca63a0c2d5ab"  # Dein API Key
REFRESH_TIME = 60  # Aktualisierung alle 60 Sekunden

# === FUNKTIONEN ===
@st.cache_data
def get_market_data(asset, period="3mo", interval="1d"):
    """ Holt historische Marktdaten und berechnet RSI & MACD. """
    df = yf.download(asset, period=period, interval=interval)
    if df.empty:
        return None
    df["RSI"] = ta.momentum.RSIIndicator(df["Close"]).rsi()
    df["MACD"] = ta.trend.MACD(df["Close"]).macd()
    df.dropna(inplace=True)
    return df

def get_news_sentiment(query, api_key):
    """ Holt aktuelle Finanznachrichten und analysiert das Sentiment. """
    url = f"https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt&apiKey={api_key}"
    response = requests.get(url).json()
    
    if "articles" not in response or not response["articles"]:
        return 0  # Falls keine Daten verfügbar

    sentiments = [TextBlob(article["title"]).sentiment.polarity for article in response["articles"][:5]]
    return np.mean(sentiments) if sentiments else 0

def generate_signal(df, sentiment_score):
    """ Erzeugt ein Trading-Signal basierend auf RSI, MACD und Sentiment-Analyse. """
    if df is None or df.empty:
        return "⚠️ Keine Daten", None

    last_row = df.iloc[-1]
    signal = "🔍 Halten"

    if last_row["RSI"] < 30 and last_row["MACD"] > 0 and sentiment_score > 0:
        signal = "📈 KAUFEN"
    elif last_row["RSI"] > 70 and last_row["MACD"] < 0 and sentiment_score < 0:
        signal = "📉 VERKAUFEN"
    
    return signal, last_row["Close"]

# === STREAMLIT DASHBOARD ===
st.set_page_config(page_title="Trading Dashboard", layout="wide")
st.title("📊 KI Trading-Signale für Forex, Gold & Öl")
st.write("Willkommen zu deinem Trading-Dashboard!")
st.set_page_config(page_title="KI Trading-Signale", page_icon="📊", layout="wide")

selected_asset = st.selectbox("Wähle ein Asset", list(ASSETS.keys()))
asset_symbol = ASSETS[selected_asset]

# Daten abrufen
df = get_market_data(asset_symbol)
sentiment_score = get_news_sentiment(selected_asset, NEWS_API_KEY)
signal, last_price = generate_signal(df, sentiment_score)

# === ERGEBNISSE ANZEIGEN ===
col1, col2 = st.columns(2)

with col1:
    st.subheader(f"{selected_asset} - Letzter Preis: {last_price:.2f} USD" if last_price else "Keine Daten verfügbar")
    st.metric(label="📌 Trading-Signal", value=signal)
    st.metric(label="📰 News Sentiment", value=round(sentiment_score, 2))

with col2:
    st.subheader("📈 Preisentwicklung")
    if df is not None:
        st.line_chart(df["Close"])
    else:
        st.error("⚠️ Keine Marktdaten verfügbar.")

# Automatische Aktualisierung
st.info(f"Die Daten werden alle {REFRESH_TIME} Sekunden aktualisiert.")
time.sleep(REFRESH_TIME)
st.experimental_rerun()
