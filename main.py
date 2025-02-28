from paho.mqtt import client as mqtt_client
import requests
import yaml
import os
import inspect
from typing import Any
import warnings


class Monitor:
    def __init__(self, broker="localhost", port=1883, topic="zigbee2mqtt/+/availability",
                 openhab_ip=None, openhab_port=8080, openhab_item="z2m_offline_devices_list",
                 report_when_disconnected=False):
        self.broker = broker
        self.port = port
        self.topic = topic
        self.openhab_ip = openhab_ip if openhab_ip is not None else broker
        self.openhab_port = openhab_port
        self.openhab_item = openhab_item
        self.client_id = 'z2m-availability-monitor'
        self.report_when_disconnected = report_when_disconnected
        self.client: mqtt_client = self.connect_mqtt()
        self.client.subscribe(self.topic)
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.device_availability: dict[str, bool] = {}
        self.client.loop_forever()

    def __del__(self):
        self.on_disconnect()

    @classmethod
    def generate_default_config_dict(cls) -> dict[str, Any]:
        """Generate a dict of the default parameters to __init__()."""
        cfg = {}
        for param_name, param in inspect.signature(cls.__init__).parameters.items():
            if param_name == "self":
                continue
            cfg[param_name] = param.default
        return cfg

    @staticmethod
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    def on_disconnect(self, *args, **kwargs):
        if self.report_when_disconnected:
            url = f"http://{self.openhab_ip}:{self.openhab_port}/rest/items/{self.openhab_item}"
            requests.post(url, data=self.client_id.encode("utf-8"), headers={'Content-Type': 'text/plain'})

    def connect_mqtt(self) -> mqtt_client:
        client = mqtt_client.Client(self.client_id)
        client.on_connect = self.on_connect
        client.connect(self.broker, self.port)
        return client

    def on_message(self, client, userdata, msg):
        availability_json = msg.payload.decode().lower()
        if availability_json == "online":
            availability = True
        elif availability_json == "offline":
            availability = False
        else:
            try:
                availability_dict = yaml.load(availability_json, yaml.Loader)
                availability = (availability_dict["state"] == "online")
                _, device_name, _ = msg.topic.split("/")
                self.device_availability[device_name] = availability
            except:
                warnings.warn(f"Failed to parse message: {availability_json}")
        print("Offline Devices:", ", ".join([dev for dev, avail in self.device_availability.items() if not avail]))
        result = self.update_openhab_item()
        if result.status_code != 200:
            raise ConnectionError(f"Failed to update openhab item '{self.openhab_item}'.")

    def update_openhab_item(self):
        return DummyResponse(200)
        url = f"http://{self.openhab_ip}:{self.openhab_port}/rest/items/{self.openhab_item}"
        device_list = ", ".join([dev for dev, avail in self.device_availability.items() if not avail])
        result = requests.post(url, data=device_list.encode("utf-8"), headers={'Content-Type': 'text/plain'})
        return result


def run():
    # if there is no config file present, generate a default one
    if not os.path.exists("data"):
        print("Creating data folder")
        os.mkdir("data")
    if not os.path.exists(os.path.join("data", "config.yaml")):
        print("Generating default config file.")
        with open(os.path.join("data", "config.yaml"), "w") as f:
            yaml.dump(Monitor.generate_default_config_dict(), f)
    # load the config file
    with open(os.path.join("data", "config.yaml"), "r") as f:
        cfg = yaml.load(f, Loader=yaml.Loader)
    # create and run the monitor daemon
    monitor = Monitor(**cfg)


if __name__ == '__main__':
    run()
