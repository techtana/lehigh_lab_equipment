import serial
import re
import tkinter as tk
from time import sleep
from tkinter import filedialog
import pandas as pd
from tkinter import scrolledtext
import traceback
from tkinter import messagebox
from decimal import getcontext, Decimal
import datetime as dt


DEFAULT_SPEED = 80000
DEFAULT_SLEEP = 1
getcontext().prec = 2  # Set Decimal precision.


class MenuBar(tk.Frame):
    def __init__(self, master, pgrm, pgrmBtn, cnvas):
        tk.Frame.__init__(self, master, bd=5)

        self.pgrm = pgrm
        self.pgrmBtn = pgrmBtn
        self.cnvas = cnvas

        self.menu_bar = tk.Menu(self)
        self.grid(row=0, column=0)
        self.master.bind('<Control-o>', self.file_load)
        self.master.bind('<Control-s>', self.file_save)

        menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=menu)
        menu.add_command(label="Save", command=self.file_save)
        menu.add_command(label="Load", command=self.file_load)
        menu.add_command(label="Exit", command=self.quit)

        menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Help", menu=menu)
        menu.add_command(label="User Manual", command=info_help)
        menu.add_command(label="About", command=info_about)

        try:
            self.master.config(menu=self.menu_bar)
        except AttributeError:
            # master is a toplevel window (Python 1.4/Tkinter 1.63)
            self.master.tk.call(master, "config", "-menu", self.menu_bar)

    def file_save(self, *arg):
        f = tk.filedialog.asksaveasfile(initialfile="DipCoat_config_", mode='w', defaultextension=".txt",
                                        filetypes=(("Text file", "*.txt"), ("All Files", "*.*")))
        if f is None:  # asksaveasfile return `None` if dialog closed with "cancel".
            return
        f.write(str(self.cnvas.description.get(1.0, 'end')))
        for k in range(0, avail_entry(self.pgrm.entriesX)):
            statement = str(k) + "\t" + \
                        str(self.pgrm.entriesX[k].get()) + "\t" + \
                        str(self.pgrm.entriesY[k].get()) + "\t" + \
                        str(self.pgrm.entriesSpeedX[k].get()) + "\t" + \
                        str(self.pgrm.entriesSpeedY[k].get()) + "\t" + \
                        str(self.pgrm.entriesWait[k].get()) + "\t" + \
                        str(self.pgrm.entriesComment[k].get()) + "\n"
            f.write(statement)
        f.close()
        return

    def file_load(self, *arg):
        self.pgrmBtn.pgrm_clear()
        f = tk.filedialog.askopenfile(mode='r', defaultextension='.txt')
        if f is None:  # asksaveasfile return `None` if dialog closed with "cancel".
            return

        try:
            for line in f:
                content = line.split('\t')
                # print(line)
                # print(content)
                try:
                    self.pgrm.entriesX[int(content[0])].insert(0, float(content[1]))
                    self.pgrm.entriesY[int(content[0])].insert(0, float(content[2]))
                    self.pgrm.entriesSpeedX[int(content[0])].insert(0, float(content[3]))
                    self.pgrm.entriesSpeedY[int(content[0])].insert(0, float(content[4]))
                    self.pgrm.entriesWait[int(content[0])].insert(0, float(content[5]))
                    self.pgrm.entriesComment[int(content[0])].insert(0, content[6])
                except ValueError:
                    self.cnvas.description.insert('insert', str(line))
            f.close()
            self.pgrmBtn.pgrm_refresh()
            return
        except ValueError:
            print("ValueError Exception")
            return


