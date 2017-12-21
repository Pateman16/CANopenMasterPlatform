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

#Left and right seen from the front of the platform.
motornodeLeft = network.add_node(1, 'Eds/AKD CANopen.eds')
motornodeRight = network.add_node(2, 'Eds/AKD CANopen.eds')

#sets parameter
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
    nodeLeft.sdo['Home offset'].raw = 80
    nodeRight.sdo['Home offset'].raw = 1

    #set pvScaling factor
    nodeLeft.sdo['PV scaling factor']['DS402.VELSCALENUM'].raw = 80
    nodeRight.sdo['PV scaling factor']['DS402.VELSCALENUM'].raw = 80

    # set homing speed
    nodeLeft.sdo['Homing speeds']['Fast homing speed'].raw = 1
    nodeRight.sdo['Homing speeds']['Fast homing speed'].raw = 1
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

    latchStatusLeft = 0
    latchStatusRight = 0
    #While until home is found by hall effect sensors
    while ((latchStatusLeft != 1) or (latchStatusRight != 1)):
        time.sleep(0.3)
        latchStatusLeft = motornodeLeft.sdo['LatchStatus'].raw
        latchStatusLeft = latchStatusLeft >> 15
        latchStatusRight = motornodeRight.sdo['LatchStatus'].raw
        latchStatusRight = latchStatusRight >> 15

    print("Home is set")

#set position in degrees and acceleration and deceleration in rpm/s and start motor
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

#sets the software limits for the motors, in this application dont go more than 0 to 120
def setSWLimits(lowerLimit, upperLimit):

    motornodeLeft.sdo['Software position limit']['Min position limit'].raw = lowerLimit
    motornodeLeft.sdo['Software position limit']['Max position limit'].raw = upperLimit
    motornodeRight.sdo['Software position limit']['Min position limit'].raw = lowerLimit
    motornodeRight.sdo['Software position limit']['Max position limit'].raw = upperLimit
    motornodeLeft.sdo['SWLS.ENM'].raw = 3
    motornodeRight.sdo['SWLS.ENM'].raw = 3
    #softwareEnable(motornodeLeft, motornodeRight)
    #softwareEnable(motornodeLeft, motornodeRight)

#calibrateVal is the value that determines how many samples is made. degree/sample = 120 / calibrateVal
def calibratePlatform(calibrateVal):
    # Here we define the UDP IP address as well as the port number that we have
    SERVER_IP_ADDRESS = "169.254.209.246"  # Ip address of the raspberry server
    SERVER_PORT_NO = 8888  # Port from the raspberry server

    rPiCom = RpiPitchRoll(SERVER_IP_ADDRESS, SERVER_PORT_NO)
    dataSet = np.empty(shape=[0, 4])
    for i in range(calibrateVal):
        degreeLeft = i * (80 / calibrateVal)
        setPosAcc(motornodeLeft, 350, 350, degreeLeft)
        posReachedLeft = 0
        while((posReachedLeft == 0)):
            posReachedLeft = motornodeLeft.sdo['Statusword'].raw
            posReachedLeft = posReachedLeft & (1 << 10)
            print("posReachL: {}".format(posReachedLeft))
        for j in range(calibrateVal):
            degreeRight = 80 - j * (80 / calibrateVal)
            setPosAcc(motornodeRight, 350, 350, degreeRight)
            #read statusword bit 10 for position reached? for both motors
            ############################wait for ack from both motors before doing this below.#################################################################################
            posReachedRight = 0
            while (posReachedRight == 0):
                posReachedRight = motornodeRight.sdo['Statusword'].raw
                posReachedRight = posReachedRight & (1 << 10)
                print("posReachR: {}".format(posReachedRight))

            time.sleep(0.5)
            dataSet = np.append(dataSet, [[degreeLeft, degreeRight, rPiCom.getPitchRoll()[0], rPiCom.getPitchRoll()[1]]], axis=0)

    rPiCom.closeSocket()
    np.savetxt('values2.txt', dataSet)
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

initPDOs(motornodeLeft, motornodeRight)

init(motornodeLeft, motornodeRight)

softwareEnable(motornodeLeft, motornodeRight)
findHome(motornodeLeft, motornodeRight)
#
setSWLimits(0, 81)
#
network.nmt.state = 'OPERATIONAL'
#
# #degrees/second
acceleration = 50
deceleration = 50
# #f_in = open(r'\\.\pipe\NPtest', 'r+b', 0)
#
polyModel = getModel()
# HOST = '127.0.0.1'
# PORT = 9050
# sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# sock.bind((HOST, PORT))
#while(True):
#    print("hej")
    # get unity data
    # data, addr = sock.recvfrom(4096)
    # dataASCII = data.decode('ascii')
    # dataSplit = dataASCII.split(',')
    # floatArr = [float(dataSplit[0]), float(dataSplit[1]), float(dataSplit[2])]
    # pitch = floatArr[0]
    # roll = floatArr[1]
    # #print("pitch: {}, roll: {}".format(pitch, roll))
    # #time.sleep(0.1)
    # pos = polyModel.getMotorPos(pitch, roll)
    # if(pos[0][1] > 80):
    #     pos[0][1] = 80
    # if(pos[0][1] < 1):
    #     pos[0][1] = 1
    # if (pos[0][0] > 80):
    #     pos[0][0] = 80
    # if (pos[0][0] < 1):
    #     pos[0][0] = 1
    #
    # print("left: {}, right: {}".format(pos[0][0], pos[0][1]))
    # setPosAcc(motornodeLeft, acceleration, deceleration, pos[0][0])
    # setPosAcc(motornodeRight, acceleration, deceleration, pos[0][1])






while(True):
    leftpos = input('position left: ')
    if(leftpos == 'stop'):
     break
    rightpos = input('position right: ')

    leftpos = float(leftpos)
    rightpos = float(rightpos)
    if(rightpos >80):
        rightpos = 80
    if(rightpos < 1):
        rightpos = 1
    if (leftpos > 80):
        leftpos = 80
    if (leftpos < 1):
        leftpos = 1

    setPosAcc(motornodeLeft, acceleration, deceleration, leftpos)
    setPosAcc(motornodeRight, acceleration, deceleration, rightpos)



# shutdown
#setPosAcc(motornodeLeft,acceleration, deceleration, 120)
#setPosAcc(motornodeRight,acceleration, deceleration, 1)
print("shutting down")
time.sleep(1)
#motornodeLeft.sdo[0x6040].raw = 6
#motornodeRight.sdo[0x6040].raw = 6
network.disconnect()