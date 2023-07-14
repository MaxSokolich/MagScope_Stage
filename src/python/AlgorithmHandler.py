"""
reads all algoritgms from algorothm folder and assigns each one to the checkbox widget

"""
import numpy as np
from src.python.ArduinoHandler import ArduinoHandler
from src.python.AcousticClass import AcousticClass
from src.python.algorithms.Roll_Algorithm import Roll_Algorithm
from src.python.algorithms.Orient_Algorithm_V2 import Orient_Algorithm
from src.python.algorithms.PID_code_forMax import PID_Algorithm
from src.python.algorithms.MultiAgent_Algorithm import Multi_Agent_Algorithm
from src.python.algorithms.Orient_Bubble import PI_Algorithm
from src.python.algorithms.Acoustic_Algorithm import Acoustic_Algorithm

class AlgorithmHandler:
    """
    Algorithm class for handleing new algorithms. You can import an algorithm from the 
    algorithm folder or create a new one.

    only 5 will be displayed on the gui at a time but you can sub certain ones out
    """

    def __init__(self):
        #every time middle mouse button is pressed, it will reinitiate the following classes
        self.Roll_Robot = Roll_Algorithm()
        self.Orient_Robot = Orient_Algorithm()
        self.Multi_Agent_Robot = Multi_Agent_Algorithm()
        self.PID_Robot = PID_Algorithm()   
        self.acoustic_Robot = Acoustic_Algorithm()
        

    def run(self, 
            robot_list, 
            control_params, 
            camera_params, 
            status_params, 
            arduino: ArduinoHandler,
            AcousticModule: AcousticClass,
            frame: np.ndarray):
        

        if status_params["rolling_status"] == 1:
            self.Roll_Robot.control_trajectory(frame, arduino, robot_list, control_params)
        
        elif status_params["PID_status"] == 1:  
            self.PID_Robot.control_trajectory(frame, arduino, robot_list, control_params)
        
        elif status_params["orient_status"] == 1:
            self.Orient_Robot.control_trajectory(frame, arduino, robot_list, control_params)
        
        elif status_params["multi_agent_status"] == 1:
            self.Multi_Agent_Robot.control_trajectory(frame, arduino, robot_list, control_params)
            
        elif status_params["acoustic_status"] == 1:
            self.acoustic_Robot.run(frame, arduino, robot_list, AcousticModule)


        else: 
            arduino.send(0, 0, 0, 0, 0, 0, 0)
    
        
