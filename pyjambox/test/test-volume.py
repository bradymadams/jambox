import volume

import time

dr = 0.1
delay = 0.01

v = volume.Volume(0)

r = 0.0
while r <= 9.0:
    v.setlog(r)
    time.sleep(delay)
    r += dr

r = 0.0
while r <= 9.0:
    v.setlog(9.0 - r)
    time.sleep(delay)
    r += dr


