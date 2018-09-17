#!/usr/bin/python

"""
This example shows how to create a simple network and
how to create docker containers (based on existing images)
to it.
"""

from src.mininet.net import Containernet
from src.mininet.node import Controller, Docker, OVSSwitch
from src.mininet.cli import CLI
from src.mininet.log import setLogLevel, info


def topology():

    "Create a network with some docker containers acting as hosts."

    net = Containernet(controller=Controller)

    info('*** Adding controller\n')
    net.addController('c0')

    info('*** Adding docker containers\n')
    d1 = net.addDocker('d1', ip='10.0.0.251', dimage="mpeuster/stress", cpuset_cpus="0,1")
    d1.sendCmd("./start.sh")

    info('*** Starting network\n')
    net.start()

    info('*** Running CLI\n')
    CLI(net)

    info('*** Stopping network')
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    topology()
