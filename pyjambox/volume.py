import serial
import math

COM = '/dev/ttyAMA0'
BAUD = 9600

#MINVOL = 0
#MAXVOL = 255

class Knob(object):
    def __init__(self, vol0, minvol=0, maxvol=255):
        self.current = vol0
        self.minvol = minvol
        self.maxvol = maxvol

        self.ser = serial.Serial(COM, BAUD)

        self.set(vol0)

    def limit(self, vol):
        vol = min(vol, self.maxvol)
        vol = max(vol, self.minvol)
        return vol

    def set(self, vol):
        vol = self.limit(vol)
        try:
            n = self.ser.write(chr(vol))
            self.current = vol
        except:
            print 'Unable to set volume'

    def up(self, n=1):
        self.set(self.current + n)

    def down(self, n=1):
        self.set(self.current - n)

    def setlog(self, lvol):
        lvol = min(lvol, 9.0)
        lvol = max(lvol, 0.0)
        lvol += 1.0

        f = math.log10(lvol)
        i = int((self.maxvol - self.minvol) * f + self.minvol)

        self.set(i)

    def tolog(self):
        f = float((self.current - self.minvol)) / float((self.maxvol - self.minvol))
        lvol = math.pow(10.0, f) - 1.0
        return lvol

    def uplog(self, n=1.0):
        lvol = self.tolog() + n
        self.setlog(lvol)

    def downlog(self, n=1.0):
        lvol = self.tolog() - n
        self.setlog(lvol)

