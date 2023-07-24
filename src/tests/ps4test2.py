"""

Path planning with Rapidly-Exploring Random Trees (RRT)

author: Aakash(@nimrobotics)
web: nimrobotics.github.io

"""

import cv2
import numpy as np
import math
import random
import argparse
import os
import time




if __name__ == '__main__':


    # remove previously stored data
    imagepath = "/Users/bizzarohd/Desktop/mask.png"
    img = cv2.imread(imagepath,0)   # load grayscale maze image
    x,y,w,h = 900,200,100,100

    cv2.rectangle(img, (x, y), (x + w, y + h), (255, 255, 255), -1)

    cv2.imshow("img", img)
    if cv2.waitKey(0) & 0xFF == ord("q"):
        cv2.destroyAllWindows()


