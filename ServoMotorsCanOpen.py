import canopen
import time

# Start with creating a network representing one CAN bus
network = canopen.Network()

# Add some nodes with corresponding Object Dictionaries


# Connect to the CAN bus
# Arguments are passed to python-can's can.interface.Bus() constructor
# (see https://python-can.readthedocs.io/en/latest/bus.html).
network.connect(bustype='ixxat', channel=0, bitrate=250000)

# network.scanner.search()
#
# time.sleep(0.10)

network.nmt.state = 'PRE-OPERATIONAL'

# for node_id in network.scanner.nodes:
#     print("Found node %d!" % node_id)
#     if(node_id == 1):
motornode = network.add_node(1, 'Eds/AKD CANopen.eds')

# Read a variable using SDO
device_name = motornode.sdo['Manufacturer device name'].raw
print(device_name)

motornode.sdo['Modes of operation'].raw = 1
#set 0_V=500 rpm
motornode.sdo['Profile velocity in pp-mode'].raw = 500
rpm = motornode.sdo['Profile velocity in pp-mode'].raw
print(rpm)
#set O_ACC and O_DEC to 10
motornode.sdo['Profile acceleration'].raw = 500
motornode.sdo['Profile deceleration'].raw = 500
acc = motornode.sdo['Profile acceleration'].raw
print(acc)
dec = motornode.sdo['Profile deceleration'].raw
print(dec)

#set control word to operation enabled
motornode.sdo[0x6040].raw = 15
controlWord = motornode.sdo[0x6040].raw
print(controlWord)
#set target position to 10000 counts(one rev for me)
motornode.sdo['Target position'].raw = 180

#set control word bit 4 to start the move
motornode.sdo['Controlword'].raw = 0x1F
controlWord = motornode.sdo[0x6040].raw
print(controlWord)

acc = motornode.sdo['Profile acceleration'].raw
print(acc)
dec = motornode.sdo['Profile deceleration'].raw
print(dec)


# def print_joystick(id, dataByteArray, unknown):
#     print("id:{}, data:{}, timestamp:{}".format(id,dataByteArray,unknown))
#
#
# while(True):
#     network.subscribe(0x481, print_joystick)


network.disconnect()