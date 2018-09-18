from src.maxinet.Frontend.maxinet_main import Experiment, Cluster
from src.maxinet.WorkerServer.server import TCLinkParams
from src.mininet.link import TCIntf
from src.mininet.net import Fogbed
from src.mininet.node import UserSwitch, Controller


class FogbedDistributedExperiment(object):

    def __init__(self, topology, controller=Controller, switch=UserSwitch,
                 nodemapping=None, hostnamemapping=None, sharemapping=None,
                 minworkers=None, maxworkers=None):
        cluster = Cluster(minWorkers=minworkers, maxWorkers=maxworkers)
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

    def start(self):
        self.exp.setup()

    def stop(self):
        self.exp.stop()


class FogbedExperiment(object):

    def __init__(self, topology, controller=Controller, switch=UserSwitch):
        self.net = Fogbed(topo=topology, intf=TCIntf, link=TCLinkParams,
                          switch=switch, controller=controller)

    def __getattr__(self, item):
        return getattr(self.net, item)

    def start(self):
        self.net.start()

    def stop(self):
        self.net.stop()
