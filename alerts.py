import json

# Funktion: Alarme aus JSON-Datei laden
def load_alerts_from_file(filename="alerts.json"):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Funktion: Alarme in JSON-Datei speichern
def save_alerts_to_file(alerts, filename="alerts.json"):
    with open(filename, "w") as f:
        json.dump(alerts, f, indent=4)

# Funktion: Neue Alarme hinzufügen
def add_alert(threshold, email, alerts, filename="alerts.json"):
    alerts.append({"threshold": threshold, "email": email})
    save_alerts_to_file(alerts, filename)
    return alerts

# Funktion: Alarme prüfen
def check_alerts(current_yield, alerts):
    triggered_alerts = []
    for alert in alerts:
        if current_yield > alert["threshold"]:
            triggered_alerts.append(alert)
    return triggered_alerts
