#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#I changed the code so that instead of re-calculating the mapped angle, it saves all of them and takes an average. This
#should allow for a lower memory to be used while not having to worry as much about noise. Also it means that it can 
#update the magnetic field angle on every frame, once it initially captures memory number of frames, so it should be more
#responsive. Although there is one tricky bit to this, and that's that since the velocity is an average over the last memory
#number of frames, once a new target is chosen and a new B field is applied, it will think that the velcity has not responded
#to the new field until memory number of frames has passed. This is why we only updated the rotation matrix every memory
#number of frames, otherwise it will overcompensate. Since we are now averaging theta_map over a bunch of frames, it 
#should average out this error. So long as memory is kept sufficiently small so that it's just large enough to overcome
#the noise, then this shouldn't be an issue. I would guess that a rule of thumb would be to set memory to be about the 
#number of frames required for the bot to move it's own size. If the stage is shaking or something like that, then it
# needs to be larger obviously so that an accurate estimate of the true velocity can be found
import cv2
import numpy as np
import time
from src.python.ArduinoHandler import ArduinoHandler
from src.python.Params import CONTROL_PARAMS, CAMERA_PARAMS, STATUS_PARAMS, ACOUSTIC_PARAMS, MAGNETIC_FIELD_PARAMS,PID_PARAMS



