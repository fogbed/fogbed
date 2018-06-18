import os
import random
import time

import requests
from flask import Flask
from flask import jsonify
from flask import request

app = Flask(__name__)


@app.route('/')
def temperature():
    n = int(os.environ.get("VALUES", 10))
    return jsonify({
        'ip': request.remote_addr,
        'temps': [random.randint(1, 100) for x in range(n)]
    }), 200


def notify_manager():
    while True:
        try:
            r = requests.get("%s/sensor" % os.environ['MANAGER_ADDR'])

            if r.status_code == 200:
                break
        except:
            print("Failed to connect to manager. Trying again in 2 seconds.")
            time.sleep(1)

        time.sleep(1)


notify_manager()
