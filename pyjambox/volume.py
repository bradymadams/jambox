import serial
import math
import time

COM = '/dev/ttyUSB0'
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
        return int( round(NLEDS * self.tolog()) )
        

