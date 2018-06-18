import os

import requests
from flask import Flask
from flask import request

app = Flask(__name__)

_ADDR_MAPPINGS = {
    'cloud': [],
    'fog': [],
    'sensor': []
}


@app.route('/register/<type>')
def register(type):
    addr = request.remote_addr
    print (_ADDR_MAPPINGS)

    if type not in _ADDR_MAPPINGS:
        return "Invalid type '%s'" % type, 500

    if addr not in _ADDR_MAPPINGS[type]:
        _ADDR_MAPPINGS[type].append(addr)

    if check():
        notify()
        return "OK", 200

    return "CREATED", 201


def check():
    n_clouds = int(os.environ.get('CLOUDS', 1))
    n_fogs = int(os.environ.get('FOGS', 2))
    n_sensors = n_fogs * int(os.environ.get('SENSORS_PER_FOG', 2))

    return len(_ADDR_MAPPINGS['cloud']) == n_clouds and len(_ADDR_MAPPINGS['fog']) == n_fogs and len(
        _ADDR_MAPPINGS['sensor']) == n_sensors


def notify():
    for cloud_addr in _ADDR_MAPPINGS['cloud']:
        payload = {
            'fog_addrs': _ADDR_MAPPINGS['fog'],
            'sensor_addrs': _ADDR_MAPPINGS['sensor']
        }
        requests.post("%s:5000/notify" % cloud_addr, data=payload)

    sensors_per_fog = int(os.environ.get('SENSORS_PER_FOG', 2))
    for fog_addr in _ADDR_MAPPINGS['fog']:

        sensors = []
        for x in range(sensors_per_fog):
            if len(_ADDR_MAPPINGS['sensor']) > 0:
                sensors.append(_ADDR_MAPPINGS['sensor'].pop(0))

        payload = {
            'sensor_addrs': sensors
        }
        requests.post("%s:4000/notify" % fog_addr, data=payload)
