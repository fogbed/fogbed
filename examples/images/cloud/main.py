import os
import time
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
        start_time = time.start()

        ret = fn(*args, **kwargs)

        elapsed_time = time.time() - start_time

        if fn.__name__ not in PROF_DATA:
            PROF_DATA[fn.__name__] = [0, []]
        PROF_DATA[fn.__name__][0] += 1
        PROF_DATA[fn.__name__][1].append(elapsed_time)

        return ret

    return profiled


@app.route('/tempsFromFog')
@profile
def temperature_from_fogs():
    global _SENSOR_ADDRS
    k = int(os.environ.get('K_VALUE', 10))
    temps = []
    for sensor_addr in _SENSOR_ADDRS:
        r = requests.get("%s:3000" % sensor_addr)

        data = r.json()

        temps += data['temps']

    return jsonify({'ip': request.remote_addr, 'temps': topk(temps, k)}), 200


@app.route('/tempsFromSensor')
@profile
def temperature_from_sensors():
    global _FOG_ADDRS
    k = int(os.environ.get('K_VALUE', 10))
    temps = []
    for fog_addr in _FOG_ADDRS:
        r = requests.get("%s:4000" % fog_addr)

        data = r.json()

        temps += data['temps']

    return jsonify({'ip': request.remote_addr, 'temps': topk(temps, k)}), 200

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


def notify_manager():
    while True:
        try:
            r = requests.get("%s/cloud" % os.environ['MANAGER_ADDR'])

            if r.status_code == 200:
                break
        except:
            print("Failed to connect to manager. Trying again in 2 seconds.")
            time.sleep(1)

        time.sleep(1)


notify_manager()
