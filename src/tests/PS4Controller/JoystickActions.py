import numpy as np
from scipy import interpolate

#typ =0 : stage motor actions [0,x, y, z]
#typ =1 : spherical ---> Roll [1, alpha, freq, gamma]
#typ =2 : cartesian --> Orient [2, Bx, By, Bz]
#actions = [typ, input1, input2, input3, acoustic_status]

class Actions:
    """
    Actions are inherited in the Controller class.
    In order to bind to the controller events, subclass the Controller class and
    override desired action events in this class.
    """
    def __init__(self,joystick_q):
        self.right_stick = [0,0]
        self.left_stick = [0,0]
        self.queue = joystick_q  #multiprocessing queue for storing joystick actions in seperate thread
        
        #initlize coil actions
        self.typ = 4
        self.input1 = 0
        self.input2 = 0
        self.input3 = 0
        self.acoustic_status = 0
        return
    
    def on_x_press(self):
        """
        acoustic on
        """
        self.acoustic_status = 1
        actions = [self.typ, self.input1, self.input2, self.input3, self.acoustic_status]
        self.queue.put(actions)

    def on_x_release(self):
        """
        acoustic off
        """
        self.acoustic_status = 0
        actions = [self.typ, self.input1, self.input2, self.input3, self.acoustic_status]
        self.queue.put(actions)

    def on_triangle_press(self):
        """
        quick spin 10 Hz on
        """
        self.typ = 1
        self.input1 = 0
        self.input2 = 10
        self.input3 = 0
        
        actions = [self.typ, self.input1, self.input2, self.input3, self.acoustic_status]
        self.queue.put(actions)
       

    def on_triangle_release(self):
        """
        quick spin 10 Hz off
        """
        self.typ = 4
        self.input1 = 0
        self.input2 = 0
        self.input3 = 0
        
        actions = [self.typ, self.input1, self.input2, self.input3, self.acoustic_status]
        self.queue.put(actions)
        

    def on_circle_press(self):
        pass

    def on_circle_release(self):
        pass

    def on_square_press(self):
        pass

    def on_square_release(self):
        pass

    """
    # FUNCTIONS FOR TYP 0 --> MOTOR STAGE
    """
    def on_L2_press(self, value):
        """
        negative Z stage on
        """
        self.typ = 0
        f = interpolate.interp1d([-1,1], [0,1])  #need to map the -1 to 1 output to 0-1
        self.input3 = -round(float(f(value/32767)),3)
        actions = [self.typ, self.input1, self.input2, self.input3, self.acoustic_status]
        self.queue.put(actions)
        
    def on_L2_release(self):
        """
        negative Z stage off
        """
        self.typ = 0
        self.input3 = 0
        actions = [self.typ, self.input1, self.input2, self.input3, self.acoustic_status]
        self.queue.put(actions)
        

    def on_R2_press(self, value):
        """
        positive Z stage on
        """
        self.typ = 0
        f = interpolate.interp1d([-1,1], [0,1])  #need to map the -1 to 1 output to 0-1
        self.input3 = round(float(f(value/32767)),3)
        actions = [self.typ, self.input1, self.input2, self.input3, self.acoustic_status]
        self.queue.put(actions)

    def on_R2_release(self):
        """
        positive Z stage off
        """
        self.typ = 0
        self.input3 = 0
        actions = [self.typ, self.input1, self.input2, self.input3, self.acoustic_status]
        self.queue.put(actions)

    def on_up_arrow_press(self):
        """
        postitive Y stage motor on 
        """
        self.typ = 0
        self.input1 = 0
        self.input2 = 1
        actions = [self.typ, self.input1, self.input2, self.input3, self.acoustic_status]
        self.queue.put(actions)
        
    def on_up_down_arrow_release(self):
        """
        Y stage motor off 
        """
        self.typ = 0
        self.input1 = 0
        self.input2 = 0
        actions = [self.typ, self.input1, self.input2, self.input3, self.acoustic_status]
        self.queue.put(actions)
        
    def on_down_arrow_press(self):
        """
        negative Y stage motor on
        """
        self.typ = 0
        self.input1 = 0
        self.input2 = -1
        actions = [self.typ, self.input1, self.input2, self.input3, self.acoustic_status]
        self.queue.put(actions)

    def on_left_arrow_press(self):
        """
        negative X stage motor on
        """
        self.typ = 0
        self.input1 = -1
        self.input2 = 0
        actions = [self.typ, self.input1, self.input2, self.input3, self.acoustic_status]
        self.queue.put(actions)

    def on_left_right_arrow_release(self):
        """
        X stage motor off
        """
        self.typ = 0
        self.input1 = 0
        self.input2 = 0
        actions = [self.typ, self.input1, self.input2, self.input3, self.acoustic_status]
        self.queue.put(actions)
        

    def on_right_arrow_press(self):
        """
        positive X stage motor on
        """
        self.typ = 0
        self.input1 = 1
        self.input2 = 0
        actions = [self.typ, self.input1, self.input2, self.input3, self.acoustic_status]
        self.queue.put(actions)
    

    """
    # FUNCTIONS FOR TYP 1 --> COIL ROLL
    """
    def get_right_stick_xy(self): ######new adding
        """
        coil roll on
        """
        x = round(self.right_stick[0]/32767,3)
        y = -round(self.right_stick[1]/32767,3)
        if self.right_stick == [0,0]:
            self.typ = 4
            self.input1 = 0
            self.input2 = 0
            self.input3 = 0

        elif x == 0 and y > 0:
            self.typ = 1
            self.input1 = 90
            self.input2 = int(np.sqrt((x)**2 + (y)**2)*20)
            self.input3 = 90
            
        elif x == 0 and y < 0:
            self.typ = 1
            self.input1 = -90
            self.input2 = int(np.sqrt((x)**2 + (y)**2)*20)
            self.input3 = 90
        else:
            angle = round(np.arctan2(y,x),3)
            self.typ = 1
            self.input1 = angle+ np.pi/2
            self.input2 = int(np.sqrt((x)**2 + (y)**2)*20)
            self.input3 = 90
        
        actions = [self.typ, self.input1, self.input2, self.input3, self.acoustic_status]
        self.queue.put(actions)
    

    """
    # FUNCTIONS FOR TYP 2 --> COIL ORIENT
    """
    def get_left_stick_xy(self): ######new adding
        """
        coil orient on
        """
        x = round(self.left_stick[0],3)
        y = -round(self.left_stick[1],3)
        if self.left_stick == [0,0]:
            self.typ = 4
            self.input1 = 0
            self.input2 = 0
            self.input3 = 0
        else:
            self.typ = 2
            self.input1 = round(x/32767,3)
            self.input2 = round(y/32767,3)
            

        actions = [self.typ, self.input1, self.input2, self.input3, self.acoustic_status]
        self.queue.put(actions)
    
    def on_L1_press(self):
        """
        coil orient -Z on
        """
        self.typ = 2
        self.input3 = -1 #Z
        actions = [self.typ, self.input1, self.input2, self.input3, self.acoustic_status]
        self.queue.put(actions)
        

    def on_L1_release(self):
        """
        coil orient -Z off
        """
        self.typ = 2
        self.input3 = 0
        actions = [self.typ, self.input1, self.input2, self.input3, self.acoustic_status]
        self.queue.put(actions)
        
    def on_R1_press(self):
        """
        coil orient +Z on
        """
        self.typ = 2
        self.input3 = 1 #Z
        actions = [self.typ, self.input1, self.input2, self.input3, self.acoustic_status]
        self.queue.put(actions)

    def on_R1_release(self):
        """
        coil orient +Z off
        """
        self.typ = 2
        self.input3 = 0 #-Z
        actions = [self.typ, self.input1, self.input2, self.input3, self.acoustic_status]
        self.queue.put(actions)

    def on_L3_up(self, value):
        pass

    def on_L3_down(self, value):
        pass

    def on_L3_left(self, value):
        pass

    def on_L3_right(self, value):
        pass

    def on_L3_y_at_rest(self):
        """L3 joystick is at rest after the joystick was moved and let go off"""
        pass

    def on_L3_x_at_rest(self):
        """L3 joystick is at rest after the joystick was moved and let go off"""
        pass

    def on_L3_press(self):
        """L3 joystick is clicked. This event is only detected when connecting without ds4drv"""
        pass

    def on_L3_release(self):
        """L3 joystick is released after the click. This event is only detected when connecting without ds4drv"""
        pass

    def on_R3_up(self, value):
        pass

    def on_R3_down(self, value):
        pass

    def on_R3_left(self, value):
        pass

    def on_R3_right(self, value):
        pass

    def on_R3_y_at_rest(self):
        """R3 joystick is at rest after the joystick was moved and let go off"""
        pass

    def on_R3_x_at_rest(self):
        """R3 joystick is at rest after the joystick was moved and let go off"""
        pass

    def on_R3_press(self):
        """R3 joystick is clicked. This event is only detected when connecting without ds4drv"""
        pass

    def on_R3_release(self):
        """R3 joystick is released after the click. This event is only detected when connecting without ds4drv"""
        pass

    def on_options_press(self):
        pass

    def on_options_release(self):
        pass

    def on_share_press(self):
        """this event is only detected when connecting without ds4drv"""
        pass

    def on_share_release(self):
        """this event is only detected when connecting without ds4drv"""
        pass

    def on_playstation_button_press(self,exit):
        """this event is only detected when connecting without ds4drv"""
        print("Disconnecting")
        actions = False
        self.queue.put(actions)
        exit(1)

    def on_playstation_button_release(self):
        """this event is only detected when connecting without ds4drv"""
        pass
