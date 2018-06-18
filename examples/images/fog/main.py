import os
import time

import requests
from flask import Flask
from flask import jsonify
from flask import request

app = Flask(__name__)

_SENSOR_ADDRS = []


@app.route('/')
def temperature():
    global _SENSOR_ADDRS
    k = int(os.environ.get('K_VALUE', 10))
    temps = []
    for sensor_addr in _SENSOR_ADDRS:
        r = requests.get("%s:3000" % sensor_addr)

        data = r.json()

        temps += data['temps']

    return jsonify({'ip': request.remote_addr, 'temps': topk(temps, k)}), 200


@app.route('/notify', methods=['POST'])
def notification_handler():
    global _SENSOR_ADDRS
    payload = request.get_json(force=True)
    _SENSOR_ADDRS = payload['sensor_addrs']

    return "OK", 200


def topk(arr, k):
    return sorted(arr, reverse=True)[:k]


def notify_manager():
    while True:
        try:
            r = requests.get("%s/fog" % os.environ['MANAGER_ADDR'])

            if r.status_code == 200:
                break
        except:
            print("Failed to connect to manager. Trying again in 2 seconds.")
            time.sleep(1)

        time.sleep(1)


notify_manager()
