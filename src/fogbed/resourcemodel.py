from src.mininet.log import info, warn

CPU_PERIOD = 1000000

PREDEFINED_RESOURCES = {
    "tiny": {"cu": 0.5, "mu": 32},
    "small": {"cu": 1, "mu": 128},
    "medium": {"cu": 4, "mu": 256},
    "large": {"cu": 8, "mu": 512},
    "xlarge": {"cu": 16, "mu": 1024},
    "xxlarge": {"cu": 32, "mu": 2048}
}


class ResourcesTable(object):

    def __init__(self, emulation_max_cpu=1.0, emulation_max_mem=2048):
        self.e_cpu = emulation_max_cpu
        self.e_mem = emulation_max_mem

        self._resource_models = dict()
        self._allocated_resources = dict()
        self._device_to_vi = dict()

        info("Network Resources initiated with max_cpu=%r and max_mem=%r\n" % (self.e_cpu, self.e_mem))

    def addResourceModel(self, vi, rm):
        if vi in self._resource_models:
            raise Exception("There is already an resource model assigned to this VI.\n")

        self._resource_models[vi] = rm
        rm.setResourcesTable(self)
        rm.vis.append(vi)

        info("Network Resources: added resource model: %r\n" % rm)

    def provideResources(self, vi, d, resources):

        if vi in self._allocated_resources:
            self._allocated_resources[vi][d] = resources
        else:
            self._allocated_resources[vi] = {
                d: resources
            }

        self._device_to_vi[d] = vi

        info("Resources %s provided to device %s in VI %s\n" % (resources, d, vi))

    def calculateRealResources(self, d):
        if d not in self._device_to_vi:
            raise Exception("No resources assigned to %s\n" % d)

        vi = self._device_to_vi[d]

        resource_model = self._resource_models[vi]

        resources = self._allocated_resources[vi][d]

        resource_model.allocate(d, resources)

        cpu_period, cpu_quota = resource_model.real_cpu(resources['cu'])
        mem_limit = resource_model.real_mem(resources['mu'])

        return {'cpu_period': cpu_period, 'cpu_quota': cpu_quota, 'mem_limit': mem_limit, 'memswap_limit': -1}

    @property
    def resource_models(self):
        return list(self._resource_models.itervalues())


class BaseResourceModel(object):

    def __init__(self):
        self.res_table = None
        self.vis = list()

        info("Resource model %r initialized\n" % self)

    def setResourcesTable(self, res_table):
        self.res_table = res_table

    def __repr__(self):
        return self.__class__.__name__


