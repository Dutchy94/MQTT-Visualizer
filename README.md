# MQTT-Visualizer
Flask Web-UI, die auf einem Mosquitto-Broker lauscht und eingehende MQTT-Nachrichten live anzeigt.

## Changelog
- 2026-01-17: Test-Publisher fuer Sensor-Daten hinzugefuegt, UI kann JSON-Payloads mit `value` und `unit` anzeigen.

## Features
- Abonniert einen konfigurierbaren MQTT-Topic-Filter (Default: `#`)
- Live-Dashboard mit Charts fuer numerische Payloads
- Kacheln mit letzten Werten je Topic
- Filter + Auto-Refresh in der UI
- Kleine JSON-API zum Abfragen und optionalen Publishen
- Läuft lokal oder im Netzwerk

## Voraussetzungen
- Python 3.10+
- Ein laufender Mosquitto/MQTT-Broker (lokal oder remote)
- Internetzugang fuer Chart.js (CDN) oder lokale Einbindung

## Schnellstart (empfohlen)
```
git clone <repo-url>
cd MQTT-Visualizer
make run
```

Optional: Testdaten senden
```
make test-publish
```

Die Web-UI erreichst du unter:
- `http://127.0.0.1:5000`

## Installation (ausfuehrlich)
1) Repository holen
```
cd /Projekte
# falls noch nicht vorhanden:
# git clone <repo-url> MQTT-Visualizer
cd /Projekte/MQTT-Visualizer
```

2) Virtuelle Umgebung erstellen und aktivieren
```
python3 -m venv .venv
source .venv/bin/activate
```

3) Abhaengigkeiten installieren
```
pip install -r requirements.txt
```

4) Mosquitto installieren (optional, falls kein Broker vorhanden)
- Debian/Ubuntu:
```
sudo apt-get update
sudo apt-get install mosquitto mosquitto-clients
sudo systemctl enable --now mosquitto
```
- macOS (Homebrew):
```
brew install mosquitto
brew services start mosquitto
```

5) Konfiguration setzen (Beispiele)
```
# Default ist localhost:1883 und Topic '#'
export MQTT_BROKER_HOST=127.0.0.1
export MQTT_BROKER_PORT=1883
export MQTT_TOPIC=sensors/#

# Optional
export MQTT_USERNAME=benutzer
export MQTT_PASSWORD=passwort
export MQTT_TLS=false
```

6) Server starten
```
python app.py
```

7) Im Browser oeffnen
- `http://127.0.0.1:5000`

Hinweis: Die Charts werden aktuell ueber ein CDN geladen. In abgeschotteten Netzen kannst du Chart.js lokal einbinden.

## Konfiguration per .env (optional)
Du kannst eine `.env` im Repo anlegen (oder `.env.example` kopieren). Diese wird automatisch geladen.
```
cp .env.example .env
```

## Makefile (optional)
Wenn du lieber kurze Befehle willst:
```
make venv
make install
make run
make test-publish
```

## MQTT Test (optional)
### Schnelltest per Mosquitto
Nachrichten senden, um die UI zu testen:
```
mosquitto_pub -h 127.0.0.1 -t sensors/test -m "hello"
```

### Test-Publisher (Sensor-Demo)
Mit dem beiliegenden Skript kannst du fuer 10 Sekunden alle 500ms Messwerte auf mehrere Topics schicken.
Die Payload ist JSON mit `value` und `unit`, die UI liest diese automatisch aus und zeichnet Charts.

Start (Default: `127.0.0.1:1883`):
```
python3 test_publisher.py
```

Mit Broker im Netzwerk:
```
MQTT_BROKER_HOST=192.168.178.74 MQTT_BROKER_PORT=1883 python3 test_publisher.py
```

Aktuelle Demo-Topics:
- `sensors/dickenmessung` (mm)
- `sensors/halle_x/temperatur` (C)
- `sensors/entfernung` (mm)
- `sensors/mmwave/presence` (0/1)
- `sensors/stoerung` (0/1)

## Konfiguration
Umgebungsvariablen:
- `MQTT_BROKER_HOST` (Default `127.0.0.1`)
- `MQTT_BROKER_PORT` (Default `1883`)
- `MQTT_TOPIC` (Default `#`)
- `MQTT_USERNAME` / `MQTT_PASSWORD`
- `MQTT_CLIENT_ID` (Default `mqtt-visualizer`)
- `MQTT_KEEPALIVE` (Default `60`)
- `MQTT_TLS` (Default `false`)
- `MAX_MESSAGES` (Default `1000`)
- `PORT` (Default `5000`)

## API
- `GET /api/messages?limit=200` -> letzte Nachrichten
- `GET /api/status` -> Broker/Status
- `POST /api/publish` -> Nachricht publishen

Beispiel `publish`:
```
curl -X POST http://127.0.0.1:5000/api/publish \
  -H 'Content-Type: application/json' \
  -d '{"topic": "sensors/test", "message": "hello"}'
```

## Hinweise
- Der Broker muss erreichbar sein. Bei Fehlverbindungen zeigt die UI eine Meldung.
- Messages werden im Speicher gehalten (Ringpuffer). Fuer produktive Nutzung ggf. persistieren.
