import canopen
import time
import socket
from RPiCom import RpiPitchRoll
from motorModelPls import MotorPositionModel
import numpy as np
import pickle


# Start with creating a network representing one CAN bus
network = canopen.Network()

# Add some nodes with corresponding Object Dictionaries

network.connect(bustype='ixxat', channel=1, bitrate=250000)
motornodeTop = network.add_node(3, 'Eds/AKD CANopen.eds')
#sets parameter
def init(nodeTop):
    # set mode to position profile mode
    nodeTop.sdo['Modes of operation'].raw = 1

    nodeTop.sdo['FBUS.PARAM05'].raw = 16

    fbusparam5Top = nodeTop.sdo['FBUS.PARAM05'].raw
    print(fbusparam5Top)

    #set home mode to 4
    nodeTop.sdo['HOME.MODEM'].raw = 4

    #set rotation direction of homing
    nodeTop.sdo['HOME.DIRM'].raw = 0   #rotera vänster
    #set digital input as home reference switch
    nodeTop.sdo['DIN1.MODE'].raw = 11

    # sets the home auto move flag
    nodeTop.sdo['HOME.AUTOMOVE'].raw = 1

    # set gear ratio to 100:1
    nodeTop.sdo['Gear ratio']['Motor revolutions'].raw = 100
    nodeTop.sdo['Gear ratio']['Shaft revolutions'].raw = 1
    nodeTop.sdo['Feed constant']['Feed'].raw = 360

    # set home offset
    nodeTop.sdo['Home offset'].raw = 1

    #set pvScaling factor
    nodeTop.sdo['PV scaling factor']['DS402.VELSCALENUM'].raw = 100

    # set homing speed
    nodeTop.sdo['Homing speeds']['Fast homing speed'].raw = 0.5
############################################MODULO###############################################
    # enables modulo
    nodeTop.sdo['PL.MODPEN'].raw = 1

    # sets modulo lower range
    nodeTop.sdo['PL.MODP1'].raw = 0

    # sets modulo higher range
    nodeTop.sdo['PL.MODP2'].raw = 360

    #sets direction for motion tasks
    nodeTop.sdo['PL.MODPDIR'].raw = 3

def initPDOs(nodeTop):

    for i in range(1, 4):
        nodeTop.pdo.tx[i].stop()
        nodeTop.pdo.rx[i].stop()

    nodeTop.pdo.rx[1].clear()

    nodeTop.pdo.rx[1].add_variable('Target position')
    nodeTop.pdo.rx[1].add_variable('Profile velocity in pp-mode')
    nodeTop.pdo.rx[2].add_variable('Profile acceleration')
    nodeTop.pdo.rx[2].add_variable('Profile deceleration')
    nodeTop.pdo.rx[3].add_variable('Controlword')
    nodeTop.pdo.rx[1].enabled = True
    nodeTop.pdo.rx[2].enabled = True
    nodeTop.pdo.rx[3].enabled = True

    network.nmt.state = 'PRE-OPERATIONAL'
    nodeTop.pdo.save()

#software enable
def softwareEnable(nodeTop):
    print("software enable")
    # shutdown
    nodeTop.sdo[0x6040].raw = 6
    # enable
    nodeTop.sdo[0x6040].raw = 7

    # set control word to operation enabled
    nodeTop.sdo[0x6040].raw = 15

def findHome(nodeTop):

    latchStatusTop = 0
    #While until home is found by hall effect sensors
    while ((latchStatusTop != 1)):
        latchStatusTop = nodeTop.sdo['LatchStatus'].raw
        latchStatusTop = latchStatusTop >> 15
        time.sleep(0.1)

    print("Home is set, sleeping 1 sec")
    time.sleep(1)

#set position in degrees and acceleration and deceleration in rpm/s and start motor
def setPosAcc(motornode, acc, dec, pos):
    try:
        #motornode.sdo[0x6040].raw = 7
        #time.sleep(0.001)
        #motornode.sdo[0x6040].raw = 15
        motornode.pdo.rx[3]['Controlword'].raw = 15
        motornode.pdo.rx[3].transmit()
        motornode.pdo.rx[2]['Profile deceleration'].raw = dec
        motornode.pdo.rx[2]['Profile acceleration'].raw = acc
        motornode.pdo.rx[1]['Target position'].raw = pos
        motornode.pdo.rx[1]['Profile velocity in pp-mode'].raw = 150
        motornode.pdo.rx[1].transmit()
        motornode.pdo.rx[2].transmit()

        #motornode.sdo['Controlword'].raw = 0x3F
        motornode.pdo.rx[3]['Controlword'].raw = 0x3F
        motornode.pdo.rx[3].transmit()
    except:
        pass

initPDOs(motornodeTop)
print('initpdo done')
init(motornodeTop)
print('init done')
softwareEnable(motornodeTop)
findHome(motornodeTop)
print('findhome done')
network.nmt.state = 'OPERATIONAL'

while(True):
    toppos = input('position top: ')

    toppos = float(toppos)
    if(toppos > 10):
        toppos = 10
    if(toppos < -10):
        toppos = -10

    setPosAcc(motornodeTop, 75, 75, toppos)
    print("Going to pos: {}".format(toppos))