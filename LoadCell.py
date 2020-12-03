import socket
import time, pdb
import csv
from telnetlib import Telnet
import crc16
from datetime import datetime
import threading
import multiprocessing


# SENSOR_IP_ADDRESS = '192.168.1.101'
# SENSOR_TELNET_PORT = 23
# SENSOR_UDPout_PORT = 57229 #magic number #Use 'IP' command over telnet to figure out where this should be going


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



class LoadCellCongiguration(object):
    def __init__(self, SENSOR_IP_ADDRESS = '192.168.1.101',SENSOR_TELNET_PORT = 23, SENSOR_UDPout_PORT = 57229):
        self.SENSOR_IP_ADDRESS = SENSOR_IP_ADDRESS
        self.SENSOR_TELNET_PORT = SENSOR_TELNET_PORT
        self.SENSOR_UDPout_PORT = SENSOR_UDPout_PORT
        self.TELNET = None
        self.DefaultCommands = ['RATE 125', 'BIAS 2 ON', 'TRANS 1', 'CALIB 1'] #'DEVIP 192.168.1.103', 'T ON'
        self.Connect()


    def Connect(self):
        print('-'*50)
        print('Attempting TELNET Connection to '+str(self.SENSOR_IP_ADDRESS))

        ## Connect to telnet
        self.TELNET = Telnet(self.SENSOR_IP_ADDRESS, self.SENSOR_TELNET_PORT)
        print('Connected to '+str(self.SENSOR_IP_ADDRESS))

        ## Read Telnet Output
        print(self.TELNET.read_until(b'\r\n', timeout=2).decode())
        print('-'*50)

        ## Send IP to Telnet, should return IP Information
        ipmessage = bytes('IP\r\n', 'ascii')
        self.TELNET.write(ipmessage)
        print(self.TELNET.read_until(b'IP\r\n', timeout=2).decode())

        StopReading = True
        while StopReading:
            # Read = self.TELNET.read_very_lazy()
            Read = self.TELNET.read_until(b'\r\n', timeout=1)
            print(Read.decode().strip('\n'))
            if Read == b'':
                StopReading = False

    def SendCommand(self, Command):
        commandbyte = bytes(Command+'\r\n', 'ascii')
        self.TELNET.write(commandbyte)
        StopReading = True
        while StopReading:
            # Read = self.TELNET.read_very_lazy()
            Read = self.TELNET.read_until(b'\r\n', timeout=1)
            print(Read.decode().strip('\n'))
            if Read == b'':
                StopReading = False
        #end

    def Configure(self):
        for Command in self.DefaultCommands:
            self.SendCommand(Command)
        #end

    def Bias(self):
        self.SendCommand('BIAS 2 ON \r\n')
        #end

    def Calibration(self, CalID):
        # CalID = 1 , 2 , 3
        Command = 'CALIB '+str(CalID)+' \r\n'
        self.SendCommand(Command)
        #end

    def Rate(self, Freq):
        Command = 'RATE '+str(Freq)+' \r\n'
        self.SendCommand(Command)
        #end


