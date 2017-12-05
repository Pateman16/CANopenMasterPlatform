import canopen
import time

# Start with creating a network representing one CAN bus
network = canopen.Network()

# Add some nodes with corresponding Object Dictionaries

network.connect(bustype='ixxat', channel=0, bitrate=250000)

#Left and right seen from the front of the platform.
motornodeLeft = network.add_node(1, 'Eds/AKD CANopen.eds')
motornodeRight = network.add_node(1, 'Eds/AKD CANopen.eds')
#defines rx and tx PDOs of the nodes in network
def initPDOs(nodeLeft, nodeRight):

    for i in range(1, 4):
        nodeLeft.pdo.tx[i].stop()
        nodeLeft.pdo.rx[i].stop()
        nodeRight.pdo.tx[i].stop()
        nodeRight.pdo.rx[i].stop()

    nodeLeft.pdo.rx[1].clear()

    nodeLeft.pdo.rx[1].add_variable('Target position')
    nodeLeft.pdo.rx[1].add_variable('Profile velocity in pp-mode')
    nodeLeft.pdo.rx[2].add_variable('Profile acceleration')
    nodeLeft.pdo.rx[2].add_variable('Profile deceleration')
    nodeLeft.pdo.rx[1].enabled = True
    nodeLeft.pdo.rx[2].enabled = True

    nodeRight.pdo.rx[1].clear()

    nodeRight.pdo.rx[1].add_variable('Target position')
    nodeRight.pdo.rx[1].add_variable('Profile velocity in pp-mode')
    nodeRight.pdo.rx[2].add_variable('Profile acceleration')
    nodeRight.pdo.rx[2].add_variable('Profile deceleration')
    nodeRight.pdo.rx[1].enabled = True
    nodeRight.pdo.rx[2].enabled = True

    network.nmt.state = 'PRE-OPERATIONAL'
    motornodeLeft.pdo.save()
    nodeRight.pdo.save()

#enable drivemode, go to hall effect sensor, set home.
def findHome(nodeLeft, nodeRight):
    # shutdown
    nodeLeft.sdo[0x6040].raw = 6
    nodeRight.sdo[0x6040].raw = 6
    # enable
    nodeLeft.sdo[0x6040].raw = 7
    nodeRight.sdo[0x6040].raw = 7

    # set control word to operation enabled
    nodeLeft.sdo[0x6040].raw = 15
    nodeRight.sdo[0x6040].raw = 15

    # set control word bit 4 to start the move
    #?

    latchStatusLeft = 0
    latchStatusRight = 0
    #While until home is found by hall effect sensors
    while (latchStatusLeft != 1 and latchStatusRight != 1):
        latchStatusLeft = motornodeLeft.sdo['LatchStatus'].raw
        latchStatusLeft = latchStatusLeft >> 15

        latchStatusRight = motornodeRight.sdo['LatchStatus'].raw
        latchStatusRight = latchStatusRight >> 15

    print("Home is set, sleeping 5 sec")
    time.sleep(1)

#set position in degrees and acceleration and deceleration in rpm/s and start motor
def setPosAcc(motornode, acc, dec, pos):
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

#sets the software limits for the motors, in this application dont go more than 0 to 120
def setSWLimits(lowerLimit, upperLimit):
    motornodeLeft.sdo['Software position limit']['Min position limit'].raw = lowerLimit
    motornodeLeft.sdo['Software position limit']['Max position limit'].raw = upperLimit
    motornodeRight.sdo['Software position limit']['Min position limit'].raw = lowerLimit
    motornodeRight.sdo['Software position limit']['Max position limit'].raw = upperLimit

initPDOs(motornodeLeft, motornodeRight)

#set mode to position profile mode
motornodeLeft.sdo['Modes of operation'].raw = 1
motornodeRight.sdo['Modes of operation'].raw = 1

findHome(motornodeLeft, motornodeRight)

setSWLimits(0, 121)

network.nmt.state = 'OPERATIONAL'

acceleration = 1000*6
deceleration = 1000*6
#f_in = open(r'\\.\pipe\NPtest', 'r+b', 0)
while(True):
    leftpos = input('position left: ')
    if(leftpos == 'stop'):
        break
    rightpos = input('position right: ')

    leftpos = float(leftpos)
    rightpos = float(rightpos)
    if(rightpos > 120):
        rightpos = 120
    if(rightpos < 1):
        rightpos = 1
    if (leftpos > 120):
        leftpos = 120
    if (leftpos < 1):
        leftpos = 1

    setPosAcc(motornodeLeft,acceleration, deceleration, leftpos)
    setPosAcc(motornodeLeft,acceleration, deceleration, rightpos)

    posReachedLeft = 0
    posReachedRight = 0
    #While until home is found by hall effect sensors
    while (posReachedLeft != 1 and posReachedRight != 1):
        posReachedLeft = motornodeLeft.sdo['Statusword'].raw
        print(posReachedLeft)
        posReachedLeft = posReachedLeft & 0b10000000000
        posReachedLeft = posReachedLeft >> 10
        print(posReachedLeft)

        posReachedRight = motornodeRight.sdo['Statusword'].raw
        print(posReachedRight)
        posReachedRight = posReachedRight & 0b10000000000
        posReachedRight = posReachedRight >> 10
        posReachedRight


# shutdown
setPosAcc(motornodeLeft,acceleration, deceleration, 60)
setPosAcc(motornodeRight,acceleration, deceleration, 60)
time.sleep(1)
motornodeLeft.sdo[0x6040].raw = 6
motornodeRight.sdo[0x6040].raw = 6
network.disconnect()