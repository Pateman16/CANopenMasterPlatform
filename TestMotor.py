import canopen
import time

# Start with creating a network representing one CAN bus
network = canopen.Network()

# Add some nodes with corresponding Object Dictionaries

network.connect(bustype='ixxat', channel=1, bitrate=250000)

#Left and right seen from the front of the platform.
motornodeLeft = network.add_node(1, 'Eds/AKD CANopen.eds')
motornodeRight = network.add_node(2, 'Eds/AKD CANopen.eds')
#defines rx and tx PDOs of the nodes in network

def init(nodeLeft, nodeRight):
    # set mode to position profile mode
    nodeLeft.sdo['Modes of operation'].raw = 1
    nodeRight.sdo['Modes of operation'].raw = 1

    nodeLeft.sdo['FBUS.PARAM05'].raw = 16
    nodeRight.sdo['FBUS.PARAM05'].raw = 16

    fbusparam5Left = nodeLeft.sdo['FBUS.PARAM05'].raw
    print(fbusparam5Left)

    fbusparam5Right = nodeRight.sdo['FBUS.PARAM05'].raw
    print(fbusparam5Right)

    #set home mode to 4
    nodeLeft.sdo['HOME.MODEM'].raw = 4
    nodeRight.sdo['HOME.MODEM'].raw = 4

    #set rotation direction of homing
    nodeLeft.sdo['HOME.DIRM'].raw = 1
    nodeRight.sdo['HOME.DIRM'].raw = 0

    #set digital input as home reference switch
    nodeLeft.sdo['DIN1.MODE'].raw = 11
    nodeRight.sdo['DIN1.MODE'].raw = 11

    # sets the home auto move flag
    nodeLeft.sdo['HOME.AUTOMOVE'].raw = 1
    nodeRight.sdo['HOME.AUTOMOVE'].raw = 1
    #set gear ratio to 80:1
    nodeLeft.sdo['Gear ratio']['Motor revolutions'].raw = 80
    nodeLeft.sdo['Gear ratio']['Shaft revolutions'].raw = 1
    nodeLeft.sdo['Feed constant']['Feed'].raw = 360

    nodeRight.sdo['Gear ratio']['Motor revolutions'].raw = 80
    nodeRight.sdo['Gear ratio']['Shaft revolutions'].raw = 1
    nodeRight.sdo['Feed constant']['Feed'].raw = 360

    # set home offset
    nodeLeft.sdo['Home offset'].raw = 120
    nodeRight.sdo['Home offset'].raw = 1

    #set pvScaling factor
    nodeLeft.sdo['PV scaling factor']['DS402.VELSCALENUM'].raw = 80
    nodeRight.sdo['PV scaling factor']['DS402.VELSCALENUM'].raw = 80

    # set homing speed
    nodeLeft.sdo['Homing speeds']['Fast homing speed'].raw = 5
    nodeRight.sdo['Homing speeds']['Fast homing speed'].raw = 5
############################################MODULO###############################################
    # enables modulo
    nodeLeft.sdo['PL.MODPEN'].raw = 1
    nodeRight.sdo['PL.MODPEN'].raw = 1

    # sets modulo lower range
    nodeLeft.sdo['PL.MODP1'].raw = 0
    nodeRight.sdo['PL.MODP1'].raw = 0

    # sets modulo higher range
    nodeLeft.sdo['PL.MODP2'].raw = 360
    nodeRight.sdo['PL.MODP2'].raw = 360

    #sets direction for motion tasks
    nodeLeft.sdo['PL.MODPDIR'].raw = 3
    nodeRight.sdo['PL.MODPDIR'].raw = 3
##################################################################################################


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
    nodeLeft.pdo.save()
    nodeRight.pdo.save()

#software enable
def softwareEnable(nodeLeft, nodeRight):
    print("software enable")
    # shutdown
    nodeLeft.sdo[0x6040].raw = 6
    nodeRight.sdo[0x6040].raw = 6
    # enable
    nodeLeft.sdo[0x6040].raw = 7
    nodeRight.sdo[0x6040].raw = 7

    # set control word to operation enabled
    nodeLeft.sdo[0x6040].raw = 15
    nodeRight.sdo[0x6040].raw = 15
