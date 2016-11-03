import jambox
import sys

def help():
    print 'Usage %s COMMAND [ARGS]' % sys.argv[0]
    print 'Valid commands:'
    print '\tset VALUE - Set volume to VALUE'
    print '\tsetlog VALUE - Set volume to log VALUE (0 <= VALUE <= 1)'

if len(sys.argv) <= 1:
    help()
    sys.exit(0)

command = sys.argv[1]

knob = jambox.Knob((0, 1))

if command == 'set':
    knob.set(int(sys.argv[2]))
    print 'Volume set to %f (%i)' % (knob.tolog(), knob.current)
elif command == 'setlog':
    knob.setlog(float(sys.argv[2]))
    print 'Volume set to %f (%i)' % (knob.tolog(), knob.current)

