import canopen
import time
import socket
from RPiCom import RpiPitchRoll
from motorModelPls import MotorPositionModel
import numpy as np
import pickle
import struct

# Start with creating a network representing one CAN bus
network = canopen.Network()

# Add some nodes with corresponding Object Dictionaries

network.connect(bustype='ixxat', channel=1, bitrate=250000)
#Left and right seen from the front of the platform.
motornodeLeft = network.add_node(1, 'Eds/AKD CANopen.eds')
motornodeRight = network.add_node(2, 'Eds/AKD CANopen.eds')
rightJoystickStick = network.add_node(5, None)
leftJoystickStick = network.add_node(6, None)
rightJoystickButtons = network.add_node(7, None)
leftJoystickButtons = network.add_node(8, None)
rightJoystickStick.nmt.state = 'PRE-OPERATIONAL'
leftJoystickStick.nmt.state = 'PRE-OPERATIONAL'
rightJoystickButtons.nmt.state = 'PRE-OPERATIONAL'
leftJoystickButtons.nmt.state = 'PRE-OPERATIONAL'

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

##################################################################################################


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
        time.sleep(0.2)
        latchStatusLeft = motornodeLeft.sdo['LatchStatus'].raw
        latchStatusLeft = latchStatusLeft >> 15
        latchStatusRight = motornodeRight.sdo['LatchStatus'].raw
        latchStatusRight = latchStatusRight >> 15

    print("Home is set, sleeping 1 sec")
    setPosAcc(nodeLeft, 100, 100, 40)
    setPosAcc(nodeRight, 100, 100, 40)

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

#sets the software limits for the motors, in this application dont go more than 0 to 80
def setSWLimits(lowerLimit, upperLimit):

    motornodeLeft.sdo['Software position limit']['Min position limit'].raw = lowerLimit
    motornodeLeft.sdo['Software position limit']['Max position limit'].raw = upperLimit
    motornodeRight.sdo['Software position limit']['Min position limit'].raw = lowerLimit
    motornodeRight.sdo['Software position limit']['Max position limit'].raw = upperLimit
    motornodeLeft.sdo['SWLS.ENM'].raw = 3
    motornodeRight.sdo['SWLS.ENM'].raw = 3
    #softwareEnable(motornodeLeft, motornodeRight)
    #softwareEnable(motornodeLeft, motornodeRight)

initPDOs(motornodeLeft, motornodeRight)
print('initpdo done')
init(motornodeLeft, motornodeRight)
print('init done')
#softwareEnable(motornodeLeft,motornodeRight)
#findHome(motornodeLeft, motornodeRight)
print('findhome done')
setSWLimits(0, 81)
print('swlimits done')
network.nmt.state = 'OPERATIONAL'

def checkSigned(value):
    value = int(value, 16)
    value = value & 0x0fff
    if(value > 0x3ff):
        value = value & 0x3ff
        value = value - 0x400
        return value
    else:
        return value
def getbyte(byteNr, byteArray):
    val1 = byteArray[byteNr * 2]
    val2 = byteArray[byteNr * 2 + 1]
    val2 = val2 << 8
    val= val1|val2
    val = val.to_bytes(2, byteorder='big')
    val= val.hex()
    return val


rightxyString = ""
rightButtonString = ""
leftxyString = ""
leftButtonString = ""
totString = ""
#Using a callback to asynchronously receive values
def print_joystick(id, dataByteArray, unknown):
    print("id: {} x: {} y: {}".format(hex(id), checkSigned(getbyte(0,dataByteArray)),checkSigned(getbyte(2,dataByteArray))))
    global rightxyString
    global rightButtonString
    global leftxyString
    global leftButtonString
    global totString
    if(id == int('0x185',16)):
        rightxyString = "{},{}".format(checkSigned(getbyte(0,dataByteArray)), checkSigned(getbyte(2,dataByteArray)))
    if(id == int('0x186',16)):
        leftxyString = "{},{}".format(checkSigned(getbyte(0, dataByteArray)), checkSigned(getbyte(2, dataByteArray)))
    if(id == int('387',16)):
        rightButtonString = "{}".format(checkSigned(getbyte(0, dataByteArray)))
    if (id == int('388', 16)):
        leftButtonString = "{}".format(checkSigned(getbyte(0, dataByteArray)))

    # if (rightxyString and rightButtonString and leftxyString and leftButtonString):
    #     f_out.write(struct.pack('I', len(totString)))
    #     f_out.write(totString.encode('utf-8'))
    #     f_out.seek(0)

    totString = "{},{},{},{}".format(rightxyString, leftxyString, rightButtonString, leftButtonString)

polyModel = getModel()
print('model done')

#send empty TXPDO with RTR to get the nodes start sending values
time.sleep(0.05);
network.send_message(0x185, 0, True);
time.sleep(0.05);
network.send_message(0x186, 0, True);
time.sleep(0.05);
network.send_message(0x387, 0, True);
time.sleep(0.05);
network.send_message(0x388, 0, True);
time.sleep(0.05);
print("sent empty PDOs")
#degrees/second^2
acceleration = 700
deceleration = 700
network.subscribe(0x185, print_joystick)
network.subscribe(0x186, print_joystick)
network.subscribe(0x387, print_joystick)
network.subscribe(0x388, print_joystick)
#f_out = open(r'\\.\pipe\NP', 'r+b', 0)
while(True):
    try:
        pitchRoll = rightxyString.split(',')
        print(pitchRoll)
        pitch = float(pitchRoll[1])
        roll = float(pitchRoll[0])
        pitch = (pitch / 1024) * 20
        roll = (roll / 1024) * 20
        time.sleep(0.1)
        # lengTH = struct.unpack('I', f_out.read(4))[0]
        # data = f_out.read(lengTH)
        # f_out.seek(0)
        # dataASCII = data.decode('ascii')
        # dataSplit = dataASCII.split(',')
        # floatArr = [float(dataSplit[0]), float(dataSplit[1]), float(dataSplit[2])]
        # print(floatArr)
        # pitch = floatArr[0]
        # roll = floatArr[1]
        pos = polyModel.getMotorPos(pitch, roll)
        if ((pitch is not None) or (roll is not None)):
            pos = polyModel.getMotorPos(pitch, roll)
            print(pos)
            if (pos[0][1] > 80):
                pos[0][1] = 80
            if (pos[0][1] < 1):
                pos[0][1] = 1
            if (pos[0][0] > 80):
                pos[0][0] = 80
            if (pos[0][0] < 1):
                pos[0][0] = 1

            setPosAcc(motornodeLeft, acceleration, deceleration, pos[0][0])
            setPosAcc(motornodeRight, acceleration, deceleration, pos[0][1])
    except:
        print("HEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEJ")



# shutdown
setPosAcc(motornodeLeft,acceleration, deceleration, 80)
setPosAcc(motornodeRight,acceleration, deceleration, 1)
print("shutting down")
time.sleep(1)
motornodeLeft.sdo[0x6040].raw = 6
motornodeRight.sdo[0x6040].raw = 6
network.disconnect()