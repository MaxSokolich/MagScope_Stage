from queue import Empty
from ControllerClass import Controller
from ArduinoHandler import ArduinoHandler
from MotorStageClass import MotorStage

from multiprocessing import Process, Queue, Event
#from src.python.AcousticClass import AcousticClass
import time



class MyController(Controller):

    def __init__(self, **kwargs):
        Controller.__init__(self, **kwargs)

     




if __name__ == "__main__":
    #create instance of motor stage class
    stage = MotorStage()

    #create instance and connect to arduino module
    PORT = "/dev/ttyACM0"
    arduino = ArduinoHandler()
    arduino.connect(PORT)
    
    #create queue to handle joystick commands
    joystick_q = Queue(1)
    controller = MyController(joystick_q=joystick_q,interface="/dev/input/js0", connecting_using_ds4drv=False)
    
    joystick_process = Process(target = controller.listen, args = (joystick_q,))
    joystick_process.start()

    while True:
        try:
            actions = joystick_q.get(0)

            if actions == False:
                break
        
            else:
                acoustic = actions[4]
                
                
                if actions[0] == 0:
                    x = actions[1]
                    y = actions[2]
                    z = actions[3]
                    stage.MoveX(x)
                    stage.MoveY(y)
                    stage.MoveZ(z)
                    print("Stage Moving: ",[x,y,z])
                else:
                    arduino.send(actions[0], actions[1], actions[2], actions[3])
        except Empty:
            pass
 

    joystick_process.join()
    stage.stop()


