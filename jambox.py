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

class RotaryEnc(object):
    def __init__(self, knob, pinA, pinB, dvdd=0.01):
        self.knob = knob
        self.pinA = pinA
        self.pinB = pinB
        self.dvdd = dvdd
        self.watch = False

        GPIO.setup(self.pinA, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.pinB, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def monitor(self):
        ap = GPIO.input(self.pinA)
        bp = GPIO.input(self.pinB)
        dirp = -1 # Assume CCW direction to start

        self.watch = True

        while self.watch:
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

class ControlPanelD(object):
    CMD_POWER = 'O'
    CMD_STDBY = 'Z'
    CMD_SOURC = 'S'
    CMD_VOLCH = 'V'
    CMD_MUTE  = 'M'

    def __init__(self, host='127.0.0.1', port=PORT):
        self.host = host
        self.port = port

        self.panel = ControlPanel()

    def _exec_cmd(self, data):
        cmd, args = data.split(':')

        args = args.strip(' ').split(' ')

        if cmd == ControlPanelD.CMD_POWER:
            return self._exec_cmd_power(args)
        elif cmd == ControlPanelD.CMD_STDBY:
            return self._exec_cmd_stdby(args)
        elif cmd == ControlPanelD.CMD_SOURC:
            return self._exec_cmd_sourc(args)
        elif cmd == ControlPanelD.CMD_VOLCH:
            return self._exec_cmd_volch(args)
        elif cmd == ControlPanelD.CMD_MUTE:
            return self._exec_cmd_mute(args)
        else:
            print 'Unrecognized command: %s' % cmd
    
    def _exec_cmd_power(self, args):
        print 'CMD power', args
    
    def _exec_cmd_stdby(self, args):
        print 'CMD stdby', args
    
    def _exec_cmd_sourc(self, args):
        print 'CMD sourc', args
    
    def _exec_cmd_volch(self, args):
        self.panel.knob_vol.turnlog(float(args[0]))
        non = self.panel.knob_vol.numleds()
        noff = KNOB_NLEDS - non
        return '%s %s' % (non, noff)
    
    def _exec_cmd_mute(self, args):
        print 'CMD mute', args

    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.host, self.port))
        s.listen(1)

        self.watch = True
        while self.watch:
            conn, addr = s.accept()

            data = conn.recv(64).strip(' ')
            stat = self._exec_cmd(data)

            if stat is None:
                stat = '0'

            conn.sendall(stat)
            conn.close()

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
        return self._send_cmd(ControlPanelD.CMD_POWER)

    def send_cmd_stdby(self):
        return self._send_cmd(ControlPanelD.CMD_STDBY)

    def send_cmd_sourc(self, source):
        return self._send_cmd(ControlPanelD.CMD_SOURC, source)

    def send_cmd_volch(self, dv):
        return self._send_cmd(ControlPanelD.CMD_VOLCH, dv)

    def send_cmd_mute(self):
        return self._send_cmd(ControlPanelD.CMD_MUTE)

if __name__ == '__main__':
    cpd = ControlPanelD()
    cpd.run()

