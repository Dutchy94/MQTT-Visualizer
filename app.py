import os
import json
import time
from collections import deque
from threading import Lock

from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv
import paho.mqtt.client as mqtt


def _env_bool(value, default=False):
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


load_dotenv()

app = Flask(__name__)

MAX_MESSAGES = int(os.getenv("MAX_MESSAGES", "1000"))

MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "127.0.0.1")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "#")
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "mqtt-visualizer")
MQTT_KEEPALIVE = int(os.getenv("MQTT_KEEPALIVE", "60"))
MQTT_TLS = _env_bool(os.getenv("MQTT_TLS"), default=False)

_messages = deque(maxlen=MAX_MESSAGES)
_messages_lock = Lock()
_last_connect_error = None


def _append_message(topic, payload, qos, retain):
    entry = {
        "ts": time.time(),
        "topic": topic,
        "payload": payload,
        "qos": qos,
        "retain": retain,
    }
    with _messages_lock:
        _messages.append(entry)


mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_ID, clean_session=True, userdata=None)

if MQTT_USERNAME:
    mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

if MQTT_TLS:
    mqtt_client.tls_set()


def on_connect(client, userdata, flags, rc):
    global _last_connect_error
    if rc == 0:
        _last_connect_error = None
        client.subscribe(MQTT_TOPIC)
    else:
        _last_connect_error = f"Connect failed with code {rc}"


def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8", errors="replace")
    except Exception:
        payload = "<binary>"
    _append_message(msg.topic, payload, msg.qos, msg.retain)


def on_disconnect(client, userdata, rc):
    global _last_connect_error
    if rc != 0:
        _last_connect_error = f"Unexpected disconnect ({rc})"


mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.on_disconnect = on_disconnect


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/messages")
def api_messages():
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
    payload = request.json or {}
    topic = payload.get("topic")
    message = payload.get("message")
    if not topic or message is None:
        return jsonify({"error": "topic and message are required"}), 400
    result = mqtt_client.publish(topic, str(message))
    return jsonify({"rc": result.rc})



def start_mqtt():
    mqtt_client.connect_async(MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_KEEPALIVE)
    mqtt_client.loop_start()


start_mqtt()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
