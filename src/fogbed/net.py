from src.fogbed.node import VirtualInstance
from src.mininet.log import info
from src.mininet.net import Containernet


class Fogbed(Containernet):
    """
    A Containernet with virtual instances related methods.
    Inherits Containernet.
    """

    def __init__(self, **params):
        Containernet.__init__(self, **params)

        self.vinsts = {}

    def addVirtualInstance(self, label):

        if label in self.vinsts:
            raise Exception('Virtual Instance label already exists: %s' % label)

        if ' ' in label:
            label = self.removeSpace(label)
            info("Replacing label empty spaces, new label: %s" % label)

        vi = VirtualInstance(label, self)
        self.vinsts[label] = vi
        info("added virtual instance: %s\n" % label)
        return vi

    def addLink(self, node1, node2, **params):

        assert node1 is not None
        assert node2 is not None

        if isinstance(node1, VirtualInstance):
            node1 = node1.switch

        if isinstance(node2, VirtualInstance):
            node2 = node2.switch

        return Containernet.addLink(self, node1, node2, **params)

    def removeLink(self, node1=None, node2=None):

        assert node1 is not None
        assert node2 is not None

        if isinstance(node1, VirtualInstance):
            node1 = node1.switch

        if isinstance(node2, VirtualInstance):
            node2 = node2.switch

        return Containernet.removeLink(self, node1=node1, node2=node2)

    @classmethod
    def removeSpace(name):
        return name.replace(' ', '_')