class ProgTable(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.entriesX = {}
        self.entriesY = {}
        self.entriesSpeedX = {}
        self.entriesSpeedY = {}
        self.entriesWait = {}
        self.entriesComment = {}
        self.labels = {}
        self.tableheight = 15
        self.tablewidth = 6
        self.grid(row=1, column=0)
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="Loc X (mm)", width=15).grid(row=0, column=1)
        tk.Label(self, text="Loc Y (mm)", width=15).grid(row=0, column=2)
        tk.Label(self, text="Speed X (mm/s)", width=15).grid(row=0, column=3)
        tk.Label(self, text="Speed Y (mm/s)", width=15).grid(row=0, column=4)
        tk.Label(self, text="Wait time (s)", width=15).grid(row=0, column=5)
        tk.Label(self, text="Comment", width=15).grid(row=0, column=6)

        for row in range(0, self.tableheight):  # create entry number
            self.labels[row] = tk.Label(self, text=str(row + 1), width=5)
            self.labels[row].grid(row=row + 1, column=0)

        for row in range(0, self.tableheight):  # X location entry
            self.entriesX[row] = tk.Entry(self, width=15)
            self.entriesX[row].grid(row=row + 1, column=1, padx=0)

        for row in range(0, self.tableheight):  # Y location entry
            self.entriesY[row] = tk.Entry(self, width=15)
            self.entriesY[row].grid(row=row + 1, column=2, padx=0)

        for row in range(0, self.tableheight):  # X speed entry
            self.entriesSpeedX[row] = tk.Entry(self, width=15)
            self.entriesSpeedX[row].grid(row=row + 1, column=3, padx=0)

        for row in range(0, self.tableheight):  # Y speed entry
            self.entriesSpeedY[row] = tk.Entry(self, width=15)
            self.entriesSpeedY[row].grid(row=row + 1, column=4, padx=0)

        for row in range(0, self.tableheight):  # wait time entry
            self.entriesWait[row] = tk.Entry(self, width=15)
            self.entriesWait[row].grid(row=row + 1, column=5, padx=0)

        for row in range(0, self.tableheight):  # wait time entry
            self.entriesComment[row] = tk.Entry(self, width=15)
            self.entriesComment[row].grid(row=row + 1, column=6, padx=0)


class CtrlButtons(tk.Frame):
    def __init__(self, master, pgrm, pgrmBtn, motor, ser):
        tk.Frame.__init__(self, master)

        self.prgm = pgrm
        self.pgrmBtn = pgrmBtn
        self.motor = motor
        self.ser = ser

        self.grid(row=0, column=1)
        self.master.config()

        self.master.bind('<Control-Left>', self.left)
        self.master.bind('<Control-Right>', self.right)
        self.master.bind('<Control-Up>', self.up)
        self.master.bind('<Control-Down>', self.down)

        bttn_en = tk.Button(self, text='Enter', bg='lightgreen', height=2, width=5, command=self.enter)
        bttn_a = tk.Button(self, text='Left', bg='lightblue', height=2, width=5, command=self.left)
        bttn_w = tk.Button(self, text='Up', bg='lightblue', height=2, width=5, command=self.up)
        bttn_s = tk.Button(self, text='Down', bg='lightblue', height=2, width=5, command=self.down)
        bttn_d = tk.Button(self, text='Right', bg='lightblue', height=2, width=5, command=self.right)

        bttn_w.grid(row=0, column=1, padx=5, pady=5)
        bttn_s.grid(row=2, column=1, padx=5, pady=5)
        bttn_a.grid(row=1, column=0, padx=5, pady=5)
        bttn_d.grid(row=1, column=2, padx=5, pady=5)
        bttn_en.grid(row=1, column=1, padx=5, pady=5)

    def up(self, *args):
        print("UP button")
        statement = "<Xr:" + str(0) + \
                    ",Xs:" + str(0) + \
                    ",Yr:" + str(int(self.pgrmBtn.parse_mm_to_step(2, self.motor.step2.get()))) + \
                    ",Ys:" + str(DEFAULT_SPEED) + \
                    ",T:" + str(0) + ">"
        print(statement)
        self.ser.write(str.encode(statement))
        return

    def down(self, *args):
        print("DOWN button")
        statement = "<Xr:" + str(0) + \
                    ",Xs:" + str(0) + \
                    ",Yr:" + str(int(self.pgrmBtn.parse_mm_to_step(2, self.motor.step2.get()))) + \
                    ",Ys:" + str(-DEFAULT_SPEED) + \
                    ",T:" + str(0) + ">"
        print(statement)
        self.ser.write(str.encode(statement))
        return

    def left(self, *args):
        print("LEFT button")
        print(self.motor.step1.get())
        statement = "<Xr:" + str(int(self.pgrmBtn.parse_mm_to_step(1, self.motor.step1.get()))) + \
                    ",Xs:" + str(DEFAULT_SPEED) + \
                    ",Yr:" + str(0) + \
                    ",Ys:" + str(0) + \
                    ",T:" + str(0) + ">"
        print(statement)
        self.ser.write(str.encode(statement))
        return

    def right(self, *args):
        print("RIGHT button")
        statement = "<Xr:" + str(int(self.pgrmBtn.parse_mm_to_step(1, self.motor.step1.get()))) + \
                    ",Xs:" + str(-DEFAULT_SPEED) + \
                    ",Yr:" + str(0) + \
                    ",Ys:" + str(0) + \
                    ",T:" + str(0) + ">"
        print(statement)
        self.ser.write(str.encode(statement))
        # cnvas.loc_refresh()
        return

    def enter(self, *args):
        global motor
        for row in range(1, self.pgrm.tableheight):
            if self.pgrm.entriesX[row].get() == "" and self.pgrm.entriesY[row].get() == "":
                self.pgrm.entriesX[row].insert(0, self.motor.loc_0.get())
                self.pgrm.entriesY[row].insert(0, self.motor.loc_1.get())
                self.pgrmBtn.pgrm_refresh()
                return


