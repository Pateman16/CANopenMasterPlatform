import canopen
import can
import time
import struct


class MessageListener(can.Listener):
    def __init__(self):
        can.Listener.__init__(self)
    def on_message_received(self,msg):
        print(msg)

network = canopen.Network()

network.connect(bustype='ixxat', channel=1, bitrate=250000)
rightJoystickStick = network.add_node(5, None)
leftJoystickStick = network.add_node(6, None)
rightJoystickButtons = network.add_node(7, None)
leftJoystickButtons = network.add_node(8, None)
rightJoystickStick.nmt.state = 'PRE-OPERATIONAL'
leftJoystickStick.nmt.state = 'PRE-OPERATIONAL'
rightJoystickButtons.nmt.state = 'PRE-OPERATIONAL'
leftJoystickButtons.nmt.state = 'PRE-OPERATIONAL'

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
def print_joystick(id, dataByteArray, unknown):
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

    totString = "{},{},{},{}".format(rightxyString, leftxyString, rightButtonString, leftButtonString)



network.nmt.state = 'OPERATIONAL'

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

network.subscribe(0x185, print_joystick)
network.subscribe(0x186, print_joystick)
network.subscribe(0x387, print_joystick)
network.subscribe(0x388, print_joystick)

f_out = open(r'\\.\pipe\NP', 'r+b', 0)
while(True):
    if(rightxyString and rightButtonString and leftxyString and leftButtonString):
        print(totString)
        f_out.write(struct.pack('I', len(totString)))
        f_out.write(totString.encode('utf-8'))
        f_out.flush()
        f_out.seek(0, 0)
    time.sleep(0.1)
    lengTH = struct.unpack('I', f_out.read(4))[0]
    data = f_out.read(lengTH)
    f_out.seek(0, 0)
    print("the read: {}".format(data))