class EdgeResourceModel(BaseResourceModel):

    def __init__(self, max_cu=32, max_mu=1024):
        super(EdgeResourceModel, self).__init__()

        self.max_cu = max_cu
        self.max_mu = max_mu

        self.alloc_cu = 0
        self.alloc_mu = 0

        self.cpu_op_factor = 1.0
        self.mem_op_factor = 1.0

        self.allocated_containers = {}
        self.allocated_resources = {}

        self.raise_no_cpu_res_left = True
        self.raise_no_mem_res_left = True

    def allocate(self, d, resources):

        self.allocated_resources[d] = resources

        self.allocate_cpu(resources['cu'])
        self.allocate_mem(resources['mu'])

    def allocate_cpu(self, cu):

        cu = float(cu)

        if self.alloc_cu + cu > self.max_cu and self.raise_no_cpu_res_left:
            raise NotEnoughResourcesAvailable("Not enough cpu resources left.")

        self.alloc_cu += cu

    def allocate_mem(self, mu):

        mu = float(mu)

        if self.alloc_mu + mu > self.max_mu and self.raise_no_mem_res_left:
            raise NotEnoughResourcesAvailable("Not enough memory resources left.")

        self.alloc_mu += mu

    def free(self, d):

        resources = self.allocated_resources.pop(d, {"cu": 0, "mu": 0})

        self.free_cpu(resources['cu'])
        self.free_mem(resources['mu'])

    def free_cpu(self, cu):
        self.alloc_cu -= float(cu)

    def free_mem(self, mu):
        self.alloc_mu -= float(mu)

    def real_cpu(self, cu):

        cu = float(cu)

        self.single_cu = self.compute_single_cu()

        cpu_time_percentage = self.single_cu * cu

        cpu_period, cpu_quota = self.calculate_cpu_cfs_values(cpu_time_percentage)

        return int(cpu_period), int(cpu_quota)

    def real_mem(self, mu):

        mu = float(mu)

        e_mem = self.res_table.e_mem

        self.single_mu = float(e_mem) / sum([rm.max_mu for rm in list(self.res_table.resource_models)])

        mem_limit = self.single_mu * mu
        mem_limit = self.calculate_mem_value(mem_limit)

        return int(mem_limit)

    # def apply(self):
    #
    #     for d in self.allocated_containers.itervalues():
    #         self.apply_cpu(d)
    #         self.apply_mem(d)

    # def apply_cpu(self, d):
    #     n_cu = self.allocated_resources[d.name]['cpu']
    #
    #     self.single_cu = self.compute_single_cu()
    #
    #     cpu_time_percentage = self.single_cu * n_cu
    #
    #     cpu_period, cpu_quota = self.calculate_cpu_cfs_values(cpu_time_percentage)
    #
    #     if d.resources['cpu_period'] != cpu_period or d.resources['cpu_quota'] != cpu_quota:
    #         debug("Setting CPU limit for %r: cpu_period = %r cpu_quota = %r\n" % (d.name, cpu_period, cpu_quota))
    #         d.updateCpuLimit(cpu_period=int(cpu_period), cpu_quota=int(cpu_quota))
    #
    # def apply_mem(self, d):
    #
    #     n_mu = self.allocated_resources[d.name]['mem']
    #
    #     e_mem = self.res_table.e_mem
    #
    #     self.single_mu = float(e_mem) / sum([rm.max_mu for rm in list(self.res_table.resource_models)])
    #
    #     mem_limit = self.single_mu * n_mu
    #     mem_limit = self.calculate_mem_value(mem_limit)
    #
    #     if d.resources['mem_limit'] != mem_limit:
    #         debug("Setting MEM limit for %r: mem_limit = %f MB\n" % (d.name, mem_limit / 1024 / 1024))
    #         d.updateMemoryLimit(mem_limit=mem_limit)

    def calculate_cpu_cfs_values(self, cpu_time_percentage):

        cpu_period = CPU_PERIOD

        cpu_quota = cpu_period * cpu_time_percentage
        if cpu_quota < 1000:
            cpu_quota = 1000
            warn("Increased CPU quota to avoid system error")

        return cpu_period, cpu_quota

    def compute_single_cu(self):

        e_cpu = self.res_table.e_cpu
        return float(e_cpu) / sum([rm.max_cu for rm in list(self.res_table.resource_models)]) * self.cpu_op_factor

    def calculate_mem_value(self, mem_limit):

        if mem_limit < 4:
            mem_limit = 4
            warn("Increased MEM limit because it was less the 4 MB")

        return int(mem_limit * 1024 * 1024)


class FogResourceModel(EdgeResourceModel):

    def __init__(self, *args, **kwargs):
        super(FogResourceModel, self).__init__(*args, **kwargs)
        self.raise_no_cpu_res_left = False

    def compute_single_cu(self):
        e_cpu = self.res_table.e_cpu

        self.cpu_op_factor = float(self.max_cu) / (max(self.max_cu, self.alloc_cu))

        return float(e_cpu) / sum([rm.max_cu for rm in list(self.res_table.resource_models)])


class CloudResourceModel(FogResourceModel):

    def __init__(self, *args, **kwargs):
        super(CloudResourceModel, self).__init__(*args, **kwargs)


class NotEnoughResourcesAvailable(BaseException):
    pass
