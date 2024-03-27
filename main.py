from paho.mqtt import client as mqtt_client


class Monitor:
    def __init__(self, broker, port=1883, topic="zigbee2mqtt/+/availability"):
        self.broker = broker
        self.port = port
        self.topic = topic
        self.client_id = 'z2m-availability-monitor'
        self.client: mqtt_client = self.connect_mqtt()
        self.client.subscribe(self.topic)
        self.client.on_message = self.on_message
        self.device_availability: dict[str, bool] = {}
        self.client.loop_forever()

    @staticmethod
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    def connect_mqtt(self) -> mqtt_client:
        client = mqtt_client.Client(self.client_id)
        client.on_connect = self.on_connect
        client.connect(self.broker, self.port)
        return client

    def on_message(self, client, userdata, msg):
        availability = (msg.payload.decode().lower() == "online")
        _, device_name, _ = msg.topic.split("/")
        self.device_availability[device_name] = availability
        print("Offline Devices:", ", ".join([dev for dev, avail in self.device_availability.items() if not avail]))


def run():
    monitor = Monitor("g3")


if __name__ == '__main__':
    run()
