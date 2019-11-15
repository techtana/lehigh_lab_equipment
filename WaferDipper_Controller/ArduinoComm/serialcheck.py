import serial
import tkinter as tk
import time

class Check:
    counter = 0

    def __init__(self, port="COM3", baud_rate=9600): # default port and baud rate of connection
        self.ser = serial.Serial()
        self.isConnected = False
        self.port = port
        self.baud_rate = baud_rate
        self.wndw = tk.Tk(screenName=None, baseName=None, className="Tk", useTk=1)
        self.wndw.title('Dip Coater Controller ')
        self.wndw.maxsize(width=100, height=35)
        self.label_ConnectSerial = tk.Label(self.wndw, text='Checking Serials...', bg='lightblue', height=2, width=35)
        self.label_ConnectSerial.place(relx=0.5, rely=0.5, anchor='center')
        self.scanner = self.wndw.after(500, self.scanning)
        self.wndw.mainloop()

    def scanning(self):
        try:
            self.ser = serial.Serial(self.port, self.baud_rate)
            print('Serial found')
            time.sleep(1)
            self.isConnected = True
            self.wndw.after_cancel(self.scanner)
            self.wndw.destroy()
        except serial.serialutil.SerialException:
            self.counter = self.counter+1 if self.counter<10 else 0
            print('\rException '+('.'*self.counter), end='')
            time.sleep(0.5)
            scanner = self.wndw.after(500, self.scanning)