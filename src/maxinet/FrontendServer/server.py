#!/usr/bin/python2

import atexit
import logging
import threading
import time

import Pyro4
import Pyro4.naming

from src.maxinet.tools import MaxiNetConfig

Pyro4.config.SOCK_REUSE = True

class NameServer(object):
    def __init__(self, config=MaxiNetConfig()):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def start(self):
        """Start namserver instance
        """
        Pyro4.config.SERVERTYPE = "thread"
        Pyro4.config.THREADPOOL_SIZE = self.config.get_frontend_threads()

        self._ns_thread = threading.Thread(target=Pyro4.naming.startNSloop,
                                kwargs={
                                    "host": self.config.get_nameserver_ip(),
                                    "port": self.config.get_nameserver_port(),
                                    "hmac": self.config.get_nameserver_password()
                                })
        self._ns_thread.daemon = True
        self._ns_thread.start()
        time.sleep(1)
        atexit.register(self.stop)
        self.config.register()

    def stop(self):
        """Shut down nameserver instance.
        """
        self.config.unregister()


class MaxiNetManager(object):

    """Manager class which manages distribution of workers to clusters.

    The MaxiNetManager class manages the distribution of workers to clusters
    After connecting to the nameserver every Worker registers itself with the
    MaxiNetManager instance. Workers can than be reserved by Clusters to
    to run Experiments on them. The Cluster has to free the Worker if it doesn't
    use it anymore. Note that MaxiNet does not implement any "security" features,
    meaning that there is no mechanism in place to prevent a malicious cluster
    from messing with Workers that are not reserved for it.

    Attributes:
        config: instance of class MaxiNetConfig which is registerd on the
            nameserver and accessible by clusters, experiments and workers.
        logger: logging instance
    """
    def __init__(self, config=MaxiNetConfig()):
        self.config = config
        self._worker_dict = {}
        self._worker_dict_lock = threading.Lock()
        self._ns = None
        self._pyrodaemon = None
        self.logger = logging.getLogger(__name__)
        self.idents = []

        self._monitor_thread = threading.Thread(target=self.monitor_clusters)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()

    @Pyro4.expose
    def register_ident(self, ident):
        """Register identifier on manager.

        To identify a cluster instance when communicating with the MaxiNetManager
        an identifier string is used. The Cluster instance needs to generate
        this string and register it with the Manager.

        Args:
            ident: Identifier string the Cluster instance wants to register

        Returns:
            True if successful, False if identifier is already registered.
        """
        # maybe we should use a lock here
        if not ident in self.idents:
            self.idents.append(ident)
            return True
        else:
            return False

    @Pyro4.expose
    def unregister_ident(self, ident):
        """Unregister identifier.

        Frees up the identifier string of a cluster instance to use by other
        instances. The unregistering instance must not use this string anymore
        when communicating with the Manager if it did not reregister it
        beforehand.

        Args:
            ident: Identifier string to unregister

        Returns:
            True
        """
        if ident in self.idents:
            self.idents.remove(ident)
        return True

    @Pyro4.expose
    def valid_ident(self, ident):
        """Check if identifier is registerd with manager instance.

        Args:
            ident: Identifier to check

        Returns:
            True if identifier is registered, False if not.
        """
        if ident in self.idents:
            return True
        else:
            return False

    @Pyro4.expose
    def monitor_clusters(self):
        """check if the clusters (which allocated workers) are alive
        otherwise, deallocate the workers from the cluster
        """

        print "Monitoring clusters..."

        while(True):
            time.sleep(5)   #we check all 5 seconds.
            clusters = list()
            for worker in self._worker_dict.keys():
                if (self._worker_dict[worker]["assigned"] != None):
                    if (not (self._worker_dict[worker]["assigned"] in clusters)):
                        clusters.append(self._worker_dict[worker]["assigned"])

            #iterate over clusters and check if still alive:
            for cluster in clusters:
                try:
                    alive = False
                    uri = self._ns.lookup(cluster)
                    cluster_instance = Pyro4.Proxy(uri)
                    if(cluster_instance):
                        cluster_instance._pyroHmacKey=self.config.get_nameserver_password()
                        if(cluster_instance.get_status_is_alive()):
                            alive = True
                except Exception as e:
                    pass

                if(not alive):
                    #we just detected that this cluster is no more alive!
                    self.logger.warn("Detected a hung cluster. Freeing workers.")
                    for worker in self._worker_dict.keys():
                        if(self._worker_dict[worker]["assigned"] == cluster):
                            pn = self._worker_dict[worker]["pyroname"]+".mnManager"
                            p = Pyro4.Proxy(self._ns.lookup(pn))
                            p._pyroHmacKey=self.config.get_nameserver_password()
                            p.destroy_mininet()
                            self.free_worker(worker, cluster, True)
                    self.unregister_ident(cluster)

    @Pyro4.expose
    def getStatus(self):
        """ used to check if the frontend server is still alive.
        """
        return True


    def start(self):
        self.logger.debug("starting up and connecting to  %s:%d"
                         % (self.config.get_nameserver_ip(), self.config.get_nameserver_port()))
        #Pyro4.config.HMAC_KEY = self.config.get_nameserver_password()
        self._ns = Pyro4.locateNS(self.config.get_nameserver_ip(), self.config.get_nameserver_port(), hmac_key=self.config.get_nameserver_password())
        #  replace local config with the one from nameserver
        pw = self.config.get_nameserver_password()
        self.config = Pyro4.Proxy(self._ns.lookup("config"))
        self.config._pyroHmacKey=pw
        self._pyrodaemon = Pyro4.Daemon(host=self.config.get_nameserver_ip())
        self._pyrodaemon._pyroHmacKey=self.config.get_nameserver_password()
        uri = self._pyrodaemon.register(self)
        self._ns.register("MaxiNetManager", uri)
        atexit.register(self._stop)
        self.logger.info("startup successful. Waiting for workers to register...")
        self._pyrodaemon.requestLoop()

    def _stop(self):
        self.logger.info("shutting down...")

        #
        # comment back in if the workerservers should shutdown once the frontend is terminated.
        #
        #self._worker_dict_lock.acquire()
        #workers = self._worker_dict.keys()
        #for worker in workers:
        #    pn = self._worker_dict[worker]["pyroname"]
        #    self._worker_dict_lock.release()
        #    p = Pyro4.Proxy(self._ns.lookup(pn))
        #    p._pyroHmacKey=self.config.get_nameserver_password()
        #    p.remoteShutdown()
        #    self._worker_dict_lock.acquire()
        #self._worker_dict_lock.release()
        #while(len(self.get_workers()) > 0):
        #    self.logger.debug("waiting for workers to unregister...")
        #    time.sleep(0.5)
        self._ns.remove("MaxiNetManager")
        self._pyrodaemon.unregister(self)
        self._pyrodaemon.shutdown()

    @Pyro4.expose
    def stop(self):
        """Stop FrontendServer.

        Tries to stop FrontendServer. Fails if there are workers assigned
        to a cluster.

        returns: True if FrontendServer was successfully stopped, False if not
        """
        self._worker_dict_lock.acquire()
        if (len(filter(lambda x: not (x["assigned"] is None),
                       self._worker_dict.values())) > 0):
            self.logger.warn("shutdown not possible as there are still \
                             reserved workers")
            self._worker_dict_lock.release()
            return False
        else:
            self._worker_dict_lock.release()
            self._stop()
            return True

    @Pyro4.expose
    def worker_signin(self, worker_pyroname, worker_hostname):
        """Register Worker with FrontendServer.

        Fails if Worker is already registered.

        Args:
            worker_pyroname: Pyro Identifier of Worker (String)
            worker_hostname: Hostname of Worker
        Returns:
            True if successful, False if not.
        """
        self._worker_dict_lock.acquire()
        if(worker_hostname in self._worker_dict):
            self._worker_dict_lock.release()
            self.logger.warn("failed to register worker %s (pyro: %s) as it is\
                              already registered."
                             % (worker_hostname, worker_pyroname))
            return False
        self._worker_dict[worker_hostname] = {"assigned": None,
                                              "pyroname": worker_pyroname}
        self._worker_dict_lock.release()
        self.logger.info("new worker signed in: %s (pyro: %s)"
                         % (worker_hostname, worker_pyroname))
        return True

    def _is_assigned(self, worker_hostname):
        return not (self._worker_dict[worker_hostname]["assigned"] is None)

    @Pyro4.expose
    def print_worker_status(self):
        numWorkers = len(self._worker_dict)
        out = ""
        out += "MaxiNet Frontend server running at %s\n" % self.config.get_nameserver_ip()
        out += "Number of connected workers: %d\n" % numWorkers
        if numWorkers > 0:
            out += "--------------------------------\n"
        for worker_name in self._worker_dict.keys():
            status = "free"
            if (self._worker_dict[worker_name]["assigned"]):
                status = "assigned to %s" % self._worker_dict[worker_name]["assigned"]
            out += "%s\t\t%s\n" % (worker_name, status)
        return out

    @Pyro4.expose
    def get_worker_status(self, worker_hostname):
        signed_in = False
        assigned = None
        self._worker_dict_lock.acquire()
        if(worker_hostname in self._worker_dict):
            signed_in = True
            assigned = self._worker_dict[worker_hostname]["assigned"]
        self._worker_dict_lock.release()
        return (signed_in, assigned)

    @Pyro4.expose
    def worker_signout(self, worker_hostname):
        """Unregister Worker from FrontendServer.

        Fails if worker is still assigned to a cluster.

        Returns:
            True if successful, False if not.
        """
        self._worker_dict_lock.acquire()
        if(worker_hostname in self._worker_dict):
            if(not self._is_assigned(worker_hostname)):
                del self._worker_dict[worker_hostname]
                self._worker_dict_lock.release()
                self.logger.info("worker signed out: %s" % (worker_hostname))
                return True
            else:
                self._worker_dict_lock.release()
                self.logger.warn("failed to sign out worker %s as it is still \
                                 reserved" % (worker_hostname))
                return False
        self._worker_dict_lock.release()
        return True

    @Pyro4.expose
    def reserve_worker(self, worker_hostname, id):
        """Assign Worker to cluster.

        Fails if worker is already assigned to another cluster.

        Args:
            worker_hostname: Hostname of worker
            id: identifier to identify cluster
        Returns:
            True if successful, False if not.
        """
        self._worker_dict_lock.acquire()
        if(self._is_assigned(worker_hostname)):
            self._worker_dict_lock.release()
            return None
        else:
            if self.valid_ident(id):
                self._worker_dict[worker_hostname]["assigned"] = id
                pyname = self._worker_dict[worker_hostname]["pyroname"]
                self._worker_dict_lock.release()
                self.logger.info("reserved worker %s for id %s"
                                 % (worker_hostname, id))
                return pyname
            else:
                # self._worker_dict_lock.release()
                self.logger.warn("unknown identifier %s encountered. Something is \
                                  not right here." % id)
                return None

    @Pyro4.expose
    def free_worker(self, worker_hostname, id, force=False):
        """Deassign worker from cluster.

        Fails if id is not equal to id provided at assignment call. Can be overriden
        by force flag.

        Args:
            worker_hostname: Hostname of Worker
            id: identifier of cluster
            force: override flag for identifier verification
        """
        self._worker_dict_lock.acquire()
        if((self._worker_dict[worker_hostname]["assigned"] == id) or force):
            self._worker_dict[worker_hostname]["assigned"] = None
            self._worker_dict_lock.release()
            self.logger.info("worker %s was freed" % worker_hostname)
            return True
        else:
            self._worker_dict_lock.release()
            self.logger.warn("failed to free worker %s as it was either not\
                              reserved or not reserved by freeing id %s"
                             % (worker_hostname, id))
            return False

    @Pyro4.expose
    def get_free_workers(self):
        """Get list of unassigned workers"""
        rd = {}
        self._worker_dict_lock.acquire()
        w = filter(lambda x: self._worker_dict[x]["assigned"] is None,
                   self._worker_dict)
        for x in w:
            rd[x] = self._worker_dict[x]
        self._worker_dict_lock.release()
        return rd

    @Pyro4.expose
    def get_workers(self):
        """Get list of all workers"""
        self._worker_dict_lock.acquire()
        w = self._worker_dict.copy()
        self._worker_dict_lock.release()
        return w


def main():
    NameServer().start()
    MaxiNetManager().start()

if(__name__ == "__main__"):
    main()
