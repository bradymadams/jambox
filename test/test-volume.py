import jambox
import time

dr = 0.01
delay = 0.1

knob = jambox.Knob((0, 1), maxval=61)

r = 0.0
while r <= 1.0:
    knob.setlog(r)
    time.sleep(delay)
    r += dr

r = 0.0
while r <= 1.0:
    knob.setlog(1.0 - r)
    time.sleep(delay)
    r += dr


