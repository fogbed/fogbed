from src.mininet.log import info, error, warn, debug

CPU_PERIOD = 1000000

class NetworkResources (object):

    def __init__(self, emulation_max_cpu=1.0, emulation_max_mem=1024):
        self.e_cpu = emulation_max_cpu
        self.e_mem = emulation_max_mem

        self._resource_models = dict()

        info("Network Resources initiated with max_cpu=%r and max_mem=%r\n" % (self.e_cpu, self.e_mem) )

    def addResourceModel(self, vi, rm):

        if vi in self._resource_models:
            raise Exception("There is already an resource model assigned to this VI.")
        
        self._resource_models[vi] = rm
        rm.net_resources = self
        rm.vis.append(vi)

        info ("Network Resources: added resource model: %r\n" % rm)
    
    @property
    def resource_models(self):
        return list(self._resource_models.itervalues())


class BaseResourceModel (object):

    def __init__(self):
        self.net_resources = None
        self.vis = list()

        info ("Resource model %r initialized\n" % self)
    
    def __repr__(self):
        return self.__class__.__name__

class EdgeResourceModel (BaseResourceModel):
    
    def __init__ (self, max_cu=32, max_mu=1024):
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

        self.allocated_containers[d.name] = d
        self.allocated_resources[d.name] = resources

        self.allocate_cpu(d)
        self.allocate_mem(d)

        self.apply()

    def allocate_cpu(self, d):

        cu = self.allocated_resources[d.name]['cpu']

        if self.alloc_cu + cu > self.max_cu and self.raise_no_cpu_res_left:
            raise NotEnoughResourcesAvailable("Not enough cpu resources left.")

        self.alloc_cu += cu

    def allocate_mem(self, d):

        mu = self.allocated_resources[d.name]['mem']

        if self.alloc_mu + mu > self.max_mu and self.raise_no_mem_res_left:
            raise NotEnoughResourcesAvailable("Not enough memory resources left.")

        self.alloc_mu += mu

    def free(self, d):

        self.allocated_containers.pop(d.name, None)
        resources = self.allocated_resources.pop(d.name, {"cpu": 0, "mem": 0})

        self.free_cpu(d, resources)
        self.free_mem(d, resources)

        self.apply()

    def free_cpu(self, d, resources):
        self.alloc_cu -= resources['cpu']

    def free_mem(self, d, resources):
        self.alloc_mu -= resources['mem']

    def apply(self):

        for d in self.allocated_containers.itervalues():
            self.apply_cpu(d)
            self.apply_mem(d)

    def apply_cpu(self, d):
        n_cu = self.allocated_resources[d.name]['cpu']
        
        self.single_cu = self.compute_single_cu()

        cpu_time_percentage = self.single_cu * n_cu

        cpu_period, cpu_quota = self.calculate_cpu_cfs_values(cpu_time_percentage)

        if d.resources['cpu_period'] != cpu_period or d.resources['cpu_quota'] != cpu_quota:
            debug("Setting CPU limit for %r: cpu_period = %r cpu_quota = %r\n" % (d.name, cpu_period, cpu_quota))
            d.updateCpuLimit(cpu_period=int(cpu_period), cpu_quota=int(cpu_quota))

    def apply_mem(self, d):

        n_mu = self.allocated_resources[d.name]['mem']

        e_mem = self.net_resources.e_mem

        self.single_mu = float(e_mem) / sum([rm.max_mu for rm in list(self.net_resources.resource_models)])

        mem_limit = self.single_mu * n_mu
        mem_limit = self.calculate_mem_value(mem_limit)

        if d.resources['mem_limit'] != mem_limit:
            debug("Setting MEM limit for %r: mem_limit = %f MB\n" % (d.name, mem_limit/1024/1024))
            d.updateMemoryLimit(mem_limit=mem_limit)
    
    def calculate_cpu_cfs_values (self, cpu_time_percentage):

        cpu_period = CPU_PERIOD

        cpu_quota = cpu_period * cpu_time_percentage
        if cpu_quota < 1000:
            cpu_quota = 1000
            warn("Increased CPU quota to avoid system error")
        
        return cpu_period, cpu_quota
    
    def compute_single_cu(self):
        
        e_cpu = self.net_resources.e_cpu
        return float(e_cpu) / sum([rm.max_cu for rm in list(self.net_resources.resource_models)]) * self.cpu_op_factor
    
    def calculate_mem_value(self, mem_limit):

        if mem_limit < 4:
            mem_limit = 4
            warn("Increased MEM limit because it was less the 4 MB")
        
        return int(mem_limit*1024*1024)


class FogResourceModel (EdgeResourceModel):
    
    def __init__(self, *args, **kwargs):

        super(FogResourceModel, self).__init__(*args, **kwargs)
        self.raise_no_cpu_res_left = False

    def compute_single_cu(self):

        e_cpu = self.net_resources.e_cpu

        self.cpu_op_factor = float(self.max_cu) / (max(self.max_cu, self.alloc_cu))

        return float(e_cpu) / sum([rm.max_cu for rm in list(self.net_resources.resource_models)])

class CloudResourceModel(FogResourceModel):

    def __init__(self, *args, **kwargs):
        super(CloudResourceModel, self).__init__(*args, **kwargs)




class NotEnoughResourcesAvailable(BaseException):
    pass