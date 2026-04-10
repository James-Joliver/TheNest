############################################################################
#  This goal of this code is to demonstrate a simple MQTT client that can communicate with an ESP32 device.
#  This code publishes commands to control the light and listens for the status update from the EPS32
#  James Wilkinson 
#############################################################################

import paho.mqtt.client as mqtt
import time

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()

    # Routing Logic
    if topic == "ESP32/1/light/state":
        print(f"Device update: {payload}")



client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_message = on_message


client.connect("localhost", 1883)       # Connect to the MQTT broker (adjust host and port as needed)
client.subscribe("ESP32/1/light/state")    # Subscribe to topic to receive updates from device

# loop_start runs the listener in the background so the 
# rest of your script can keep moving or stay alive.
client.loop_start()

try:
    while True:
        # Your "Brain" can do other things here, 
        # like periodic health checks or heartbeats.
        time.sleep(1)
        client.publish("ESP32/1/light", "on")
        time.sleep(1)
        client.publish("ESP32/1/light", "off")
except KeyboardInterrupt:
    client.loop_stop()
