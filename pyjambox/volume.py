import serial
import math

COM = '/dev/ttyAMA0'
BAUD = 9600

MINVAL = 0
MAXVAL = 255
NLEDS = 10

class Knob(object):
    def __init__(self, channels, init=MINVAL, minval=MINVAL, maxval=MAXVAL):
        self.channels = channels
        if type(self.channels) is int:
            self.channels = (self.channels, )

        self.current = init
        self.minval = minval
        self.maxval = maxval

        self.ser = serial.Serial(COM, BAUD)

        self.set(init)

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
        lval = min(lval, 9.0)
        lval = max(lval, 0.0)
        lval += 1.0

        f = math.log10(lval)
        i = int( round((self.maxval - self.minval) * f) ) + self.minval

        self.set(i)

    def tolog(self):
        f = float((self.current - self.minval)) / float((self.maxval - self.minval))
        lval = math.pow(10.0, f) - 1.0
        return lval

    def uplog(self, n=1.0):
        self.setlog(self.tolog() + n)

    def downlog(self, n=1.0):
        self.setlog(self.tolog() - n)

    # use log scale to determine how many LEDs should be lit
    def numleds(self):
        return int( round(NLEDS * self.tolog() / 9.0) )
        

