import socket

class RpiPitchRoll(object):



    def __init__(self, serverIp, port):
        #here we define the udp ip address as well as the port number that we have.
        self.port = port
        self.serverIp = serverIp
        #declare our serverSocket upon which
        #we will be listening for UDP messages
        self.serverSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def getPitchRoll(self):
        client_server_address = (self.serverIp, self.port)
        try:
            self.serverSock.sendto(b'send data', client_server_address)
            data, addr = self.serverSock.recvfrom(4096)
            # convert binary array to string array
            data = data.decode('ascii')
            # split by comma to another array
            dataSplit = data.split(',')
            # convert pitch and roll to float
            floatArr = [float(dataSplit[0]), float(dataSplit[1])]

            return floatArr

        except:
            print("didnt send")
            return 0

    def closeSocket(self):
        self.serverSock.close()