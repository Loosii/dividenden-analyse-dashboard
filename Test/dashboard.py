import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from stock_data import fetch_stock_data, calculate_dividend_yield
from main_prod.alerts import load_alerts_from_file, add_alert, check_alerts
from email_utils import send_email

# Alarme laden
if "alerts" not in st.session_state:
    st.session_state["alerts"] = load_alerts_from_file()

# Streamlit-Konfiguration
st.title("Dividenden-Analyse-Dashboard")
st.sidebar.header("Einstellungen")

# Initiale Liste der Aktien (leere Liste)
if "stock_list" not in st.session_state:
    st.session_state["stock_list"] = ["AAPL"]  # Standardmäßig Apple hinzufügen

# Eingabefeld zum Hinzufügen eines neuen Tickers
new_ticker = st.sidebar.text_input("Neuen Aktien-Ticker hinzufügen", value="")
if st.sidebar.button("Ticker hinzufügen"):
    if new_ticker.upper() not in st.session_state["stock_list"]:
        st.session_state["stock_list"].append(new_ticker.upper())
        st.success(f"Ticker {new_ticker.upper()} hinzugefügt!")
    else:
        st.warning(f"Ticker {new_ticker.upper()} ist bereits in der Liste.")

# Auswahlliste für den Benutzer
if len(st.session_state["stock_list"]) > 0:
    ticker = st.sidebar.selectbox("Aktie auswählen", st.session_state["stock_list"])
    if st.sidebar.button("Ticker entfernen"):
        st.session_state["stock_list"].remove(ticker)
        st.success(f"Ticker {ticker} wurde aus der Liste entfernt.")
else:
    st.sidebar.warning("Die Aktienliste ist leer. Fügen Sie Aktien hinzu.")

# Zeitraum auswählen
time_period = st.sidebar.selectbox("Zeitraum auswählen", ["1y", "2y", "5y", "10y", "20y"], index=2)

# Alarm-Schwelle definieren
st.sidebar.header("Alarmeinstellungen")
alert_threshold = st.sidebar.number_input("Dividendenrendite-Alarm setzen (%)", min_value=0.0, max_value=100.0, step=0.1, value=5.0)
email_address = st.sidebar.text_input("E-Mail-Adresse für Benachrichtigungen")

# Alarme speichern
if st.sidebar.button("Alarm speichern"):
    st.session_state["alerts"] = add_alert(alert_threshold, email_address, st.session_state["alerts"])
    st.success(f"Alarm bei Dividendenrendite > {alert_threshold}% für {email_address} gespeichert!")

# Gespeicherte Alarme anzeigen
st.subheader("Gespeicherte Alarme")
for alert in st.session_state["alerts"]:
    st.write(f"Alarm: Dividendenrendite über {alert['threshold']}% | E-Mail: {alert['email']}")

# Zeitraum korrekt interpretieren
time_period_years = int(time_period[:-1])  # Entferne das "y" und wandle in eine Zahl um
start_date = pd.Timestamp.today() - pd.DateOffset(years=time_period_years)  # Startdatum berechnen
extended_start_date = start_date - pd.DateOffset(years=1)  # 1 Jahr vor dem Startdatum

# Abrufen des erweiterten Zeitraums
extended_history, dividends = fetch_stock_data(ticker, extended_start_date, pd.Timestamp.today())

# Berechnen der Dividendenrendite
history = calculate_dividend_yield(extended_history, dividends)

# Filter für den sichtbaren Zeitraum
history = history.loc[start_date:]

# Sicherheitsprüfung für `history`
if history is None or history.empty:
    st.error("Keine Daten im sichtbaren Zeitraum verfügbar.")
else:
    # Berechnung der geglätteten Dividendenrendite
    smoothing_window = st.sidebar.slider("Glättungsfenster (in Tagen)", min_value=5, max_value=90, value=30)
    history = history.copy()  # Create a copy of the DataFrame to avoid the warning
    history['Dividendenrendite_geglättet'] = history['Dividendenrendite'].rolling(window=smoothing_window, min_periods=1).mean()

    # Chart mit geglätteter Dividendenrendite
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax1.plot(history.index, history['Close'], label="Kursverlauf", color="blue")
    ax1.set_ylabel("Kurs ($)", color="blue")
    ax1.tick_params(axis="y", labelcolor="blue")

    ax2 = ax1.twinx()
    ax2.plot(history.index, history['Dividendenrendite_geglättet'], label="Geglättete Dividendenrendite", color="green", linestyle="--")
    ax2.set_ylabel("Dividendenrendite (%)", color="green")
    ax2.tick_params(axis="y", labelcolor="green")

    # Waagrechte Linien für Kauf- und Verkaufssignale
    average_yield = history['Dividendenrendite_geglättet'].mean()
    buy_threshold = average_yield * 1.2  # Kaufsignal-Schwelle
    sell_threshold = average_yield * 0.8  # Verkaufssignal-Schwelle
    ax2.axhline(y=buy_threshold, color="green", linestyle="-", linewidth=2, label="Kaufen-Schwelle")
    ax2.axhline(y=sell_threshold, color="red", linestyle="-", linewidth=2, label="Verkaufen-Schwelle")

    ax2.legend(loc="upper left")
    fig.tight_layout()
    st.pyplot(fig)

    # Signalberechnung und Alarme
    if not history['Dividendenrendite_geglättet'].dropna().empty:
        current_yield = history['Dividendenrendite_geglättet'].iloc[-1]  # Aktuelle Rendite

        for alert in st.session_state["alerts"]:
            if current_yield > alert["threshold"]:
                st.warning(f"Alarm: Dividendenrendite von {current_yield:.2f}% hat die Schwelle von {alert['threshold']}% überschritten.")
                try:
                    send_email(
                        alert["email"],
                        f"Dividendenalarm für {ticker.upper()}",
                        f"Die Dividendenrendite von {ticker.upper()} beträgt {current_yield:.2f}% und hat die Schwelle von {alert['threshold']}% überschritten."
                    )
                    st.info(f"Benachrichtigung an {alert['email']} gesendet.")
                except Exception as e:
                    st.error(f"Fehler beim Senden der E-Mail: {e}")

    # Statistiken anzeigen
    st.subheader("Statistische Analyse")
    st.write(f"**Durchschnittliche geglättete Dividendenrendite:** {average_yield:.2f}%")
    st.write(f"**Aktuelle geglättete Dividendenrendite:** {current_yield:.2f}%")
    st.write(f"**Minimale geglättete Dividendenrendite:** {history['Dividendenrendite_geglättet'].min():.2f}%")
    st.write(f"**Maximale geglättete Dividendenrendite:** {history['Dividendenrendite_geglättet'].max():.2f}%")
