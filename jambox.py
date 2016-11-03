import serial
import math
import time

COM = '/dev/ttyUSB0'
BAUD = 9600

KNOB_MINVAL = 0
KNOB_MAXVAL = 255
KNOB_NLEDS = 10

VOLUME_CHANNELS = (0, 1)
VOLUME_MAX = 255
VOLUME_MAX_ON = 0.5

class Knob(object):
    def __init__(self, channels, minval=KNOB_MINVAL, maxval=KNOB_MAXVAL):
        self.channels = channels
        if type(self.channels) is int:
            self.channels = (self.channels, )

        self.current = 0
        self.minval = minval
        self.maxval = maxval

        self.ser = serial.Serial(COM, BAUD)

        # If we're connecting via USB, take a moment to allow
        # the serial connection to be made and send an instruction
        # (I believe opening the connection via USB resets the Arduino)
        if 'USB' in COM:
            time.sleep(1.0)
            self._send_instruction('S:0')
            self._send_instruction('S:0')

        #self.set(init)

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
        sval += '$'

        self._send_instruction(sval)
        self.current = val

        sled = 'L:%i$' % self.numleds()
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


class ControlPanel(object):
    MASTERPANEL = None

    def __init__(self):
        self.knob_vol = Knob(VOLUME_CHANNELS, maxval=VOLUME_MAX)

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

