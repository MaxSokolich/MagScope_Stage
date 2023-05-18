#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module containing the GUI class

@authors: Max Sokolich, Brennan Gallamoza, Luke Halko, Trea Holley,
          Alexis Mainiero, Cameron Thacker, Zoe Valladares
pix = 1936 x 1464 mono
maxframerate = 130 (actually ~60)
exptime = 10us - 30s
iamge buffer = 240 MB

or 

pix - 2448 x 2048 color
maxframerate = 35 (actually 24)
"""
import colorsys
from queue import Empty
import multiprocessing
import time as time
import numpy as np
from typing import Union
from tkinter import *
from tkinter import Tk
from tkinter import filedialog

from src.new_python_src.AcousticClass import AcousticClass
from src.new_python_src.HallEffect import HallEffect
from src.new_python_src.Tracker import Tracker
from src.new_python_src.ArduinoHandler import ArduinoHandler
from src.new_python_src.JoystickHandler import JoystickHandler



# with jetson orin, cam can get up to 35 fps

PID_PARAMS = {
    "Iframes": 100,
    "Dframes": 10,
    "Kp": 0.1,
    "Ki": 0.01,
    "Kd": 0.01,
}

CONTROL_PARAMS = {
    "lower_thresh": np.array([0,0,0]),  #HSV
    "upper_thresh": np.array([180,255,140]),  #HSV   #130/150
    "blur_thresh": 100,
    "initial_crop": 100,       #intial size of "screenshot" cropped frame 
    "tracking_frame": 1,            #cropped frame dimensions mulitplier
    "avg_bot_size": 5,
    "field_strength": 1,
    "rolling_frequency": 10,
    "arrival_thresh": 10,
    "gamma": 90,
    "memory": 15,
    "PID_params": PID_PARAMS,
}

CAMERA_PARAMS = {
    "resize_scale": 50, 
    "framerate": 24, 
    "exposure": 6000,   #6000
    "Obj": 50}

STATUS_PARAMS = {
    "rolling_status": 0,
    "orient_status": 0,
    "multi_agent_status": 0,
    "PID_status": 0,
    "algorithm_status": False,
    "record_status": False,
}

ACOUSTIC_PARAMS = {
    "acoustic_freq": 0,
    "acoustic_amplitude": 0
}

MAGNETIC_FIELD_PARAMS = {
    "PositiveY": 0,
    "PositiveX": 0,
    "NegativeY": 0,
    "NegativeX": 0,
}



class GUI:
    """
    Handles the Tkinter GUI actions for the microbot tracking user interface,
    including global adjustments to the tracker, file input and output, CUDA
    toggling, and other features

    Args:
        master: Tk window acting as the main window of the GUI
        arduino: ArduinoHandler object containing arduino connection information
    """

    def __init__(self, master: Tk, arduino: ArduinoHandler):
        # Tkinter window attributes
        self.main_window = master
        self.screen_width = self.main_window.winfo_screenwidth()
        self.screen_height = self.main_window.winfo_screenheight()
        self.x, self.y = 0, 0
        self.w, self.h = (
            self.main_window.winfo_reqwidth(),
            self.main_window.winfo_reqheight(),
        )

        #update sensor process/queue
        self.sensor = None
        self.sense_q = multiprocessing.Queue(1)
        self.checksensor = None

         #update joystick process/queue
        self.joystick = None
        self.joystick_q =  multiprocessing.Queue(1)
        self.checkjoy = None
     

          
        # Tracker-related attributes
        self.arduino = arduino
        
        #define instance of acoustic module
        self.AcousticModule = AcousticClass()

        #acoustic conditioning/logic
        self.button_state = 0
        self.last_state = 0
        self.counter = 0
        self.switch_state = 0

        # Tkinter widget attributes
        self.text_box = Text(master, width=22, height=4)
        self.scroll_bar = Scrollbar(
            master, 
            command=self.text_box.yview, 
            orient="vertical"
        )
        self.text_box.configure(yscrollcommand=self.scroll_bar.set)
        self.text_box.grid(row=7, column=2, columnspan =2,sticky="nwse")

       


        coil_joystick_button = Button(
            master, 
            text="Joystick On", 
            command=self.joy_proc, 
            height=1, 
            width=18,
            bg = 'magenta',
            fg= 'white'
        )
        coil_joystick_button.grid(row=0, column=3,rowspan =1)

        sensor_button = Button(
            master, 
            text="Sensor On", 
            command=self.sensor_proc, 
            height=1, 
            width=18,
            bg = 'black',
            fg= 'white'
        )
        sensor_button.grid(row=1, column=3,rowspan =1)

        acoustic_params_button = Button(
            master,
            text="Edit Acoustic Params",
            command=self.edit_acoustic_params,
            height=1,
            width=20,
            bg = 'cyan',
            fg= 'black'
        )  
        acoustic_params_button.grid(row=2, column=0)
    
        #5 BIG BUTTONS

        Big_button_frame = Frame(master = master)
        Big_button_frame.grid(row=0,column=1,rowspan = 7)

        status_button = Button(
            Big_button_frame, 
            text="Stop:\nZero All Signals", 
            command=self.status, 
            height=5, 
            width=20,
            bg = 'red',
            fg= 'white'
        )

        track_button = Button(
            Big_button_frame, 
            text="Track", 
            command=self.track, 
            height=4, 
            width=20,
            bg = 'blue',
            fg= 'white'
        )

  

        close_button = Button(master, 
            text="Exit", 
            width=10, 
            height=4, 
            command=self.exit, 
            bg = 'black',
            fg= 'white')

        status_button.grid(row=0, column=1,rowspan =3)
        track_button.grid(row=3, column=1,rowspan=2)
        close_button.grid(row=7, column=0)

  

    
        #BFIELD FRAME
        Bfield_frame = Frame(master = master)
        Bfield_frame.grid(row=3,column=0,rowspan = 2)

        Yfield_label = Label(master=Bfield_frame, text="Y", width=10)
        Yfield_label.grid(row=0, column=0)
        self.Yfield_Entry = Entry(master=Bfield_frame, width=5)
        self.Yfield_Entry.grid(row=0, column=1)
        
        Xfield_label = Label(master=Bfield_frame, text="X", width=10)
        Xfield_label.grid(row=1, column=0)
        self.Xfield_Entry = Entry(master=Bfield_frame, width=5)
        self.Xfield_Entry.grid(row=1, column=1)

        nYfield_label = Label(master=Bfield_frame, text="-Y", width=10)
        nYfield_label.grid(row=2, column=0)
        self.nYfield_Entry = Entry(master=Bfield_frame, width=5)
        self.nYfield_Entry.grid(row=2, column=1)

        nXfield_label = Label(master=Bfield_frame, text="-X", width=10)
        nXfield_label.grid(row=3, column=0)
        self.nXfield_Entry = Entry(master=Bfield_frame, width=5)
        self.nXfield_Entry.grid(row=3, column=1)

        


    
   



    
    def edit_acoustic_params(self):
        """
        Creates a new window to control the AD9850 Signal generator module. 
        genereates sinusoidal or square waveforms from 0-40 MHz

        Args:
            None

        Returns:
            None
        """
        window5 = Toplevel(self.main_window)
        window5.title("Acoustic Module")

        
        
        def apply_freq():
            self.AcousticModule.start(ACOUSTIC_PARAMS["acoustic_freq"],ACOUSTIC_PARAMS["acoustic_amplitude"])
            self.text_box.insert(END," -- waveform ON -- \n")
            self.text_box.see("end")
        
        def stop_freq():
            self.AcousticModule.stop()
            self.text_box.insert(END," -- waveform OFF -- \n")
            self.text_box.see("end")
        
        def test_freq():
            self.AcousticModule.start(int(10000),ACOUSTIC_PARAMS["acoustic_amplitude"])
            self.text_box.insert(END," -- 10kHz Test -- \n")
            self.text_box.see("end")
        
        def update_loop_slider_values(event):
            """
            Constantly updates acoustic params when the sliders are used.
            Params:
                event
            Returns:
                None
            """
            ACOUSTIC_PARAMS["acoustic_freq"] = int(acoustic_slider.get())
            ACOUSTIC_PARAMS["acoustic_amplitude"] = int(amplitude_slider.get())
            apply_freq()
            self.main_window.update()

        #create apply widget
        apply_button = Button(
            window5, 
            text="Apply", 
            command=apply_freq, 
            height=1, width=10,
            bg = 'blue',
            fg= 'white'
        )
        apply_button.pack()
        
        #create stop widget
        stop_button = Button(
            window5, 
            text="Stop", 
            command=stop_freq, 
            height=1, width=10,
            bg = 'red',
            fg= 'white'
        )
        stop_button.pack()

        #create test widget
        test_button = Button(
            window5, 
            text="Test 10kHz", 
            command=test_freq, 
            height=1, width=10,
            bg = 'green',
            fg= 'white'
        )

        test_button.pack()


        #create freq widget
        acoustic_frequency = DoubleVar()
        acoustic_slider = Scale(
            master=window5,
            label="Acoustic Frequency",
            from_=1000000,
            to=2000000,
            resolution=1000,
            variable=acoustic_frequency,
            width=50,
            length=1000,
            orient=HORIZONTAL,
            command=update_loop_slider_values,
        )
       
        acoustic_slider.set(ACOUSTIC_PARAMS["acoustic_freq"])        
        acoustic_slider.pack()
        
        #create amplitude widget
        acoustic_amplitude = DoubleVar()
        amplitude_slider = Scale(
            master=window5,
            label="Acoustic Amplitude",
            from_=0,
            to=5,
            resolution=.1,
            variable=acoustic_amplitude,
            width=50,
            length=1000,
            orient=HORIZONTAL,
            command=update_loop_slider_values,
        )
       
        amplitude_slider.set(ACOUSTIC_PARAMS["acoustic_amplitude"])        
        amplitude_slider.pack()
        
        def EXIT():
            window5.destroy()
        window5.protocol("WM_DELETE_WINDOW",EXIT)
    

 


   

    def track(self):
        """
        Initiates a Tracker instance for microbot tracking

        Args:
            None

        Returns:
            None
        """
        tracker = Tracker(self.main_window,CONTROL_PARAMS,
            CAMERA_PARAMS,
            STATUS_PARAMS,)
        tracker.main(self.arduino)


        

        



    def status(self):
        """
        Resets and zeros all status variables in tracker (i.e. zeros all outputs)

        Args:
            None

        Returns:
            None
        """
       

        STATUS_PARAMS["algorithm_status"] = False
        

        #self.tracker.robot_window.destroy()
        self.arduino.send(4, 0, 0, 0)
        
        #shutdown hall sensor readings
        if self.sensor is not None:
            self.sensor.shutdown()
            self.main_window.after_cancel(self.checksensor)

        if self.joystick is not None:
            self.joystick.shutdown()
            self.main_window.after_cancel(self.checkjoy)
          
    
            

    def get_widget(self, window: Union[Tk, Toplevel], widget_name: str) -> Widget:
        """
        Gets a widget in the main window by name

        Args:
            widget_name:    name of the desired widget on the main window

        Returns:
            None
        """
        try:
            return window.nametowidget(widget_name)
        except KeyError:
            raise KeyError(f"Cannot find widget named {widget_name}")


    def sensor_proc(self):
        """
        creates an instance of HallEffect class and starts a subprocess to read values

        Args:
            None
        Returns:
            None
        """
        self.sensor = HallEffect()
        self.sensor.start(self.sense_q)
        self.checksensor = self.main_window.after(10, self.CheckSensorPoll, self.sense_q)
    
    def CheckSensorPoll(self,s_queue):
        """
        checks the hall effect sensor queue for incoming sensors values

        Args:
            c_queue: queue object
        Returns:
            None
        """
        try:
            value_array = s_queue.get(0) # [s1,s2,s3,s4]
            
            #update Yfield
            self.Yfield_Entry.delete(0,END)
            self.Yfield_Entry.insert(0,"{}".format(value_array[0])) 

            #update Xfield
            self.Xfield_Entry.delete(0,END)
            self.Xfield_Entry.insert(0,"{}".format(value_array[1])) 

            #update nYfield
            self.nYfield_Entry.delete(0,END)
            self.nYfield_Entry.insert(0,"{}".format(value_array[2]))

            #update nXfield
            self.nXfield_Entry.delete(0,END)
            self.nXfield_Entry.insert(0,"{}".format(value_array[3]))
        except Empty:
            pass
        finally:
            self.main_window.after(10,self.CheckSensorPoll, s_queue)
    
    def joy_proc(self):
        """
        creates an instance of JoystickProcess class and starts a subprocess to read values

        Args:
            None
        Returns:
            None
        """
        self.joystick = JoystickHandler()
        self.joystick.start(self.joystick_q)
        self.checkjoy = self.main_window.after(10, self.CheckJoystickPoll, self.joystick_q)

    
    def CheckJoystickPoll(self,j_queue):
        """
        checks the joystick queue for incoming command values

        Args:
            c_queue: queue object
            joy_array: [typ, input1, input2, input3]
            input1(typ1 | typ2) = angle|  Bx
            input2(typ1 | typ2) = freq | By
            input3(typ1 | typ2) = gamma | Bz
        Returns:
            None
        """
        try:
            joy_array = j_queue.get(0) # [typ,input1,input2,input3]
            typ = joy_array[0]   # type of acuation method
            
            #Send arduino signal
            if typ == 1:
                #gamma toggle logic.
                if joy_array[3] == 0:
                    self.arduino.send(typ, joy_array[1], CONTROL_PARAMS["rolling_frequency"], joy_array[3]) #use gamma = 0
                else: 
                    self.arduino.send(typ, joy_array[1], CONTROL_PARAMS["rolling_frequency"], CONTROL_PARAMS["gamma"])
            else:
                self.arduino.send(typ, joy_array[1], joy_array[2], joy_array[3]) 
                
            #A Button Function --> Acoustic Module Toggle
            self.button_state = joy_array[4]
            if self.button_state != self.last_state:
                if self.button_state == True:
                    self.counter +=1
            self.last_state = self.button_state
            if self.counter %2 != 0 and self.switch_state !=0:
                self.switch_state = 0
                self.AcousticModule.start(ACOUSTIC_PARAMS["acoustic_freq"],ACOUSTIC_PARAMS["acoustic_amplitude"])
                self.text_box.insert(END, " -- waveform ON -- \n")
                self.text_box.see("end")
                #print("acoustic: on")
            elif self.counter %2 == 0 and self.switch_state !=1:
                self.switch_state = 1
                self.AcousticModule.stop()
                self.text_box.insert(END, " -- waveform OFF -- \n")
                self.text_box.see("end")

        except Empty:
            pass
        finally:
            self.main_window.after(10,self.CheckJoystickPoll, j_queue)



    def exit(self):
        """
        Quits the main window (self.main_window) and quits the ardunio connection
            exit()

        Args:
            None

        Returns:
            None
        """
        self.AcousticModule.exit()
        self.main_window.quit()
        self.main_window.destroy()
        self.arduino.close()


    def main(self) -> None:
        """
        Starts the tkinter GUI by opening up the main window
        continously displays magnetic field values if checked

        Args:
            None

        Returns:
            None
        """
        self.main_window.mainloop()
