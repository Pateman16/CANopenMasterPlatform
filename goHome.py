import canopen
import time

# Start with creating a network representing one CAN bus
network = canopen.Network()

# Add some nodes with corresponding Object Dictionaries

network.connect(bustype='ixxat', channel=0, bitrate=250000)

motornode = network.add_node(1, 'Eds/AKD CANopen.eds')

# shutdown
motornode.sdo[0x6040].raw = 6
# enable
motornode.sdo[0x6040].raw = 7
# set control word to operation enabled
motornode.sdo[0x6040].raw = 15

while(True):
    latchStatus = motornode.sdo['LatchStatus'].raw
    latchStatus = latchStatus >> 15
    print(latchStatus)

network.disconnect()