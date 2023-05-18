"""
Module containing the DigitalPot class

@authors: Max Sokolich
"""
import time 

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)

class AcousticClass:
    def __init__(self):
        '''
        Acosutic Handler Class that enables use of the AD9850 0-40 MHz DDS signal generator module
        and  X9C104 100K Pot Module to vary the amplitude of the signal

        Args:
            None
        '''


        ##DEFINE ACOUSTIC DDS PINS
        self.W_CLK = 21 #Orange
        self.FQ_UD = 22 #Blue
        self.DATA = 23 #Yellow
        self.RESET = 24 #Green
        GPIO.setup(self.W_CLK, GPIO.OUT)
        GPIO.setup(self.FQ_UD, GPIO.OUT)
        GPIO.setup(self.DATA, GPIO.OUT)
        GPIO.setup(self.RESET, GPIO.OUT)

        GPIO.output(self.W_CLK, GPIO.LOW)
        GPIO.output(self.FQ_UD, GPIO.LOW)
        GPIO.output(self.DATA, GPIO.LOW)
        GPIO.output(self.RESET, GPIO.HIGH)

        #keep track of total amplitude
        self.count = 0 
    

    # Function to send a pulse to GPIO pin
    def am_pulseHigh(self,pin):
        GPIO.output(pin, True)
        GPIO.output(pin, True)
        GPIO.output(pin, False)
        

    # Function to send a byte to AD9850 module
    def am_tfr_byte(self,data):
        for i in range (0,8):
            GPIO.output(self.DATA, data & 0x01)
            self.am_pulseHigh(self.W_CLK)
            data=data>>1
        
    # Function to send frequency (assumes 125MHz xtal) to AD9850 module
    def am_sendFrequency(self,frequency):
        freq=int(frequency*4294967296/125000000)
        for b in range (0,4):
            self.am_tfr_byte(freq & 0xFF)
            freq=freq>>8
        self.am_tfr_byte(0x00)
        self.am_pulseHigh(self.FQ_UD)
        

    # start the DDS module
    def start(self,frequency, amplitude):
        self.am_pulseHigh(self.RESET)
        self.am_pulseHigh(self.W_CLK)
        self.am_pulseHigh(self.FQ_UD)
        self.am_sendFrequency(frequency)
        
  
                                            
    # resets acoustic module to 0
    def stop(self):
        self.am_pulseHigh(self.RESET)
    
    # exits and cleansup GPIO pins
    def exit(self):
        GPIO.cleanup()

"""
max step = 30
we want a reading from 0 V to voltage maximum
~0 Volts is max on resistance

map(low_resistance, high resistance, high voltage, low voltage)
"""

"""if __name__ == "__main__":

    AcousticMod = AcousticClass()
    AcousticMod.dp_activate()
    print("starting waveform...")
    freqinput = 1000000
    amplitude =10
    AcousticMod.start(freqinput,amplitude)
    time.sleep(10)
    AcousticMod.stop()
    print("stopped waveform")
    AcousticMod.close()
    AcousticMod.exit()"""