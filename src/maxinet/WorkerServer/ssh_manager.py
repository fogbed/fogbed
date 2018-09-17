import atexit
import os
import subprocess

import Pyro4


class SSH_Manager(object):

    def __init__(self, folder, ip, port, user):
        self.folder = folder
        self.port = port
        self.popen = None
        subprocess.call(["chown", ":%s" % user, folder])
        subprocess.call(["chmod", "g+xr", folder])
        if not self._folder_is_initialized():
            self.initialize_ssh_folder(ip, port, user)

    def _folder_is_initialized(self):
        if (os.path.exists(os.path.join(self.folder, "sshd_config")) and
           os.path.exists(os.path.join(self.folder, "authorized_keys")) and
           os.path.exists(os.path.join(self.folder, "ssh_host_rsa_key"))):
            return True
        return False

    def _write_sshd_config(self, ip, port, user, template=None):
        if template is None:
            template = os.path.abspath(os.path.dirname(os.path.abspath(__file__))
                                                       + os.sep
                                                       + "sshd_config.template")
        with open(template, "r") as f_template:
            content = f_template.read()
        content = content.replace("<!IP!>", ip)
        content = content.replace("<!USER!>", user)
        content = content.replace("<!PORT!>", str(port))
        content = content.replace("<!FOLDER!>", self.folder)
        with open(os.path.join(self.folder, "sshd_config"), "w") as fn:
            fn.write(content)

    @Pyro4.expose
    def add_key(self, key):
        with open(os.path.join(self.folder, "authorized_keys"), "a") as fn:
            fn.write("\n%s" % (key,))

    @Pyro4.expose
    def has_key(self, key):
        with open(os.path.join(self.folder, "authorized_keys"), "r") as fn:
            content = fn.read()
        if content.count(key) > 0:
            return True
        return False

    @Pyro4.expose
    def remove_key(self, key):
        with open(os.path.join(self.folder, "authorized_keys"), "r") as fn:
            content = fn.read()
        content = content.replace("key", "")
        with open(os.path.join(self.folder, "authorized_keys"), "w") as fn:
            fn.write(content)

    @Pyro4.expose
    def remove_all_keys(self):
        with open(os.path.join(self.folder, "authorized_keys"), "w") as fn:
            fn.write("")

    def _generate_host_key(self):
        subprocess.call(["ssh-keygen", "-q", "-N", "", "-t", "rsa", "-f",
                         os.path.join(self.folder, "ssh_host_rsa_key")])

    @Pyro4.expose
    def get_host_key_fingerprint(self):
        return subprocess.check_output(["ssh-keygen", "-l", "-f",
                                        os.path.join(self.folder, "ssh_host_rsa_key")]).strip()

    @Pyro4.expose
    def initialize_ssh_folder(self, ip, port, user):
        self._write_sshd_config(ip, port, user)
        subprocess.call(["touch", os.path.join(self.folder, "authorized_keys")])
        self._generate_host_key()

    @Pyro4.expose
    def start_sshd(self):
        #kill the process that might listen on MaxiNets sshd port:
        r = subprocess.call(["sudo", "fuser", "-k", "-n", "tcp", "%s" % self.port])
        if(r == 0):
            print "Killed a process that listened on port %s in order to start MaxiNets sshd." % self.port
        self.popen = subprocess.Popen(["/usr/sbin/sshd", "-D",
                                       "-f",
                                       os.path.join(self.folder, "sshd_config")
                                       ],
                                      stdin=subprocess.PIPE,
                                      stdout=open("/dev/null", "w"))
        atexit.register(self.terminate_sshd)

    @Pyro4.expose
    def sshd_running(self):
        if(self.popen):
            if(self.popen.poll() is None):
                return True
        return False

    @Pyro4.expose
    def terminate_sshd(self):
        if(self.sshd_running()):
            self.popen.terminate()
