from pyjoystick.sdl2 import Key, Joystick, run_event_loop

def print_add(joy):
    print('added', Joy)


def print_removed(joy):
    print('removed', Joy)
    
    
def keys_recv(key):
    print('Key:', key)
    
run_event_loop(print_add,print_removed,keys_recv)
    