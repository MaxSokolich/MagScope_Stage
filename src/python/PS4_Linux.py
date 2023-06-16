import cv2
import pygame
import time
import numpy as np
from scipy import interpolate


class MyController:
    """
    handles joystick inputs and outputs to main program
    """
    def __init__(self):
        #initlize actions actions
        self.Bx, self.By, self.Bz = 0,0,0
        self.Mx, self.My, self.Mz = 0,0,0
        self.alpha, self.gamma, self.freq = 0,0,0
        self.acoustic_status = 0


        #initilize class arguments
        self.queue = None
        self.arduino = None

    def deadzone(self, value):
        """
        accepts a value [0,1] and if its less than .2 make it zero otherwise use the value. limits joystick noise
        """
        if abs(value) < .2:
            return 0
        else:
            return value

    def run(self, arduino, queue):
        """
        main controller event loop the listen for commands from the joystick
        once commands are found there are converted into the proper action format and sent to the queue.
        """
        self.arduino = arduino
        self.queue = queue

        # Initialize the joystick
        pygame.init()
        pygame.joystick.init()
        joystick = pygame.joystick.Joystick(0)
        joystick.init()

        clock = pygame.time.Clock()
       
        # Main loop
        while True:
            clock.tick(1000) #ms
            # Check for joystick events
            for event in pygame.event.get():
                
                #axis condition
                if event.type == pygame.JOYAXISMOTION:
                
                    # Joystick movement event
                    if event.axis == 0:  #LY
                        ly = self.deadzone(event.value)
                        self.By = round(ly,3)
                     
                    if event.axis == 1: #LX
                        lx = self.deadzone(event.value)
                        self.Bx = round(lx,3)

                    if event.axis == 4: #RY
                        rx = self.deadzone(event.value)
                        ry = self.deadzone(joystick.get_axis(3))
                        if rx == 0 and ry == 0:
                            self.alpha = 0
                            self.gamma = 0
                            self.freq = 0

                        elif rx == 0 and ry > 0:
                            self.alpha = 0
                            self.gamma = np.pi/2
                            self.freq = int(np.sqrt((rx)**2 + (ry)**2)*20)
                            
                        elif rx == 0 and ry < 0:
                            self.alpha = -np.pi
                            self.gamma = np.pi/2
                            self.freq = int(np.sqrt((rx)**2 + (ry)**2)*20)
                        else:
                            angle = np.arctan2(ry,rx) - np.pi/2 
                            self.alpha = round(angle,3)
                            self.gamma = np.pi/2
                            self.freq = int(np.sqrt((rx)**2 + (ry)**2)*20)


                    if event.axis == 2: #LT
                        lt = round(event.value,2)
                        f = interpolate.interp1d([-1,1], [0,1])  #need to map the -1 to 1 output to 0-1
                        self.Mz = -round(float(f(lt)),3)
                        
    
                    if event.axis == 5: #RT
                        rt = round(event.value,2)
                        f = interpolate.interp1d([-1,1], [0,1])  #need to map the -1 to 1 output to 0-1
                        self.Mz = round(float(f(rt)),3)
        
                #button condition
                elif event.type == pygame.JOYBUTTONDOWN:
                    # Joystick button press event
                    button = event.button
                    if button == 0: #X
                        self.acoustic_status = 1
                    if button == 3: #square
                        pass
                    if button == 2: #triangle
                        self.freq = 10
                        self.gamma = 0
                    if button == 5: #rb
                        self.Bz = 1
                    if button == 4: #lb
                        self.Bz = -1
                
                elif event.type == pygame.JOYBUTTONUP:
                    # Joystick button press event
                    button = event.button
                    if button == 1: #circle
                        print("Controller Disconnected")
                        return True
                    if button == 0: #X
                        self.acoustic_status = 0
                    if button == 3: #square
                        pass
                    if button == 2: #triangle
                        self.freq = 0
                        self.gamma = 0
                    if button == 5: #rb
                        self.Bz = 0
                    if button == 4: #lb
                        self.Bz = 0
            
                
                #STAGE XY CONDTIONS
                elif event.type == pygame.JOYHATMOTION:
                    #JOYSTICK HAT press event
                    self.Mx, self.My = event.value
                 
            
            self.actions = [self.Bx, 
                   self.By,
                   self.Bz,
                   self.Mx, 
                   self.My, 
                   self.Mz,
                   self.alpha, 
                   self.gamma, 
                   self.freq,
                   self.acoustic_status]
            
            #add action commands to queue
            self.queue.put(self.actions)
            #self.arduino.send(self.Bx,self.By,self.Bz, self.alpha, self.gamma, self.freq)
             
        
         
