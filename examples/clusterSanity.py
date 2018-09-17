#!/usr/bin/env python

'''
A sanity check for cluster edition
'''

from src.mininet.examples import MininetCluster
from src.mininet.log import setLogLevel
from src.mininet.examples import ClusterCLI as CLI
from src.mininet.topo import SingleSwitchTopo

def clusterSanity():
    "Sanity check for cluster mode"
    topo = SingleSwitchTopo()
    net = MininetCluster( topo=topo )
    net.start()
    CLI( net )
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    clusterSanity()
