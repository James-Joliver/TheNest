import paho.mqtt.client as mqtt
import time
import Definitions
from Definitions import States, SystemState

sys = SystemState()

def on_message(client, userdata, msg):


    topic = msg.topic.split("/")
    payload = msg.payload.decode()
    if payload == "rest":
        return

    print(f"Received message on topic {topic}: {payload}")
    
    
    match topic:
        case ["ESP", "SWAP", "Status"]:
            print(f"Swap Status Update: {payload}")
            if payload == "Connected":
                sys.ESP_SWAP_CONNECTED = True

            elif payload == "Disconnected":            
                sys.ESP_SWAP_CONNECTED = False
                sys.STATE = States.STBY
                client.publish("NEST/System/State", "STBY", qos=2, retain=True)

        case ["ESP", "POS", "Status"]:
            print(f"Position Status Update: {payload}")
            if payload == "Connected":
                sys.ESP_POS_CONNECTED = True

            elif payload == "Disconnected":            
                sys.ESP_POS_CONNECTED = False
                sys.STATE = States.STBY
                client.publish("NEST/System/State", "STBY", qos=2, retain=True)
                
        case ["DRONE", "Status"]:
            print(f"Drone Status Update: {payload}")
            if payload == "Connected":
                sys.DRONE_CONNECTED = True

            elif payload == "Disconnected":            
                sys.DRONE_CONNECTED = False
                if sys.STATE != States.STBY and sys.BATTERY_CONNECTED:    # Always go to STBY if ESPs are disconnected aswell
                    sys.STATE = States.STBY_READY
                    client.publish("NEST/System/State", "STBY_READY", qos=2, retain=True)
                elif not sys.BATTERY_CONNECTED:
                    print("Battery Successfully Connected From Drone")
                else:
                    sys.STATE = States.STBY
                    client.publish("NEST/System/State", "STBY", qos=2, retain=True)

        case ["DRONE", "LANDED"]:
            print(f"Drone Landing Update: {payload}")
            if payload == "Ready":
                sys.DRONE_LANDED = True
            else:
                print("Not landed propperly")
        

        case ["ESP", "POS", "Pinch"]:
            print(f"POS Pinch Update: {payload}")
            if payload == "Complete":
                sys.PINCH_COMPLETE = True
            elif payload == "In Progress":
                print("Pinch in Progress")
            else:
                print("Pinch Failure")

        case ["ESP", "POS", "Push"]:
            print(f"POS Push Update: {payload}")
            if payload == "Complete":
                sys.PUSH_COMPLETE = True

            elif payload == "In Progress":
                print("Push in Progress")

            else:
                print("Push Failure")
        
        case ["ESP", "SWAP", "Align"]:
            print(f"SWAP Alignment update: {payload}")
            if payload == "Complete":
                sys.ALIGN_COMPLETE = True

            elif payload == "In Progress":
                print("Alignment in progress")
                
            else:
                print("Alignment Failure")
        
        case ["ESP", "SWAP", "Remove"]:
            print(f"SWAP Removeal update: {payload}")
            if payload == "Complete":
                sys.REMOVE_COMPLETE = True

            elif payload == "In Progress":
                print("Removal In Progress")

            else:
                print("Removal Failure")
        
        case ["ESP", "SWAP", "Insert"]:
            print(f"SWAP Insertion update: {payload}")
            if payload == "Complete":
                sys.INSERT_COMPLETE = True

            elif payload == "In Progress":
                print("Alignment In Progress")

            else:
                print("Alignment Failure")
        
        case ["DRONE", "SEND_OFF"]:
            if payload == "Ready":
                sys.SEND_OFF_CONFIRM = True
        


def on_connect(client, userdata, flags, rc, properties):
    print("Connected with result code "+str(rc))
    client.publish("NEST/Status", "Connected", qos=2, retain=True)

def on_subscribe(client, userdata, mid, reason_codes, properties):
    print("Subscribed to topic with Qos: " + str(reason_codes[0]))
    


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

client.on_message = on_message
client.on_connect = on_connect
client.on_subscribe = on_subscribe

client.will_set("NEST/Status", "Disconnected", qos=2, retain=True)

client.connect("localhost", 1883)       

client.loop_start()

client.subscribe("#")



sys.STATE = States.STBY

client.publish("NEST/System/State", "rest", qos=2)
client.publish("ESP/SWAP/Status", "Connected", qos=2)
client.publish("ESP/POS/Status", "Connected", qos=2)
client.publish("DRONE/Status", "Connected", qos=2)
client.publish("ESP/POS/Pinch", "rest", qos=2)
client.publish("ESP/POS/Push", "rest", qos=2)
client.publish("ESP/SWAP/Align", "rest", qos=2)
client.publish("ESP/SWAP/Remove", "rest", qos=2)
client.publish("ESP/SWAP/Insert", "rest", qos=2)
client.publish("DRONE/SEND_OFF","rest", qos=2)
client.publish("DRONE/LANDED", "rest", qos=2)




