#!/usr/bin/env python2
"""
This is the most simple example to showcase Fogbed.
"""
import time

from src.maxinet.Frontend import maxinet_main
from src.mininet.link import TCIntf
from src.mininet.log import info, setLogLevel
from src.mininet.node import OVSSwitch
from src.mininet.topo import Topo

setLogLevel('info')

SENSORS_PER_FOG = 1

FOG_NODES = ["f{}".format(x + 1) for x in range(3)]
SENSOR_NODES = ["h{}".format(x + 1) for x in range(SENSORS_PER_FOG * len(FOG_NODES))]

fogs = []
sensors = []

MANAGER_ADDR = '10.0.0.1:2000'
MANAGER_ENV = {
    "CLOUDS": 1,
    "FOGS": len(FOG_NODES),
    "SENSORS_PER_FOG": SENSORS_PER_FOG
}

topo = Topo()

switch_idx = 1

info('**** Adding Manager\n')
mngr = topo.addDocker('m1', ip=MANAGER_ADDR.split(':')[0], dimage="manager:latest", environment=MANAGER_ENV)
sw_mngr = topo.addSwitch('s%d' % switch_idx)
switch_idx += 1
topo.addLink(mngr, sw_mngr)
info('*** Adding docker containers\n')
info('*** Cloud\n')
c1 = topo.addDocker('c1', ip='10.0.0.2', dimage="cloud:latest", environment={"MANAGER_ADDR": MANAGER_ADDR})
sw_cloud = topo.addSwitch('s%d' % switch_idx)
switch_idx += 1
topo.addLink(sw_cloud, c1)
topo.addLink(sw_mngr, sw_cloud)
info('*** Fogs\n')
for idx, f_name in enumerate(FOG_NODES):
    f = topo.addDocker(f_name, ip='10.0.1.{}'.format(idx + 1), dimage="fog:latest",
                       environment={"MANAGER_ADDR": MANAGER_ADDR})
    sw_fog = topo.addSwitch('s%d' % (switch_idx))
    switch_idx += 1
    fogs.append((f, sw_fog))
    topo.addLink(sw_fog, f)
    topo.addLink(sw_fog, sw_cloud, delay='100ms')
info('*** Sensors\n')
vid = 1
for idx, f_name in enumerate(FOG_NODES):
    sw_sensor = topo.addSwitch("s%d" % (switch_idx))
    switch_idx += 1
    topo.addLink(fogs[idx][1], sw_sensor, delay='10ms')
    for x in range(SENSORS_PER_FOG):
        se = topo.addDocker(SENSOR_NODES[vid - 1], ip='10.0.2.{}'.format(vid), dimage="sensor:latest",
                            environment={"MANAGER_ADDR": MANAGER_ADDR})
        vid += 1
        topo.addLink(se, sw_sensor)
        sensors.append((se, sw_sensor))

info('*** Starting network\n')
cluster = maxinet_main.Cluster()
exp = maxinet_main.Experiment(cluster, topo, switch=OVSSwitch)
exp.setup()

try:
    time.sleep(5)
    print exp.get_node("c1").cmd("curl localhost:5000/tempsFromSensor/2")
    print exp.get_node("c1").cmd("curl localhost:5000/tempsFromFog/2")
    print exp.get_node("c1").cmd("curl localhost:5000/stats")
finally:
    exp.stop()

#exp.CLI(locals(), globals())

#exp.stop()
