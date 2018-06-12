#!/usr/bin/python
"""
This is the most simple example to showcase Fogbed.
"""
from mininet.net import Fogbed
from mininet.node import Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import info, setLogLevel
from mininet.resourcemodel import EdgeResourceModel, FogResourceModel, CloudResourceModel
setLogLevel('info')

net = Fogbed(controller=Controller)
info('**** Adding Virtual Instances\n')
c1 = net.addVirtualInstance("cloud")
f1 = net.addVirtualInstance("fog")
e1 = net.addVirtualInstance("edge")
info('*** Adding Resource Models\n')
erm = EdgeResourceModel()
frm = FogResourceModel()
crm = CloudResourceModel()
e1.assignResourceModel(erm)
f1.assignResourceModel(frm)
c1.assignResourceModel(crm)
info('*** Adding controller\n')
net.addController('c0')
info('*** Adding docker containers\n')
d1 = c1.addDocker('d1', ip='10.0.0.251', dimage="ubuntu:trusty")
d2 = f1.addDocker('d2', ip='10.0.0.252', dimage="ubuntu:trusty")
d3 = e1.addDocker('d3', ip='10.0.0.253', dimage="ubuntu:trusty")
d4 = net.addDocker('d4', ip='10.0.0.254', dimage="ubuntu:trusty")
info('*** Adding switches\n')
s1 = net.addSwitch('s1')
s2 = net.addSwitch('s2')
info('*** Creating links\n')
net.addLink(d4, e1)
#net.addLink(s1, s2, cls=TCLink, delay='100ms', bw=1)
#net.addLink(s2, d3)
info('*** VIs Links\n')
net.addLink(c1, f1, cls=TCLink, delay='200ms', bw=1)
net.addLink(f1, e1, cls=TCLink, delay='350ms', bw=2)
info('*** Starting network\n')
net.start()
info('*** Testing connectivity\n')
net.ping([d1, d2, d3, d4])
info('*** Running CLI\n')
CLI(net)
info('*** Stopping network\n')
net.stop()

