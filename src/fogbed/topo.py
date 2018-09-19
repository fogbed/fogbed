from src.fogbed.node import VirtualInstance
from src.fogbed.resourcemodel import ResourcesTable
from src.mininet.topo import Topo


class FogTopo( Topo ):

    def __init__(self, *args, **kwargs):
        Topo.__init__(self, *args, **kwargs)

        self.res_table = ResourcesTable()

    def addLink( self, node1, node2, port1=None, port2=None,
                 key=None, **opts ):

        if isinstance(node1, VirtualInstance):
            node1 = node1.getSwitch()

        if isinstance(node2, VirtualInstance):
            node2 = node2.getSwitch()

        return Topo.addLink(self, node1, node2, port1, port2, key, **opts)

    def calculateRealResources(self, node):
        return self.res_table.calculateRealResources(node)

    def addVirtualInstance(self, name):
        return VirtualInstance(name, self, resources_table=self.res_table)
