"""
Main program
"""
from ArduinoComm import serialvalidate
from ArduinoComm import serialcomm
import tkinter as tk


PORT = 'COM6'
BAUD_RATE = 9600


if __name__ == '__main__':
    serialvalidate.Check(PORT, BAUD_RATE)
    if serialvalidate.isConnected is False: exit()  # Exit if the window is closed without serial connection verified
    print("pass")
    ser = serialvalidate.serialObj
    root = tk.Tk()
    # client = serialcomm.ThreadedSlackComm(root, ser)
    root.mainloop()



