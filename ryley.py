import socket
import time
import csv
from telnetlib import Telnet
#import crc16

SENSOR_IP_ADDRESS = '192.168.1.101'
SENSOR_TELNET_PORT = 23
SENSOR_UDPout_PORT = 49152 #magic number #Use 'IP' command over telnet to figure out where this should be going

LOCAL_IP_ADDRESS = 'localhost'
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

    def bytes_for(self, command, parameters):
        buff = bytes(bytearray.fromhex('0000044084'))
        #crc16.crc16xmodem
        return buff


class Communicator:
    def __init__(self):
        print('Creating Communicator Object')
        self.udp_packetizer = udp_RecvFrame_Send_UDP_Packetizer()


    # Reads config        

    def the_new_thing(self):

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((LOCAL_IP_ADDRESS,LOCAL_UDP_PORT))

        init_message = self.udp_packetizer.bytes_for('ping','')
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




    

