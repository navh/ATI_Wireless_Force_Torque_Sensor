#!/usr/bin/env python
import socket
import time
import csv

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


class Listener:
    def __init__(self):
        print('Opening Listener Object')

    def start(self):
        print('Opening Socket')
        #Open the socket to receive F/T data
        HOST = 'localhost'    # The remote host
        PORT = 49389              # The same port as used by the server
        input_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        time.sleep(2.0)
        input_socket.connect((HOST, PORT))
        input_fhandle = input_socket.makefile('r')

        #Identify the columns we want to output
        header = input_fhandle.readline()
        header = header.split(',')
        header = [column.strip() for column in header]
        output_cols = [header.index(name) for name in OUTPUT_NAMES]
        print(header)
        print(output_cols)

        listener_out_path = 'listener-out-' + time.strftime('%Y%m%d-%H%M%S') + '.csv'

        with open(listener_out_path,'wb') as myfile:
            wrtr = csv.writer(myfile, delimiter=',', quotechar='"')
            wrtr.writerow(['force_x','force_y','force_z','torque_x','torque_y','torque_z'])

            try:
                while True:
                    input_str = input_fhandle.readline()
                    input_str = input_str.split(',')
                    input_str = [column.strip() for column in input_str]
                    try:
                        ft = FT()
                        ft.force_x = float(input_str[output_cols[1]])
                        ft.force_y = float(input_str[output_cols[2]])
                        ft.force_z = float(input_str[output_cols[3]])
                        ft.torque_x = float(input_str[output_cols[4]])
                        ft.torque_y = float(input_str[output_cols[5]])
                        ft.torque_z = float(input_str[output_cols[6]])
                        wrtr.writerow(ft.csv_list())
                    except:
                        print('An unknown read error occurred - discarding this F/T sample')
            except KeyboardInterrupt:
                print('sigint: Program Killed Gracefully')


if __name__ == '__main__':
    try:
        l = Listener()
        l.start()
    except:
        pass