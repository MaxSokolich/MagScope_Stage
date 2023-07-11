"""
inputs: status_params, control_params, camera_params, robot_list

outputs: arduino commands

"""
import cv2
import numpy as np
import time
from src.python.ArduinoHandler import ArduinoHandler
from src.python.Params import MAGNETIC_FIELD_PARAMS
class Roll_Algorithm:
    def __init__(self):
        #every time middle mouse button is pressed, it will reinitiate this classe
        self.node = 0
        self.robot_list = []
        self.control_params = None
        self.start = time.time()



    def control_trajectory(self, frame: np.ndarray, arduino: ArduinoHandler, robot_list, control_params):
        """
        Used for real time closed loop feedback on the jetson to steer a microrobot along a
        desired trajctory created with the right mouse button. Does so by:
            -defining a target position
            -displaying the target position
            -if a target position is defined, look at most recently clicked bot and display its trajectory

        In summary, moves the robot to each node in the trajectory array.
        If the error is less than a certain amount, move on to the next node

        Args:
            frame: np array representation of the current video frame read in
            start: start time of the tracking
        Return:
            None
        """
        self.robot_list = robot_list
        self.control_params = control_params
            
        if len(self.robot_list[-1].trajectory) > 1:
            #logic for arrival condition
            if self.node == len(self.robot_list[-1].trajectory):
                alpha = 0
                gamma = 0
                psi =0
                freq = 0
                print("arrived")


            #closed loop algorithm 
            else:
                #define target coordinate
                targetx = self.robot_list[-1].trajectory[self.node][0]
                targety = self.robot_list[-1].trajectory[self.node][1]

                #define robots current position
                robotx = self.robot_list[-1].position_list[-1][0]
                roboty = self.robot_list[-1].position_list[-1][1]
                
                #calculate error between node and robot
                direction_vec = [targetx - robotx, targety - roboty]
                error = np.sqrt(direction_vec[0] ** 2 + direction_vec[1] ** 2)
                self.alpha = np.arctan2(-direction_vec[1], direction_vec[0])


                #draw error arrow
                cv2.arrowedLine(
                    frame,
                    (int(robotx), int(roboty)),
                    (int(targetx), int(targety)),
                    [0, 0, 0],
                    3,
                )
        
                if error < self.control_params["arrival_thresh"]:
                    self.node += 1

                
                #OUTPUT SIGNAL
                my_alpha = self.alpha - np.pi/2  #subtract 90 for roll
                alpha = round(my_alpha,2)
                gamma = self.control_params["gamma"] * np.pi/180
                psi = self.control_params["psi"] * np.pi/180
                freq = self.control_params["rolling_frequency"]
                
                MAGNETIC_FIELD_PARAMS["alpha"] = alpha
                MAGNETIC_FIELD_PARAMS["gamma"] = gamma
                MAGNETIC_FIELD_PARAMS["psi"] = psi
                MAGNETIC_FIELD_PARAMS["freq"] = freq
                
        
            
                self.robot_list[-1].add_track(
                error,
                [robotx, roboty],
                [targetx, targety],
                alpha,
                self.control_params["rolling_frequency"],
                time.time()-self.start,
                )

            
            arduino.send(0,0,0, alpha, gamma, freq, psi)

            