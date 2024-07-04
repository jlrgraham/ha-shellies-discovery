import paho.mqtt.client as mqtt
import certifi

import yaml
import json
import logging
import os


logger = logging.getLogger(__name__)
log_handler = logging.StreamHandler()
log_formatter = logging.Formatter(
    "%(asctime)s [%(name)-12s] %(levelname)-8s %(message)s"
)
log_handler.setFormatter(log_formatter)
logger.addHandler(log_handler)
logger.setLevel(os.getenv("LOG_LEVEL", default="INFO").upper())


SHELLEY_ANNOUNCE_MQTT_PREFIX = os.getenv(
    "SHELLEY_ANNOUNCE_MQTT_PREFIX", default="shellies"
)

MQTT_BROKER = os.getenv("MQTT_BROKER", default="mqtt")
MQTT_PORT = os.getenv("MQTT_PORT", default=8883)
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", default="ha-shellies-discovery")
MQTT_USERNAME = os.getenv("MQTT_USERNAME", default=None)
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", default=None)

HA_DISCOVERY_PREFIX = os.getenv("HA_DISCOVERY_PREFIX", default="homeassistant")
HA_STATUS_TOPIC = os.getenv("HA_STATUS_TOPIC", default=None)

DEVICE_CONFIG_FILE = "/config/device-config.yml"


class FakeHassServices(object):
    def __init__(self, client):
        self.client = client

    def call(self, service, action, service_data, *args, **kwargs):
        if service == "mqtt" and action == "publish":
            (result, mid) = self.client.publish(
                service_data.get("topic"),
                service_data.get("payload"),
                retain=service_data.get("retain", False),
                qos=service_data.get("qos", 0),
            )
            if result != 0:
                logger.error(
                    f"MQTT: Error publishing discovery, result: {result}, topic: {service_data.get('topic')}"
                )
            else:
                logger.info(
                    f"MQTT: Published discovery, topic: {service_data.get('topic')}"
                )
        else:
            logger.warn(
                f"FakeHassServices: Unhandled service/action pair: {service}/{action}"
            )


class FakeHass(object):
    def __init__(self, client):
        self.services = FakeHassServices(client)


# Load the source from upstream
filename = "python_scripts/shellies_discovery.py"
with open(filename, encoding="utf8") as f:
    source = f.read()

compiled = compile(source, filename=filename, mode="exec")


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        logger.info("MQTT: Connected to broker.")
        announce_subscribe = f"{SHELLEY_ANNOUNCE_MQTT_PREFIX}/announce"
        logger.info(f"MQTT: Subscribe: {announce_subscribe}")
        client.subscribe(announce_subscribe)

        if HA_STATUS_TOPIC is not None:
            logger.info(f"MQTT: Subscribe: {HA_STATUS_TOPIC}")
            client.subscribe(HA_STATUS_TOPIC)
    else:
        logger.error(f"MQTT: Failed to connect, reason_code: {reason_code}")


def on_message(client, userdata, msg):
    payload = msg.payload.decode("utf-8")

    logger.debug(
        f"MQTT: Message received: Topic: {msg.topic}, QOS: {msg.qos}, Retain Flag: {msg.retain}"
    )
    logger.debug(f"MQTT: Message received: {str(payload)}")

    fakehass = FakeHass(client)

    if msg.topic == HA_STATUS_TOPIC:
        if payload == "online":
            logger.info("MQTT: Detected HA now online, will ask devices to announce.")

            fakehass.services.call(
                service="mqtt",
                action="publish",
                service_data={
                    "topic": f"{SHELLEY_ANNOUNCE_MQTT_PREFIX}/command",
                    "payload": "announce",
                    "qos": 2,
                },
            )

    else:
        event = json.loads(payload)

        # Sigh, some gen 2 devices using gen 1 patterns?
        if event.get("gen", 1) == 2:
            return

        ha_discovery_payload = {
            "id": event.get("id"),
            "mac": event.get("mac"),
            "fw_ver": event.get("fw_ver"),
            "model": event.get("model"),
            "mode": event.get("mode", ""),
            "host": event.get("ip"),
            "discovery_prefix": HA_DISCOVERY_PREFIX,
        }

        device_config = {}
        if os.path.exists(DEVICE_CONFIG_FILE):
            with open(DEVICE_CONFIG_FILE, "r") as f:
                device_config = yaml.safe_load(f)

        exec(
            compiled,
            {
                "data": ha_discovery_payload | device_config,
                "logger": logger,
                "hass": fakehass,
            },
        )


def run():
    logger.debug("DEBUG logging enabled.")

    if MQTT_BROKER is None:
        raise Exception("MQTT_BROKER must be defined.")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=MQTT_CLIENT_ID)

    if MQTT_USERNAME is not None and MQTT_PASSWORD is not None:
        logger.info(f"MQTT: Authentication enabled, connect as: {MQTT_USERNAME}")
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    client.on_connect = on_connect
    client.on_message = on_message

    if MQTT_PORT == 8883:
        logger.info("MQTT: Enable TLS.")
        client.tls_set(certifi.where())

    logger.info(f"MQTT: Connect to {MQTT_BROKER}:{MQTT_PORT} ({MQTT_CLIENT_ID})")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    client.loop_forever()


if __name__ == "__main__":
    run()
