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

_ADDR_SENSOR = []
_ADDR_CLOUD = []
_ADDR_FOG = []

@app.route('/register/<type>')
def register(type):
    addr = request.remote_addr
    hn = request.args.get('hostname', 'no hostname')
    print(hn)

    if type not in ['cloud', 'fog', 'sensor']:
        return "Invalid type '%s'" % type, 500

    if type == 'sensor' and addr not in list(map(lambda x: x['ip'], _ADDR_SENSOR)):
        _ADDR_SENSOR.append({'ip': addr, 'hn': hn})
    if type == 'fog' and addr not in list(map(lambda x: x['ip'], _ADDR_FOG)):
        _ADDR_FOG.append({'ip': addr, 'hn': hn})
    if type == 'cloud' and addr not in list(map(lambda x: x['ip'], _ADDR_CLOUD)):
        _ADDR_CLOUD.append({'ip': addr, 'hn': hn})

    if check():
        notify()
        print("RETURNING OK")
        return "OK", 200

    print (_ADDR_SENSOR)
    print (_ADDR_FOG)
    print (_ADDR_CLOUD)
    return "CREATED", 201


def check():
    n_clouds = int(os.environ.get('CLOUDS', 1))
    n_fogs = int(os.environ.get('FOGS', 2))
    n_sensors = n_fogs * int(os.environ.get('SENSORS_PER_FOG', 2))

    return len(_ADDR_CLOUD) == n_clouds and len(_ADDR_FOG) == n_fogs and len(
        _ADDR_SENSOR) == n_sensors


def notify():
    for cloud_addr in _ADDR_CLOUD:
        payload = {
            'fog_addrs': _ADDR_FOG,
            'sensor_addrs': _ADDR_SENSOR
        }
        requests.post("http://%s:5000/notify" % cloud_addr['ip'], json=payload)

    sensors_per_fog = int(os.environ.get('SENSORS_PER_FOG', 2))

    idx = 0
    for fog_addr in _ADDR_FOG:

        sensors = []
        for x in range(sensors_per_fog):
            sensors.append(_ADDR_SENSOR[idx])
            idx += 1

        payload = {
            'sensor_addrs': sensors
        }
        requests.post("http://%s:4000/notify" % fog_addr['ip'], json=payload)