class Acoustic_Algorithm:
    """
    algorithm template
    """
    def __init__(self):
        #initilize base action commands
        self.Bx, self.By, self.Bz = 0,0,0
        self.alpha, self.gamma, self.freq = 0,0,0

        #initilize params
        self.control_params = CONTROL_PARAMS
        self.acoustic_params = ACOUSTIC_PARAMS

        #self.frequency = self.control_params["acoustic_freq"] #Hz

        #values for magnetic orienting algorithm
        self.node = 0
        self.B_vec = np.array([1,0])
        self.T_R = 1
        self.theta_maps = np.array([])
        self.theta = 0
        self.start = time.time()


        #values for finding optimal resonant frequency
        self.min_freq = 1200000   #current minimum freq to start at
        self.max_freq = 1600000  #current maximum freq to stop at
        self.current_freq = self.min_freq   #current freq we are applying (start at 0)
        self.count = 0        #counter to keep track of each frame
        self.increment = 1000   #increment to step frequency by
        self.optimal_freq = None
        self.resistance = 0

        self.velocity_max_thresh =  min(ACOUSTIC_PARAMS["min_vel"] *5, 50) #um/s
        
    def reset(self):

        self.node = 0
        self.B_vec = np.array([1,0])
        self.T_R = 1
        self.theta_maps = np.array([])
        self.theta = 0

        
        self.min_freq = 1200000   #current minimum freq to start at
        self.max_freq = 1600000  #current maximum freq to stop at
        self.current_freq = self.min_freq   #current freq we are applying (start at 0)
        self.count = 0        #counter to keep track of each frame
        self.increment = 1000   #increment to step frequency by
        self.optimal_freq = None
        self.resistance = 0
        print("algorithm reset")

    def find_optimal_freqv2(self, robot_list, AcousticModule):
            #take a rolling average of the velocity from past 10 frames and average
            if len(robot_list[-1].velocity_list) >= self.control_params["memory"]:
                vmag = [v.mag for v in robot_list[-1].velocity_list[-self.control_params["memory"]:]]
                vmag_avg = round(sum(vmag) / len(vmag),2)
          

                ## CASE #1
                if vmag_avg < ACOUSTIC_PARAMS["min_vel"]: 
                    """
                    if vmag < vmin, we need to sweep through the user defined frequency range until 
                    we find a frequency that puts vmag into the goldilocks vel range (> vmin)
                    """
                    self.resistance = 0  #zero resistance 

                    ## SUBCASE #1
                    
                    if self.optimal_freq is not None:
                        '''
                        """
                        so if an optimal frequency was found previously but for whatever reason the robot dipped under vmin,
                        recenter the min and max freqs about this optimal freq and resweep
                        """
                         #reset optimal_freq as unfound
                        
                        

                        if (self.max_freq - self.min_freq) < 1000: # need a condition to prevent the range from converging to zero
                            self.current_freq = self.min_freq #just rest the current freq at previous min_freq
                        else:
                            self.min_freq = max(self.optimal_freq - int((self.optimal_freq/10)), 1200000)  #so that the 
                            self.max_freq = min(self.optimal_freq + int((self.optimal_freq/10)), 1600000)
                            self.increment = int(self.optimal_freq/100)   #decrease increment to accomdate decreased range
                            self.current_freq = self.min_freq  #reset current freq at the new minimum
                        '''
                        self.optimal_freq = None
                    

                    if self.current_freq < self.max_freq: #if we increment and get to max
                        if self.count % 10 == 0:  #every 10 frames adjust frequency by the increment value may need to change this
                            self.current_freq += self.increment  #increment. once a frequency is found that puts vmag > vmin, the current_freq will be the optmial
                            AcousticModule.start(self.current_freq, self.resistance) #apply the crrent freq at 0 resistance

                    
                    ## SUBCASE #2
                    elif self.current_freq >= self.max_freq: 
                        """
                        if we get to the end of the range and no frequency was found, 
                        restart the count at a difference and use a smaller increment
                        """    
                        if self.increment <= 50:
                            pass
                        else:
                            self.increment = int(self.increment/2)    #reduce the incriment to increase resolution of frequency sweep
                        self.current_freq = self.min_freq  #reset current freq to new minimum

                
                ## CASE #2
                elif vmag_avg > ACOUSTIC_PARAMS["min_vel"] and vmag_avg < self.velocity_max_thresh:
                    """
                    if vmin < vmag < vmax: stay at this frequency, this is the optimal frequency
                    """
                    self.optimal_freq = self.current_freq  #set the optimal frequency to be used later if vmag dips < vmin
                    AcousticModule.start(self.optimal_freq, self.resistance)
         

                
                ## CASE #3
                elif vmag_avg > self.velocity_max_thresh:
                    """
                    if vmag > vmax then we run the risk of the robot losing control and losing the tracking.
                    Thus apply a resistance value to dampen the waveform and thus slow the robot
                    """
                    #self.resistance = 1
                    #self.AcousticMod.start(self.current_freq, self.resistance)
                    AcousticModule.stop()
                    ACOUSTIC_PARAMS["acoustic_freq"] = 0


                self.count += 1#increment counter

            ACOUSTIC_PARAMS["acoustic_freq"] = self.current_freq  # save variables to global param variables
            ACOUSTIC_PARAMS["acoustic_resistance"] = self.resistance
        
        

    def run(self, frame, arduino, robot_list,AcousticModule):
        """
        inputs: the robot list from tracking
        outputs: actions list in the form of [Bx,By,Bz,alpha,gamma,freq]
        """
        #DO STUFF HERE
        
        if len(robot_list) > 0:  #if we clicked on a robot

            if len(robot_list[-1].trajectory) > 1:  # if we drew a trajectory
                
                
                self.find_optimal_freqv2(robot_list, AcousticModule)

                #logic for arrival condition
                if self.node == len(robot_list[-1].trajectory):
                    #zero B field signals
                    self.Bx, self.By, self.Bz = 0,0,0
                    self.alpha, self.gamma, self.freq = 0,0,0

                    #stop acoustic module
                    AcousticModule.stop()
                    ACOUSTIC_PARAMS["acoustic_freq"] = 0
                    print("arrived")
                
                #closed loop algorithm 
                else:
                    #define target coordinate
                    targetx = robot_list[-1].trajectory[self.node][0]
                    targety = robot_list[-1].trajectory[self.node][1]

                    #define robots current position
                    robotx = robot_list[-1].position_list[-1][0]
                    roboty = robot_list[-1].position_list[-1][1]
                    
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

        
                    # OUTPUT SIGNAL
                    bot = robot_list[-1]
                    if len(bot.velocity_list) >= self.control_params["memory"]:
                        
                        #find the velocity avearge over the last memory number of frames to mitigate noise: 
                        vx = np.mean(np.array([v.x for v in bot.velocity_list[-self.control_params["memory"]:]]))
                        vy = np.mean(np.array([v.y for v in bot.velocity_list[-self.control_params["memory"]:]]))
                        
                        vel_bot = np.array([vx, vy])  # current velocity of self propelled robot
                        vd = np.linalg.norm(vel_bot)
                        bd = np.linalg.norm(self.B_vec)

                        if vd != 0 and bd != 0:
                            costheta = np.dot(vel_bot, self.B_vec) / (vd * bd)
                            sintheta = (vel_bot[0] * self.B_vec[1] - vel_bot[1] * self.B_vec[0]) / (vd * bd)
                            self.theta = np.arctan2(sintheta,costheta)
                    
                        
                        if not np.isnan(vd):
                            self.theta_maps = np.append(self.theta_maps,self.theta)
                    
                            if len(self.theta_maps) > 150:
                                self.theta_maps = self.theta_maps[-150:len(self.theta_maps)]#this makes sure that we only look at the latest 150 frames of data to keep it adaptable. It should be bigger if there's a lot of noise (slow bot) and smaller if its traj is well defined (fast bot) 
                            thetaNew = np.median(self.theta_maps)#take the average, or median, so that the mapped angle is robust to noise                        
                            self.T_R = np.array([[np.cos(thetaNew), -np.sin(thetaNew)], [np.sin(thetaNew), np.cos(thetaNew)]])

                    self.B_vec = np.dot(self.T_R, direction_vec)

                    #OUTPUT SIGNAL      
                    
                    Bx = self.B_vec[0] / np.sqrt(self.B_vec[0] ** 2 + self.B_vec[1] ** 2)
                    By = self.B_vec[1] / np.sqrt(self.B_vec[0] ** 2 + self.B_vec[1] ** 2)
                    Bz = 0
                    self.alpha = np.arctan2(By, Bx)
                    
                    self.Bx = round(Bx,2)
                    self.By = round(By,2)
                    self.Bz = round(Bz,2)
                    MAGNETIC_FIELD_PARAMS["Bx"] = self.Bx
                    MAGNETIC_FIELD_PARAMS["By"] = self.By
                    MAGNETIC_FIELD_PARAMS["Bz"] = self.Bz
                    try:
                        start_arrow = (100, 150 + (self.num_bots - 1) * 20)
                        end_arrow = (
                            int(start_arrow[0] + Bx * 15),
                            int(start_arrow[1] + By * 15),
                        )
                        cv2.arrowedLine(
                            frame, start_arrow, end_arrow, [255, 255, 255], 2
                        )
                    except:
                        pass
                
                    robot_list[-1].add_track(
                        error,
                        [robotx, roboty],
                        [targetx, targety],
                        self.alpha,
                        ACOUSTIC_PARAMS["acoustic_freq"],
                        time.time()-self.start,
                        )

        else:
            self.Bx, self.By, self.Bz = 0,0,0
            self.alpha, self.gamma, self.freq = 0,0,0
            AcousticModule.stop()

        
            
        actions = [self.Bx, self.By, self.Bz, self.alpha, self.resistance, self.min_freq, self.current_freq, self.max_freq, self.optimal_freq] #chaning the actions to better align with acoustic bots
        arduino.send(self.Bx, self.By, self.Bz,0,0,0,0)
    
        