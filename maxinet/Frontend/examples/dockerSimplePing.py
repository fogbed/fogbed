#!/usr/bin/env python2
""" A small example showing the usage of Docker containers.
"""

import time

from maxinet.Frontend import maxinet_main
from maxinet.Frontend.container import Docker
from mininet.topo import Topo
from mininet.node import OVSSwitch

topo = Topo()

d1 = topo.addHost("d1", cls=Docker, ip="10.0.0.251", dimage="ubuntu:trusty")
d2 = topo.addHost("d2", cls=Docker, ip="10.0.0.252", dimage="ubuntu:trusty")

s1 = topo.addSwitch("s1")
s2 = topo.addSwitch("s2")
topo.addLink(d1, s1)
topo.addLink(s1, s2)
topo.addLink(d2, s2)

mappings = {
    "s1": 0,
    "s2": 1
}

cluster = maxinet_main.Cluster()
exp = maxinet_main.Experiment(cluster, topo, switch=OVSSwitch, nodemapping=mappings)
exp.setup()

try:
    print exp.get_node("d1").cmd("ifconfig")
    print exp.get_node("d2").cmd("ifconfig")

    print "waiting 5 seconds for routing algorithms on the controller to converge"
    time.sleep(5)

    print exp.get_node("d1").cmd("ping -c 5 10.0.0.251")
    print exp.get_node("d2").cmd("ping -c 5 10.0.0.251")

finally:
    exp.stop()