#enable drivemode, go to hall effect sensor, set home.
def findHome(nodeLeft, nodeRight):
    softwareEnable(nodeLeft, nodeRight)

    latchStatusLeft = 0
    latchStatusRight = 0
    #While until home is found by hall effect sensors
    while ((latchStatusLeft != 1) or (latchStatusRight != 1)):
        latchStatusLeft = motornodeLeft.sdo['LatchStatus'].raw
        latchStatusLeft = latchStatusLeft >> 15
        latchStatusRight = motornodeRight.sdo['LatchStatus'].raw
        latchStatusRight = latchStatusRight >> 15

    print("Home is set, sleeping 1 sec")
    time.sleep(1)

#set position in degrees and acceleration and deceleration in rpm/s and start motor
def setPosAcc(motornode, acc, dec, pos):
    motornode.sdo[0x6040].raw = 7
    motornode.sdo[0x6040].raw = 15
    motornode.pdo.rx[2]['Profile deceleration'].raw = dec
    motornode.pdo.rx[2]['Profile acceleration'].raw = acc
    motornode.pdo.rx[1]['Target position'].raw = pos
    motornode.pdo.rx[1]['Profile velocity in pp-mode'].raw = 150
    motornode.pdo.rx[1].transmit()
    motornode.pdo.rx[2].transmit()
    motornode.sdo['Controlword'].raw = 0x3F

#sets the software limits for the motors, in this application dont go more than 0 to 120
def setSWLimits(lowerLimit, upperLimit):

    motornodeLeft.sdo['Software position limit']['Min position limit'].raw = lowerLimit
    motornodeLeft.sdo['Software position limit']['Max position limit'].raw = upperLimit
    motornodeRight.sdo['Software position limit']['Min position limit'].raw = lowerLimit
    motornodeRight.sdo['Software position limit']['Max position limit'].raw = upperLimit
    motornodeLeft.sdo['SWLS.ENM'].raw = 3
    motornodeRight.sdo['SWLS.ENM'].raw = 3
    softwareEnable(motornodeLeft, motornodeRight)
    softwareEnable(motornodeLeft, motornodeRight)

initPDOs(motornodeLeft, motornodeRight)

init(motornodeLeft, motornodeRight)

#softwareEnable(motornodeLeft, motornodeRight)
#findHome(motornodeLeft, motornodeRight)

setSWLimits(0, 121)

network.nmt.state = 'OPERATIONAL'

#degrees/second
acceleration = 700
deceleration = 700
#f_in = open(r'\\.\pipe\NPtest', 'r+b', 0)

# while(True):
#     leftpos = input('position left: ')
#     if(leftpos == 'stop'):
#         break
#     rightpos = input('position right: ')
#
#     leftpos = float(leftpos)
#     rightpos = float(rightpos)
#     if(rightpos > 120):
#      rightpos = 120
#     if(rightpos < 1):
#      rightpos = 1
#     if (leftpos > 120):
#      leftpos = 120
#     if (leftpos < 1):
#      leftpos = 1
for i in range(40):
    time.sleep(0.6)
    if(i%2 == 0):
        setPosAcc(motornodeLeft, acceleration, deceleration, 60)
        setPosAcc(motornodeRight, acceleration, deceleration, 60)
    else:
        setPosAcc(motornodeLeft, acceleration, deceleration, 120)
        setPosAcc(motornodeRight, acceleration, deceleration, 1)

    # #While until home is found by hall effect sensors
    # while (posReachedLeft != 1 and posReachedRight != 1):
    #     posReachedLeft = motornodeLeft.sdo['Statusword'].raw
    #     print(posReachedLeft)
    #     posReachedLeft = posReachedLeft & 0b10000000000
    #     posReachedLeft = posReachedLeft >> 10
    #     print(posReachedLeft)
    #
    #     posReachedRight = motornodeRight.sdo['Statusword'].raw
    #     print(posReachedRight)
    #     posReachedRight = posReachedRight & 0b10000000000
    #     posReachedRight = posReachedRight >> 10
    #     posReachedRight


# shutdown
setPosAcc(motornodeLeft,acceleration, deceleration, 120)
setPosAcc(motornodeRight,acceleration, deceleration, 1)
print("shutting down")
time.sleep(1)
motornodeLeft.sdo[0x6040].raw = 6
motornodeRight.sdo[0x6040].raw = 6
network.disconnect()