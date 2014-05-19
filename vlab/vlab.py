"""
This is the main object of this app

It instantiates VmConfigLoader and creates the nodes that are then started
"""

import socket

from vmconfig import VmConfigLoader
from vmhandler import VmHandler
from node import Switch, Host


class Vlab(object):
    """Network emulation with hosts spawned in Qemu"""
    LISTEN_PORT = 20000
    BACKLOG = 10

    def __init__(self):
        self.vm_config_loader = VmConfigLoader()
        self.configs = []
        self.topo = {}
        self.hosts = []
        self.switches = []

        self.notifysocket = None
        self.start_boot_listener()
        self.name_to_host = {}

        self.init_configs()

    def start_boot_listener(self):
        """Creates a socket to listen for boot signal"""
        self.notifysocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.notifysocket.bind(('0.0.0.0', Vlab.LISTEN_PORT))
        self.notifysocket.listen(Vlab.BACKLOG)

    def start_all(self):
        """Start All the VMs"""
        for i in xrange(len(self.configs)):
            self.start_vm_at(i)
        for s in self.switches:
            s.start()

        booted = 0
        while booted < len(self.configs):
            client, addr = self.notifysocket.accept()
            booted += 1

            message = client.recv(128)
            client.close()

            msgparams = message.split(" ")
            vmname = msgparams[0]
            for vm in self.hosts:
                if vm.get_hostname() == vmname:
                    vm.configure_interfaces()

            print message,

    def stop_all(self):
        """Stop All the VMs"""
        for i in xrange(len(self.configs)):
            self.stop_vm_at(i)
        for s in self.switches:
            s.stop()

    def init_configs(self):
        """Read and init the configs"""
        self.vm_config_loader.read_config()
        self.vm_config_loader.create_vm_configs()
        self.configs = self.vm_config_loader.get_configs()
        self.topo = self.vm_config_loader.get_topo_config()
        self._create_hosts()
        self._create_switches()

    def _create_hosts(self):
        """Creates the Hosts for each VmHandler instance"""
        for config in self.configs:
            vmhandler = VmHandler(config)
            host = Host(vmhandler)
            self.hosts.append(host)
            self.name_to_host[host.get_hostname()] = host

    def _create_switches(self):
        for s in self.topo['switches']:
            switch = Switch(s)
            self.switches.append(switch)

    def start_vm_at(self, index):
        """Starts the VM number index
        :param index: The index of the VM to be started
        :type index: int
        """
        self.hosts[index].start()

    def stop_vm_at(self, index):
        """Stops the VM number index
        :param index: The index of the VM to be started
        :type index: int
        """
        self.hosts[index].stop()

    def _run_xterm(self, hostname):
        host = self.get_host_by_name(hostname)
        host.run_xterm()

    def xterm(self, hostname):
        """Runs xterm on the given host if given, or on all hosts otherwise
        :param hostname: The hostname on which to start an xterm
        :type hostname: str
        """
        if hostname is None:
            for name in self.name_to_host:
                self._run_xterm(name)
        else:
            self._run_xterm(hostname)

    def get_vm_names(self):
        """Returns a list of all VM names"""
        return [host.get_hostname() for host in self.hosts]

    def get_host_by_name(self, name):
        """Returns a Node by its name
        :param name: The name of the node
        :type name: str
        :return: The Node
        """
        return self.name_to_host[name]
