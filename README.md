# MQTT / Eclipse Mosquitto — IoT Messaging Demo

> **YZV 322E Applied Data Engineering | Tool Presentation #35**
> Spring 2026 — ITU Dept. of AI and Data Engineering

---

## 1. What Is This Tool?

**MQTT** (Message Queuing Telemetry Transport) is a lightweight publish-subscribe messaging protocol designed for constrained devices and unreliable networks. **Eclipse Mosquitto** is the reference open-source broker implementation maintained by the Eclipse Foundation (EPL-2.0 licence). Together they form the de-facto standard for IoT data ingestion at the network edge — sensors publish readings to the broker, and any number of downstream consumers subscribe to receive them in real time.

---

## 2. Prerequisites

| Requirement | Version |
|-------------|---------|
| OS | Linux / macOS / Windows (WSL2 recommended) |
| Docker | ≥ 24.0 |
| Docker Compose | ≥ 2.20 (bundled with Docker Desktop) |
| Python | ≥ 3.9 |
| pip | ≥ 23.0 |

No paid licence required — everything runs locally.

---

## 3. Installation

### 3.1 Clone the repository

```bash
git clone https://github.com/itu-itis23-majidov23/mqtt-demo.git
cd mqtt-demo
```

### 3.2 Copy environment file

```bash
cp .env.example .env
```

Edit `.env` if you want to change the broker host, port, or publish interval (defaults work out of the box).

### 3.3 Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3.4 Start the Mosquitto broker

```bash
docker compose up -d
```

Verify the broker is running:

```bash
docker compose ps
# Expected: mqtt-broker   running   0.0.0.0:1883->1883/tcp
```

---

## 4. Running the Example

You need **two terminal windows** open in the project directory.

### Terminal 1 — Start the subscriber (consumer)

```bash
python subscriber.py
```

### Terminal 2 — Start the publisher (sensor simulator)

```bash
python publisher.py
```

The publisher sends one reading per second. The subscriber prints every message it receives with colour-coded output by topic.

### Stopping

Press `Ctrl+C` in each terminal. Then stop the broker:

```bash
docker compose down
```

---

## 5. Expected Output

### Publisher terminal

```
[INFO] Connecting to broker at localhost:1883 ...
[BROKER] Connected successfully
[PUB #0001] temp=24.37°C  humidity=61.82%  ts=2026-04-10T14:00:01Z
[PUB #0002] temp=27.91°C  humidity=58.44%  ts=2026-04-10T14:00:02Z
[PUB #0003] temp=22.15°C  humidity=73.20%  ts=2026-04-10T14:00:03Z
```

### Subscriber terminal

```
[INFO] Connecting to broker at localhost:1883 ...
[BROKER] Connected — subscribing to sensors/# (QoS 2)
[INFO] Subscription confirmed (QoS granted: (2,))
[INFO] Waiting for messages on sensors/# — press Ctrl+C to stop

[14:00:01] sensors/temperature  →  24.37
[14:00:01] sensors/humidity     →  61.82
[14:00:01] sensors/status       →  {"client":"sensor-node-01","status":"online","msg_count":1,...}
[14:00:02] sensors/temperature  →  27.91
...
```

Topics are colour-coded: **green** = temperature, **cyan** = humidity, **magenta** = status JSON.

---

## 6. AI Usage Disclosure

See [AI_USAGE.md](./AI_USAGE.md) for a full breakdown of which AI tools were used and for what purpose. All code was reviewed and tested independently before submission.

---

## Architecture Overview

```
┌─────────────────┐        TCP:1883        ┌─────────────────────┐
│  publisher.py   │  ──── PUBLISH ────►    │  Eclipse Mosquitto  │
│  (IoT sensor)   │                        │  (Docker container) │
└─────────────────┘                        └─────────┬───────────┘
                                                     │
                                           ◄── DELIVER ──
                                                     │
                                          ┌──────────▼──────────┐
                                          │  subscriber.py       │
                                          │  (dashboard / NiFi) │
                                          └─────────────────────┘

Topics:
  sensors/temperature  (QoS 0 — fire and forget)
  sensors/humidity     (QoS 1 — at least once)
  sensors/status       (QoS 2 — exactly once)
```

## Where It Fits in the Course Pipeline

```
IoT Devices
    │  MQTT publish
    ▼
Mosquitto Broker  ◄── this demo
    │  subscribe / NiFi MQTT Consumer processor
    ▼
Apache NiFi  →  Elasticsearch / PostgreSQL  →  Kibana
```

---

## Repository Structure

```
mqtt-demo/
├── docker-compose.yml        # Spins up the Mosquitto broker
├── mosquitto/
│   └── mosquitto.conf        # Broker configuration (anon, port 1883)
├── publisher.py              # Simulates an IoT sensor (QoS 0/1/2 demo)
├── subscriber.py             # Wildcard subscriber with coloured output
├── requirements.txt          # paho-mqtt==1.6.1
├── .env.example              # Environment variable template
├── AI_USAGE.md               # AI tool disclosure
└── README.md                 # This file
```

---

## Troubleshooting

### Port 1883 already in use

If `docker compose up -d` fails with `address already in use`, a native Mosquitto instance is already running on your machine (common on Ubuntu, which auto-starts it after `apt install mosquitto`).

Check what's using the port:

```bash
sudo lsof -i :1883
```

**Option A — stop the system Mosquitto and use Docker (recommended for the demo):**

```bash
sudo systemctl stop mosquitto
sudo systemctl disable mosquitto   # prevent it from restarting on reboot
docker compose up -d
```

Re-enable it afterwards if you need it:

```bash
sudo systemctl enable --now mosquitto
```

**Option B — skip Docker and use the system Mosquitto directly:**

The system broker is already running and accepts anonymous connections by default. Just run the scripts against it:

```bash
python subscriber.py   # terminal 1
python publisher.py    # terminal 2
```

No `docker compose` step needed. Everything else in the README applies as-is.

**Option C — change the Docker port mapping:**

Edit `docker-compose.yml` and map to a free port (e.g. `1884`), then tell the scripts to use it:

```yaml
ports:
  - "1884:1883"
```

```bash
MQTT_PORT=1884 python subscriber.py
MQTT_PORT=1884 python publisher.py
```

> **Note:** The `version` field warning (`the attribute version is obsolete`) is harmless — Docker Compose v2 ignores it. It does not affect functionality.

---

## References

- [Eclipse Mosquitto Documentation](https://mosquitto.org/documentation/)
- [OASIS MQTT 3.1.1 Specification](https://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html)
- [paho-mqtt Python client](https://eclipse.dev/paho/files/paho.mqtt.python/html/index.html)
- [eclipse-mosquitto Docker Hub](https://hub.docker.com/_/eclipse-mosquitto)
- [MQTT QoS levels explained — HiveMQ](https://www.hivemq.com/blog/mqtt-essentials-part-6-mqtt-quality-of-service-levels/)
