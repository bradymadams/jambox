import serial
import math
import time

import threading
from RPi import GPIO

#COM = '/dev/ttyUSB0'
COM = '/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0'
BAUD = 9600

KNOB_MINVAL = 0
KNOB_MAXVAL = 255
KNOB_NLEDS = 10

VOLUME_CHANNELS = (0, )
#VOLUME_CHANNELS = (0, 1)
VOLUME_MAX = 255
VOLUME_MAX_ON = 0.5

VOLUME_RE_PINA = 23
VOLUME_RE_PINB = 24

class RotaryEnc(object):
    def __init__(self, knob, pinA, pinB, dvdd=0.01):
        self.knob = knob
        self.pinA = pinA
        self.pinB = pinB
        self.dvdd = dvdd

        GPIO.setup(self.pinA, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.pinB, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def monitor(self):
        ap = GPIO.input(self.pinA)
        bp = GPIO.input(self.pinB)
        dirp = -1 # Assume CCW direction to start

        while True:
            a = GPIO.input(self.pinA)
            b = GPIO.input(self.pinB)

            if a ^ b:
                dir_a_diff = 1
                dir_b_diff = -1
            else:
                dir_a_diff = -1
                dir_b_diff = 1

            if a != ap or b != bp:
                if a != ap and b == bp:
                    dir0 = dir_a_diff
                    count = 1
                elif a == ap and b != bp:
                    dir0 = dir_b_diff
                    count = 1
                else:
                    dir0 = dirp
                    count = 2

                # To avoid noise only change volume if knob is moving in same direction
                if dir0 == dirp:
                    if dir0 == 1:
                        self.knob.uplog(self.dvdd * count)
                    else:
                        self.knob.downlog(self.dvdd * count)
                
                ap = a
                bp = b
                dirp = dir0


class Knob(object):
    def __init__(self, channels, minval=KNOB_MINVAL, maxval=KNOB_MAXVAL):
        self.channels = channels
        if type(self.channels) is int:
            self.channels = (self.channels, )

        self.current = 0
        self.minval = minval
        self.maxval = maxval

        self.ser = serial.Serial(COM, BAUD, timeout=10.0)

        # If we're connecting via USB, take a moment to allow
        # the serial connection to be made and send an instruction
        # (I believe opening the connection via USB resets the Arduino)
        if 'USB' in COM.upper():
            time.sleep(1.0)
            self._send_instruction('D:0')
            self._send_instruction('D:0')

        self.getstatus()

    def _send_instruction(self, inst):
        inst += '$' # add instruction termination character
        try:
            n = self.ser.write(inst)
        except:
            print 'Instruction "%s" was unsuccessful' % inst

    def limit(self, val):
        val = min(val, self.maxval)
        val = max(val, self.minval)
        return val

    def set(self, val):
        val = self.limit(val)

        sval = 'P:%i' % val
        for c in self.channels:
            sval += ' %i' % c

        self._send_instruction(sval)
        self.current = val

        sled = 'L:%i' % self.numleds()
        self._send_instruction(sled)

    def up(self, n=1):
        self.set(self.current + n)

    def down(self, n=1):
        self.set(self.current - n)

    def setlog(self, lval):
        lval = min(lval, 1.0)
        lval = max(lval, 0.0)
        #lval += 1.0

        f = math.pow(10.0, lval)
        i = int( round((f - 1.0) * float(self.maxval - self.minval) / 9.0) ) + self.minval

        self.set(i)

    def tolog(self):
        lval = float(self.current - self.minval) * 9.0 / float(self.maxval - self.minval) + 1.0
        lval = math.log10(lval)
        return lval

    def uplog(self, n=0.1):
        self.setlog(self.tolog() + n)

    def downlog(self, n=0.1):
        self.setlog(self.tolog() - n)

    # use log scale to determine how many LEDs should be lit
    def numleds(self):
        return int( round(KNOB_NLEDS * self.tolog()) )

    def getstatus(self, c=None):
        if c is None:
            # just get the status of our first channel
            c = self.channels[0]

        sstat = 'S:%i' % c
        self._send_instruction(sstat)
        n = self.ser.readline()

        # try to convert the returned string to
        # an int and set it to the current value
        if n:
            try:
                clevel = int(n)
                self.current = clevel
            except:
                print 'Unable to get status'

        return self.current

    def mute(self, on):
        m = 1 if on else 0
        self._send_instruction('M:%i' % m)

    def standby(self, on):
        z = 1 if on else 0
        self._send_instruction('Z:%i' % z)

class ControlPanel(object):
    MASTERPANEL = None

    def __init__(self):
        GPIO.setmode(GPIO.BCM)

        self.knob_vol = Knob(VOLUME_CHANNELS, maxval=VOLUME_MAX)
        self.knob_vol.rotary_encoder(VOLUME_RE_PINA, VOLUME_RE_PINB)

        self._limit_volume()

    @staticmethod
    def master():
        if ControlPanel.MASTERPANEL is None:
            ControlPanel.MASTERPANEL = ControlPanel()
        return ControlPanel.MASTERPANEL

    def power_on(self):
        self._limit_volume()

    def power_off(self):
        pass

    # This function is used to ensure the volume is not
    # set too high during various events, e.g. when power is turned on
    def _limit_volume(self):
        if self.knob_vol.tolog() > VOLUME_MAX_ON:
            self.knob.setlog(VOLUME_MAX_ON)

