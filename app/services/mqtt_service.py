import os
import ssl
import json
import paho.mqtt.publish as publish
from dotenv import load_dotenv

load_dotenv()

MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT", "8883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")


def send_device_command(
        device_id: str,
        command: str,
        patient_id: str,
        first_name: str,
        last_name: str
):
    topic = f"devices/{device_id}/commands"

    payload = {
        "command": command,
        "cmd": command,
        "patient_id": patient_id,
        "first_name": first_name,
        "last_name": last_name
    }

    tls_context = ssl.create_default_context()

    publish.single(
        topic=topic,
        payload=json.dumps(payload),
        hostname=MQTT_BROKER,
        port=MQTT_PORT,
        auth={
            "username": MQTT_USERNAME,
            "password": MQTT_PASSWORD
        },
        tls=tls_context
    )

    return True