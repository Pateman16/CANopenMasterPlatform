import canopen
import time

# Start with creating a network representing one CAN bus
network = canopen.Network()

# Add some nodes with corresponding Object Dictionaries

network.connect(bustype='ixxat', channel=1, bitrate=250000)
motornode = network.add_node(2, 'Eds/AKD CANopen.eds')

def init(node):
    # set mode to position profile mode
    node.sdo['Modes of operation'].raw = 1

    node.sdo['FBUS.PARAM05'].raw = 16

    fbusparam5Left = node.sdo['FBUS.PARAM05'].raw
    print(fbusparam5Left)

    #set home mode to 4
    node.sdo['HOME.MODEM'].raw = 4

    #set rotation direction of homing
    node.sdo['HOME.DIRM'].raw = 0 #0 på right och 1 på left

    #set digital input as home reference switch
    node.sdo['DIN1.MODE'].raw = 11

    # sets the home auto move flag
    node.sdo['HOME.AUTOMOVE'].raw = 1
    #set gear ratio to 80:1
    node.sdo['Gear ratio']['Motor revolutions'].raw = 80
    node.sdo['Gear ratio']['Shaft revolutions'].raw = 1
    node.sdo['Feed constant']['Feed'].raw = 360

    # set home offset
    node.sdo['Home offset'].raw = 1 #1 om vi ska ha höger, 80 om vi ska ha vänster


    #set pvScaling factor
    node.sdo['PV scaling factor']['DS402.VELSCALENUM'].raw = 80

    # set homing speed
    node.sdo['Homing speeds']['Fast homing speed'].raw = 1
############################################MODULO###############################################
    # enables modulo
    node.sdo['PL.MODPEN'].raw = 1

    # sets modulo lower range
    node.sdo['PL.MODP1'].raw = 0

    # sets modulo higher range
    node.sdo['PL.MODP2'].raw = 360

    #sets direction for motion tasks
    node.sdo['PL.MODPDIR'].raw = 3

#defines rx and tx PDOs of the nodes in network
def initPDOs(node):

    for i in range(1, 4):
        node.pdo.tx[i].stop()
        node.pdo.rx[i].stop()

    node.pdo.rx[1].clear()

    node.pdo.rx[1].add_variable('Target position')
    node.pdo.rx[1].add_variable('Profile velocity in pp-mode')
    node.pdo.rx[2].add_variable('Profile acceleration')
    node.pdo.rx[2].add_variable('Profile deceleration')
    node.pdo.rx[1].enabled = True
    node.pdo.rx[2].enabled = True

    network.nmt.state = 'PRE-OPERATIONAL'
    node.pdo.save()

#software enable
def softwareEnable(node):
    print("software enable")
    # shutdown
    node.sdo[0x6040].raw = 6
    # enable
    node.sdo[0x6040].raw = 7

    # set control word to operation enabled
    node.sdo[0x6040].raw = 15

def findHome(node):

    latchStatus = 0
    #While until home is found by hall effect sensors
    while ((latchStatus != 1)):
        latchStatus = motornode.sdo['LatchStatus'].raw
        latchStatus = latchStatus >> 15

    print("Home is set, sleeping 1 sec")
    time.sleep(1)

def setPosAcc(motornode, acc, dec, pos):
    motornode.sdo[0x6040].raw = 7
    motornode.sdo[0x6040].raw = 15
    motornode.pdo.rx[2]['Profile deceleration'].raw = dec
    motornode.pdo.rx[2]['Profile acceleration'].raw = acc
    motornode.pdo.rx[1]['Target position'].raw = pos
    motornode.pdo.rx[1]['Profile velocity in pp-mode'].raw = 75
    motornode.pdo.rx[1].transmit()
    motornode.pdo.rx[2].transmit()
    motornode.sdo['Controlword'].raw = 0x3F

def setSWLimits(lowerLimit, upperLimit):

    motornode.sdo['Software position limit']['Min position limit'].raw = lowerLimit
    motornode.sdo['Software position limit']['Max position limit'].raw = upperLimit

    motornode.sdo['SWLS.ENM'].raw = 3

initPDOs(motornode)

init(motornode)

softwareEnable(motornode)
findHome(motornode)
#
setSWLimits(0, 81)
#
network.nmt.state = 'OPERATIONAL'
#
# #degrees/second
acceleration = 350
deceleration = 350
# #f_in = open(r'\\.\pipe\NPtest', 'r+b', 0)
#
while(True):
    pos = input('position: ')
    if(pos == 'stop'):
     break

    pos = float(pos)
    if (pos > 80):
        pos = 80
    if (pos < 1):
        pos = 1

    setPosAcc(motornode, acceleration, deceleration, pos)