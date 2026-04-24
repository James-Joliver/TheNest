import paho.mqtt.client as mqtt
import time
import Definitions
from Definitions import States



global STATE
global ESP_SWAP_CONNECTED
global ESP_POS_CONNECTED
global DRONE_CONNECTED 

ESP_SWAP_CONNECTED = False
ESP_POS_CONNECTED = False
DRONE_CONNECTED = False

def on_message(client, userdata, msg):

    global STATE
    global ESP_SWAP_CONNECTED
    global ESP_POS_CONNECTED
    global DRONE_CONNECTED 

    topic = msg.topic.split("/")
    payload = msg.payload.decode()
    print(f"Received message on topic {topic}: {payload}")
    
    
    match topic:
        case ["ESP", "SWAP", "Status"]:
            print(f"Swap Status Update: {payload}")
            if payload == "Connected":
                ESP_SWAP_CONNECTED = True

            elif payload == "Disconnected":            
                ESP_SWAP_CONNECTED = False
                STATE = States.STBY
                client.publish("NEST/System/Status", "STBY", qos=2, retain=True)

        case ["ESP", "POS", "Status"]:
            print(f"Position Status Update: {payload}")
            if payload == "Connected":
                ESP_POS_CONNECTED = True

            elif payload == "Disconnected":            
                ESP_POS_CONNECTED = False
                STATE = States.STBY
                client.publish("NEST/System/Status", "STBY", qos=2, retain=True)
                
        case ["DRONE", "Status"]:
            print(f"Drone Status Update: {payload}")
            if payload == "Connected":
                DRONE_CONNECTED = True

            elif payload == "Disconnected":            
                DRONE_CONNECTED = False
                if STATE != States.STBY:    # Always go to STBY if ESPs are disconnected aswell
                    STATE = States.STBY_READY
                    client.publish("NEST/System/Status", "STBY_READY", qos=2, retain=True)
                else:
                    STATE = States.STBY
                    client.publish("NEST/System/Status", "STBY", qos=2, retain=True)
                


def on_connect(client, userdata, flags, rc, properties):
    print("Connected with result code "+str(rc))
    client.publish("NEST/Status", "Connected", qos=2, retain=True)

def on_subscribe(client, userdata, mid, reason_codes, properties):
    print("Subscribed to topic with Qos: " + str(reason_codes[0]))
    


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

client.on_message = on_message
client.on_connect = on_connect
client.on_subscribe = on_subscribe

client.connect("localhost", 1883)       

client.loop_start()

client.subscribe("ESP/SWAP/Status")
client.subscribe("ESP/POS/Status")
client.subscribe("DRONE/Status")



STATE = States.STBY


client.publish("ESP/SWAP/Status", "TEST", qos=2)
client.publish("ESP/POS/Status", "TEST", qos=2)
client.publish("DRONE/Status", "TEST", qos=2)



try:


    while True:
        match STATE:
            case States.STBY:
                print("ESP_SWAP_CONNECTED: " + str(ESP_SWAP_CONNECTED) + " | ESP_POS_CONNECTED: " + str(ESP_POS_CONNECTED))
                if ESP_SWAP_CONNECTED and ESP_POS_CONNECTED:
                    STATE = States.STBY_READY
                    client.publish("NEST/System/Status", "STBY_READY", qos=2, retain=True)
                    print(f"State: {STATE}")
                elif ESP_SWAP_CONNECTED and not ESP_POS_CONNECTED:
                    print("Waiting for Position ESP to Connect...")
                    time.sleep(1)
                elif not ESP_SWAP_CONNECTED and ESP_POS_CONNECTED:
                    print("Waiting for Swap ESP to Connect...")
                    time.sleep(1)
                else:
                    print("Waiting for ESPs to Connect...")
                time.sleep(1)

            case States.STBY_READY:
                if DRONE_CONNECTED:
                    STATE = States.STBY_DRONE_LAND
                    client.publish("NEST/System/Status", "STBY_DRONE_LAND", qos=2, retain=True)
                    print(f"State: {STATE}")
                else:
                    print("Waiting for Drone to Connect...")
                    time.sleep(1)
            
            case States.STBY_DRONE_LAND:
                if DRONE_CONNECTED:
                    STATE = States.POS_PINCH
                    client.publish("NEST/System/Status", "POS_PINCH", qos=2, retain=True)
                    print(f"State: {STATE}")
                else:
                    print("Waiting for Drone to Land...")
                    time.sleep(1)
                    
            case States.POS_PINCH:
                print("Initiating Position Pinch Process...")
                time.sleep(1)
                    

        print("Current State: " + str(STATE))


except KeyboardInterrupt:
    client.loop_stop()
    client.disconnect()