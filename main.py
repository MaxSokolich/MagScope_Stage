"""
Main script for performing microbot tracking

@authors: Max Sokolich, Brennan Gallamoza, Luke Halko, Trea Holley,
          Alexis Mainiero, Cameron Thacker, Zoe Valladares
"""

from tkinter import Tk
import asyncio
from src.python.GUI import GUI
from src.python.ArduinoHandler import ArduinoHandler
import platform

if __name__ == "__main__":

    if "mac" in platform.platform():
        print("Detected OS: macos")
        PORT = "/dev/cu.usbmodem11401"
    elif "linux" in platform.platform():
        print("Detected OS: ubuntu")
        PORT = "/dev/ttyACM0"
    elif "Windows" in platform.platform():
        print("Detected OS:  Windows")
        PORT = "COM3"
    else:
        print("undetected operating system")
        PORT = None


    #gui window
    window = Tk()
    window.title("Microbot Tracking GUI")

    #arduino
    arduino = ArduinoHandler()
    arduino.connect(PORT)

    #initiate gui window
    gui = GUI(window, arduino)
   
    #start gui mainwindow
    asyncio.run(gui.main())

 

