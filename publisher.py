"""
publisher.py
Simulates an IoT sensor device publishing temperature and humidity readings
to an MQTT broker every second.

Topics published:
  sensors/temperature  → float (°C)
  sensors/humidity     → float (%)
  sensors/status       → JSON summary

QoS levels demonstrated:
  0 — fire and forget (temperature)
  1 — at least once   (humidity)
  2 — exactly once    (status)
"""

import json
import random
import time
import os
import paho.mqtt.client as mqtt

# ── Config ──────────────────────────────────────────────────────────────────
BROKER   = os.getenv("MQTT_BROKER", "localhost")
PORT     = int(os.getenv("MQTT_PORT", 1883))
PREFIX   = os.getenv("MQTT_TOPIC_PREFIX", "sensors")
INTERVAL = float(os.getenv("PUBLISH_INTERVAL", 1))
CLIENT_ID = "sensor-node-01"

# ── Callbacks ────────────────────────────────────────────────────────────────
def on_connect(client, userdata, flags, rc):
    codes = {
        0: "Connected successfully",
        1: "Bad protocol version",
        2: "Client ID rejected",
        3: "Server unavailable",
        4: "Bad credentials",
        5: "Not authorised",
    }
    print(f"[BROKER] {codes.get(rc, f'Unknown code {rc}')}")

def on_publish(client, userdata, mid):
    pass  # called when broker ACKs a QoS 1/2 message

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print(f"[BROKER] Unexpected disconnect (rc={rc})")

# ── Sensor simulation ─────────────────────────────────────────────────────────
def read_temperature():
    """Simulate a temperature sensor with slight drift."""
    return round(random.uniform(18.0, 35.0), 2)

def read_humidity():
    """Simulate a humidity sensor."""
    return round(random.uniform(30.0, 90.0), 2)

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    client = mqtt.Client(client_id=CLIENT_ID)
    client.on_connect    = on_connect
    client.on_publish    = on_publish
    client.on_disconnect = on_disconnect

    # Last Will and Testament — broker publishes this if we disconnect ungracefully
    client.will_set(
        topic=f"{PREFIX}/status",
        payload=json.dumps({"client": CLIENT_ID, "status": "offline"}),
        qos=1,
        retain=True,
    )

    print(f"[INFO] Connecting to broker at {BROKER}:{PORT} ...")
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_start()

    msg_count = 0
    try:
        while True:
            temp  = read_temperature()
            humid = read_humidity()
            msg_count += 1

            # QoS 0 — temperature (best effort, lowest overhead)
            client.publish(f"{PREFIX}/temperature", payload=temp, qos=0)

            # QoS 1 — humidity (at-least-once delivery)
            client.publish(f"{PREFIX}/humidity", payload=humid, qos=1)

            # QoS 2 — status JSON (exactly once, highest overhead)
            status = {
                "client":      CLIENT_ID,
                "status":      "online",
                "msg_count":   msg_count,
                "temperature": temp,
                "humidity":    humid,
                "timestamp":   time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            client.publish(f"{PREFIX}/status", payload=json.dumps(status), qos=2)

            print(
                f"[PUB #{msg_count:04d}] "
                f"temp={temp:5.2f}°C  "
                f"humidity={humid:5.2f}%  "
                f"ts={status['timestamp']}"
            )
            time.sleep(INTERVAL)

    except KeyboardInterrupt:
        print("\n[INFO] Publisher stopped.")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
