import os
import time

import socket
from functools import wraps

import requests
from flask import Flask
from flask import jsonify
from flask import request

app = Flask(__name__)

PROF_DATA = {}

_SENSOR_ADDRS = []
_FOG_ADDRS = []


def profile(fn):
    @wraps(fn)
    def profiled(*args, **kwargs):
        start_time = time.time()

        ret = fn(*args, **kwargs)

        elapsed_time = time.time() - start_time

        if fn.__name__ not in PROF_DATA:
            PROF_DATA[fn.__name__] = [0, []]
        PROF_DATA[fn.__name__][0] += 1
        PROF_DATA[fn.__name__][1].append(elapsed_time)

        return ret

    return profiled


@app.route('/tempsFromSensor/<runs>')
def temperature_from_sensor(runs):
    global _SENSOR_ADDRS
    k = int(os.environ.get('K_VALUE', 10))

    temps = []

    for x in range(int(runs)):
        temps.append(topk(get_temperatures_sensor(), k))

    return jsonify({'ip': request.remote_addr, 'temps': temps}), 200


@app.route('/tempsFromFog/<runs>')
def temperature_from_fogs(runs):
    global _FOG_ADDRS
    k = int(os.environ.get('K_VALUE', 10))

    temps = []

    for x in range(int(runs)):
        temps.append(topk(get_temperatures_fog(), k))

    return jsonify({'ip': request.remote_addr, 'temps': temps}), 200

@profile
def get_temperatures_fog():
    global _FOG_ADDRS
    temps = []
    for addr in _FOG_ADDRS:
        r = requests.get("http://%s:%d" % (addr, 4000))

        data = r.json()

        temps += data['temps']

    return temps

@profile
def get_temperatures_sensor():
    global _SENSOR_ADDRS
    temps = []
    for addr in _SENSOR_ADDRS:
        r = requests.get("http://%s:%d" % (addr, 3000))

        data = r.json()

        temps += data['temps']

    return temps

def topk(arr, k):
    return sorted(arr, reverse=True)[:k]

@app.route('/notify', methods=['POST'])
def notification_handler():
    global _SENSOR_ADDRS, _FOG_ADDRS
    payload = request.get_json(force=True)
    _SENSOR_ADDRS = payload['sensor_addrs']
    _FOG_ADDRS = payload['fog_addrs']

    return "OK", 200

@app.route('/stats')
def stats():
    payload = {}
    for fname, data in PROF_DATA.items():
        if fname not in payload:
            payload[fname] = {}
        payload[fname]['max_time'] = max(data[1])
        payload[fname]['avg_time'] = sum(data[1]) / len(data[1])
        payload[fname]['runs'] = data[0]

    return jsonify(payload), 200


def print_prof_data():
    for fname, data in PROF_DATA.items():
        max_time = max(data[1])
        avg_time = sum(data[1]) / len(data[1])
        print("Function %s called %d times. " % (fname, data[0]))
        print('Execution time max: %.3f, average: %.3f' % (max_time, avg_time))


def clear_prof_data():
    global PROF_DATA
    PROF_DATA = {}
