"""
Threading asynchronous serial I/O
This contains parser for a standard Arduino serial communication
https://www.oreilly.com/library/view/python-cookbook/0596001673/ch09s07.html
"""
import threading
import queue
import tkinter as tk
# import local module
import slackcomm
import serialconfig
import serial


class ThreadedSlackComm:
    def __init__(self, root, ser):
        """
        Start the GUI and the asynchronous threads. We are in the main
        (original) thread of the application, which will later be used by
        the GUI as well. We spawn a new thread for the worker (I/O).
        """

        self.gui = serialconfig.GuiPart(root)
        self.ser = ser

        # Start thread
        self.startThread()

        # Create the queue
        self.queue = queue.Queue()

        # Check if the queue contains anything
        self.periodicCall()

    def startThread(self):
        # Set up the thread to do asynchronous I/O
        self.thread1 = threading.Thread(target=self.workerThread)
        self.thread1.start()

    def periodicCall(self):
        """
        Check every 200 ms if there is something new in the queue.
        """
        REFRESH_INTERVAL = 200
        self.processIncoming()
        self.gui.after(REFRESH_INTERVAL, self.periodicCall)

    def workerThread(self):
        while True:
            # msg = self.ser.read(10)  # read up to ten bytes (timeout)
            # print('threading')
            msg = self.ser.readline()  # read a '\n' terminated line
            self.queue.put(msg)

    def processIncoming(self):
        """
        Handle all messages currently in the queue, if any.
        """
        # print(self.queue.qsize())
        while self.queue.qsize():
            print('trying')
            try:
                msg = self.queue.get(False)
                parsed_msg = slackcomm.parser(msg)
                slackcomm.send_message_to_slack(parsed_msg)  # to container SlackComm
                self.startThread()
            except queue.Empty:
                pass
