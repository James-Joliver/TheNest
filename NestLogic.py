import paho.mqtt.client as mqtt
import time
import Definitions
from Definitions import States, SystemState

sys = SystemState()

def on_message(client, userdata, msg):


    topic = msg.topic.split("/")
    payload = msg.payload.decode()
    print(f"Received message on topic {topic}: {payload}")
    
    
    match topic:
        case ["ESP", "SWAP", "Status"]:
            print(f"Swap Status Update: {payload}")
            if payload == "Connected":
                sys.ESP_SWAP_CONNECTED = True

            elif payload == "Disconnected":            
                sys.ESP_SWAP_CONNECTED = False
                sys.STATE = States.STBY
                client.publish("NEST/System/Status", "STBY", qos=2, retain=True)

        case ["ESP", "POS", "Status"]:
            print(f"Position Status Update: {payload}")
            if payload == "Connected":
                sys.ESP_POS_CONNECTED = True

            elif payload == "Disconnected":            
                sys.ESP_POS_CONNECTED = False
                sys.STATE = States.STBY
                client.publish("NEST/System/Status", "STBY", qos=2, retain=True)
                
        case ["DRONE", "Status"]:
            print(f"Drone Status Update: {payload}")
            if payload == "Connected":
                sys.DRONE_CONNECTED = True

            elif payload == "Disconnected":            
                sys.DRONE_CONNECTED = False
                if sys.STATE != States.STBY:    # Always go to STBY if ESPs are disconnected aswell
                    sys.STATE = States.STBY_READY
                    client.publish("NEST/System/Status", "STBY_READY", qos=2, retain=True)
                else:
                    sys.STATE = States.STBY
                    client.publish("NEST/System/Status", "STBY", qos=2, retain=True)

        case ["ESP", "POS", "Pinch", "State"]:
            print(f"POS Pinch Update: {payload}")
            if payload == "Complete":
                sys.PINCH_COMPLETE = True
            
            elif payload == "In Progress":
                print("Pinch in Progress")
            
            else:
                print("Pinch Failure")

        case ["ESP", "POS", "Push", "State"]:
            print(f"POS Push Update: {payload}")
            if payload == "Complete":
                sys.PUSH_COMPLETE = True
                print("EPIC COMPLETE FOR REAL")
            
            elif payload == "In Progress":
                print("Push in Progress")

            else:
                print("Push Failure")
        
        case ["ESP", "SWAP", "Align", "State"]:
            print(f"SWAP Alignment update: {payload}")
            if payload == "Complete":
                sys.ALIGN_COMPLETE = True
            
            elif payload == "In Progress":
                print("Alignment in progress")

            else:
                print("Alignment Failure")



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

client.subscribe("#")



sys.STATE = States.STBY


client.publish("ESP/SWAP/Status", "TEST", qos=2)
client.publish("ESP/POS/Status", "TEST", qos=2)
client.publish("DRONE/Status", "TEST", qos=2)




try:


    while True:
        match sys.STATE:
            case States.STBY:
                print("ESP_SWAP_CONNECTED: " + str(sys.ESP_SWAP_CONNECTED) + " | ESP_POS_CONNECTED: " + str(sys.ESP_POS_CONNECTED))
                if sys.ESP_SWAP_CONNECTED and sys.ESP_POS_CONNECTED:
                    sys.STATE = States.STBY_READY
                    client.publish("NEST/System/Status", "STBY_READY", qos=2, retain=True)
                    print(f"State: {sys.STATE}")
                elif sys.ESP_SWAP_CONNECTED and not sys.ESP_POS_CONNECTED:
                    print("Waiting for Position ESP to Connect...")
                elif not sys.ESP_SWAP_CONNECTED and sys.ESP_POS_CONNECTED:
                    print("Waiting for Swap ESP to Connect...")
                else:
                    print("Waiting for ESPs to Connect...")

            case States.STBY_READY:
                if sys.DRONE_CONNECTED:
                    sys.STATE = States.STBY_DRONE_LAND
                    client.publish("NEST/System/State", "STBY_DRONE_LAND", qos=2, retain=True)
                    print(f"State: {sys.STATE}")
                else:
                    print("Waiting for Drone to Connect...")
                    time.sleep(1)
            
            case States.STBY_DRONE_LAND:
                if sys.DRONE_CONNECTED:
                    sys.STATE = States.POS_PINCH
                    client.publish("NEST/System/State", "POS_PINCH", qos=2, retain=True)
                    print(f"State: {sys.STATE}")
                else:
                    print("Waiting for Drone to Land...")
                    time.sleep(1)
                    
            case States.POS_PINCH:
                print("Initiating Position Pinch Process...")
                time.sleep(1)
                if sys.PINCH_COMPLETE:
                    sys.STATE = States.POS_PUSH
                    client.publish("NEST/System/State", "POS_PUSH", qos=2, retain=True)
                    print(f"State: {sys.STATE}")
                    
            case States.POS_PUSH:
                print("Initiating Position PUSH Process...")
                time.sleep(1)
                if sys.PUSH_COMPLETE:
                    sys.STATE = States.SWAP_ALIGN
                    client.publish("NEST/System/State", "SWAP_ALIGN", qos=2, retain=True)
                    print(f"State: {sys.STATE}")
            
                
        time.sleep(2) 
        print("Current State: " + str(sys.STATE))


except KeyboardInterrupt:
    client.loop_stop()
    client.disconnect()