class LoadCellCollection(object):
    def __init__(self, LOCAL_IP_ADDRESS = '', LOCAL_UDP_PORT = 5678, SENSOR_IP_ADDRESS = '192.168.1.101',SENSOR_TELNET_PORT = 23, SENSOR_UDPout_PORT = 57229, Filename = None):
        ### Load Cell Communications
        self.SENSOR_IP_ADDRESS = SENSOR_IP_ADDRESS
        self.SENSOR_TELNET_PORT = SENSOR_TELNET_PORT
        self.SENSOR_UDPout_PORT = SENSOR_UDPout_PORT
        self.LOCAL_IP_ADDRESS = LOCAL_IP_ADDRESS
        self.LOCAL_UDP_PORT = LOCAL_UDP_PORT
        self.sequence = 0
        self.sock = None

        ### Specify File to Write to
        if Filename == None:
            self.Filename = 'LoadCellReport'+datetime.today().strftime('%Y-%m-%d-%H-%M')+'.csv'
        ### Store Raw Data
        self.raw_data = None

        ### Specify Boolean for Recording and Stop
        self.Stop = False
        self.Collect = False

        ### Setup UPD Socket
        self.Setup()

        ### Start Threading
        self.StartThreads()


    def Setup(self):
        print('Opening UPD Socket')
        ### Instatiate Socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        ### Bind Socket
        self.sock.bind((self.LOCAL_IP_ADDRESS, self.LOCAL_UDP_PORT))

        ### Send Ping Command to Confirm, Command = 4
        init_message = self._bytes_for_command(4)
        self.sock.sendto(init_message,(self.SENSOR_IP_ADDRESS, self.SENSOR_UDPout_PORT))

        ### Wait for Pong
        ###Change this to just read until pong
        # while True:
            # data, addr = self.sock.recvfrom(10240)
            # print(data)

    def StartThreads(self):
        ### Start Background Threads
        self.ReadThread = threading.Thread(target=self._ReadLC)
        # self.ReadThread.daemon = True
        self.ReadThread.start()
        print('> Read Load Cell Data Thread Started')

        self.WriteThread = threading.Thread(target=self._Write2File)
        # self.WriteThread.daemon = True
        self.WriteThread.start()
        print('> Write Load Cell Data Thread Started')


    def _bytes_for_command(self, command, parameters = 0):
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
        # print(buff)
        lenbuff = len(buff)+4
        length_bytes = int(lenbuff).to_bytes(2, byteorder='big')
        # print(length_bytes)
        # length_bytes += 2 # To account for crc code added to the end

        buff = length_bytes + buff

        crc_code = crc16.crc16xmodem(buff)

        crc_bytes = int(crc_code).to_bytes(2, byteorder='big')

        buff = buff + crc_bytes

        # print(buff)

        # buff = bytes(bytearray.fromhex('000a 00 02 00000000 f224'))
        print('Bytes Sent: ' + str(buff))
        return buff


    def SendCommand(self, command, parameters = 0):
        send_command = self._bytes_for_command(command, parameters = parameters)
        self.sock.sendto(send_command,(self.SENSOR_IP_ADDRESS, self.SENSOR_UDPout_PORT))
        #end


    def _ReadLC(self):
        ### Send Command to Start Sending Packets
        start_message = self._bytes_for_command(1,parameters=0)
        # start_message =  bytes(bytearray.fromhex('000a 00 01 00000000 f224'))
        self.sock.sendto(start_message,(self.SENSOR_IP_ADDRESS, self.SENSOR_UDPout_PORT))

        ### Start infinite read loop
        while True:
            data, addr = self.sock.recvfrom(102400) #1024 is magic number
            print(f'packet: {data}')
            self.raw_data = data
            time.sleep(0.1)
            if self.Stop:
                break
            #end
        #end

    def _Write2File(self):
        while True:
            if self.Collect:
                File = open(self.Filename, 'a+', newline='')
                FileWriter = csv.writer(File)
                FileWriter.writerow(self.raw_data)
            if self.Stop:
                break
            #end
        #end

    def StartCollect(self):
        self.Collect = True
    def StopCollect(self):
        self.Collect = False
    def kill(self):
        self.Stop = True

if __name__ == '__main__':
    print('---Testing LoadCellCongiguration Class---')
    lcconfig = LoadCellCongiguration( SENSOR_IP_ADDRESS = '192.168.1.41', SENSOR_UDPout_PORT = 49152)
    lcconfig.Configure()
    # time.sleep(3)
    # lcconfig.Bias()

    print('---Testing LoadCellCollection Class---')
    lccollection = LoadCellCollection( SENSOR_IP_ADDRESS = '192.168.1.41', SENSOR_UDPout_PORT = 49152)
    lccollection.StartCollect()
    time.sleep(3)
    lccollection.StopCollect()
    lccollection.SendCommand(2)
    lccollection.kill()
    print('Killed Bytes')
    time.sleep(2)