try:


    while True:
        match sys.STATE:
            case States.STBY:
                print("ESP_SWAP_CONNECTED: " + str(sys.ESP_SWAP_CONNECTED) + " | ESP_POS_CONNECTED: " + str(sys.ESP_POS_CONNECTED))
                if sys.ESP_SWAP_CONNECTED and sys.ESP_POS_CONNECTED:
                    sys.STATE = States.STBY_READY
                    client.publish("NEST/System/State", "STBY_READY", qos=2, retain=True)
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
                elif not sys.BATTERY_CONNECTED:
                    sys.STATE = State.SWAP_ALIGN
                else:
                    print("Waiting for Drone to Connect...")
            
            case States.STBY_DRONE_LAND:
                if sys.DRONE_LANDED:
                    sys.STATE = States.POS_PINCH
                    client.publish("NEST/System/State", "POS_PINCH", qos=2, retain=True)
                    print(f"State: {sys.STATE}")
                else:
                    print("Waiting for Drone to Land...")
                    
            case States.POS_PINCH:
                print("Initiating Position Pinch Process...")
                if sys.PINCH_COMPLETE:
                    sys.STATE = States.POS_PUSH
                    client.publish("NEST/System/State", "POS_PUSH", qos=2, retain=True)
                    print(f"State: {sys.STATE}")
                    
            case States.POS_PUSH:
                print("Initiating Position PUSH Process...")
                if sys.PUSH_COMPLETE:
                    sys.STATE = States.SWAP_ALIGN
                    client.publish("NEST/System/State", "SWAP_ALIGN_EMPTY", qos=2, retain=True)
                    print(f"State: {sys.STATE}")
        
            case States.SWAP_ALIGN:
                print("Initiating Alignment Process...")
                if sys.ALIGN_COMPLETE and sys.BATTERY_CONNECTED:
                    sys.STATE = States.SWAP_REMOVE
                    client.publish("NEST/System/State", "SWAP_REMOVE", qos=2, retain=True)
                    sys.ALIGN_COMPLETE = False
                    print(f"State: {sys.STATE}")
                
                elif sys.ALIGN_COMPLETE and not sys.BATTERY_CONNECTED:
                    sys.STATE = States.SWAP_INSERT
                    client.publish("NEST/System/State", "SWAP_INSERT", qos=2, retain=True)
                    sys.ALIGN_COMPLETE = False
                    print(f"State: {sys.STATE}")
            
            case States.SWAP_REMOVE:
                print("Initiating Removal Process...")
                sys.BATTERY_CONNECTED = False
            
                if sys.REMOVE_COMPLETE:
                    sys.STATE = States.SWAP_ALIGN
                    client.publish("NEST/System/State", "SWAP_ALIGN_NEW", qos=2, retain=True)

                
            case States.SWAP_INSERT:
                print("Initiating Insertion Process...")
                
                if sys.INSERT_COMPLETE:
                    sys.BATTERY_CONNECTED = True
                    sys.STATE = States.RECONNECT
                    client.publish("NEST/System/State", "RECONNECT", qos=2, retain=True)
                
            case States.RECONNECT:
                print("Reconnecting with drone to confirm battery swap")

                if sys.DRONE_CONNECTED:
                    sys.STATE = States.SEND_OFF
                    client.publish("NEST/System/State", "SEND_OFF", qos=2, retain=True)
            
            case States.SEND_OFF:
                print("Sending Drone Away")
                
                if sys.SEND_OFF_CONFIRM:

                    sys.reset()
                    client.publish("NEST/System/State", "rest", qos=2)
                    client.publish("DRONE/Status", "rest", qos=2)
                    client.publish("DRONE/Landed", "rest", qos=2)
                    client.publish("ESP/POS/Pinch", "rest", qos=2)
                    client.publish("ESP/POS/Push", "rest", qos=2)
                    client.publish("ESP/SWAP/Align", "rest", qos=2)
                    client.publish("ESP/SWAP/Remove", "rest", qos=2)
                    client.publish("ESP/SWAP/Insert", "rest", qos=2)
                    client.publish("DRONE/SEND_OFF","rest", qos=2)

                    sys.STATE = States.STBY_READY
                    client.publish("NEST/System/State", "STBY_READY", qos=2, retain=True)


                
                

            
                
        time.sleep(2) 
        print("Current State: " + str(sys.STATE))


except KeyboardInterrupt:
    client.loop_stop()
    client.disconnect()