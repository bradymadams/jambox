import time
import jambox
import RPi.GPIO as GPIO

class ControlPanelM(object):
    def __init__(self):
        self.inputs = []

    def add_input(self, inp):
        self.inputs.append(inp)

    # Continuously monitor all inputs
    def monitor(self):
        while True:
            for inp in self.inputs:
                inp.check()
            time.sleep(0.01)

if __name__ == '__main__':
    GPIO.setmode(GPIO.BCM)

    panel = jambox.ControlPanelC()

    def volcb(dv):
        panel.send_cmd_volch(str(dv))

    def mutecb():
        panel.send_cmd_mute()

    volre = jambox.RotaryEncoder(volcb, 23, 24)
    mutebutton = jambox.PushButton(mutecb, 25)

    panelm = ControlPanelM()
    panelm.add_input(volre)
    panelm.add_input(mutebutton)

    panelm.monitor()

