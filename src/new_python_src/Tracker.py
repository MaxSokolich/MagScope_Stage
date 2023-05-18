#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module containing the Tracker class

@authors: Max Sokolich, Brennan Gallamoza, Luke Halko, Trea Holley,
          Alexis Mainiero, Cameron Thacker, Zoe Valladares
"""

import time
from typing import List, Tuple, Union
import numpy as np
import cv2
from tkinter import Tk
from tkinter import *
from src.new_python_src.FPSCounter import FPSCounter
from src.new_python_src.ArduinoHandler import ArduinoHandler

import EasyPySpin
import warnings

warnings.filterwarnings("error")
class Tracker:
    """
    Tracker class for tracking microbots. Creates an interactable interface using OpenCV for
    tracking the trajectories of microbots on a video input (either through a live camera
    or a video file).

    Args:
        control_params: dict containing modifiable controller variables in the GUI
        camera_params: dict containing modifiable camera variables in the GUI
        status_params: dict containing modifiable status variables in the GUI
    """

    def __init__(self,  main_window: Tk,
                        control_params: dict,
                        camera_params: dict,
                        status_params: dict,):
    
        self.start = time.time()
        self.draw_trajectory = False  # determines if trajectory is manually being drawn
        self.robot_list = []  # list of actively tracked robots
        # self.raw_frames = []
        # self.bot_loc = None
        # self.target = None
        self.curr_frame = np.array([])
        self.num_bots = 0  # current number of bots
        self.frame_num = 0  # current frame count
        self.elapsed_time = 0  # time elapsed while tracking
        # self.fps_list = []  # Store the self.fps at the current frame

        self.width = 0  # width of cv2 window
        self.height = 0  # height of cv2 window
        
        #self.pix2metric = 1#((resize_ratio[1]/106.2)  / 100) * self.camera_params["Obj"] 
        self.main_window = main_window
        self.control_params = control_params
        self.camera_params = camera_params
        self.status_params = status_params
   
                
    
    def main(self,arduino: ArduinoHandler):
        """
        Connect to a camera or video file and perform real time tracking and analysis of microbots
        through a separate OpenCV window

        Args:
            filepath:   filepath to video file to be analyzed

        Returns:
            None
        """
        cam = EasyPySpin.VideoCapture(0)
        self.width = int(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(cam.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        #params = {"arduino": arduino}
        cv2.namedWindow("im")  # name of CV2 window

   
        fps_counter = FPSCounter()

        while True:
            fps_counter.update()
            success, frame = cam.read()


            w = frame.shape[0]
            h = frame.shape[1]
            
            #fps
            cv2.putText(frame,str(int(fps_counter.get_fps())),
                (int(w / 40),int(h / 30)),
                cv2.FONT_HERSHEY_COMPLEX,
                0.5,
                (255, 255, 255),
                1,
            )

            self.curr_frame = frame
            if not success or frame is None:
                break

            # Set exposure of camera
            cam.set(cv2.CAP_PROP_EXPOSURE, self.camera_params["exposure"])
            cam.set(cv2.CAP_PROP_FPS, self.camera_params["framerate"])
            # resize output based on the chosen ratio
            resize_scale = self.camera_params["resize_scale"]
            resize_ratio = (
                self.width * resize_scale // 100,
                self.height * resize_scale // 100,
            )
            frame = cv2.resize(frame, resize_ratio, interpolation=cv2.INTER_AREA)

           
            cv2.imshow("im", frame)

            
        
            
            # Exit
            self.main_window.update()
            if cv2.waitKey(1) & 0xFF == ord("q"):
                arduino.send(4, 0, 0, 0)
                break
            

        
        cam.release()
        cv2.destroyAllWindows()
 
        