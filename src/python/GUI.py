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
import matplotlib.pyplot as plt
import threading
import colorsys
from queue import Empty
import multiprocessing
multiprocessing.set_start_method('forkserver', force=True)
multiprocessing.freeze_support()
import cv2
from datetime import datetime
import time as time
import numpy as np
from typing import Union
from tkinter import *
from tkinter import Tk
from tkinter import filedialog
import platform

from src.python.AcousticClass import AcousticClass
from src.python.HallEffect import HallEffect
from src.python.Custom2DTracker import Tracker
from src.python.ArduinoHandler import ArduinoHandler
from src.python.Brightness import Brightness
from src.python.AnalysisClass import Analysis
from src.python.PS4_Linux import MyController
from src.python.Params import CONTROL_PARAMS, CAMERA_PARAMS, STATUS_PARAMS, ACOUSTIC_PARAMS, MAGNETIC_FIELD_PARAMS,PID_PARAMS,MASK

if "mac" in platform.platform():
    from src.python.PS4_Mac import MyController
    #from tkmacosx import Button
elif "linux" in platform.platform():
    from src.python.PS4_Linux import MyController
elif "Windows" in platform.platform():
    from src.python.PS4_Windows import MyController






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
        self.joystick_process = None
        self.joystick_q =  multiprocessing.Queue(1)
        self.checkjoy = None
     
          
          
        # Tracker-related attributes
        self.arduino = arduino
        self.external_file = None



        
        #define instance of acoustic module
        self.AcousticModule = AcousticClass()
        self.AcousticModule.dp_activate()

        #define instance of MotorStage


        # Tkinter widget attributes



        closed_loop_params_button = Button(
            master,
            text="Edit Control Params",
            command=self.edit_closed_loop_params,
            height=1,
            width=20,
            bg = 'green',
            fg= 'black'
        )

        cam_params_button = Button(
            master,
            text="Edit Camera Params",
            command=self.edit_camera_params,
            height=1,
            width=20,
            bg = 'yellow',
            fg= 'black'
        )

        acoustic_params_button = Button(
            master,
            text="Edit Acoustic Params",
            command=self.edit_acoustic_params,
            height=1,
            width=20,
            bg = 'cyan',
            fg= 'black'
        )

        pid_params_button = Button(
            master,
            text="Edit PID Params",
            command=self.edit_pid_params,
            height=1,
            width=20,
            bg = 'black',
            fg= 'white'
        )

        closed_loop_params_button.grid(row=0, column=0)
        cam_params_button.grid(row=1, column=0)
        acoustic_params_button.grid(row=2, column=0)
        pid_params_button.grid(row=3,column=0)



         #BFIELD FRAME
        Bfield_frame = Frame(master = master)
        Bfield_frame.grid(row=4,column=0,rowspan = 4)

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

        close_button = Button(master, 
            text="Exit", 
            width=20, 
            height=4, 
            command=self.exit, 
            bg = 'black',
            fg= 'white')
        close_button.grid(row=8, column=0)
        

         #5 BIG BUTTONS

        self.Big_button_frame = Frame(master = master)
        self.Big_button_frame.grid(row=0,column=1,rowspan = 4)

        status_button = Button(
            self.Big_button_frame, 
            text="Stop:\nZero All Signals", 
            command=self.status, 
            height=4, 
            width=20,
            bg = 'red',
            fg= 'white'
        )

        self.track_button = Button(
            self.Big_button_frame, 
            text="Track", 
            command=self.track, 
            height=4, 
            width=20,
            relief="raised",
            highlightbackground = "blue",
            bg = 'blue',
            fg= 'white'
        )

        status_button.grid(row=0, column=0)
        self.track_button.grid(row=1, column=0)


        #3 CHECKBOXES FRAME
        self.checkboxes_frame = Frame(master = master)
        self.checkboxes_frame.grid(row=4,column=1,rowspan = 4)

        vid_name = Button(
            master= self.checkboxes_frame,
            name="vid_name",
            text="Choose Video",
            command=self.upload_vid,
            height=1,
            width=10,
            bg = 'red',
            fg= 'black'
        )

        live_var = IntVar(master=master, name="live_var")
        livecam_button = Checkbutton(
            master = self.checkboxes_frame,
            name="live_checkbox",
            text="Live Cam for \nTracking?",
            variable=live_var,
            onvalue=1,
            offvalue=0,
        )
        livecam_button.var = live_var
    
    
        """cuda_var = IntVar(master=master, name="cuda_var")
        cuda_button = Checkbutton(
            master=self.checkboxes_frame,
            name="cuda_checkbox",
            text="Use CUDA?",
            variable=cuda_var,
            onvalue=1,
            offvalue=0,
        )
        cuda_button.var = cuda_var
        cuda_button.grid(row=2, column=0)"""


        vid_name.grid(row=0, column=0)
        livecam_button.grid(row=1, column=0)
        

        self.mask_button = Button(
            self.checkboxes_frame, 
            text="View Mask", 
            command=self.viewmask, 
            height=1, 
            width=10,
            relief="raised",
            highlightbackground = "blue",
            bg = 'blue',
            fg= 'black'
        )
        self.mask_button.grid(row=2, column=0)

        

        orientsign_button = Button(
            self.checkboxes_frame, 
            text="sign flip", 
            command=self.orientsign, 
            height=1, 
            width=5,
            bg = 'black',
            fg= 'white'
        )
        orientsign_button.grid(row=3, column=0)




        #VIDEO RECORD FRAME
        self.video_record_frame = Frame(master = master)
        self.video_record_frame.grid(row=8,column=1,rowspan = 2)


        output_name = Entry(master=self.video_record_frame, name="output_name")
        output_name.insert(10, "")

        record_button = Button(
            self.video_record_frame, 
            text="Record", 
            command=self.record, 
            height=1, 
            width=10,
            bg = 'red',
            fg= 'black'
        )

        stop_record_button = Button(
            self.video_record_frame, 
            text="Stop Record", 
            command=self.stop_record, 
            height=1, 
            width=10,
            bg = 'white',
            fg= 'black'
        )

        Label(master = self.video_record_frame, text="Output Name").grid(row=0, column=0)
        output_name.grid(row=1, column=0)
        record_button.grid(row=2, column=0)
        stop_record_button.grid(row=3, column=0)







        



        
        #2 ALGORITHM FRAME
        self.algorithm_frame = Frame(master = master)
        self.algorithm_frame.grid(row=0,column=2,rowspan = 5)
        
        Label(master = self.algorithm_frame, text="--Algorithm List--").grid(row=0, column=0)

        AlgoRoll = IntVar(master=master, name="roll")
        AlgoRoll_box = Checkbutton(
            master=self.algorithm_frame, 
            name = "roll",
            text="Roll", 
            command = self.coil_roll,
            variable=AlgoRoll, 
            onvalue=1, 
            offvalue=0
        )
        AlgoRoll_box.var = AlgoRoll

        AlgoOrient = IntVar(master=master, name="orient")
        AlgoOrient_box = Checkbutton(
            master=self.algorithm_frame, 
            name = "orient",
            text="Orient", 
            command = self.coil_orient,
            variable=AlgoOrient, 
            onvalue=1, 
            offvalue=0
        )
        AlgoOrient_box.var = AlgoOrient

        AlgoMulti = IntVar(master=master, name="multi")
        AlgoMulti_box = Checkbutton(
            master=self.algorithm_frame, 
            name = "multi",
            text="Multi-Agent", 
            command = self.coil_multi_agent,
            variable=AlgoMulti, 
            onvalue=1, 
            offvalue=0
        )
        AlgoMulti_box.var = AlgoMulti

        AlgoPID = IntVar(master=master, name="pid")
        AlgoPID_box = Checkbutton(
            master=self.algorithm_frame, 
            name = "pid",
            text="PID", 
            command = self.coil_PID,
            variable=AlgoPID, 
            onvalue=1, 
            offvalue=0
        )
        AlgoPID_box.var = AlgoPID

        AlgoAcoustic = IntVar(master=master, name="acoustic")
        AlgoAcoustic_box = Checkbutton(
            master=self.algorithm_frame, 
            name = "acoustic",
            text="Acoustic", 
            command = self.coil_acoustic,
            variable=AlgoAcoustic, 
            onvalue=1, 
            offvalue=0
        )
        AlgoAcoustic_box.var = AlgoAcoustic


        AlgoPathPanner = IntVar(master=master, name="pathplanner")
        AlgoPathPanner_box = Checkbutton(
            master=self.algorithm_frame, 
            name = "pathplanner",
            text="RRT", 
            command = self.coil_pathplanner,
            variable=AlgoPathPanner, 
            onvalue=1, 
            offvalue=0
        )
        AlgoPathPanner_box.var = AlgoPathPanner


        run_algo_button = Button(
            self.algorithm_frame,
            text="Run Algo", 
            command=self.run_algo, 
            height=1, 
            width=10,
            bg = 'yellow',
            fg= 'black'
        )


        AlgoRoll_box.grid(row=1, column=0)
        AlgoOrient_box.grid(row=2, column=0)
        AlgoMulti_box.grid(row=3, column=0)
        AlgoPID_box.grid(row=4, column=0)
        AlgoAcoustic_box.grid(row=5, column=0)
        AlgoPathPanner_box.grid(row=6,column=0)
        run_algo_button.grid(row=7, column=0)

        

    

        savepickle = IntVar(master=master, name="savepickle_var")
        savepickle_box = Checkbutton(
            master=self.main_window, 
            name = "savepickle",
            text="Save Pickle File", 
            variable=savepickle, 
            onvalue=1, 
            offvalue=0
        )
        savepickle_box.var = savepickle
        savepickle_box.grid(row=5, column=2)
       

        

        #under algo list stuff
        coil_joystick_button = Button(
            master, 
            text="Joystick On", 
            command=self.joy_proc, 
            height=1, 
            width=10,
            bg = 'magenta',
            fg= 'white'
        )

        sensor_button = Button(
            master, 
            text="Sensor On", 
            command=self.sensor_proc, 
            height=1, 
            width=10,
            bg = 'black',
            fg= 'white'
        )

        
        coil_joystick_button.grid(row=6, column=2)
        sensor_button.grid(row=7, column=2)

        self.text_box = Text(master, width=22, height=4)
        self.scroll_bar = Scrollbar(
            master, 
            command=self.text_box.yview, 
            orient="vertical"
        )
        self.text_box.configure(yscrollcommand=self.scroll_bar.set)
        self.text_box.grid(row=8, column=2, columnspan =2,sticky="nwse")

         #6 GUI MAINFRAME: OTHER
        Label(master, text="---Robot List---").grid(row=0, column=4)
        
        
        
        


    def orientsign(self):
        STATUS_PARAMS["orientsign"] *=-1
        self.text_box.insert(END,"sign of Bx = {}\n".format(STATUS_PARAMS["orientsign"]))
        self.text_box.see("end")


    def viewmask(self):
        if self.mask_button.config("relief")[-1] == "sunken":
            self.mask_button.config(relief = "raised")
            self.mask_button.config(text = "View Mask", bg = 'blue',fg= 'black',highlightbackground = "blue")
            
            if MASK["img"] is not None:
                out = "src/imgs/mask.png"   #svae  mask to png
                cv2.imwrite(out, MASK["img"])

                STATUS_PARAMS["mask_status"] = False
                cv2.destroyWindow("Max's Mask")
                self.text_box.insert(END,"Saved Mask\n to "+ out +"\n")
                self.text_box.see("end")

        else:
            self.mask_button.config(relief = "sunken")
            self.mask_button.config(text = "Close Mask", bg = 'blue',fg= 'red',highlightbackground = "red")

            STATUS_PARAMS["mask_status"] = True
            self.text_box.insert(END,"Displaying Mask\n")
            self.text_box.see("end")
            


    def upload_vid(self):
        """
        Helper function for uploading a video to be tracked

        Args:
            None
        Returns:
            None
        """
        filename = filedialog.askopenfilename()
        self.text_box.insert(END,"Loaded: {}\n".format(filename))
        self.text_box.see("end")
        self.external_file = filename

    def coil_roll(self):
        """
        Flips the state of Rolling_Status to True when "Roll" is clicked

        Args:
            None
        Returns:
            None
        """
        STATUS_PARAMS["rolling_status"] = self.get_widget(self.algorithm_frame, "roll").var.get()
        
    def coil_orient(self):
        """
        Flips the state of Orient_Status to True when "Orient" is clicked

        Args:
            None
        Returns:
            None
        """
        STATUS_PARAMS["orient_status"] = self.get_widget(self.algorithm_frame, "orient").var.get()

    def coil_multi_agent(self):
        """
        Flips the state of "multi_agent_status" to True when "Multi-Agent" is clicked

        Args:
            None
        Returns:
            None
        """
        STATUS_PARAMS["multi_agent_status"] = self.get_widget(self.algorithm_frame, "multi").var.get()

    def coil_PID(self):
        """
        Flips the state of "pid_status" to True when "PID is clicked

        Args:
            None
        Returns:
            None
        """
        STATUS_PARAMS["PID_status"] = self.get_widget(self.algorithm_frame, "pid").var.get()
    
    def coil_acoustic(self):
        """
        Flips the state of "acoustic_status" to True when "acoustic" is clicked

        Args:
            None
        Returns:
            None
        """
        STATUS_PARAMS["acoustic_status"] = self.get_widget(self.algorithm_frame, "acoustic").var.get()

    def coil_pathplanner(self):
        """
        Flips the state of "pathplanner_status" to True when "pathplanner" is clicked

        Args:
            None
        Returns:
            None
        """
        STATUS_PARAMS["pathplanner_status"] = self.get_widget(self.algorithm_frame, "pathplanner").var.get()

    def run_algo(self):
        """
        Flips the state of algorthm status to True when "run_algo" is clicked

        Args:
            None
        Returns:
            None
        """
        STATUS_PARAMS["algorithm_status"] = True


    def edit_closed_loop_params(self):
        """
        Creates a new window for
            Lower and Upper Threshold,
            Bounding length, Area Filter,
            Field Strength,
            Rolling Frequency,
            gamma,
            and memory

        All of the widgets and sliders are initialized here when the Edit CLosed
        Loop Paramater buttons is clicked.

        Args:
            None
        Return:
            None

        """
        window3 = Toplevel(self.main_window)
        window3.title("ControlParams")

      
        
        #handle sliders
        def update_loop_slider_values(event):
            """
            Constantly updates control_params when the sliders are used.

            Params:
                event

            Returns:
                None
            """

            CONTROL_PARAMS["lower_thresh"] = int(lower_thresh_slider.get())
            CONTROL_PARAMS["upper_thresh"] = int(upper_thresh_slider.get())
            CONTROL_PARAMS["blur_thresh"] = int(blur_thresh_slider.get())
            CONTROL_PARAMS["initial_crop"] = int(initial_crop_slider.get())
            CONTROL_PARAMS["tracking_frame"] = float(tracking_frame_slider.get())
            CONTROL_PARAMS["memory"] = int(memory_slider.get())
            ACOUSTIC_PARAMS["min_vel"] = float(minvel_slider.get())
            MAGNETIC_FIELD_PARAMS["rolling_frequency"] = int(rolling_freq_slider.get())
            CONTROL_PARAMS["arrival_thresh"] = int(arrival_thresh_slider.get())
            MAGNETIC_FIELD_PARAMS["gamma"] = int(gamma_slider.get())
            MAGNETIC_FIELD_PARAMS["psi"] = int(psi_slider.get())

            self.main_window.update()

        lower_thresh = DoubleVar()
        upper_thresh = DoubleVar()
        blur_thresh = DoubleVar()
        initial_crop = DoubleVar()
        memory = DoubleVar()
        tracking_frame = DoubleVar()
        minvel = DoubleVar()
        rolling_frequency = DoubleVar()
        arrival_thresh = DoubleVar()
        gamma = DoubleVar()
        psi = DoubleVar()

        lower_thresh_slider = Scale(
            master=window3,
            label="lower",
            from_=0,
            to=255,
            resolution=1,
            variable=lower_thresh,
            width=20,
            length=200,
            orient=HORIZONTAL,
            command=update_loop_slider_values,
        )
        upper_thresh_slider = Scale(
            master=window3,
            label="upper",
            from_=0,
            to=255,
            resolution=1,
            variable=upper_thresh,
            width=20,
            length=200,
            orient=HORIZONTAL,
            command=update_loop_slider_values,
        )

        blur_thresh_slider = Scale(
            master=window3,
            label="blur_thresh",
            from_=1,
            to=250,
            resolution=1,
            variable=blur_thresh,
            width=20,
            length=200,
            orient=HORIZONTAL,
            command=update_loop_slider_values,
        )
        initial_crop_slider = Scale(
            master=window3,
            label="initial crop length",
            from_=10,
            to=200,
            resolution=5,
            variable=initial_crop,
            width=20,
            length=200,
            orient=HORIZONTAL,
            command=update_loop_slider_values,
        )
        tracking_frame_slider = Scale(
            master=window3,
            label="tracking frame size",
            from_=.5,
            to=5,
            resolution=.1,
            variable=tracking_frame,
            width=20,
            length=200,
            orient=HORIZONTAL,
            command=update_loop_slider_values,
        )
        memory_slider = Scale(
            master=window3,
            label="memory",
            from_=1,
            to=100,
            resolution=1,
            variable=memory,
            width=20,
            length=200,
            orient=HORIZONTAL,
            command=update_loop_slider_values,
        )
        minvel_slider = Scale(
            master=window3,
            label="min vel (um/s)",
            from_=1,
            to=20,
            digits=4,
            resolution=0.1,
            variable=minvel,
            width=20,
            length=200,
            orient=HORIZONTAL,
            command=update_loop_slider_values,
        )
        rolling_freq_slider = Scale(
            master=window3,
            label="Rolling Frequency",
            from_=0,
            to=40,
            digits=4,
            resolution=1,
            variable=rolling_frequency,
            width=20,
            length=200,
            orient=HORIZONTAL,
            command=update_loop_slider_values,
        )
        arrival_thresh_slider = Scale(
            master=window3,
            label="Arrival Threshold",
            from_=1,
            to=50,
            digits=1,
            resolution=1,
            variable=arrival_thresh,
            width=20,
            length=200,
            orient=HORIZONTAL,
            command=update_loop_slider_values,
        )
        gamma_slider = Scale(
            master=window3,
            label="gamma",
            from_=0,
            to=180,
            resolution=5,
            variable=gamma,
            width=20,
            length=200,
            orient=HORIZONTAL,
            command=update_loop_slider_values,
        )
        psi_slider = Scale(
            master=window3,
            label="psi",
            from_=1,
            to=90,
            resolution=1,
            variable=psi,
            width=20,
            length=200,
            orient=HORIZONTAL,
            command=update_loop_slider_values,
        )

        lower_thresh_slider.set(CONTROL_PARAMS["lower_thresh"])
        upper_thresh_slider.set(CONTROL_PARAMS["upper_thresh"])
        blur_thresh_slider.set(CONTROL_PARAMS["blur_thresh"])
        initial_crop_slider.set(CONTROL_PARAMS["initial_crop"])
        tracking_frame_slider.set(CONTROL_PARAMS["tracking_frame"])
        memory_slider.set(CONTROL_PARAMS["memory"])
        minvel_slider.set(ACOUSTIC_PARAMS["min_vel"])
        rolling_freq_slider.set(MAGNETIC_FIELD_PARAMS["rolling_frequency"])
        arrival_thresh_slider.set(CONTROL_PARAMS["arrival_thresh"])
        gamma_slider.set(MAGNETIC_FIELD_PARAMS["gamma"])
        psi_slider.set(MAGNETIC_FIELD_PARAMS["psi"])

        lower_thresh_slider.pack()
        upper_thresh_slider.pack()
        blur_thresh_slider.pack()
        initial_crop_slider.pack()
        tracking_frame_slider.pack()
        memory_slider.pack()
        minvel_slider.pack()
        rolling_freq_slider.pack()
        arrival_thresh_slider.pack()
        gamma_slider.pack()
        memory_slider.pack()
        psi_slider.pack()

    def edit_camera_params(self):
        """
        Creates a new window for Window Size, Frame Rate, exposure, and
        (Whatever Object slider does) The new window is defined, initialized,
        and opened when cam_params_button button is clicked

        Args:
            None

        Returns:
            None
        """
        window4 = Toplevel(self.main_window)
        window4.title("Camera Params")

        def update_loop_slider_values(event):
            """
            Constantly updates camera_params when the sliders are used.

            Params:
                event

            Returns:
                None
            """
            CAMERA_PARAMS["resize_scale"] = int(resize_scale_slider.get())
            CAMERA_PARAMS["framerate"] = int(frame_rate_slider.get())
            CAMERA_PARAMS["exposure"] = int(exposure_slider.get())
            # CAMERA_PARAMS["exposure"] = Brightness()
            CAMERA_PARAMS["Obj"] = int(obj_slider.get())

            self.main_window.update()

        resize_scale = DoubleVar()
        frame_rate = DoubleVar()
        exposure = DoubleVar()
        obj = DoubleVar()

        resize_scale_slider = Scale(
            master=window4,
            label="Resize Scale",
            from_=1,
            to=100,
            resolution=1,
            variable=resize_scale,
            width=20,
            length=200,
            orient=HORIZONTAL,
            command=update_loop_slider_values,
        )
        frame_rate_slider = Scale(
            master=window4,
            label="Frame Rate",
            from_=1,
            to=24,
            resolution=1,
            variable=frame_rate,
            width=20,
            length=200,
            orient=HORIZONTAL,
            command=update_loop_slider_values,
        )
        exposure_slider = Scale(
            master=window4,
            label="exposure",
            from_=1,
            to=100000,
            resolution=10,
            variable=exposure,
            width=20,
            length=200,
            orient=HORIZONTAL,
            command=update_loop_slider_values,
        )
        obj_slider = Scale(
            master=window4,
            label="Obj x",
            from_=5,
            to=50,
            resolution=5,
            variable=obj,
            width=20,
            length=200,
            orient=HORIZONTAL,
            command=update_loop_slider_values,
        )

        resize_scale_slider.set(CAMERA_PARAMS["resize_scale"])
        frame_rate_slider.set(CAMERA_PARAMS["framerate"])
        exposure_slider.set(CAMERA_PARAMS["exposure"])
        obj_slider.set(CAMERA_PARAMS["Obj"])

        resize_scale_slider.pack()
        frame_rate_slider.pack()
        exposure_slider.pack()
        obj_slider.pack()



    
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
            ACOUSTIC_PARAMS["acoustic_freq"] = int(acoustic_slider.get())
            self.AcousticModule.start(ACOUSTIC_PARAMS["acoustic_freq"],ACOUSTIC_PARAMS["acoustic_amplitude"])
            self.text_box.insert(END," -- waveform ON -- \n")
            self.text_box.see("end")
        
        def stop_freq():
            ACOUSTIC_PARAMS["acoustic_freq"] = 0
            self.AcousticModule.stop()
            self.text_box.insert(END," -- waveform OFF -- \n")
            self.text_box.see("end")
        
        def test_freq():
            ACOUSTIC_PARAMS["acoustic_amplitude"] = int(amplitude_slider.get())
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
            length=500,
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
            length=500,
            orient=HORIZONTAL,
            command=update_loop_slider_values,
        )
       
        amplitude_slider.set(ACOUSTIC_PARAMS["acoustic_amplitude"])        
        amplitude_slider.pack()
        
        def EXIT():
            self.AcousticModule.close()
            window5.destroy()
        window5.protocol("WM_DELETE_WINDOW",EXIT)
    

    def edit_pid_params(self):
        """
        Creates a new window for Window Size, Frame Rate, exposure, and
        (Whatever Object slider does) The new window is defined, initialized,
        and opened when cam_params_button button is clicked

        Args:
            None

        Returns:
            None
        """
        window6 = Toplevel(self.main_window)
        window6.title("PID Params")

        def update_pid_slider_values(event):
            """
            Constantly updates camera_params when the sliders are used.

            Params:
                event

            Returns:
                None
            """

            PID_PARAMS["Iframes"] = int(Iframes_slider.get())
            PID_PARAMS["Dframes"] = int(Dframes_slider.get())
            PID_PARAMS["Kp"] = int(Kp_slider.get())
            PID_PARAMS["Ki"] = int(Ki_slider.get())
            PID_PARAMS["Kd"] = int(Kd_slider.get())

            self.main_window.update()

        Iframes = DoubleVar()
        Dframes = DoubleVar()
        Kp = DoubleVar()
        Ki = DoubleVar()
        Kd = DoubleVar()

        Iframes_slider = Scale(
            master=window6,
            label="Iframes",
            from_=1,
            to=100,
            resolution=1,
            variable=Iframes,
            width=20,
            length=200,
            orient=HORIZONTAL,
            command=update_pid_slider_values,
        )
        Dframes_slider = Scale(
            master=window6,
            label="Dframes",
            from_=1,
            to=100,
            resolution=1,
            variable=Dframes,
            width=20,
            length=200,
            orient=HORIZONTAL,
            command=update_pid_slider_values,
        )
        Kp_slider = Scale(
            master=window6,
            label="Kp",
            from_=0.01,
            to=10,
            resolution=.01,
            variable=Kp,
            width=20,
            length=200,
            orient=HORIZONTAL,
            command=update_pid_slider_values,
        )
        Ki_slider = Scale(
            master=window6,
            label="Ki",
            from_=0.01,
            to=10,
            resolution=.01,
            variable=Ki,
            width=20,
            length=200,
            orient=HORIZONTAL,
            command=update_pid_slider_values,
        )
        Kd_slider = Scale(
            master=window6,
            label="Kd",
            from_=0.01,
            to=10,
            resolution=.01,
            variable=Kd,
            width=20,
            length=200,
            orient=HORIZONTAL,
            command=update_pid_slider_values,
        )

        Iframes_slider.set(PID_PARAMS["Iframes"])
        Dframes_slider.set(PID_PARAMS["Dframes"])
        Kp_slider.set(PID_PARAMS["Kp"])
        Ki_slider.set(PID_PARAMS["Ki"])
        Kd_slider.set(PID_PARAMS["Kd"])

        Iframes_slider.pack()
        Dframes_slider.pack()
        Kp_slider.pack()
        Ki_slider.pack()
        Kd_slider.pack()


    def record(self):
        """
        Records and downloads mp4 file of tracking and live feed.

        Args:
            None

        Returns:
            None
        """
        CAMERA_PARAMS["outputname"] = str(self.get_widget(self.video_record_frame, "output_name").get())
        STATUS_PARAMS["record_status"] = True

    def stop_record(self):
        """
        Stops the recording for the current video

        Args:
            None

        Returns:
            None
        """

        STATUS_PARAMS["record_status"] = False
        CAMERA_PARAMS["outputname"] =  str(datetime.now())

    def track(self):
        """
        Initiates a Tracker instance for microbot tracking

        Args:
            None

        Returns:
            None
        """

        if self.track_button.config("relief")[-1] == "sunken":
            self.track_button.config(relief = "raised")
            self.track_button.config(text = "Track",bg = 'blue',fg= 'white',highlightbackground = "blue")
            STATUS_PARAMS["tracker_status"] = False
 

        else:
            self.track_button.config(relief = "sunken")
            STATUS_PARAMS["tracker_status"] = True
            self.track_button.config(text = "Close Tracker, \nSave Data if Applicable", bg = 'blue',fg= 'red',highlightbackground = "red")
          
            tracker = Tracker(self.main_window, self.text_box,
            CONTROL_PARAMS,
            CAMERA_PARAMS,
            STATUS_PARAMS,
            False,#self.get_widget(self.checkboxes_frame, "cuda_checkbox").var.get(),
            )
            #self.tracker = tracker

            if (self.get_widget(self.checkboxes_frame, "live_checkbox").var.get()):
                video_name = None
            else:
                video_name = self.external_file

            
            robot_list = tracker.main(video_name, self.arduino, self.AcousticModule)

            
            if self.get_widget(self.main_window, "savepickle").var.get():
                if len(robot_list) > 0:
                    output_name = str(self.get_widget(self.video_record_frame, "output_name").get())
                    analyze = Analysis(CONTROL_PARAMS, CAMERA_PARAMS,STATUS_PARAMS,robot_list)
                    analyze.convert2pickle(output_name)


            
                
            


        
        
        

        



    def status(self):
        """
        Resets and zeros all status variables in tracker (i.e. zeros all outputs)

        Args:
            None

        Returns:
            None
        """
       
        
        STATUS_PARAMS["algorithm_status"] = False
        
        self.text_box.insert(END, "____ZEROED ____\n")
        self.text_box.see("end")

        #self.tracker.robot_window.destroy()
        self.arduino.send(0,0,0,0,0,0,0)
        self.AcousticModule.stop()
        ACOUSTIC_PARAMS["acoustic_freq"] = 0

        #ensure motors are off
        
        
        #shutdown hall sensor readings
        if self.sensor is not None:
            self.sensor.shutdown()
            self.main_window.after_cancel(self.checksensor)
          
        
        if self.joystick is not None:
            self.main_window.after_cancel(self.checkjoy)
            STATUS_PARAMS["joystick_status"] = False
            
        plt.close()
       
            

    

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


    def joy_proc(self):
        """
        creates an instance of ControllerClass and starts a seperate process to read values

        Args:
            None
        Returns:
            None
        """

        self.joystick = MyController()
        STATUS_PARAMS["joystick_status"] = True
        self.joystick_process = multiprocessing.Process(target = self.joystick.run, args = (None,self.joystick_q))
        self.joystick_process.start()
        self.checkjoy = self.main_window.after(10, self.CheckJoystickPoll, self.joystick_q)
    
    def CheckJoystickPoll(self,j_queue):
        """
        checks the joystick queue for incoming command values

        Args:
            c_queue: queue object
            joy_array: [typ, input1, input2, input3,input4]
            input1(typ1 | typ2) = angle|  Bx
            input2(typ1 | typ2) = freq | By
            input3(typ1 | typ2) = gamma | Bz
        Returns:
            None
        """
        try:
            actions = j_queue.get(0)

            alpha = actions[6] - np.pi/2 #subtract 90 for rolling 
            gamma = np.radians(MAGNETIC_FIELD_PARAMS["gamma"])  
            psi = np.radians(MAGNETIC_FIELD_PARAMS["psi"])

            if actions[8] != 0:  
                freq = MAGNETIC_FIELD_PARAMS["rolling_frequency"]
            else:
                freq = 0

            MAGNETIC_FIELD_PARAMS["Bx"] = actions[0]
            MAGNETIC_FIELD_PARAMS["By"] = actions[1]
            MAGNETIC_FIELD_PARAMS["Bz"] = actions[2]
            MAGNETIC_FIELD_PARAMS["alpha"] = alpha

            
            
            self.arduino.send(actions[0], actions[1], actions[2], alpha, gamma, freq, psi )

                
        except Empty:
            pass
        finally:
            self.checkjoy = self.main_window.after(10,self.CheckJoystickPoll, j_queue)
            

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
            self.checksensor = self.main_window.after(10,self.CheckSensorPoll, s_queue)

        
    
   
    def exit(self):
        """
        Quits the main window (self.main_window) and quits the ardunio connection
            exit()

        Args:
            None

        Returns:
            None
        """
        STATUS_PARAMS["tracker_status"] = False
        cv2.destroyAllWindows()
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
