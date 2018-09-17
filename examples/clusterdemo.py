#!/usr/bin/python

"clusterdemo.py: demo of Mininet Cluster Edition prototype"

from src.mininet.examples import MininetCluster, SwitchBinPlacer
from src.mininet.topolib import TreeTopo
from src.mininet.log import setLogLevel
from src.mininet.examples import ClusterCLI as CLI

def demo():
    "Simple Demo of Cluster Mode"
    servers = [ 'localhost', 'ubuntu2', 'ubuntu3' ]
    topo = TreeTopo( depth=3, fanout=3 )
    net = MininetCluster( topo=topo, servers=servers,
                          placement=SwitchBinPlacer )
    net.start()
    CLI( net )
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    demo()