class ProgButtons(tk.Frame):
    def __init__(self, master, pgrm, cnvas, motor, ser, slackcomm):
        tk.Frame.__init__(self, master)

        self.pgrm = pgrm
        self.cnvas = cnvas
        self.motor = motor
        self.ser = ser
        self.slackcomm = slackcomm

        self.grid(row=1, column=1)
        inner_frame1 = tk.Frame(master)
        inner_frame1.grid(row=3, column=0)
        bttn_prgm_refresh = tk.Button(inner_frame1, text='Refresh', bg='orange', width=25, command=self.pgrm_refresh) \
            .grid(row=0, column=0, padx=5, pady=15)
        bttn_prgm_clear = tk.Button(inner_frame1, text='Clear', bg='orange', width=25, command=self.pgrm_clear) \
            .grid(row=0, column=1, padx=5, pady=15)

        inner_frame2 = tk.Frame(master)
        inner_frame2.grid(row=3, column=1)
        bttn_manual = tk.Button(inner_frame2, text='Calibrate Origin', bg='orange', width=15, command=self.calibrate) \
            .grid(row=0, column=0, padx=5, pady=15)
        bttn_origin = tk.Button(inner_frame2, text='Go to Origin', bg='orange', width=15, command=self.motor.origin) \
            .grid(row=0, column=1, padx=5, pady=15)

        self.bttn_prgm_run = tk.Button(master, text='Run Program', bg='pink', width=35, command=self.pgrm_run) \
            .grid(row=4, column=0, padx=5, pady=15)
        self.bttn_manual = tk.Button(master, text='Go to location', bg='pink', width=35, command=self.manual_ctrl) \
            .grid(row=4, column=1, padx=5, pady=15)

    def calibrate(self):
        print("Calibrate origin")
        statement = "<Calibrate>"
        self.ser.write(str.encode(statement))
        return

    def pgrm_run(self):
        global recv
        self.pgrm_refresh()
        print("Program Run")
        self.ser.write(str.encode("<Sending>"))

        program_time = 0
        for k in range(0, avail_entry(self.pgrm.entriesX)):
            program_time = program_time + float(self.pgrm.entriesWait[k].get()) + \
                           max(float(self.pgrm.entriesX[k].get()) / float(self.pgrm.entriesSpeedX[k].get()),
                               float(self.pgrm.entriesY[k].get()) / float(self.pgrm.entriesSpeedY[k].get()))
        print('total runtime = ' + str(Decimal(program_time) / Decimal(60)) + ' minutes')

        for k in range(1, avail_entry(self.pgrm.entriesX)):
            program_time = 0
            statement = "<Xabs:" + str(int(float(self.parse_mm_to_step(1, self.pgrm.entriesX[k].get())))) + \
                        ",Yabs:" + str(int(float(self.parse_mm_to_step(2, self.pgrm.entriesY[k].get())))) + \
                        ",Xs:" + str(int(float(self.parse_mm_to_step(1, self.pgrm.entriesSpeedX[k].get())))) + \
                        ",Ys:" + str(int(float(self.parse_mm_to_step(2, self.pgrm.entriesSpeedY[k].get())))) + \
                        ",T:" + str(int(float(self.self.pgrm.entriesWait[k].get()))) + ">"
            print(statement)
            self.ser.write(str.encode(statement))
            print("Runtime X:" + str((float(self.pgrm.entriesX[k].get()) - float(self.pgrm.entriesX[k - 1].get())) / float(
                self.pgrm.entriesSpeedX[k].get())))
            print("Runtime Y:" + str((float(self.pgrm.entriesY[k].get()) - float(self.pgrm.entriesY[k - 1].get())) / float(
                self.pgrm.entriesSpeedY[k].get())))

            program_time = DEFAULT_SLEEP + max(abs(
                (float(self.pgrm.entriesX[k].get()) - float(self.pgrm.entriesX[k - 1].get())) / float(
                    self.pgrm.entriesSpeedX[k].get())),
                                               abs((float(self.pgrm.entriesY[k].get()) - float(
                                                   self.pgrm.entriesY[k - 1].get())) / float(self.pgrm.entriesSpeedY[k].get())))
            print(program_time + float(self.pgrm.entriesWait[k].get()))
            sleep(program_time + float(self.pgrm.entriesWait[k].get()))

        self.motor.origin()
        self.slackcomm.send_message_to_slack('Dip Coater has completed a run.' + dt.datetime.now().strftime("%Y-%m-%d %H:%M"))
        return
        '''
        i = avail_entry(pgrm.entriesX)
        k = 0
        while True:
            recv = ReadLine(self.ser)
            text = recv.read_line().decode("utf-8")
            print('*<' + text)
            print('>*')
            if text == "<Ready>" and k < i:
                statement = "<Xabs:" + str(int(parse_mm_to_step(1, pgrm.entriesX[k].get()))) + \
                            ",Yabs:" + str(int(parse_mm_to_step(2, pgrm.entriesY[k].get()))) + \
                            ",Xs:" + str(int(parse_mm_to_step(1, pgrm.entriesSpeedX[k].get()))) + \
                            ",Ys:" + str(int(parse_mm_to_step(2, pgrm.entriesSpeedY[k].get()))) + \
                            ",T:" + str(int(pgrm.entriesWait[k].get())) + ">"
                print(statement)
                self.ser.write(str.encode(statement))

                k = k + 1
            if i == 0 or k >= i:
                return
        '''

    def pgrm_clear(self):
        for k in range(0, avail_entry(self.pgrm.entriesX)):
            self.pgrm.entriesX[k].delete(0, 'end')
            self.pgrm.entriesY[k].delete(0, 'end')
            self.pgrm.entriesSpeedX[k].delete(0, 'end')
            self.pgrm.entriesSpeedY[k].delete(0, 'end')
            self.pgrm.entriesWait[k].delete(0, 'end')
            self.pgrm.entriesComment[k].delete(0, 'end')
        self.cnvas.description.delete('1.0', 'end')
        return

    def pgrm_refresh(self):
        if self.pgrm.entriesX[0].get() == "":
            self.pgrm.entriesX[0].insert(0, 0)
        if self.pgrm.entriesY[0].get() == "":
            self.pgrm.entriesY[0].insert(0, 0)
        if self.pgrm.entriesX[0].get() != "" or self.pgrm.entriesY[0].get() != "":
            if self.pgrm.entriesSpeedX[0].get() == "":
                self.pgrm.entriesSpeedX[0].insert(0, self.parse_step_to_mm(1, DEFAULT_SPEED))
            if self.pgrm.entriesSpeedY[0].get() == "":
                self.pgrm.entriesSpeedY[0].insert(0, self.parse_step_to_mm(2, DEFAULT_SPEED))
            if self.pgrm.entriesWait[0].get() == "":
                self.pgrm.entriesWait[0].insert(0, 0)

        for row in range(1, self.pgrm.tableheight):
            if self.pgrm.entriesX[row].get() != "" or self.pgrm.entriesY[row].get() != "":
                if self.pgrm.entriesX[row].get() == "":
                    self.pgrm.entriesX[row].insert(0, self.pgrm.entriesX[row - 1].get())
                if self.pgrm.entriesY[row].get() == "":
                    self.pgrm.entriesY[row].insert(0, self.pgrm.entriesY[row - 1].get())
                if self.pgrm.entriesX[row].get() != "" or self.pgrm.entriesY[row].get() != "":
                    if self.pgrm.entriesSpeedX[row].get() == "":
                        self.pgrm.entriesSpeedX[row].insert(0, self.parse_step_to_mm(1, DEFAULT_SPEED))
                    if self.pgrm.entriesSpeedY[row].get() == "":
                        self.pgrm.entriesSpeedY[row].insert(0, self.parse_step_to_mm(2, DEFAULT_SPEED))
                    if self.pgrm.entriesWait[row].get() == "":
                        self.pgrm.entriesWait[row].insert(0, 0)
            else:
                break
        print("Refreshed input table")
        self.cnvas.update_runtime()
        self.cnvas.update_path(self.pgrm)
        return

    def manual_ctrl(self):
        print("Go to location")
        if (self.motor.loc_2.get() == "" or self.motor.loc_3.get() == ""):
            return
        statement = "<Xabs:" + str(int(self.parse_mm_to_step(1, self.motor.loc_2.get()))) + \
                    ",Xs:" + str(DEFAULT_SPEED) + \
                    ",Yabs:" + str(int(self.parse_mm_to_step(2, self.motor.loc_3.get()))) + \
                    ",Ys:" + str(DEFAULT_SPEED) + \
                    ",T:" + str(0) + ">"
        print(statement)
        self.ser.write(str.encode(statement))
        # self.motor.loc_2.delete(0, 'end')  # delete the number in entry after data is sent
        # self.motor.loc_3.delete(0, 'end')  # delete the number in entry after data is sent
        return

    def parse_mm_to_step(self, motor_id, distance_mm):
        switcher_spr = {
            1: self.motor.m1_spr.get(),
            2: self.motor.m2_spr.get()
        }
        switcher_mmpr = {
            1: self.motor.m1_pitch.get(),
            2: self.motor.m2_pitch.get()
        }
        spr = switcher_spr.get(motor_id, 0)  # steps per revolution
        mmpr = switcher_mmpr.get(motor_id, 0)  # millimeters per revolution
        step_num = (float(distance_mm) / float(mmpr)) * float(spr)
        print(step_num)
        return step_num

    def parse_step_to_mm(self, motor_id, distance_step):
        switcher_spr = {
            1: self.motor.m1_spr.get(),
            2: self.motor.m2_spr.get()
        }
        switcher_mmpr = {
            1: self.motor.m1_pitch.get(),
            2: self.motor.m2_pitch.get()
        }
        spr = switcher_spr.get(motor_id, 0)  # steps per revolution
        mmpr = switcher_mmpr.get(motor_id, 0)  # millimeters per revolution
        mm_travel = (float(distance_step) * float(mmpr)) / float(spr)
        return mm_travel


