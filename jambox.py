import sys
import serial
import math
import time
import socket

import threading
from RPi import GPIO

#COM = '/dev/ttyUSB0'
COM = '/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0'
BAUD = 9600

PORT = 9000

KNOB_MINVAL = 0
KNOB_MAXVAL = 255
KNOB_NLEDS = 10

#VOLUME_CHANNELS = (0, )
VOLUME_CHANNELS = (0, 1)
VOLUME_MAX = 255
VOLUME_MAX_ON = 0.5

VOLUME_RE_PINA = 23
VOLUME_RE_PINB = 24

class Input(object):
    def __init__(self, cb):
        self.cb = cb # callback function

    def check(self):
        pass

# Checks a single pin connected to a momentary push button
class PushButton(Input):
    def __init__(self, cb, pin):
        Input.__init__(self, cb)
        self.pin = pin

        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self.pstate = GPIO.input(self.pin)

    def check(self):
        state = GPIO.input(self.pin)
        print state
        if state == 0 and state != self.pstate:
            self.cb()

        self.pstate = state

class RotaryEncoder(Input):
    def __init__(self, cb, pinA, pinB, dvdd=0.01):
        Input.__init__(self, cb)
        self.pinA = pinA
        self.pinB = pinB
        self.dvdd = dvdd
        self.watch = False

        GPIO.setup(self.pinA, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.pinB, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self.ap = GPIO.input(self.pinA)
        self.bp = GPIO.input(self.pinB)
        self.dirp = -1 # Assume CCW direction to start

    def check(self):
        turning = True
        while turning:
            a = GPIO.input(self.pinA)
            b = GPIO.input(self.pinB)

            if a ^ b:
                dir_a_diff = 1
                dir_b_diff = -1
            else:
                dir_a_diff = -1
                dir_b_diff = 1

            turning = a != self.ap or b != self.bp

            if turning:
                if a != self.ap and b == self.bp:
                    dir0 = dir_a_diff
                    count = 1
                elif a == self.ap and b != self.bp:
                    dir0 = dir_b_diff
                    count = 1
                else:
                    dir0 = self.dirp
                    count = 2

                # To avoid noise only change volume if knob is moving in same direction
                if dir0 == self.dirp:
                    if dir0 == 1:
                        self.cb(self.dvdd * count)
                    else:
                        self.cb(-self.dvdd * count)
                
                self.ap = a
                self.bp = b
                self.dirp = dir0

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

        self.mute_state = False
        self.sdby_state = False

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

        sled = 'L:%i' % self.numledson()
        self._send_instruction(sled)

    def turn(self, n):
        self.set(self.current + n)

    def up(self, n=1):
        self.turn(abs(n))

    def down(self, n=1):
        self.turn(-abs(n))

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

    def turnlog(self, n):
        self.setlog(self.tolog() + n)

    def uplog(self, n=0.1):
        self.turnlog(abs(n))

    def downlog(self, n=0.1):
        self.turnlog(-abs(n))

    # use log scale to determine how many LEDs should be lit
    def numledson(self):
        return int( round(KNOB_NLEDS * self.tolog()) )

    def numledsoff(self):
        return KNOB_NLEDS - self.numledson()

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

    def mute(self):
        self.mute_state = not self.mute_state
        m = 1 if self.mute_state else 0
        self._send_instruction('M:%i' % m)

    def standby(self):
        self.sdby_state = not self.sdby_state
        z = 1 if self.sdby_state else 0
        self._send_instruction('Z:%i' % z)

class ControlPanel(object):
    MASTERPANEL = None

    CMD_POWER = 'O'
    CMD_STDBY = 'Z'
    CMD_SOURC = 'S'
    CMD_VOLCH = 'V'
    CMD_MUTE  = 'M'

    def __init__(self):
        self.knob_vol = Knob(VOLUME_CHANNELS, maxval=VOLUME_MAX)

        self._limit_volume()

    def power_on(self):
        self._limit_volume()

    def power_off(self):
        pass

    # This function is used to ensure the volume is not
    # set too high during various events, e.g. when power is turned on
    def _limit_volume(self):
        if self.knob_vol.tolog() > VOLUME_MAX_ON:
            self.knob.setlog(VOLUME_MAX_ON)

class ControlPanelC(object):
    def __init__(self, serv='127.0.0.1', port=PORT):
        self.serv = serv
        self.port = port

    def _send_cmd(self, cmd, *args):
        scmd = cmd + ':'

        if args:
            for a in args:
                scmd += ' %s' % str(a)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.serv, self.port))
        s.sendall(scmd)
        stat = s.recv(64)
        s.close()

        return stat

    def send_cmd_power(self):
        return self._send_cmd(ControlPanel.CMD_POWER)

    def send_cmd_stdby(self):
        return self._send_cmd(ControlPanel.CMD_STDBY)

    def send_cmd_sourc(self, source):
        return self._send_cmd(ControlPanel.CMD_SOURC, source)

    def send_cmd_volch(self, dv):
        return self._send_cmd(ControlPanel.CMD_VOLCH, dv)

    def send_cmd_mute(self):
        return self._send_cmd(ControlPanel.CMD_MUTE)

