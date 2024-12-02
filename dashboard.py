import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import smtplib
from email.mime.text import MIMEText

def send_email(to_email, subject, body):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    from_email = "philipploos@gmail.com"  # Deine E-Mail
    from_password = "iiqy ocxl byag smnt"  # Dein E-Mail-Passwort

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(from_email, from_password)
        server.sendmail(from_email, to_email, msg.as_string())

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
if "alerts" not in st.session_state:
    st.session_state["alerts"] = []

if st.sidebar.button("Alarm speichern"):
    st.session_state["alerts"].append({
        "threshold": alert_threshold,
        "email": email_address
    })
    st.success(f"Alarm bei Dividendenrendite > {alert_threshold}% für {email_address} gespeichert!")

# Zeitraum korrekt interpretieren
time_period_years = int(time_period[:-1])  # Entferne das "y" und wandle in eine Zahl um
start_date = pd.Timestamp.today() - pd.DateOffset(years=time_period_years)  # Startdatum berechnen
extended_start_date = start_date - pd.DateOffset(years=1)  # 1 Jahr vor dem Startdatum

# Abrufen des erweiterten Zeitraums
stock = yf.Ticker(ticker)
extended_history = stock.history(start=extended_start_date, end=pd.Timestamp.today())
dividends = stock.dividends

# Debugging: Verfügbarkeit der Daten prüfen
# st.write("### Verfügbarkeit der Kursdaten:")
# st.write(extended_history)

# st.write("### Verfügbarkeit der Dividenden-Daten:")
# st.write(dividends)

# Sicherstellen, dass der Index ein tz-naive DatetimeIndex ist
extended_history.index = extended_history.index.tz_localize(None)
dividends.index = dividends.index.tz_localize(None)  # Dividendenindex ebenfalls tz-naive machen

# Fallback für fehlende Dividenden-Daten
if dividends.empty:
    st.warning("Keine Dividenden-Daten verfügbar. Dividendenrendite wird auf 0 gesetzt.")
    extended_history['Dividenden_12M'] = 0
    extended_history['Dividendenrendite'] = 0
else:
    dividenden_12m = []
    for date in extended_history.index:
        date = date.tz_localize(None)  # Konvertiere den aktuellen Index-Wert zu tz-naive
        last_12_months = dividends[(dividends.index > date - pd.DateOffset(months=12)) & (dividends.index <= date)]
        dividenden_12m.append(last_12_months.sum())
    extended_history['Dividenden_12M'] = dividenden_12m
    extended_history['Dividendenrendite'] = (extended_history['Dividenden_12M'] / extended_history['Close']) * 100
    extended_history['Dividendenrendite'] = extended_history['Dividendenrendite'].replace(0, float('nan'))

# Filter für den sichtbaren Zeitraum
history = extended_history.loc[start_date:]

# Sicherstellen, dass es Daten im sichtbaren Zeitraum gibt
if history.empty:
    st.error("Keine Daten im ausgewählten Zeitraum verfügbar. Bitte wählen Sie einen anderen Zeitraum aus.")
else:
    # Gleitender Mittelwert für Dividendenrendite
    smoothing_window = st.sidebar.slider("Glättungsfenster (in Tagen)", min_value=5, max_value=90, value=30)
    history = history.copy()  # Explizite Kopie erstellen
    history['Dividendenrendite_geglättet'] = history['Dividendenrendite'].rolling(window=smoothing_window, min_periods=1).mean()

# Signalberechnung
    average_yield = history['Dividendenrendite'].mean()
    if not history['Dividendenrendite'].dropna().empty:
        current_yield = history['Dividendenrendite'].iloc[-1]  # Aktuelle Rendite
        if current_yield > average_yield * 1.2:
            signal = "Kaufen"
        elif current_yield < average_yield * 0.8:
            signal = "Verkaufen"
        else:
            signal = "Halten"
    else:
        current_yield = None
        signal = "Keine Daten"

    # Signalberechnung und Alarme
average_yield = history['Dividendenrendite'].mean()
if not history['Dividendenrendite'].dropna().empty:
    current_yield = history['Dividendenrendite'].iloc[-1]  # Aktuelle Rendite

    # Alarm überprüfen und E-Mail senden
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


# Anzeige des Signals
    st.subheader("Investitionssignal")
    if signal == "Kaufen":
        st.markdown(f'<h3 style="color:green;">Signal: {signal}</h3>', unsafe_allow_html=True)
    elif signal == "Verkaufen":
        st.markdown(f'<h3 style="color:red;">Signal: {signal}</h3>', unsafe_allow_html=True)
    elif signal == "Halten":
        st.markdown(f'<h3 style="color:orange;">Signal: {signal}</h3>', unsafe_allow_html=True)
    else:
        st.markdown(f'<h3 style="color:gray;">Signal: {signal}</h3>', unsafe_allow_html=True)

    # Diagramm erstellen
    st.subheader(f"Kursverlauf und geglättete Dividendenrendite von {ticker.upper()}")
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Kursverlauf
    ax1.plot(history.index, history['Close'], label="Kursverlauf", color="blue")
    ax1.set_ylabel("Kurs ($)", color="blue")
    ax1.tick_params(axis="y", labelcolor="blue")

    # Zweite Achse für geglättete Dividendenrendite
    ax2 = ax1.twinx()
    ax2.plot(history.index, history['Dividendenrendite_geglättet'], label="Geglättete Dividendenrendite", color="green", linestyle="--")
    ax2.set_ylabel("Dividendenrendite (%)", color="green")
    ax2.tick_params(axis="y", labelcolor="green")

    # Waagrechte Linien für Kauf- und Verkaufssignale
    buy_threshold = average_yield * 1.2  # Kaufsignal-Schwelle
    sell_threshold = average_yield * 0.8  # Verkaufssignal-Schwelle
    ax2.axhline(y=buy_threshold, color="green", linestyle="-", linewidth=2, label="Kaufen-Schwelle")
    ax2.axhline(y=sell_threshold, color="red", linestyle="-", linewidth=2, label="Verkaufen-Schwelle")

    # Legende hinzufügen
    ax2.legend(loc="upper left")

    # Legenden und Titel
    fig.tight_layout()
    ax1.set_title(f"{ticker.upper()} Kurs und Dividendenrendite mit Signalen")
    st.pyplot(fig)

    # Statistiken anzeigen
    st.subheader("Statistische Analyse")
    st.write(f"**Durchschnittliche Dividendenrendite:** {average_yield:.2f}%")
    if current_yield is not None:
        st.write(f"**Aktuelle Dividendenrendite:** {current_yield:.2f}%")
    st.write(f"**Minimale Dividendenrendite:** {history['Dividendenrendite'].min():.2f}%")
    st.write(f"**Maximale Dividendenrendite:** {history['Dividendenrendite'].max():.2f}%")