class MotorSetup(tk.Frame):
    def __init__(self, ser):
        tk.Frame.__init__(self, None)
        self.ser = ser

        self.grid(row=1, column=1)
        self.label_2 = tk.Label(self, text="Motor 2 - SPR", width=25)
        self.label_2.grid(row=0, column=0)
        self.m1_spr = tk.Entry(self, width=25)
        self.m1_spr.insert(0, 25000)
        self.m1_spr.grid(row=1, column=0)
        self.label_3 = tk.Label(self, text="Motor 2 - MMPR", width=25)
        self.label_3.grid(row=2, column=0)
        self.m1_pitch = tk.Entry(self, width=25)
        self.m1_pitch.insert(0, 5)
        self.m1_pitch.grid(row=3, column=0)
        self.label_0 = tk.Label(self, text="Real-time X (mm)", width=25)
        self.label_0.grid(row=4, column=0)
        self.loc_0 = tk.Entry(self, width=25)
        self.loc_0.grid(row=5, column=0)

        self.label_4 = tk.Label(self, text="Motor 1 - SPR", width=25)
        self.label_4.grid(row=0, column=1)
        self.m2_spr = tk.Entry(self, width=25)
        self.m2_spr.insert(0, 25000)
        self.m2_spr.grid(row=1, column=1)
        self.label_5 = tk.Label(self, text="Motor 1 - MMPR", width=25)
        self.label_5.grid(row=2, column=1)
        self.m2_pitch = tk.Entry(self, width=25)
        self.m2_pitch.insert(0, 5)
        self.m2_pitch.grid(row=3, column=1)
        self.label_1 = tk.Label(self, text="Real-time Y (mm)", width=25)
        self.label_1.grid(row=4, column=1)
        self.loc_1 = tk.Entry(self, width=25)
        self.loc_1.grid(row=5, column=1)

        self.label_8 = tk.Label(self, text="step X (mm)", width=25)
        self.label_8.grid(row=6, column=0)
        self.step1 = tk.Entry(self, width=25)
        self.step1.insert(0, 10)
        self.step1.grid(row=7, column=0)
        self.label_9 = tk.Label(self, text="step Y (mm)", width=25)
        self.label_9.grid(row=6, column=1)
        self.step2 = tk.Entry(self, width=25)
        self.step2.insert(0, 10)
        self.step2.grid(row=7, column=1)

        self.label_6 = tk.Label(self, text="Go to X (mm)", width=25)
        self.label_6.grid(row=8, column=0)
        self.loc_2 = tk.Entry(self, width=25)
        self.loc_2.grid(row=9, column=0)
        self.label_7 = tk.Label(self, text="Go to Y (mm)", width=25)
        self.label_7.grid(row=8, column=1)
        self.loc_3 = tk.Entry(self, width=25)
        self.loc_3.grid(row=9, column=1)

    def origin(self, *args):
        global ser
        print("Return to Origin")
        statement = "<Xabs:" + str(0) + \
                    ",Yabs:" + str(0) + \
                    ",Xs:" + str(DEFAULT_SPEED) + \
                    ",Ys:" + str(DEFAULT_SPEED) + \
                    ",T:" + str(0) + ">"
        print(statement)
        self.ser.write(str.encode(statement))
        # cnvas.loc_refresh()
        return


