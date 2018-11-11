#!/usr/bin/python2

import argparse
import atexit
import logging
import os
import signal
import subprocess
import sys
import tempfile
import time

from src.mininet.node import UserSwitch, OVSSwitch
from src.mininet.link import Link, TCIntf, Intf

import src.mininet.term
import Pyro4
import threading
import traceback

from src.maxinet.tools import Tools, MaxiNetConfig
from src.maxinet.WorkerServer.ssh_manager import SSH_Manager

try:
    from src.mininet.net import Containernet as Mininet
except ImportError:
    from src.mininet.net import Mininet

class WorkerServer(object):
    """Manages the Worker

    The WorkerServer class connects to the nameserver and registers
    itself with the MaxiNetManager instance. It is used by the Cluster instances
    to start mininet instances, manage the ssh daemon and run commands etc.

    Attributes:
        logger: logging instance
        mnManager: instance of class MininetManager which is used to create mininet
            instances
        sshManager: instance of class SSH_Manager which is used to manage the ssh
            daemon.
        ssh_folder: folder which holds configuration files for the ssh daemon.
        ip: ip address of Worker
    """
    def __init__(self):
        self._ns = None
        self._pyrodaemon = None
        self.logger = logging.getLogger(__name__)
        self._manager = None
        self.mnManager = MininetManager()
        self.sshManager = None
        self.ssh_folder = tempfile.mkdtemp()
        atexit.register(subprocess.call, ["rm", "-rf", self.ssh_folder])
        logging.basicConfig(level=logging.DEBUG)
        self.ip = None
        self._shutdown = False
        #Pyro4.config.COMMTIMEOUT = 2

        #for frontend
        self._ip = None
        self._port = None
        self._password = None

        self._looping_thread = None


    def exit_handler(self, signal, frame):
        # I have absolutely no clue why but without this print atexit sometimes
        # doesn't seem to wait for called functions to finish...
        print "exiting..."
        self._shutdown = True
        sys.exit()

    @Pyro4.expose
    def monitorFrontend(self):
        """ function to monitor if the frontend is still alive.
            if not, try to reconnect.
        """
        while(not self._shutdown):
            try:
                self._manager.getStatus()
            except:
                if self._ip != None:
                    #self.ip as an indicator that this worker was connected to the frontend once.
                    print "Trying to reconnect to FrontendServer..."
                    try:
                        try:
                            self._pyrodaemon.unregister(self)
                        except:
                            pass
                        try:
                            self._pyrodaemon.unregister(self.mnManager)
                        except:
                            pass
                        try:
                            self._pyrodaemon.unregister(self.sshManager)
                        except:
                            pass
                        try:
                            self._pyrodaemon.shutdown()
                        except:
                            pass
                        try:
                            self._pyrodaemon.close()
                        except:
                            pass
                        self.start(self._ip, self._port, self._password)
                    except Exception as e:
                        traceback.print_exc(e)
                        pass
                pass
            time.sleep(5)

    @Pyro4.expose
    def start(self, ip, port, password, retry=float("inf")):
        """Start WorkerServer and ssh daemon and connect to nameserver."""

        self.logger.info("Cleaning previously created interfaces...")
        print subprocess.check_output(["mn", "-c"]).strip()

        self.logger.info("starting up and connecting to  %s:%d"
                         % (ip, port))

        #store for reconnection attempts
        self._ip = ip
        self._port = port
        self._password = password

        #Pyro4.config.HMAC_KEY = password
        tries=1
        self._ns = None
        while not self._ns:
            try:
                self._ns = Pyro4.locateNS(ip, port, hmac_key=password)
            except Pyro4.errors.NamingError:
                if tries < retry:
                    self.logger.warn("Unable to locate Nameserver. Trying again in 5 seconds...")
                    time.sleep(5)
                    tries += 1
                else:
                    self.logger.error("Unable to locate Nameserver.")
                    sys.exit()
        self.config = Pyro4.Proxy(self._ns.lookup("config"))
        self.config._pyroHmacKey=password
        self.ip = self.config.get_worker_ip(self.get_hostname())
        if(not self.ip):
            self.ip = Tools.guess_ip()
            if not self.config.has_section(self.get_hostname()):
                self.config.add_section(self.get_hostname())
            self.config.set(self.get_hostname(), "ip", self.ip)
            self.logger.warn("""FrontendServer did not know IP of this host (check configuration for hostname).
                             Guessed: %s""" % self.ip)
        self.logger.info("configuring and starting ssh daemon...")
        self.sshManager = SSH_Manager(folder=self.ssh_folder, ip=self.ip, port=self.config.get_sshd_port(), user=self.config.get("all", "sshuser"))
        self.sshManager.start_sshd()
        self._pyrodaemon = Pyro4.Daemon(host=self.ip)
        self._pyrodaemon._pyroHmacKey=password
        uri = self._pyrodaemon.register(self)
        self._ns.register(self._get_pyroname(), uri)
        uri = self._pyrodaemon.register(self.mnManager)
        self._ns.register(self._get_pyroname()+".mnManager", uri)
        uri = self._pyrodaemon.register(self.sshManager)
        self._ns.register(self._get_pyroname()+".sshManager", uri)
        atexit.register(self._stop)
        self.logger.info("looking for manager application...")
        manager_uri = self._ns.lookup("MaxiNetManager")
        if(manager_uri):
            self._manager = Pyro4.Proxy(manager_uri)
            self._manager._pyroHmacKey=self._password
            self.logger.info("signing in...")
            if(self._manager.worker_signin(self._get_pyroname(), self.get_hostname())):
                self.logger.info("done. Entering requestloop.")
                self._started = True
                self._looping_thread = threading.Thread(target=self._pyrodaemon.requestLoop)
                self._looping_thread.daemon = True
                self._looping_thread.start()
            else:
                self.logger.error("signin failed.")
        else:
            self.logger.error("no manager found.")

    def _get_pyroname(self):
        return "MaxiNetWorker_%s" % self.get_hostname()

    @Pyro4.expose
    def get_hostname(self):
        return subprocess.check_output(["hostname"]).strip()

    def _stop(self):
        self.logger.info("signing out...")
        if(self._manager):
            self._manager.worker_signout(self.get_hostname())
        self.logger.info("shutting down...")
        self._ns.remove(self._get_pyroname())
        self._ns.remove(self._get_pyroname()+".mnManager")
        self._pyrodaemon.unregister(self)
        self._pyrodaemon.unregister(self.mnManager)
        self._pyrodaemon.unregister(self.sshManager)
        self._pyrodaemon.shutdown()
        self._pyrodaemon.close()

    @Pyro4.expose
    def remoteShutdown(self):
        self._pyrodaemon.shutdown()


    @Pyro4.expose
    def stop(self):
        (signedin, assigned) = self._manager.get_worker_status(self.get_hostname())
        if(assigned):
            self.logger.warn("can't shut down as worker is still assigned to id %d" % assigned)
            return False
        else:
            self._stop()
            return True

    @Pyro4.expose
    def check_output(self, cmd):
        """Run cmd on Worker and return output

        Args:
            cmd: command to call with optional parameters

        Returns:
            Shell output of command
        """
        self.logger.debug("Executing %s" % cmd)
        return subprocess.check_output(cmd, shell=True,
                                       stderr=subprocess.STDOUT).strip()

    @Pyro4.expose
    def script_check_output(self, cmd):
        """Call MaxiNet Script and return output

        Args:
            cmd: name of script to call
        Returns:
            Shell output of script
        """
        # Prefix command by our worker directory
        cmd = Tools.get_script_dir() + cmd
        return self.check_output(cmd)

    @Pyro4.expose
    def run_cmd(self, command):
        """Call command (blocking)

        Args:
            command: command to call with optional parameters
        """
        subprocess.call(command, shell=True)

    @Pyro4.expose
    def daemonize(self, cmd):
        """Call command (non-blocking)

        Args:
            command: command to call with optional parameters
        """
        p = subprocess.Popen(cmd, shell=True)
        atexit.register(p.terminate)

    @Pyro4.expose
    def daemonize_script(self, script, args):
        """Call MaxiNet Script (non-blocking)

        Args:
            cmd: name of script to call
        """
        cmd = Tools.get_script_dir()+script+" "+args
        p = subprocess.Popen(cmd, shell=True)
        atexit.register(p.terminate)


