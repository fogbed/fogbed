#!/usr/bin/python2

#
# Minimal example showing how to use MaxiNet
#

import time

from src.maxinet.Frontend import maxinet_main
from src.maxinet.tools import FatTree
from src.mininet.node import OVSSwitch

topo = FatTree(4, 10, 0.1)
cluster = maxinet_main.Cluster()

exp = maxinet_main.Experiment(cluster, topo, switch=OVSSwitch)
exp.setup()

print exp.get_node("h1").cmd("ifconfig")  # call mininet cmd function of h1
print exp.get_node("h4").cmd("ifconfig")

print "waiting 5 seconds for routing algorithms on the controller to converge"
time.sleep(5)

print exp.get_node("h1").cmd("ping -c 5 10.0.0.4")

exp.stop()
