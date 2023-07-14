import pandas as pd

data = pd.read_pickle("/Users/bizzarohd/Desktop/MagScope_Stage/src/data/test.pickle")
robotlist = data[0]
magneticfield = data[1]


"""
MAGNETIC_FIELD_PARAMS = {
    "Bx": 0,
    "By": 0,
    "Bz": 0,
    "alpha": 0,
    "gamma": 90,
    "rolling_frequency": 10,
    "psi": 90,
   
}


robotlist[i] = {
            "Frame": self.frame_list,
            "Times": self.times,
            "Position": self.position_list,
            "Velocity": self.velocity_list,
            "Area": self.area_list,
            "Cropped Frame Dim": self.cropped_frame,
            "Avg Area": self.avg_area,
            "Trajectory": self.trajectory,
            "Acoustic Frequency": self.acoustic_freq,
 
        }
"""