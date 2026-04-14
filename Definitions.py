from enum import Enum

class States(Enum):
    STBY                    # Waiting for ESPs to Connect
    STBY_READY              # ESPs are connected, waiting for drone
    STBY_DRONE_LAND         # All devices are connected, waiting for confirmation of drone landing
    POS_PINCH               # Position Pinch Process Initiated
    POS_PUSH                # Position Push Process Initiated
    SWAP_ALIGN              # Swap Alignment Process Initiated
    SWAP_REMOVE             # Swap Removal Process Initiated
    SWAP_INSERT             # Swap Inert Process Initiated
    SWAP_CONNECT            # Attempt to Reconnect to Drone
    FINAL_POS_PUSH          # Position Push To Final Position Process Initiated
    FINAL_POS_REL           # Release Drone for Flight
    

ESP_SWAP_CONNECTED = False
ESP_POS_CONNECTED = False
DRONE_CONNECTED = False