class MotionPath(tk.Canvas):
    def __init__(self, master, pgrm, ser):

        self.pgrm = pgrm
        self.ser = ser

        self.canvas_frame = tk.Frame(master)
        self.canvas_frame.grid(row=0, column=0)
        self.canvas_height = 250
        self.canvas_width = 150
        self.originX = 10
        self.originY = 10
        self.pointerRadius = 5

        tk.Canvas.__init__(self, master=self.canvas_frame, width=self.canvas_width + 20, height=self.canvas_height + 20)
        self.grid(row=0, column=0, padx=15, pady=15)
        self.canvas_frame_inner = tk.Frame(self.canvas_frame)
        self.canvas_frame_inner.grid(row=0, column=1)
        self.description_label = tk.Label(self.canvas_frame_inner, text="Note to program users", width=35)
        self.description_label.grid(row=0, column=0)
        self.description = scrolledtext.ScrolledText(self.canvas_frame_inner, wrap=tk.WORD, width=35, height=10)
        self.description.grid(row=1, column=0)
        mytext = "Please put a short description of your CNC configurations here, so other " \
                 "users will know the use of this configuration and related precautions."
        self.description.insert('insert', mytext)

        total_runtime = "Total runtime: N/A minutes"
        self.description_label = tk.Label(self.canvas_frame_inner, text=total_runtime)
        self.description_label.grid(row=2, column=0)

        self.create_widget()

    def update_runtime(self):
        self.description_label.destroy()
        program_time = 0
        for k in range(1, avail_entry(self.pgrm.entriesX)):
            program_time = program_time + DEFAULT_SLEEP + \
                           max(abs((float(self.pgrm.entriesX[k].get()) - float(self.pgrm.entriesX[k - 1].get())) / float(
                               self.pgrm.entriesSpeedX[k].get())),
                               abs((float(self.pgrm.entriesY[k].get()) - float(self.pgrm.entriesY[k - 1].get())) / float(
                                   self.pgrm.entriesSpeedY[k].get())))
        total_runtime = "Total runtime: " + str(float(Decimal(program_time) / Decimal(60))) + " minutes"
        print(total_runtime)
        self.description_label = tk.Label(self.canvas_frame_inner, text=total_runtime)
        self.description_label.grid(row=2, column=0)

    def create_widget(self):
        self.create_rectangle(10, 10, self.canvas_width, self.canvas_height, fill='lightgray')
        self.create_line(10, self.canvas_height, self.canvas_width, self.canvas_height, arrow=tk.LAST)
        self.create_line(10, self.canvas_height, 10, 10, arrow=tk.LAST)

    def update_path(self, pgrm):
        self.delete("all")
        self.create_widget()
        # print(pgrm.entriesX[0].get() + '&' + pgrm.entriesY[0].get())
        self.create_oval(float(pgrm.entriesX[0].get()) + self.originX - self.pointerRadius,
                         float(pgrm.entriesY[0].get()) + self.originY - self.pointerRadius,
                         float(pgrm.entriesX[0].get()) + self.originX + self.pointerRadius,
                         float(pgrm.entriesY[0].get()) + self.originY + self.pointerRadius,
                         fill="blue", outline="#DDD")
        for row in range(1, pgrm.tableheight):
            if pgrm.entriesX[row].get() != "" or pgrm.entriesY[row].get() != "":
                self.create_oval(float(pgrm.entriesX[row].get()) + self.originX - self.pointerRadius,
                                 float(pgrm.entriesY[row].get()) + self.originY - self.pointerRadius,
                                 float(pgrm.entriesX[row].get()) + self.originX + self.pointerRadius,
                                 float(pgrm.entriesY[row].get()) + self.originY + self.pointerRadius,
                                 fill="blue", outline="#DDD")
                self.create_line(float(pgrm.entriesX[row - 1].get()) + self.originX,
                                 float(pgrm.entriesY[row - 1].get()) + self.originY,
                                 float(pgrm.entriesX[row].get()) + self.originX,
                                 float(pgrm.entriesY[row].get()) + self.originY,
                                 arrow=tk.LAST)
                # print(pgrm.entriesX[row].get() + '&' + pgrm.entriesY[row].get())
            else:
                break

    def loc_refresh(self):
        # read location data from Arduino and parse it to X and Y values
        # draw unique marker showing the current location of the holder
        recv2 = ReadLine(self.ser)
        # text = "<locX:12345,locY:09876>"
        text = recv2.read_line().decode("utf-8")
        x, y = self.parse_location(text)
        self.create_oval(x + self.originX - self.pointerRadius,
                         y + self.originY - self.pointerRadius,
                         x + self.originX + self.pointerRadius,
                         y + self.originY + self.pointerRadius,
                         fill="red", outline="#DDD")
        return

    def parse_location(self, text):
        token = re.findall(r"[\w']+", text)
        # print(token)
        try:
            if token[0] == 'locX' and token[2] == 'locY':
                loc_x = float(token[1])
                loc_y = float(token[3])
                # print(loc_x)
                # print(loc_y)
                return loc_x, loc_y
        except ValueError:
            return None


