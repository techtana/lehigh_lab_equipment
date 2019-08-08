# import local modules
from ArduinoComm.serialcheck import *
from ControllerUI.controllergui import *
from SlackComm.messenger import *
import tkinter as tk


SLACK_URL = "https://hooks.slack.com/services/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"


if __name__ == '__main__':
    ser = Check('COM3', 9600)  # Check if serial comm is established
    #if isConnected is False: exit()  # Exit if the window is closed without serial connection verified

    wndw = tk.Tk(screenName=None, baseName=None, className="Tk", useTk=1)
    wndw.title('Dip Coater Controller')
    wndw.minsize(width=1080, height=600)

    pgrm = ProgTable()
    motor = MotorSetup(ser)
    cnvas = MotionPath(wndw, pgrm, ser)
    pgrmBtn = ProgButtons(wndw, pgrm, cnvas, motor, ser, SLACK_URL)
    ctrlBtn = CtrlButtons(wndw, pgrm, pgrmBtn, motor, ser)
    menubar = MenuBar(wndw, pgrm, pgrmBtn, cnvas)

    tk.Tk.report_callback_exception = show_error
    wndw.mainloop()
