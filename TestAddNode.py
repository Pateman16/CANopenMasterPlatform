import canopen
import time
import struct



network = canopen.Network()

network.connect(bustype='ixxat', channel=0, bitrate=250000)

network.scanner.search()

time.sleep(0.10)

network.nmt.state = 'PRE-OPERATIONAL'

for node_id in network.scanner.nodes:
    print("Found node %d!" % node_id)
    if(node_id == 8):
        leftJoystickButtons = network.add_node(node_id, None)
    elif(node_id == 7):
        rightJoystickButtons = network.add_node(node_id, None)
    elif(node_id == 6):
        leftJoystickStick = network.add_node(node_id, None)
    elif(node_id == 5):
        rightJoystickStick = network.add_node(node_id, None)


for node_id in network:
    print(network[node_id])

network.nmt.state = 'OPERATIONAL'

x = 5

#send empty TXPDO with RTR to get the nodes start sending values
time.sleep(0.05);
network.send_message(0x185, 0, True);
#time.sleep(0.05);
#network.send_message(0x186, 0, True);
time.sleep(0.05);
network.send_message(0x187, 0, True);
#time.sleep(0.05);
#network.send_message(0x188, 0, True);
#time.sleep(0.05);
print("sent empty PDOs")



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


xyString = ""
button = ""
totstring = ""
#Using a callback to asynchronously receive values
def print_joystick(id, dataByteArray, unknown):
    global xyString
    global button
    global totstring
    #print("id: {} x: {} y: {}".format(hex(id), checkSigned(getbyte(0,dataByteArray)),checkSigned(getbyte(2,dataByteArray))))
    if(id == int('0x187',16)):
        button = checkSigned(getbyte(3,dataByteArray))
    if(id == int('0x185',16)):
        xyString = "{}, {}".format(checkSigned(getbyte(0,dataByteArray)), checkSigned(getbyte(2,dataByteArray)))

    totstring = "{}, {}".format(xyString,button)


f_out = open(r'\\.\pipe\NPtest', 'r+b', 0)
while(True):
    network.subscribe(0x185, print_joystick)
    network.subscribe(0x187,print_joystick)
    f_out.write(struct.pack('I', len(totstring)))
    f_out.write(totstring.encode('utf-8'))
    time.sleep(0.1)

#
# rightJoystickStick.pdo.tx[1].add_callback(print_joystick)
# time.sleep(5)



network.disconnect()