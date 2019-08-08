"""
Serial connection checking before running a program
"""
import time
import serial
import threading
import tkinter as tk
from tkinter import messagebox

isConnected = False
serialObj = serial.Serial()

class Check:
    counter = 0

    def __init__(self, port="COM3", baud_rate=9600): # default port and baud rate of connection
        self.port = port
        self.baud_rate = baud_rate
        self.wndw = tk.Tk(screenName=None, baseName=None, className="Tk", useTk=1)
        self.wndw.title('Serial Check')
        self.label_ConnectSerial = tk.Label(self.wndw, text='Checking Serials...', bg='lightblue', height=2, width=35)
        self.label_ConnectSerial.pack()
        self.stop_threads = False
        # self.wndw.bind("<Destroy>", self.exitThread)
        self.wndw.protocol("WM_DELETE_WINDOW", self.exitThread)

        self.workthread = threading.Thread(target=self.scanning)
        self.workthread.start()

        self.wndw.mainloop()

    def scanning(self):
        global isConnected
        global serialObj
        while True:
            if self.stop_threads is False:
                try:
                    serialObj.port = self.port
                    serialObj.baudrate = self.baud_rate
                    serialObj.open()
                    isConnected = True
                    self.label_ConnectSerial.config(text='Serial found')
                    time.sleep(1)
                    self.exitThread()
                    break

                except serial.serialutil.SerialException:
                    self.counter = self.counter+1 if self.counter<10 else 0
                    print('\rException '+('.'*self.counter), end='')
                    time.sleep(0.5)
            else:
                break
        # print('\nthread ended')

    def exitThread(self):
        if isConnected is True:
            pass
        elif messagebox.askyesno('App', 'Are you sure you want to quit?'):
            self.stop_threads = True
            while self.workthread.isAlive():
                pass
        # self.wndw.after_cancel(self.scanner)
        self.wndw.destroy()
        self.wndw.quit()
        # print('window destroyed')
