#!/usr/bin/python
"""
This is the most simple example to showcase Fogbed.
"""
from mininet.net import Fogbed
from mininet.node import Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel
setLogLevel('info')

SENSORS_PER_FOG = 2

FOG_NODES = ["f{}".format(x+1) for x in range(1)]
SENSOR_NODES = ["h{}".format(x+1) for x in range(SENSORS_PER_FOG*len(FOG_NODES))]

fogs = []
sensors = []

net = Fogbed(controller=Controller)
info('**** Adding Virtual Instances\n')
vc = net.addVirtualInstance("vc")
vfs = [net.addVirtualInstance("vf{}".format(x+1)) for x in range(len(FOG_NODES))]
vss = [net.addVirtualInstance("vs{}".format(x+1)) for x in range(len(FOG_NODES))]
info('*** Adding controller\n')
net.addController('c0')
info('*** Adding docker containers\n')
info('*** Cloud\n')
c1 = vc.addDocker('c1', ip='10.0.0.1', dimage="ubuntu:trusty")
info('*** Fogs\n')
for idx, vf in enumerate(vfs):
    f = vf.addDocker(FOG_NODES[idx], ip='10.0.1.{}'.format(idx+1), dimage="ubuntu:trusty")
    fogs.append(f)
    net.addLink(vf, vc, cls=TCLink, delay='100ms')
info('*** Sensors\n')
vid = 1
for idx, vs in enumerate(vss):
    net.addLink(vs, vfs[idx], cls=TCLink, delay='10ms')
    for x in range(SENSORS_PER_FOG):
        se = vs.addDocker(SENSOR_NODES[vid-1], ip='10.0.2.{}'.format(vid), dimage="sensor:latest", dcmd='./start.sh')
        vid += 1
        sensors.append(se)

info('*** Starting network\n')
net.start()
info('*** Testing connectivity\n')
net.ping([fogs[0], sensors[0], c1])
info('*** Running CLI\n')
CLI(net)
info('*** Stopping network\n')
net.stop()

