"""
This is the main object of this app

It instantiates VmConfigLoader and creates the nodes that are then started
"""

import shlex
from subprocess import Popen
import socket

from vmconfig import VmConfigLoader
from vmhandler import VmHandler
from node import Switch


class Vlab(object):
    """Network emulation with hosts spawned in Qemu"""
    LISTEN_PORT = 20000
    BACKLOG = 10

    def __init__(self):
        self.vm_config_loader = VmConfigLoader()
        self.configs = []
        self.topo = {}
        self.vm_handlers = []
        self.hosts = []
        self.switches = []

        self.notifysocket = None
        self.start_boot_listener()
        self.name_to_node = {}

        self.init_configs()

    def start_boot_listener(self):
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
            for vm in self.vm_handlers:
                if vm.get_vm_name() == vmname:
                    vm.configure()

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
        self._create_vm_handlers()
        self._create_switches()

    def _create_vm_handlers(self):
        """Creates the VmHandler instances for each VmConfig"""
        for config in self.configs:
            vm_handler = VmHandler(config)
            self.vm_handlers.append(vm_handler)
            self.name_to_node[config.get_vm_name()] = vm_handler

    def _create_switches(self):
        for s in self.topo['switches']:
            switch = Switch(s)
            self.switches.append(switch)

    def start_vm_at(self, index):
        """Starts the VM number index
        :param index: The index of the VM to be started
        :type index: int
        """
        if not self.vm_handlers[index].is_started():
            self.vm_handlers[index].start_vm()

    def stop_vm_at(self, index):
        """Stops the VM number index
        :param index: The index of the VM to be started
        :type index: int
        """
        if self.vm_handlers[index].is_started():
            self.vm_handlers[index].stop_vm()

    def _run_xterm(self, hostname):
        node = self.get_node_by_name(hostname)
        if not node.is_started():
            print("{} is not running".format(hostname))
            return

        ssh_key = node.get_ssh_key_path()
        cmd = ("xterm -e \"/usr/bin/ssh -i " + ssh_key +
               " root@" + node.get_mgmt_ip() + "\"")
        cmd = shlex.split(cmd)
        print("DEBUG: _run_xterm cmd= " + str(cmd))
        Popen(cmd)

    def xterm(self, hostname):

        if hostname is None:
            for name in self.name_to_node:
                self._run_xterm(name)
        else:
            self._run_xterm(hostname)

    def get_vm_names(self):
        """Returns a list of all VM names"""
        return [config.get_vm_name() for config in self.configs]

    def get_node_by_name(self, name):
        """Returns a Node by its name
        :param name: The name of the node
        :type name: str
        """
        return self.name_to_node[name]
