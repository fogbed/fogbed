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
    hn = request.args.get('hostname', 'no hostname')
    print(hn)

    if type not in _ADDR_MAPPINGS:
        return "Invalid type '%s'" % type, 500

    if addr not in list(map(lambda x: x['ip'], _ADDR_MAPPINGS[type])):
        _ADDR_MAPPINGS[type].append({'ip': addr, 'hn': hn})

    if check():
        notify()
        print("RETURNING OK")
        return "OK", 200

    print (_ADDR_MAPPINGS)
    return "CREATED", 201


def check():
    n_clouds = int(os.environ.get('CLOUDS', 1))
    n_fogs = int(os.environ.get('FOGS', 2))
    n_sensors = n_fogs * int(os.environ.get('SENSORS_PER_FOG', 2))

    return len(_ADDR_MAPPINGS['cloud']) == n_clouds and len(_ADDR_MAPPINGS['fog']) == n_fogs and len(
        _ADDR_MAPPINGS['sensor']) == n_sensors


def notify():

    _ADDRS_CLOUD = list(map(lambda x: x['ip'], sorted(_ADDR_MAPPINGS['cloud'], key=lambda x: x['hn'])))
    _ADDRS_FOG = list(map(lambda x: x['ip'], sorted(_ADDR_MAPPINGS['fog'], key=lambda x: x['hn'])))
    _ADDRS_SENSOR = list(map(lambda x: x['ip'], sorted(_ADDR_MAPPINGS['sensor'], key=lambda x: x['hn'])))

    for cloud_addr in _ADDRS_CLOUD:
        payload = {
            'fog_addrs': _ADDRS_FOG,
            'sensor_addrs': _ADDRS_SENSOR
        }
        requests.post("http://%s:5000/notify" % cloud_addr, json=payload)

    sensors_per_fog = int(os.environ.get('SENSORS_PER_FOG', 2))


    idx = 0
    for fog_addr in _ADDRS_FOG:

        sensors = []
        for x in range(sensors_per_fog):
            sensors.append(_ADDRS_SENSOR[idx])
            idx += 1

        payload = {
            'sensor_addrs': sensors
        }
        requests.post("http://%s:4000/notify" % fog_addr, json=payload)