class TCLinkParams(Link):
    """Link with symmetric TC interfaces

    Like the mininet TCLink class but with support of the params1
    and params2 arguments.
    """

    def __init__(self, node1, node2, port1=None, port2=None,
                 intfName1=None, intfName2=None,
                 addr1=None, addr2=None, params1=None,
                 params2=None, **kvargs):
        Link.__init__(self, node1, node2, port1=port1, port2=port2,
                      intfName1=intfName1, intfName2=intfName2,
                      cls1=TCIntf,
                      cls2=TCIntf,
                      addr1=addr1, addr2=addr2,
                      params1=params1,
                      params2=params2)


class MininetManager(object):

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.net = None

    @Pyro4.expose
    def create_mininet(self, topo, tunnels=None,  switch=UserSwitch,
                       controller=None, STT=False, mininet_cls=Mininet):

        tunnels = tunnels if tunnels else []
        if(not self.net is None):
            self.logger.warn("running mininet instance detected!\
                              Shutting it down...")
            self.destroy_mininet()

        self.logger.info("Creating mininet instance")
        try:
            if controller:
                self.net = mininet_cls(topo=topo, intf=TCIntf, link=TCLinkParams,
                                   switch=switch, controller=controller)
            else:
                self.net = mininet_cls(topo=topo, intf=TCIntf, link=TCLinkParams,
                                   switch=switch)
        except Exception, e:
            self.logger.error("Failed to create mininet instance: %s" % traceback.format_exc())
            raise e
        if STT:
            self.logger.info("Starting Mininet...")
            self.net.start()
        self.logger.info("Adding tunnels to mininet instance")
        for tunnel in tunnels:
            port = None
            cls = None
            print(tunnel)
            if "node1" not in tunnel[2].keys():
               self.logger.info("Error! node1 is missing in tunnel metadata")
            if tunnel[2]["node1"] in topo.nodes():
               port = tunnel[2]["port1"]
            else:
               port = tunnel[2]["port2"]

            if "cls" in tunnel[2].keys():
                cls = tunnel[2]["cls"]
                del tunnel[2]["cls"]
            self.addTunnel(tunnel[0], tunnel[1], port, cls, STT=STT, **tunnel[2])
        if not STT:
            self.logger.info("Starting {}...".format(mininet_cls.__name__))
            self.net.start()
        self.logger.info("Startup complete.")
        self.x11popens = []
        return True

    @Pyro4.expose
    def destroy_mininet(self):
        """shut down mininet instance"""
        if self.net:
            for popen in self.x11popens:
                popen.terminate()
                popen.communicate()
                popen.wait()
            self.net.stop()
            self.logger.info("mininet instance terminated")
            self.net = None

    @Pyro4.expose
    def configLinkStatus(self, src, dst, status):
        self.net.configLinkStatus(src, dst, status)

    @Pyro4.expose
    def rpc(self, hostname, cmd, *params1, **params2):
        h = self.net.get(hostname)
        return getattr(h, cmd)(*params1, **params2)

    @Pyro4.expose
    def attr(self, hostname, name):
        h = self.net.get(hostname)
        return getattr(h, name)

    @Pyro4.expose
    def addHost(self, name, cls=None, **params):
        self.net.addHost(name, cls, **params)
        return name

    @Pyro4.expose
    def addSwitch(self, name, cls=None, **params):
        self.net.addSwitch(name, cls, **params)
        #TODO: This should not be done here
        self.net.get(name).start(self.net.controllers)
        return name

    @Pyro4.expose
    def addController(self, name="c0", controller=None, **params):
        self.net.addController(name, controller, **params)
        return name

    @Pyro4.expose
    def addTunnel(self, name, switch, port, intf, STT=False, **params):
        switch_i = self.net.get(switch)
        print(intf, params)
        if not intf or not isinstance(intf, Intf):
            intf = TCIntf
        if STT:
            subprocess.check_output(["ovs-vsctl","add-port", switch, name])
        else:
            intf(name, node=switch_i, port=port, link=None, **params)

    @Pyro4.expose
    def tunnelX11(self, node, display):
        node = self.net.get(node)
        from src import mininet
        (tunnel, popen) = mininet.term.tunnelX11(node, display)
        self.x11popens.append(popen)

    @Pyro4.expose
    def addLink(self, node1, node2, port1=None, port2=None, cls=None,
                **params):
        node1 = self.net.get(node1)
        node2 = self.net.get(node2)
        l = self.net.addLink(node1, node2, port1, port2, cls, **params)
        return ((node1.name, l.intf1.name), (node2.name, l.intf2.name))


    @Pyro4.expose
    def runCmdOnHost(self, hostname, command, noWait=False):
        '''
            e.g. runCmdOnHost('h1', 'ifconfig')
        '''
        h1 = self.net.get(hostname)
        if noWait:
            return h1.sendCmd(command)
        else:
            return h1.cmd(command)


