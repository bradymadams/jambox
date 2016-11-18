from jambox import ControlPanel, PORT
import socket

class ControlPanelD(object):
    def __init__(self, host='127.0.0.1', port=PORT):
        self.host = host
        self.port = port

        self.panel = ControlPanel()

    def _exec_cmd(self, data):
        cmd, args = data.split(':')

        args = args.strip(' ').split(' ')

        if cmd == ControlPanel.CMD_POWER:
            return self._exec_cmd_power(args)
        elif cmd == ControlPanel.CMD_STDBY:
            return self._exec_cmd_stdby(args)
        elif cmd == ControlPanel.CMD_SOURC:
            return self._exec_cmd_sourc(args)
        elif cmd == ControlPanel.CMD_VOLCH:
            return self._exec_cmd_volch(args)
        elif cmd == ControlPanel.CMD_MUTE:
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
        non = self.panel.knob_vol.numledson()
        noff = self.panel.knob_vol.numledsoff()
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

if __name__ == '__main__':
    cpd = ControlPanelD()
    cpd.run()

