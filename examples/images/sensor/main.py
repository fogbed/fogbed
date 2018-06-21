import os
import random
import socket
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
