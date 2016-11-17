#! /usr/bin/env python
import jambox
import os
import sys
import json
import logging
import signal
from flask import Flask, render_template, send_from_directory, request

app = Flask(__name__)

panel = jambox.ControlPanelC()

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func:
        func()

def numleds():
    stat = panel.send_cmd_volch('0.0')
    non, noff = stat.split(' ')
    return (int(non), int(noff))

@app.route('/')
def index():
    non, noff = numleds()
    return render_template('control_panel.html', non=non, noff=noff)

@app.route('/shutdown/')
def shutdown():
    shutdown_server()
    return 'Shutting Jambox http server down...'

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
    port = 8000
    log = logging.getLogger('werkzeug')
    #log.setLevel(logging.ERROR)
    for a in sys.argv:
        if '=' not in a:
            continue
        n, v = a.split('=')
        if n == 'log=':
            flog = logging.FileHandler(v)
            log.addHandler(flog)
        if n == 'port=':
            port = int(v)

    app.run(debug=True, host='0.0.0.0', port=port)

