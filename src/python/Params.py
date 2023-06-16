import numpy as np

PID_PARAMS = {
    "Iframes": 100,
    "Dframes": 10,
    "Kp": 0.1,
    "Ki": 0.01,
    "Kd": 0.01,
}

CONTROL_PARAMS = {
    "lower_thresh": np.array([0,0,0]),  #HSV
    "upper_thresh": np.array([180,255,140]),  #HSV   #130/150
    "blur_thresh": 100,
    "initial_crop": 100,       #intial size of "screenshot" cropped frame 
    "tracking_frame": 1,            #cropped frame dimensions mulitplier
    "avg_bot_size": 5,
    "field_strength": 1,
    "rolling_frequency": 10,
    "arrival_thresh": 10,
    "gamma": 90,
    "memory": 15,
    "PID_params": PID_PARAMS,
}

CAMERA_PARAMS = {
    "resize_scale": 50, 
    "framerate": 24, 
    "exposure": 6000,   #6000
    "Obj": 50}

STATUS_PARAMS = {
    "rolling_status": 0,
    "orient_status": 0,
    "multi_agent_status": 0,
    "PID_status": 0,
    "yanda_status": 0,
    "algorithm_status": False,
    "record_status": False,
}

ACOUSTIC_PARAMS = {
    "acoustic_freq": 0,
    "acoustic_amplitude": 0
}

MAGNETIC_FIELD_PARAMS = {
    "PositiveY": 0,
    "PositiveX": 0,
    "NegativeY": 0,
    "NegativeX": 0,
}