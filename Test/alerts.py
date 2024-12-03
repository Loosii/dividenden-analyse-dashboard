import json

def load_alerts_from_file(filename="alerts.json"):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        with open(filename, "w") as f:
            json.dump([], f)  # Initialisiere die Datei, falls sie fehlt
        return []
    except json.JSONDecodeError:
        with open(filename, "w") as f:
            json.dump([], f)  # Zurücksetzen bei beschädigter Datei
        return []

def save_alerts_to_file(alerts, filename="alerts.json"):
    with open(filename, "w") as f:
        json.dump(alerts, f, indent=4)

def add_alert(threshold, email, alerts, filename="alerts.json"):
    alerts.append({"threshold": threshold, "email": email})
    save_alerts_to_file(alerts, filename="alerts.json")
    return alerts

def check_alerts(current_yield, alerts):
    triggered_alerts = []
    for alert in alerts:
        if current_yield > alert["threshold"]:
            triggered_alerts.append(alert)
    return triggered_alerts
