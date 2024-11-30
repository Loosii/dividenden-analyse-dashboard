import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# 1. Aktie auswählen
ticker = "JNJ"  # Beispiel: Apple
stock = yf.Ticker(ticker)

# 2. Historische Kursdaten (5 Jahre) abrufen
history = stock.history(period="5y")
dividends = stock.dividends

# Dividenden auffüllen
dividends_reindexed = dividends.reindex(history.index, method='ffill').fillna(0)

# Sicherstellen, dass vor der ersten Dividende auch ein sinnvolles Füllen erfolgt
first_dividend_date = dividends.first_valid_index()
if first_dividend_date:
    dividends_reindexed.loc[:first_dividend_date] = dividends[first_dividend_date]

# Dividenden-Daten in den Kurs-Datensatz einfügen
history['Dividenden'] = dividends_reindexed

# Dividendenrendite berechnen
history['Dividendenrendite'] = (history['Dividenden'] / history['Close']) * 100

# Überprüfen
print(history[['Close', 'Dividenden', 'Dividendenrendite']].head(10))


# 4. Daten anzeigen
print(history[['Close', 'Dividenden', 'Dividendenrendite']].tail())

# 5. Historische Analyse der Dividendenrendite
average_yield = history['Dividendenrendite'].mean()
min_yield = history['Dividendenrendite'].min()
max_yield = history['Dividendenrendite'].max()

print(f"Durchschnittliche Dividendenrendite: {average_yield:.2f}%")
print(f"Minimale Dividendenrendite: {min_yield:.2f}%")
print(f"Maximale Dividendenrendite: {max_yield:.2f}%")


# 6. Aktuelle Dividendenrendite
current_price = history['Close'].iloc[-1]
current_dividend = dividends.iloc[-1] if not dividends.empty else 0
current_yield = (current_dividend / current_price) * 100

# 6. Signal-Logik
if current_yield > average_yield * 1.2:
    signal = "Kaufen"
elif current_yield < average_yield * 0.8:
    signal = "Verkaufen"
else:
    signal = "Halten"

print(f"Aktuelle Dividendenrendite: {current_yield:.2f}%")
print(f"Signal: {signal}")

# Ersetze 0 durch NaN, damit leere Tage im Diagramm nicht als 0 erscheinen
history['Dividendenrendite'] = history['Dividendenrendite'].replace(0, float('nan'))

# Diagramm erstellen
plt.figure(figsize=(12, 6))
plt.plot(history.index, history['Close'], label="Kursverlauf", color="blue")
plt.plot(history.index, history['Dividendenrendite'], label="Dividendenrendite", color="green")
plt.title(f"{ticker.upper()} Kurs und Dividendenrendite")
plt.xlabel("Datum")
plt.ylabel("Werte")
plt.legend()
plt.show()



