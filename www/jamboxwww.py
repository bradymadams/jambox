#! /usr/bin/env python
import jambox
import os
import json
from flask import Flask, render_template, send_from_directory

app = Flask(__name__)

panel = jambox.ControlPanelC()

def numleds():
    stat = panel.send_cmd_volch('0.0')
    non, noff = stat.split(' ')
    return (int(non), int(noff))

@app.route('/')
def index():
    non, noff = numleds()
    return render_template('control_panel.html', non=non, noff=noff)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
        'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/volstat/')
def volstat():
    non, noff = numleds()
    return json.dumps({'non':non, 'noff':noff})

@app.route('/volchange/<dv>/')
def volchange(dv):
    stat = panel.send_cmd_volch(dv)
    non, noff = stat.split(' ')
    return json.dumps({'non':int(non), 'noff':int(noff)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)

