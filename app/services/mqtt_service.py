import paho.mqtt.publish as publish
import json


MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883

def send_device_command(device_id: str, command: str, patient_id: str, first_name: str, last_name: str):

    topic = f"patient/{device_id}/commands"


    payload = {
        "cmd": command,
        "patient_id": patient_id,
        "first_name": first_name,
        "last_name": last_name
    }

    publish.single(
        topic,
        payload=json.dumps(payload),
        hostname=MQTT_BROKER,
        port=MQTT_PORT
    )