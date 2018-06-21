import os
import time

import requests
import socket
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
        r = requests.get("http://%s:3000" % sensor_addr)

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