class ReadLine:
    def __init__(self, s):
        self.buf = bytearray()
        self.s = s

    def read_line(self):
        i = self.buf.find(b"\n")
        if i >= 0:
            r = self.buf[:i + 1]
            self.buf = self.buf[i + 1:]
            return r
        while True:
            i = max(1, min(32, self.s.in_waiting))
            data = self.s.read(i)
            i = data.find(b"\n")
            if i >= 0:
                r = self.buf + data[:i + 1]
                self.buf[0:] = data[i + 1:]
                return r
            else:
                self.buf.extend(data)


# Global function

'''def recv_serial(master):
    global recv
    recv = ReadLine(ser)
    text = recv.read_line().decode("utf-8")
    print(text)
    master.after(80, recv_serial)'''


def avail_entry(array):
    member_number = 0
    for i in range(0, len(array)):
        if array[i].get() != "":
            member_number = member_number + 1
        else:
            return member_number
    print('member number: ' + member_number)
    return member_number


def show_error(*args):
    err = traceback.format_exception(*args)
    messagebox.showerror('Exception', err)


def info_help():
    manual = "Shortcuts: \n" \
             "Ctrl+s = Save Program \n" \
             "Ctrl+o = Load Program \n" \
             "Ctrl+[arrow keys] = manual motor controls \n"
    messagebox.showinfo("User Manual", manual)


def info_about():
    about = "Dip Coater Version 1: July 16, 2019 \n" \
            "Created by Phacharapol Tanasarnsopaporn"
    messagebox.showinfo("About", about)


'''
To send message to Slack, I first integrated "Incoming WebHooks" app
on Slack that generates me the simple https url that I can request 
message from or to send message to. 
'''

