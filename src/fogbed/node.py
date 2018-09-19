from src.fogbed.resourcemodel import PREDEFINED_RESOURCES
from src.mininet.log import debug, info


class VirtualInstance(object):
    _COUNTER = 1

    def __init__(self, label, topo=None, resources_table=None):
        # self.name = "vi%d" % VirtualInstance._COUNTER
        self.name = label
        VirtualInstance._COUNTER += 1

        self.topo = topo
        self.label = label
        self.res_table = resources_table
        self.containers = {}
        self.allocated_resources = {}
        self.resource_model = None
        self.switch = self.topo.addSwitch("%s.s1" % self.name)

        debug("created data center switch: %s\n" % str(self.switch))

    def __repr__(self):
        return self.label

    def addDocker(self, name, resources=None, **params):
        resources = resources if resources else PREDEFINED_RESOURCES['small']

        new_name = "%s.%s" % (self.name, name)

        d = self.topo.addDocker(new_name, virtual_instance=self.name, resources=resources, **params)

        self.topo.addLink(d, self.switch)

        self.containers[name] = d
        self.allocated_resources[name] = resources

        if self.res_table:
            self.res_table.provideResources(self, d, resources)
        #
        # if self.resource_model is not None:
        #     try:
        #         self.resource_model.allocate(d, resources)
        #     except NotEnoughResourcesAvailable as ex:
        #         info(ex.message)
        #         self.net.removeDocker(new_name)
        #         return None

        return d

    def getSwitch(self):
        return self.switch

    def removeDocker(self, name, **params):
        new_name = "%s.%s" % (self.name, name)

        d = self.containers.pop(name, None)
        resources = self.allocated_resources.pop(name, None)

        self.topo.removeLink(node1=d, node2=self.switch)

        self.resource_model.free(d, resources)

        return self.topo.removeDocker(new_name, **params)

    def assignResourceModel(self, resource_model):
        if self.resource_model is not None:
            raise Exception("There is already an resource model assigned to this VI.")
        self.resource_model = resource_model
        self.res_table.addResourceModel(self, resource_model)
        info("Assigned RM: %r to VI: %r\n" % (self.resource_model, self))
