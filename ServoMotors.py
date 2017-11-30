import canopen
import time
from RPiCom import RpiPitchRoll
from motorModelClass import MotorPositionModel
import numpy as np
import pickle

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

#set position in degrees and acceleration and decelartion in rpm/s and start motor
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

#calibrateVal is the value that determines how many samples is made. degree/sample = 120 / calibrateVal
def calibratePlatform(calibrateVal):
    # Here we define the UDP IP address as well as the port number that we have
    SERVER_IP_ADDRESS = "169.254.209.246"  # Ip address of the raspberry server
    SERVER_PORT_NO = 8888  # Port from the raspberry server

    rPiCom = RpiPitchRoll(SERVER_IP_ADDRESS, SERVER_PORT_NO)
    dataSet = np.empty(shape=[0, 4])
    for i in range(calibrateVal):
        degreeLeft = i * (120 / calibrateVal)
        setPosAcc(motornodeLeft, 1000, 1000, degreeLeft)
        for j in range(calibrateVal):
            degreeRight = 120 - j * (120 / calibrateVal)
            setPosAcc(motornodeRight, 1000, 1000, degreeRight)
            ############################wait for ack from both motors before doing this below.#################################################################################
            dataSet = np.append(dataSet,
                                [[degreeLeft, degreeRight, rPiCom.getPitchRoll()[0], rPiCom.getPitchRoll()[1]]], axis=0)

    rPiCom.closeSocket()
    np.savetxt('values.txt', dataSet)
    poly = MotorPositionModel(dataSet)
    with open('PolyModel.pkl', 'wb') as output:
        pickle.dump(poly, output, pickle.HIGHEST_PROTOCOL)

    return poly

    # while (True):
    #     pitch = float(input('pitch: '))
    #     roll = float(input('roll: '))
    #
    #     left = polyModel.getLeftpos(pitch, roll)
    #     right = polyModel.getRightpos(pitch, roll)
    #     print("leftMotor: {}, rightMotor: {}".format(left, right))

#if already calibrated, load the previous polymodel for the platform, otherwise calibrate again
#The model is a function that calculates position on motors depending on pitch and roll as input
def getModel():
    try:
        with open('PolyModel.pkl', 'rb') as inp:
            polyM = pickle.load(inp)
            inp.flush()
            inp.close()
            return polyM
    except:
        polyM = calibratePlatform(20)
        return polyM

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

polyModel = getModel()


acceleration = 1000*6
deceleration = 1000*6
#f_in = open(r'\\.\pipe\NPtest', 'r+b', 0)
while(True):
    pitch = float(input('pitch: '))
    roll = float(input('roll: '))
    polyModel.getLeftpos(pitch, roll)
    polyModel.getRightpos(pitch, roll)


# shutdown
setPosAcc(motornodeLeft,acceleration, deceleration, 60)
setPosAcc(motornodeRight,acceleration, deceleration, 60)
time.sleep(1)
motornodeLeft.sdo[0x6040].raw = 6
motornodeRight.sdo[0x6040].raw = 6
network.disconnect()
