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
        self.notifysocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.notifysocket.listen(Vlab.BACKLOG)

    def _wait_vm(self):
        """Wait a vm to boot. Returns the vmname that was sent from host"""
        client, addr = self.notifysocket.accept()

        message = client.recv(128)
        print message,

        client.close()

        msgparams = message.split(" ")
        return msgparams[0]

    def start_all(self):
        """Start All the VMs"""
        for i in xrange(len(self.configs)):
            self._start_vm_at(i)
        for s in self.switches:
            s.start()

        booted = 0
        while booted < len(self.configs):
            vmname = self._wait_vm()
            booted += 1

            for vm in self.hosts:
                if vm.get_hostname() == vmname:
                    vm.configure_interfaces()

        #add links to switches
        for s in self.switches:
            s.add_links()

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
            l = self.vm_config_loader.get_links()[s['opts']['hostname']]
            switch = Switch(s, l)
            self.switches.append(switch)

    def _start_vm_at(self, index):
        self.hosts[index].start()

    def index_in_bounds(self, index):
        """Returns whether index is in bounds of hosts array"""
        return 0 <= index < len(self.hosts)

    def start_vm_at(self, index):
        """Starts the VM number index
        :param index: The index of the VM to be started
        :type index: int
        """
        self._start_vm_at(index)
        vmname = self._wait_vm()
        vm = self.hosts[index]
        if not vmname == vm.get_hostname():
            print("ERROR: Got %s, but expected %s" %
                  (vmname, self.hosts[index].get_hostname()))
        vm.configure_interfaces()

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
