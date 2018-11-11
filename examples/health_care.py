#!/usr/bin/python
"""
This is the most simple example to showcase Fogbed.
"""
import time
import json
from src.fogbed.experiment import FogbedExperiment, FogbedDistributedExperiment
from src.fogbed.topo import FogTopo
from src.mininet.node import Controller
from src.mininet.cli import CLI
from src.mininet.link import TCLink
from src.mininet.node import OVSSwitch
from src.mininet.log import info, setLogLevel
setLogLevel('debug')

SENSORS_PER_FOG = 2

FOG_NODES = ["f{}".format(x+1) for x in range(2)]
SENSOR_NODES = ["h{}".format(x+1) for x in range(SENSORS_PER_FOG*len(FOG_NODES))]

fogs = []
sensors = []

MANAGER_ADDR = '10.0.0.1:2000'
MANAGER_ENV = {
    "CLOUDS": 1,
    "FOGS": len(FOG_NODES),
    "SENSORS_PER_FOG": SENSORS_PER_FOG
}

topo = FogTopo()

info('**** Adding Virtual Instances\n')
mngr = topo.addDocker('mngr', ip=MANAGER_ADDR.split(':')[0], dimage="manager:latest", environment=MANAGER_ENV)
vc = topo.addVirtualInstance("vc")
vfs = [topo.addVirtualInstance("vf{}".format(x+1)) for x in range(len(FOG_NODES))]
vss = [topo.addVirtualInstance("vs{}".format(x+1)) for x in range(len(FOG_NODES))]
info('*** Adding docker containers\n')
info('*** Cloud\n')
topo.addLink(vc, mngr)
c1 = vc.addDocker('c1', ip='10.0.0.2', dimage="cloud:latest", environment={"MANAGER_ADDR":MANAGER_ADDR})
info('*** Fogs\n')
for idx, vf in enumerate(vfs):
    f = vf.addDocker(FOG_NODES[idx], ip='10.0.1.{}'.format(idx+1), dimage="fog:latest", environment={"MANAGER_ADDR":MANAGER_ADDR})
    fogs.append(f)
    topo.addLink(vf, vc, cls=TCLink, delay='100ms')
info('*** Sensors\n')
vid = 1
for idx, vs in enumerate(vss):
    topo.addLink(vs, vfs[idx], cls=TCLink, delay='10ms')
    for x in range(SENSORS_PER_FOG):
        se = vs.addDocker(SENSOR_NODES[vid-1], ip='10.0.2.{}'.format(vid), dimage="sensor:latest", environment={"MANAGER_ADDR":MANAGER_ADDR})
        vid += 1
        sensors.append(se)

exp = FogbedDistributedExperiment(topo, switch=OVSSwitch)
exp.start()

runs = 5

try:
    print exp.monitor()
    time.sleep(5)
    print exp.get_node(c1).cmd("curl localhost:5000/tempsFromFog/%s" % runs)
    print exp.get_node(c1).cmd("curl localhost:5000/tempsFromSensor/%s" % runs)

    data = exp.get_node(c1).cmd("curl localhost:5000/stats")
    
    obj = json.loads(data)

    target = {
        "methodA(cloud)": {
            "avg_time": round(obj["get_temperatures_sensor"]["avg_time"], 3),
            "max_time": round(obj["get_temperatures_sensor"]["max_time"], 3),
            "runs": obj["get_temperatures_sensor"]["runs"]
        },
        "methodB(fog)": {
            "avg_time": round(obj["get_temperatures_fog"]["avg_time"], 3),
            "max_time": round(obj["get_temperatures_fog"]["max_time"], 3),
            "runs": obj["get_temperatures_fog"]["runs"]
        }
    }

    print(json.dumps(target, indent=4, separators=(',', ': ')))

    exp.CLI()
finally:
    exp.stop()
