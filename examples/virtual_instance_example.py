#!/usr/bin/python
"""
This is the most simple example to showcase Fogbed.
"""
import time

from src.fogbed.experiment import FogbedExperiment, FogbedDistributedExperiment
from src.fogbed.resourcemodel import CloudResourceModel, EdgeResourceModel, FogResourceModel, PREDEFINED_RESOURCES
from src.fogbed.topo import FogTopo
from src.mininet.link import TCLink
from src.mininet.log import setLogLevel
from src.mininet.node import OVSSwitch

setLogLevel('info')

topo = FogTopo()

c1 = topo.addVirtualInstance("cloud")
f1 = topo.addVirtualInstance("fog")
e1 = topo.addVirtualInstance("edge")

erm = EdgeResourceModel(max_cu=20, max_mu=2048)
frm = FogResourceModel()
crm = CloudResourceModel()

e1.assignResourceModel(erm)
f1.assignResourceModel(frm)
c1.assignResourceModel(crm)

d1 = c1.addDocker('d1', ip='10.0.0.251', dimage="ubuntu:trusty")
d2 = f1.addDocker('d2', ip='10.0.0.252', dimage="ubuntu:trusty")
d3 = e1.addDocker('d3', ip='10.0.0.253', dimage="ubuntu:trusty")
d4 = topo.addDocker('d4', ip='10.0.0.254', dimage="ubuntu:trusty")
d5 = e1.addDocker('d5', ip='10.0.0.255', dimage="ubuntu:trusty", resources=PREDEFINED_RESOURCES['medium'])
d6 = e1.addDocker('d6', ip='10.0.0.256', dimage="ubuntu:trusty", resources=PREDEFINED_RESOURCES['large'])

s1 = topo.addSwitch('s1')
s2 = topo.addSwitch('s2')

topo.addLink(d4, s1)
topo.addLink(s1, s2)
topo.addLink(s2, e1)
topo.addLink(c1, f1, cls=TCLink, delay='200ms', bw=1)
topo.addLink(f1, e1, cls=TCLink, delay='350ms', bw=2)

exp = FogbedDistributedExperiment(topo, switch=OVSSwitch)
exp.start()

try:
    print exp.get_node("cloud.d1").cmd("ifconfig")
    print exp.get_node(d2).cmd("ifconfig")

    print "waiting 5 seconds for routing algorithms on the controller to converge"
    time.sleep(5)

    print exp.get_node(d1).cmd("ping -c 5 10.0.0.252")
    print exp.get_node("fog.d2").cmd("ping -c 5 10.0.0.251")
finally:
    exp.stop()
