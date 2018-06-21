import requests
import time
import socket
import os

def notify_manager():
    params = {"hostname": socket.gethostname()}
    while True:
        try:
            addr = "http://%s/register/cloud" % os.environ['MANAGER_ADDR']
            r = requests.get(addr, timeout=5, params=params)

            if r.status_code == 200:
                break
        except requests.exceptions.ConnectionError:
            print("Connection Error")
            continue
        except:
            print("Failed to connect to manager. Trying again in 6 seconds.")
            time.sleep(3)

        time.sleep(3)


notify_manager()