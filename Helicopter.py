import threading
import multiprocessing
import time
from datetime import datetime
import sys
import os, pdb

import serial
import struct

import csv



class HeliControl(object):
    def __init__(self, COM = 'COM6', Baud = 9600, Filename = None):
        ### Arduino Communications
        self.COM = COM          # COM Port
        self.Baud = Baud        # Baud Rate: Recommended 9600
        self.startMarker = '<'  # Used for Serial Read
        self.arduino = None     # Arduino Class
        self.raw_data = None    # Stores Raw Data
        if Filename == None:
            self.Filename = 'ArudinoReport_'+datetime.today().strftime('%Y-%m-%d-%H-%M-%S')+'.csv'

        ### RPM and Pitch Set Parameters
        self.RPMsens = 10       # RPM Tolerance
        self.Pitchsens = 0.1    # Pitch Tolerance

        ### Initial Servo Positions
        self.Thr = 0
        self.Col = 0
        self.Ail = 127
        self.Ele = 127
        self.Rud = 127

        ### Specify Boolean for Recording and Stop
        self.Collect = False
        self.Stop = False

        ### Connect to Arduino
        self.Connect(self.COM, self.Baud)

        ### Begin Background Threads
        self.ReadThread = None
        self.ControlThread = None
        self.WriteThread = None
        self.StartThreads()

    def Connect(self, COM, Baud):
        self.arduino = serial.Serial(str(COM), Baud, timeout = 2)
        self.arduino.flush()
        print(self.arduino.read_until(b'>').decode())
        #end

    def StartThreads(self):
        self.ReadThread = threading.Thread(target=self._ReadArduino)
        # self.ReadThread.daemon = True
        self.ReadThread.start()
        print('> Read Arduino Thread Started')

        self.ControlThread = threading.Thread(target=self._Control)
        # self.ControlThread.daemon = True
        self.ControlThread.start()
        print('> Control Arduino Thread Started')

        self.WriteThread = threading.Thread(target=self._Write2File)
        # self.WriteThread.daemon = True
        self.WriteThread.start()
        print('> Arduino Data File Writing Thread Started')
        #end

    def _ReadArduino(self):
        while True:
            received = self.arduino.readline()
            # Following line is simply removing the extraneous bits of the string (byte, quotes, markers, newline symbols)
            received = str(received[1:-3])[2:-1]
            data = received.split(":")
            data.append(str(datetime.now()))
            self.raw_data = data
            # print(data)
            # time.sleep(0.5)
            if self.Stop:
                break
        #end

    def _Control(self):
        while True:
            self.arduino.write(self.startMarker.encode())
            self.arduino.write(struct.pack('>BBBBB',self.Thr,self.Col,self.Ail,self.Ele, self.Rud))
            time.sleep(0.1)
            if self.Stop:
                break
            #end
    # def Collect(self):
        # self.threading2 = threading.Thread(target=self.ReadArduino)

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

    def SetRPM(self, RPM):
        RPMcurrent = self.raw_data[0]
        while abs(RPMcurrent-RPM) > self.RPMsens:
            if RPMcurrent < RPM:
                self.Thr += 1
                time.sleep(0.1)
            else:
                self.Thr -= 1
                time.sleep(0.1)
                #end
            RPMcurrent = self.raw_data[0]
        #end

    def SetPitch(self, Pitch):
        # Pitchcurrent = self.raw_data[1]
        # 0 = -10, 255 = +10
        PitchCurrent = self.raw_data[3]*(10-(-10))/255 - 10 # Until we get sensor

        while abs(Pitchcurrent-Pitch) > self.Pitchsens:
            if Pitchcurrent < Pitch:
                self.Col += 1
                time.sleep(0.1)
            else:
                self.Col -= 1
                time.sleep(0.1)
                #end
            Pitchcurrent = self.raw_data[3]*(10-(-10))/255 - 10 # Until we get sensor
        #end

    def SetServo(self, Thr, Col, Ail, Ele):
        self.Thr = Thr
        self.Col = Col
        self.Ail = Ail
        self.Ele = Ele
        #end

    def StartCollect(self):
        self.Collect = True
    def StopCollect(self):
        self.Collect = False
    def kill(self):
        self.Thr = 0
        self.Col = 0
        time.sleep(1.)
        self.Stop = True


if __name__ == "__main__":
    print('---Testing HeliControl Class---')
    heli = HeliControl()
    for i in range(255):
        heli.SetPitch(i,i,i,i)
        print(i)
        time.sleep(0.5)
    heli.stop()
