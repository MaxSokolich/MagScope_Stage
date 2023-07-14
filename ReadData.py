import pandas as pd

data = pd.read_pickle("/Users/bizzarohd/Desktop/MagScope_Stage/src/data/test.pickle")

#iteratives
frames = data["Frame"]
times = data["Times"]

#inputs: 
positions = data["Position"]
velocities = data["Velocity"]
areas = data["Area"]
trajectory = data["Trajectory"]

#outputs
acoustic_freq = data["Acoustic Frequency"]
magnetic_field = data["Magnetic Field"]