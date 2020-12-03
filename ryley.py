import socket
import time
import csv
from telnetlib import Telnet
#import crc16

SENSOR_IP_ADDRESS = '192.168.1.101'
SENSOR_TELNET_PORT = 23
SENSOR_UDPout_PORT = 49152 #magic number #Use 'IP' command over telnet to figure out where this should be going

LOCAL_IP_ADDRESS = ''
LOCAL_UDP_PORT = 5678




OUTPUT_NAMES = ['Time', 'T1FX', 'T1FY', 'T1FZ', 'T1TX', 'T1TY', 'T1TZ']

class FT:
    def __init__(self):
        self.force_x = None
        self.force_y = None
        self.force_z = None
        self.torque_x = None
        self.torque_y = None
        self.torque_z = None
    
    def csv_list(self):
        return [self.force_x,self.force_y,self.force_z,self.torque_x,self.torque_y,self.torque_z]

class udp_RecvFrame_Send_UDP_Packetizer:
    def __init__(self):
        self.sequence = 0

    def crc16(self, data):
        data = bytearray(data)
        offset = 0
        crc = 0xFFFF
        for i in range(0, len(data)):
            crc ^= data[offset + i] << 8
            for j in range(0,8):
                if (crc & 0x8000) > 0:
                    crc =(crc << 1) ^ 0x1021
                else:
                    crc = crc << 1
        return crc & 0xFFFF

    def bytes_for(self, command, parameters = 0):
        #commands
        # 1 - Start Streaming, Parameter is number of samples to send, 0 = unlimited
        # 2 - Stop Streaming, No Params
        # 3 - Set Packet Transmission Rate, Parameter is transmission rate in µS
        # 4 - Ping, No Params
        # 5 - Reset Telnet Socket (useful to issue before connecting in case another session is still open)

        command_bytes = int(command).to_bytes(1, byteorder='big')

        sequence_bytes = int(self.sequence).to_bytes(1, byteorder='big')
        self.sequence += 1
        self.sequence %= 255 #Prevent overflow on the 1 byte tobytes

        if (command == 1) or (command == 3):
            parameters_bytes = int(parameters).to_bytes(4, byteorder='big')
        else:
            parameters_bytes = b''
        
        buff = command_bytes + sequence_bytes + parameters_bytes

        length_bytes = int(len(buff) + 2).to_bytes(2, byteorder='big') # +2 to account for crc code added later

        buff = length_bytes + buff

        crc_code = self.crc16(buff)

        crc_bytes = int(crc_code).to_bytes(2, byteorder='big')

        buff = buff + crc_bytes

        print(buff)

        #buff = bytes(bytearray.fromhex('000a 00 01 00000000 f224'))
        return buff


class Communicator:
    def __init__(self):
        print('Creating Communicator Object')
        self.udp_packetizer = udp_RecvFrame_Send_UDP_Packetizer()


    # Reads config        

    def the_new_thing(self):

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((LOCAL_IP_ADDRESS,LOCAL_UDP_PORT))

        init_message = self.udp_packetizer.bytes_for(4)
        print(init_message)

        sock.sendto(init_message,(SENSOR_IP_ADDRESS,SENSOR_UDPout_PORT))

        while True:
            data, addr = sock.recvfrom(1024)
            print(f'data: {data}')


    def read_config_and_send_initialization(self):
        print('Reading XML')

        # Read that XML and create the appropriate buffer

        buff = b'' #This should be a buffer that has all of the settings in it

        print('Telnet Session Starts')
        with Telnet(SENSOR_IP_ADDRESS,SENSOR_TELNET_PORT) as tn:
            tn.write(buff) #This should send all of those settings to the thing

        print('Telnet Session Ends')
        #Consider leaving telnet session open for Bias reset down the road.

    # reads incoming samples

    def listen_for_samples(self):
        print('Opening UDP Socket')
        udp_socket = socket.socket(socket.AF_INET, # Internet
                                     socket.SOCK_DGRAM) # UDP, example used SOCK_STREAM 

        while True:
            data, addr = udp_socket.recvfrom(1024) #1024 is magic number
            print(f'packet: {data}')

    # Bias

if __name__ == '__main__':
    c = Communicator()
    #c.read_config_and_send_initialization()
    #c.listen_for_samples()
    c.the_new_thing()



# Unit listens on port 23
# T transmits packets to WLAN




    

