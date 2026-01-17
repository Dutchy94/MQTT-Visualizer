import os
import json
import time
from collections import deque
from threading import Lock

from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv
import paho.mqtt.client as mqtt


def _env_bool(value, default=False):
    # Kleine Helper-Funktion, damit ich Env-Flags simpel lesen kann.
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


# .env laden falls vorhanden (macht lokal  einfacher).
load_dotenv()

# Flask App starten (einmal global, ist der zentrale Einstieg).
app = Flask(__name__)

# Max Anzahl Nachrichten im RAM (Ringpuffer).
MAX_MESSAGES = int(os.getenv("MAX_MESSAGES", "1000"))

# MQTT Konfig aus ENV, mit Defaults fuer schnellen Start.
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "127.0.0.1")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "#")
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "mqtt-visualizer")
MQTT_KEEPALIVE = int(os.getenv("MQTT_KEEPALIVE", "60"))
MQTT_TLS = _env_bool(os.getenv("MQTT_TLS"), default=False)

# Ringpuffer fuer letzte Nachrichten + Lock fuer Thread  Sicherheit.
_messages = deque(maxlen=MAX_MESSAGES)
_messages_lock = Lock()
# Letzter Verbindungsfehler, damit die UI was anzeigen kann.
_last_connect_error = None


def _append_message(topic, payload, qos, retain):
    # Einheitliches Format fuer UI / API.
    entry = {
        "ts": time.time(),
        "topic": topic,
        "payload": payload,
        "qos": qos,
        "retain": retain,
    }
    with _messages_lock:
        _messages.append(entry)


# MQTT Client Instanz (läuft neben Flask im Hintergrund).
mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_ID, clean_session=True, userdata=None)

if MQTT_USERNAME:
    # Optional: Auth, wenn Broker gesichert ist.
    mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

if MQTT_TLS:
    # Optional: TLS, falls euer Broker das braucht.
    mqtt_client.tls_set()


def on_connect(client, userdata, flags, rc):
    # Wird vom MQTT Client aufgerufen wenn Verbindung steht.
    global _last_connect_error
    if rc == 0:
        _last_connect_error = None
        # Topic-Filter abonnieren (default "#").
        client.subscribe(MQTT_TOPIC)
    else:
        _last_connect_error = f"Connect failed with code {rc}"


def on_message(client, userdata, msg):
    # Jedes eingehende MQTT Paket wird hier verarbeitet.
    try:
        payload = msg.payload.decode("utf-8", errors="replace")
    except Exception:
        payload = "<binary>"
    _append_message(msg.topic, payload, msg.qos, msg.retain)


def on_disconnect(client, userdata, rc):
    # Wenn die Verbindung wegbricht merken wir uns den Fehler.
    global _last_connect_error
    if rc != 0:
        _last_connect_error = f"Unexpected disconnect ({rc})"


# Callbacks am Client registrieren.
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.on_disconnect = on_disconnect


@app.route("/")
def index():
    # Hauptseite mit UI.
    return render_template("index.html")


@app.route("/api/messages")
def api_messages():
    # Letzte Messages als JSON (limitierbar per Query).
    limit = request.args.get("limit", type=int) or 200
    limit = max(1, min(limit, MAX_MESSAGES))
    with _messages_lock:
        data = list(_messages)[-limit:]
    return jsonify({
        "count": len(data),
        "messages": data,
    })


@app.route("/api/status")
def api_status():
    # Status fuer UI: Broker-Info und evtl. Fehler.
    return jsonify({
        "broker": {
            "host": MQTT_BROKER_HOST,
            "port": MQTT_BROKER_PORT,
            "topic": MQTT_TOPIC,
            "tls": MQTT_TLS,
        },
        "last_connect_error": _last_connect_error,
        "max_messages": MAX_MESSAGES,
    })


@app.route("/api/publish", methods=["POST"])
def api_publish():
    # Optional: Nachricht via API publishen.
    payload = request.json or {}
    topic = payload.get("topic")
    message = payload.get("message")
    if not topic or message is None:
        return jsonify({"error": "topic and message are required"}), 400
    result = mqtt_client.publish(topic, str(message))
    return jsonify({"rc": result.rc})


def start_mqtt():
    # Async connect + Hintergrund-Loop, damit Flask  flott bleibt.
    # connect_async blockiert nicht, loop_start kuemmert sich um I/O.
    mqtt_client.connect_async(MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_KEEPALIVE)
    mqtt_client.loop_start()


# MQTT direkt beim Import starten (sofortige Verbindung).
start_mqtt()


if __name__ == "__main__":
    # Flask dev server (host 0.0.0.0 fuer LAN Zugriff).
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
