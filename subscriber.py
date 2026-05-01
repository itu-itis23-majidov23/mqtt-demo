"""
subscriber.py
Subscribes to all sensor topics using the '#' wildcard and prints
each incoming message with a timestamp and topic breakdown.

Demonstrates:
  - Wildcard subscriptions  (sensors/#)
  - Multi-level topic paths
  - Retained message handling
  - QoS negotiation (subscriber requests QoS 2; broker delivers at min(pub, sub) QoS)
"""

import json
import os
import time
import paho.mqtt.client as mqtt

# ── Config ───────────────────────────────────────────────────────────────────
BROKER    = os.getenv("MQTT_BROKER", "localhost")
PORT      = int(os.getenv("MQTT_PORT", 1883))
PREFIX    = os.getenv("MQTT_TOPIC_PREFIX", "sensors")
CLIENT_ID = "dashboard-subscriber-01"

# ANSI colours for terminal readability
RESET  = "\033[0m"
CYAN   = "\033[36m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
MAGENTA= "\033[35m"
RED    = "\033[31m"

TOPIC_COLOUR = {
    "temperature": GREEN,
    "humidity":    CYAN,
    "status":      MAGENTA,
}

# ── Callbacks ─────────────────────────────────────────────────────────────────
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[BROKER] Connected — subscribing to {PREFIX}/# (QoS 2)")
        client.subscribe(f"{PREFIX}/#", qos=2)
    else:
        print(f"[BROKER] Connection failed (rc={rc})")

def on_message(client, userdata, msg):
    topic    = msg.topic
    payload  = msg.payload.decode("utf-8")
    retained = " [RETAINED]" if msg.retain else ""
    ts       = time.strftime("%H:%M:%S")

    # Colour-code by sub-topic
    subtopic = topic.split("/")[-1]
    colour   = TOPIC_COLOUR.get(subtopic, YELLOW)

    # Pretty-print JSON payloads
    try:
        parsed = json.loads(payload)
        payload_display = json.dumps(parsed, indent=None, separators=(",", ":"))
    except (json.JSONDecodeError, ValueError):
        payload_display = payload

    print(
        f"{colour}[{ts}] {topic}{retained}{RESET}  →  {payload_display}"
    )

def on_subscribe(client, userdata, mid, granted_qos):
    print(f"[INFO] Subscription confirmed (QoS granted: {granted_qos})")
    print(f"[INFO] Waiting for messages on {PREFIX}/# — press Ctrl+C to stop\n")

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print(f"{RED}[BROKER] Unexpected disconnect (rc={rc}){RESET}")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    client = mqtt.Client(client_id=CLIENT_ID)
    client.on_connect    = on_connect
    client.on_message    = on_message
    client.on_subscribe  = on_subscribe
    client.on_disconnect = on_disconnect

    print(f"[INFO] Connecting to broker at {BROKER}:{PORT} ...")
    client.connect(BROKER, PORT, keepalive=60)

    try:
        client.loop_forever()   # blocking; handles reconnects automatically
    except KeyboardInterrupt:
        print("\n[INFO] Subscriber stopped.")
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()