def getFrontendStatus():
    config = MaxiNetConfig(register=False)
    ip = config.get_nameserver_ip()
    port = config.get_nameserver_port()
    pw = config.get_nameserver_password()
    ns = Pyro4.locateNS(ip, port, hmac_key=pw)
    manager_uri = ns.lookup("MaxiNetManager")
    if(manager_uri):
        manager = Pyro4.Proxy(manager_uri)
        manager._pyroHmacKey=pw
        print manager.print_worker_status()
    else:
        print "Could not contact Frontend server at %s:%s" % (ip, port)


def main():
    parser = argparse.ArgumentParser(description="Fogbed Worker which hosts a mininet instance")
    parser.add_argument("--ip", action="store", help="Frontend Server IP")
    parser.add_argument("--port", action="store", help="Frontend Server Port", type=int)
    parser.add_argument("--password", action="store", help="Frontend Server Password")
    parser.add_argument("-c", "--config", metavar="FILE", action="store", help="Read configuration from FILE")
    parsed = parser.parse_args()

    ip = False
    port = False
    pw = False
    if (parsed.config or
            os.path.isfile("MaxiNet.cfg") or
            os.path.isfile(os.path.expanduser("~/.MaxiNet.cfg")) or
            os.path.isfile("/etc/MaxiNet.cfg")):
        if parsed.config:
            config = MaxiNetConfig(file=parsed.config,register=False)
        else:
            config = MaxiNetConfig(register=False)
        ip = config.get_nameserver_ip()
        port = config.get_nameserver_port()
        pw = config.get_nameserver_password()
    if parsed.ip:
        ip = parsed.ip
    if parsed.port:
        port = parsed.port
    if parsed.password:
        pw = parsed.password

    if os.getuid() != 0:
        print "FogbedWorker must run with root privileges!"
        sys.exit(1)

    if not (ip and port and pw):
        print "Please provide maxinet.cfg or specify ip, port and password of \
               the Frontend Server."
    else:
        workerserver = WorkerServer()

        signal.signal(signal.SIGINT, workerserver.exit_handler)

        workerserver.start(ip=ip, port=port, password=pw)
        workerserver.monitorFrontend()



if(__name__ == "__main__"):
    main()
