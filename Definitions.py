from enum import Enum, auto

class States(Enum):
    STBY               = auto()   # Waiting for ESPs to Connect
    STBY_READY         = auto()   # ESPs are connected, waiting for drone
    STBY_DRONE_LAND    = auto()   # All devices are connected, waiting for confirmation of drone landing
    POS_PINCH          = auto()   # Position Pinch Process Initiated
    POS_PUSH           = auto()   # Position Push Process Initiated
    SWAP_ALIGN         = auto()   # Swap Alignment Process Initiated
    SWAP_REMOVE        = auto()   # Swap Removal Process Initiated
    SWAP_INSERT        = auto()   # Swap Inert Process Initiated
    SWAP_CONNECT       = auto()   # Attempt to Reconnect to Drone
    FINAL_POS_PUSH     = auto()   # Position Push To Final Position Process Initiated
    FINAL_POS_REL      = auto()   # Release Drone for Flight
    

ESP_SWAP_CONNECTED = False
ESP_POS_CONNECTED = False
DRONE_CONNECTED = False