**LIST OF TOPICS THAT WE ARE INTERESTED IN**
--------------------------------------------------------

*** NEST SUBSCRIPTIONS ***
*FROM ESP SWAP*
ESP/SWAP/Status
- Connected
- Disconnected
ESP/SWAP/Align
- Complete
- In Progress
ESP/SWAP/Remove
- Complete
- In Progress
ESP/SWAP/Insert
- Complete
- In Progress

*FROM ESP POS*
ESP/POS/Status
- Connected
- Disconnected
ESP/POS/Pinch
- Complete
- In Progress
ESP/POS/Push
- Complete
- In Progress

*FROM DRONE*
DRONE/Status
- Connected
- Disconnected
DRONE/LANDED
- Ready
DRONE/SEND_OFF
- Ready


*** ESP POS SUBSCRIPTIONS ***
*NEST/System/State*
- POS_PINCH             # Pinch drone
- POS_PUSH              # Push drone

*NEST/Status*
- Connected             # Run as normal
- Disconnected          # Pi is disconnected, ERROR


*** ESP SWAP SUBSCRIPTIONS ***
*NEST/System/State*
- SWAP_ALIGN_EMPTY      # Move to empty battery position
- SWAP_REMOVE           # Remove process
- SWAP_ALIGN_NEW        # Move to filled battery position
- SWAP_INSERT           # Insert new battery


*NEST/Status*
- Connected             # Run as normal
- Disconnected          # Pi is disconnected, ERROR



*** DRONE SUBSCRIPTIONS ***
*NEST/System/State*
- SEND_OFF

*NEST/Status*
- Connected             # Run as normal
- Disconnected          # Pi is disconnected, ERROR

