"""
Main program
"""

# Import local modules
import serialcheck
import serialcomm
import serial
import tkinter as tk


PORT = 'COM6'
BAUD_RATE = 9600


if __name__ == '__main__':
    serialcheck.Check(PORT, BAUD_RATE)
    if serialcheck.isConnected is False: exit()  # Exit if the window is closed without serial connection verified
    print("pass")
    ser = serialcheck.serialObj
    root = tk.Tk()
    # client = serialcomm.ThreadedSlackComm(root, ser)
    root.mainloop()



