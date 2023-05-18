from adafruit_motorkit import MotorKit
import time


class MotorStage:
    def __init__(self):
        #green   =   motor1   = X
        #yellow  =   motor2   = Y
        #blue    =   motor3   = Z
        self.kit = MotorKit()
    
    def MoveX(self, speed):
        self.kit.motor1.throttle = speed
        
    def MoveY(self, speed):
        self.kit.motor2.throttle = speed
    
    def MoveZ(self, speed):
        self.kit.motor3.throttle = speed

    def stop(self):
        self.kit.motor1.throttle = 0
        self.kit.motor2.throttle = 0
        self.kit.motor3.throttle = 0

