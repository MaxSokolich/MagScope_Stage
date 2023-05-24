from pyPS4Controller.controller import Controller


def konami_callback():
    print("Konami sequence detected!")


def my_sequences():
    return [
        {"inputs": ['up', 'up', 'down', 'down', 'left', 'right'],
         "callback": konami_callback},
    ]


controller = Controller(interface="/dev/input/js0", connecting_using_ds4drv=False)
controller.listen(on_sequence=my_sequences())