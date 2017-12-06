import canopen
import time

# Start with creating a network representing one CAN bus
network = canopen.Network()

# Add some nodes with corresponding Object Dictionaries

network.connect(bustype='ixxat', channel=1, bitrate=250000)

motornode = network.add_node(1, 'Eds/AKD CANopen.eds')

for i in range(1, 4):
    motornode.pdo.tx[i].stop()
    motornode.pdo.rx[i].stop()

motornode.pdo.rx[1].clear()

motornode.pdo.rx[1].add_variable('Target position')
motornode.pdo.rx[1].add_variable('Profile velocity in pp-mode')
motornode.pdo.rx[2].add_variable('Profile acceleration')
motornode.pdo.rx[2].add_variable('Profile deceleration')
motornode.pdo.rx[1].enabled = True
motornode.pdo.rx[2].enabled = True

network.nmt.state = 'PRE-OPERATIONAL'
motornode.pdo.save()

# shutdown
motornode.sdo[0x6040].raw = 6
# enable
motornode.sdo[0x6040].raw = 7

# set control word to operation enabled
motornode.sdo[0x6040].raw = 15
controlWord = motornode.sdo[0x6040].raw
print(controlWord)

# set control word bit 4 to start the move
controlWord = motornode.sdo[0x6040].raw
print(controlWord)

latchStatus = 0
while(latchStatus != 1):
      latchStatus = motornode.sdo['LatchStatus'].raw
      latchStatus = latchStatus >> 15

print("Home is set, sleeping 5 sec")
motornode.sdo['Modes of operation'].raw = 1
time.sleep(5)


#motornode.sdo['Software position limit']['Min position limit'].raw = 0
#motornode.sdo['Software position limit']['Max position limit'].raw = 120

network.nmt.state = 'OPERATIONAL'


def setPosAcc(acc, dec, pos):
    motornode.sdo[0x6040].raw = 7
    motornode.sdo[0x6040].raw = 15
    motornode.pdo.rx[2]['Profile deceleration'].raw = dec
    motornode.pdo.rx[2]['Profile acceleration'].raw = acc
    motornode.pdo.rx[1]['Target position'].raw = pos
    motornode.pdo.rx[1].transmit()
    motornode.pdo.rx[2].transmit()
    acc = motornode.sdo['Profile acceleration'].raw
    print(acc)
    dec = motornode.sdo['Profile deceleration'].raw
    print(dec)
    posit = motornode.sdo['Target position'].raw
    print(posit)
    motornode.sdo['Controlword'].raw = 0x3F



# motornode.sdo['Homing method'].raw = 7
# motornode.sdo['HOME.DIRM'].raw = 0
# time.sleep(5)
# motornode.sdo['HOME.SET'].raw = 0

# while(True):
# acceleration = int(input("Acceleration: "))
# deceleration = int(input("Deceleration: "))
# position = int(input("Position: "))
acceleration = 200
deceleration = 200

setPosAcc(acceleration, deceleration, 60)

# for i in range(0, 5):
#     time.sleep(0.5)
#     print(i)
#     if (i % 2 == 0):
#         setPosAcc(acceleration, deceleration, 1)
#     else:
#         setPosAcc(acceleration, deceleration, 119)

# shutdown
setPosAcc(200, 200, 60)
time.sleep(1)
motornode.sdo[0x6040].raw = 6
network.disconnect()