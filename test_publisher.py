#!/usr/bin/env python3
"""
Publish sample sensor data to multiple MQTT topics every 500ms for 10 seconds.
"""

import json
import os
import random
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt


def getenv_int(name: str, default: int) -> int:
    # Nur einfache int Werte aus ENV, sonst Default.
    value = os.getenv(name)
    return int(value) if value and value.isdigit() else default


def getenv_bool(name: str, default: bool = False) -> bool:
    # Bool Flags aus ENV, kleine Varianten erlaubt.
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def main() -> int:
    # Config an die App-Defaults und .env  angleichen.
    host = os.getenv("MQTT_BROKER_HOST", "127.0.0.1")
    port = getenv_int("MQTT_BROKER_PORT", 1883)
    username = os.getenv("MQTT_USERNAME")
    password = os.getenv("MQTT_PASSWORD")
    use_tls = getenv_bool("MQTT_TLS", False)

    # Zufalls-Client-ID, damit nix  kollidiert.
    client = mqtt.Client(client_id=f"mqtt-visualizer-test-{random.randint(1000,9999)}")
    if username:
        # Optional Benutzer/Passwort falls Broker auth nutzt.
        client.username_pw_set(username, password or None)
    if use_tls:
        # TLS aktivieren (einfach, ohne custom CA).
        client.tls_set()

    # Broker verbinden und Netzwerk-Loop starten.
    client.connect(host, port, keepalive=60)
    client.loop_start()

    # Demo-Topics passend zu  unseren UI-Defaults.
    topics = [
        "sensors/dickenmessung",
        "sensors/halle_x/temperatur",
        "sensors/entfernung",
        "sensors/mmwave/presence",
        "sensors/stoerung",
    ]

    # Wir senden 20x alle 0.5s -> ca 10 Sekunden.
    start = time.time()
    iterations = 20  # 10 Sekunden / 0.5 Sekunden

    for _ in range(iterations):
        # ISO-Timestamp damit die UI  genaue Zeit zeigen kann.
        timestamp = datetime.now(timezone.utc).isoformat()
        # Werte leicht variieren fuer "live" Effekt.
        payloads = {
            topics[0]: round(random.uniform(0.5, 12.0), 2),   # mm
            topics[1]: round(random.uniform(16.0, 32.0), 2),  # C
            topics[2]: round(random.uniform(50.0, 800.0), 1), # mm
            topics[3]: random.randint(0, 1),                 # presence 0/1
            topics[4]: random.randint(0, 1),                 # stoerung 0/1
        }

        for topic, value in payloads.items():
            # JSON-Payload mit value + unit, damit die UI  beides parst.
            message = json.dumps(
                {
                    "ts": timestamp,
                    "value": value,
                    "unit": {
                        topics[0]: "mm",
                        topics[1]: "C",
                        topics[2]: "mm",
                        topics[3]: "bool",
                        topics[4]: "bool",
                    }[topic],
                }
            )
            # Publish auf Topic, QoS 0 reicht fuer Demo.
            client.publish(topic, message, qos=0, retain=False)

        # 500ms warten zwischen den Batches.
        time.sleep(0.5)

    # Aufraeumen.
    client.loop_stop()
    client.disconnect()

    elapsed = time.time() - start
    # Kleines Abschluss-Log fuer Terminal.
    print(f"Done. Sent {iterations} batches in {elapsed:.1f}s to {host}:{port}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
