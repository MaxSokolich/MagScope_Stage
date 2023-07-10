"""
Main script for performing microbot tracking

@authors: Max Sokolich, Brennan Gallamoza, Luke Halko, Trea Holley,
          Alexis Mainiero, Cameron Thacker, Zoe Valladares
"""

from tkinter import Tk
import asyncio
from src.python.GUI import GUI
from src.python.ArduinoHandler import ArduinoHandler


PORT = "COM3"#"/dev/ttyACM0" #"/dev/cu.usbmodem11401"#


if __name__ == "__main__":
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

 

