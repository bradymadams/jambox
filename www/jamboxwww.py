#! /usr/bin/env python
import jambox
import json
from flask import Flask, render_template

app = Flask(__name__)

panel = jambox.ControlPanel.master()

@app.route('/')
def index():
    non = panel.knob_vol.numleds()
    noff = jambox.KNOB_NLEDS - non
    return render_template('control_panel.html', non=non, noff=noff)

@app.route('/volstat/')
def volstat():
    #panel.knob_vol.getstatus()
    non = panel.knob_vol.numleds()
    noff = jambox.KNOB_NLEDS - non
    return json.dumps({'non':non, 'noff':noff})
    #return 'Volume at %f' % panel.knob_vol.tolog()

@app.route('/volchange/<dv>/')
def volchange(dv):
    dv = float(dv)
    if dv > 0.0:
        panel.knob_vol.uplog(dv)
    else:
        panel.knob_vol.downlog(abs(dv))
    return volstat()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)

