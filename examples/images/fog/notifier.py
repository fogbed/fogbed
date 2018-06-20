import requests
import time
import socket
import os

def notify_manager():
    params = {"hostname": socket.gethostname()}
    while True:
        try:
            addr = "http://%s/register/fog" % os.environ['MANAGER_ADDR']
            r = requests.get(addr, timeout=5, params=params)

            if r.status_code == 200:
                break
        except:
            print("Failed to connect to manager. Trying again in 5 seconds.")
            time.sleep(3)

        time.sleep(2)


notify_manager()