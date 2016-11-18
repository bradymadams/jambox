import jambox
import RPi.GPIO as GPIO


if __name__ == '__main__':
    GPIO.setmode(GPIO.BCM)

    panel = jambox.ControlPanelC()

    def volcb(dv):
        panel.send_cmd_volch(str(dv))

    re = jambox.RotaryEnc(volcb, 23, 24)
    re.monitor()

