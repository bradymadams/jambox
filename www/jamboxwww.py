#! /usr/bin/env python
import jambox
from flask import Flask, render_template

app = Flask(__name__)

panel = jambox.ControlPanel.master()

@app.route('/')
def index():
    return render_template('control_panel.html')
    #return 'Welcome to the Jambox!'

@app.route('/volstat/')
def volstat():
    return 'Volume at %f' % panel.knob_vol.tolog()

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

