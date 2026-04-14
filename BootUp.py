import paho.mqtt.client as mqtt
import time
import Definitions



# Recieve all messages from the MQTT broker
def on_message(client, userdata, msg):
    topic = msg.topic.split("/")
    payload = msg.payload.decode()
    print(f"Received message on topic {topic}: {payload}")
    
    match topic:

        case ["ESP", "SWAP", "Status"]:                 # ESP_SWAP Connection Status Update
            print(f"Swap Status Update: {payload}")
            if payload == "Connected":
                ESP_SWAP_CONNECTED = True
            else:            
                ESP_SWAP_CONNECTED = False
                STATE = States.STBY

        case ["ESP", "POS", "Status"]:                  # ESP_POS Connection Status Update
            print(f"Position Status Update: {payload}")
            if payload == "Connected":
                ESP_POS_CONNECTED = True
            else:            
                ESP_POS_CONNECTED = False
                STATE = States.STBY

        case ["Drone", "Status"]:                       # Drone Status Update
            print(f"Drone Status Update: {payload}")
            if payload == "Connected": 
                DRONE_CONNECTED = True
            else:            
                DRONE_CONNECTED = False    

        case ["Drone", "Landing"]:                      # Drone Landing Confirmation
            print(f"Drone Landing Update: {payload}")
            if payload == "Landed":
                STATE = States.POS_PINCH

    

# Triggers when the client has connected successfully to the MQTT broker
def on_connect(client, userdata, flags, rc, properties):
    print("Connected with result code "+str(rc))
    client.publish("NEST/Status", "Connected", qos=3, retain=True)

# Triggers when the client has successfully subscribed to a topic
def on_subscribe(client, userdata, mid, reason_codes, properties):
    print("Subscribed to topic with Qos: " + str(reason_codes[0]))



# Initialize MQTT Client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

# Attribute assignments for MQTT callbacks
client.on_message = on_message
client.on_connect = on_connect
client.on_subscribe = on_subscribe

# Connect to the MQTT broker 
client.connect("localhost", 1883)       

# Subscribe to topic to receive updates from device
client.subscribe("ESP/SWAP/Status")
client.subscribe("ESP/POS/Status")
client.subscribe("Drone/Status")
client.subscribe("Drone/Landing")


# Set State
STATE = States.STBY


# Actual Logic Level
client.loop_start()

try:

    match STATE:

        case States.STBY:
            print("No Devices Connected to Broker")
            if ESP_SWAP_CONNECTED and ESP_POS_CONNECTED:
                STATE = States.STBY_READY

        case States.STBY_READY:
            print("ESPs Connected, Waiting for Drone")
            if DRONE_CONNECTED:
                STATE = States.STBY_DRONE_LAND

        case States.STBY_DRONE_LAND:
            print("All Devices Connected, Waiting for Drone Landing Confirmation")


except KeyboardInterrupt:
    client.loop_stop()
    client.disconnect()
