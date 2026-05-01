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
    RECONNECT          = auto()   # Attempt to reconnect with Drone
    SEND_OFF           = auto()   # Confirm a return to STBY_READY and reset states

    
    

class SystemState:
    def __init__(self):
        self.reset()


    def reset(self):
        self.STATE = States.STBY
        self.DRONE_LANDED = False
        self.ESP_SWAP_CONNECTED = False
        self.ESP_POS_CONNECTED = False
        self.DRONE_CONNECTED = False
        self.DRONE_COMPLETE = False
        self.PINCH_COMPLETE = False
        self.PUSH_COMPLETE = False
        self.ALIGN_COMPLETE = False
        self.REMOVE_COMPLETE = False
        self.INSERT_COMPLETE = False
        self.BATTERY_CONNECTED = True
        self.SEND_OFF_CONFIRM = False

