from src.fogbed.net import Fogbed
from src.fogbed.resourcemodel import ResourcesTable
from src.maxinet.Frontend.maxinet_main import Experiment, Cluster
from src.maxinet.WorkerServer.server import TCLinkParams
from src.mininet.link import TCIntf
from src.mininet.log import debug, info
from src.mininet.node import UserSwitch, Controller


class FogbedDistributedExperiment(object):

    def __init__(self, topology, controller=Controller, switch=UserSwitch,
                 nodemapping=None, hostnamemapping=None, sharemapping=None,
                 minworkers=None, maxworkers=None):
        cluster = Cluster(minWorkers=minworkers, maxWorkers=maxworkers)
        self.topo = topology
        self.res_table = ResourcesTable()
        self.exp = Experiment(cluster,
                              topology,
                              controller,
                              is_partitioned=False,
                              switch=switch,
                              nodemapping=nodemapping,
                              hostnamemapping=hostnamemapping,
                              sharemapping=sharemapping,
                              mininet_cls=Fogbed)

    def __getattr__(self, item):
        return getattr(self.exp, item)

    def _update_hosts_resources(self):
        for node in self.topo.hosts():
            host = self.exp.get(node)
            try:
                resources = self.topo.calculateRealResources(node)
                host.update_resources(**resources)
            except Exception as err:
                info(err)

    def start(self):
        self.exp.setup()
        self._update_hosts_resources()

    def stop(self):
        self.exp.stop()


class FogbedExperiment(object):

    def __init__(self, topology, controller=Controller, switch=UserSwitch):
        self.topo = topology
        self.res_table = ResourcesTable()
        self.net = Fogbed(topo=topology, intf=TCIntf, link=TCLinkParams,
                          switch=switch, controller=controller)

    def __getattr__(self, item):
        return getattr(self.net, item)

    def _update_hosts_resources(self):

        for node in self.topo.hosts():
            host = self.net.get(node)
            try:
                resources = self.topo.calculateRealResources(node)
                host.update_resources(**resources)
            except Exception as err:
                info(err)

    def start(self):
        self.net.start()
        self._update_hosts_resources()

    def stop(self):
        self.net.stop()
