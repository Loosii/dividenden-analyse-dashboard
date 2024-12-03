import yfinance as yf
import pandas as pd

def fetch_stock_data(ticker, start_date, end_date):
    stock = yf.Ticker(ticker)
    extended_history = stock.history(start=start_date, end=end_date)
    dividends = stock.dividends
    extended_history.index = extended_history.index.tz_localize(None)
    dividends.index = dividends.index.tz_localize(None)  # Dividendenindex ebenfalls tz-naive machen
    return extended_history, dividends

def calculate_dividend_yield(extended_history, dividends):
    if dividends.empty:
        return extended_history.assign(Dividenden_12M=0, Dividendenrendite=0)

    dividenden_12m = []
    for date in extended_history.index:
        last_12_months = dividends[(dividends.index > date - pd.DateOffset(months=12)) & (dividends.index <= date)]
        dividenden_12m.append(last_12_months.sum())
    extended_history['Dividenden_12M'] = dividenden_12m
    extended_history['Dividendenrendite'] = (extended_history['Dividenden_12M'] / extended_history['Close']) * 100
    extended_history['Dividendenrendite'] = extended_history['Dividendenrendite'].replace(0, float('nan'))
    
    return extended_history
