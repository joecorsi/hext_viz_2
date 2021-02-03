#!/usr/bin/env python

from threading import Thread
import serial
import time
import collections
import matplotlib.pyplot as plt
import matplotlib.axes._axes as axes  # helps with autocomplete
import matplotlib.animation as animation
import struct
import pandas as pd


class serialPlot:
    def __init__(self, serialPort="COM3", serialBaud=9600, plotLength=100, dataNumBytes=1, numPlots=1):
        self.port = serialPort
        self.baud = serialBaud
        self.plotMaxLength = plotLength
        self.dataNumBytes = dataNumBytes
        self.numPlots = numPlots
        self.rawData = bytearray(dataNumBytes)
        self.data = []
        for i in range(numPlots):  # give an array for each type of data and store them in a list
            self.data.append(collections.deque([0] * plotLength, maxlen=plotLength))
        self.isRun = True
        self.isReceiving = False
        self.thread = None
        self.plotTimer = 0
        self.previousTimer = 0
        self.csvData = []

        print('Connecting to: ' + str(serialPort) + ' at ' + str(serialBaud) + ' BAUD...')
        try:
            self.serialConnection = serial.Serial(serialPort, serialBaud, timeout=10)
            print('Connected')
        except:
            print("Failed to connect to: " + str(serialPort) + ' at ' + str(serialBaud) + ' BAUD')

    def readSerialStart(self):
        if self.thread == None:
            self.thread = Thread(target=self.backgroundThread)
            self.thread.start()
            # Block till we start receiving values
            while self.isReceiving != True:
                time.sleep(0.1)

    def backgroundThread(self):  # retrieve data
        time.sleep(1.0)  # give some buffer time for retrieving data
        self.serialConnection.reset_input_buffer()
        while (self.isRun):
            self.serialConnection.readinto(self.rawData)
            self.isReceiving = True

    def getSerialData(self, frame, lines, lineValueText, lineLabel, timeText):
        currentTimer = time.perf_counter()
        self.plotTimer = int((currentTimer - self.previousTimer) * 1000)
        self.previousTimer = currentTimer
        timeText.set_text('Interval: ' + str(self.plotTimer) + 'ms')
        # val, = struct.unpack('d', self.rawData)
        # , after val unpacks first value of tuple and assigns to val (terse)
        mv = memoryview(self.rawData).cast('d')  # splits rawData into 8 byte chunks and casts to float ('d')
        for i in range(self.numPlots):
            self.data[i].append(mv[i])
            lines[i].set_data(range(self.plotMaxLength), self.data[i])
        self.csvData.append([self.data[0][-1], self.data[1][-1]])

    def close(self):
        self.isRun = False
        self.thread.join()
        self.serialConnection.close()
        print('Disconnected')
        df = pd.DataFrame(self.csvData)
        df.to_csv('/Users/joeco/Desktop/out.csv')  # output to csv


def main():
    portName = 'COM3'
    baudRate = 115200
    maxPlotLength = 100
    dataNumBytes = 16  # number of bytes of 1 data point, 8 bytes per value
    numPlots = 2 # number of 8 byte plots
    s = serialPlot(portName, baudRate, maxPlotLength, dataNumBytes, numPlots)
    s.readSerialStart()

    # plotting
    pltInterval = 25
    xmin = 0
    xmax = maxPlotLength
    ymin = -(1)
    ymax = 1
    fig = plt.figure()

    # don't quite know what this does, sets scales maybe?
    ax = plt.axes(xlim=(xmin, xmax), ylim=(float(ymin - (ymax - ymin) / 10), float(ymax + (ymax - ymin) / 10)))

    lineLabel = ['x1', 'y1']
    style = ['r-', 'c-']  # linestyles for the different plots
    timeText = ax.text(0.50, 0.95, '', transform=ax.transAxes)
    lines = []
    lineValueText = []
    for i in range(numPlots):
        lines.append(ax.plot([], [], style[i], label=lineLabel[i])[0])
        lineValueText.append(ax.text(0.50, 0.90, '', transform=ax.transAxes))

    # animate function, data come from getSerialData
    anim = animation.FuncAnimation(fig,
                                   s.getSerialData,
                                   fargs=(lines, lineValueText, lineLabel, timeText),  # fargs has to be a tuple
                                   interval=pltInterval)

    plt.legend(loc="upper left")
    plt.show()

    s.close()


if __name__ == '__main__':
    main()
