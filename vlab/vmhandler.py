"""
VmHandler is used by Nodes for interacting with a Qemu VM.
"""

import subprocess
from subprocess import Popen
import shlex
import socket

from vmconfig import VmConfig
from util import ssh_setup


class VmHandler(object):
    """A VmHandler provides primitives for handling a Qemu VM."""

    def __init__(self, config):
        """Create VMHandler object

        :param config: VmConfig object corresponding to this VM
        :type config: VmConfig
        """
        self.config = config

        self.tap = ''
        self.started = False
        self.vm_process = None
        self.mgmt_ip = self._generate_mgmt_ip()
        self.test_interfaces = {}

    def start_vm(self):
        """Starts the VM. Handles the creation of tap interfaces as well"""
        self.tap = self._create_tap_intf()
        self._set_mgmt_tap_ip()

        cmd = self.config.get_commandline(self.tap)
        print 'DEBUG: cmd=' + str(cmd)
        print 'Running ' + ' '.join(cmd)
        self.vm_process = subprocess.Popen(cmd)
        print 'Process is ' + str(self.vm_process.pid)
        self.started = True

    def stop_vm(self):
        """Stops the VM. Also removes the created tap interfaces"""
        self.vm_process.terminate()
        self.vm_process.wait()
        self._remove_tap_intf(self.tap)
        self.tap = ''
        self.started = False
        self.clean_interfaces()

    def is_started(self):
        """Returns whether the VM is currently started or not"""
        return self.started

    def get_vm_name(self):
        """Returns the name of this VM"""
        return self.config.vm_name

    def send_cmd(self, line):
        """Sends a command to host to be executed"""
        ssh_private_key = self.config.get_ssh_key_path()
        c = ssh_setup()
        c.connect(self.mgmt_ip, username='root', key_filename=ssh_private_key)
        line = 'source ~/.bashrc; ' + line
        stdin, stdout, stderr = c.exec_command(line)
        out_lines = stdout.readlines()
        err_lines = stderr.readlines()
        c.close()
        return out_lines, err_lines

    def run_xterm(self):
        """Starts an xterm on this host"""
        if not self.is_started():
            print("{} is not running".format(self.get_vm_name()))
            return

        ssh_key = self.get_ssh_key_path()
        cmd = ("xterm -e \"/usr/bin/ssh -i " + ssh_key +
               " root@" + self.get_mgmt_ip() + "\"")
        cmd = shlex.split(cmd)
        print("DEBUG: _run_xterm cmd= " + str(cmd))
        Popen(cmd)

    def get_ssh_key_path(self):
        """Returns the path of this VM's private SSH key"""
        return self.config.get_ssh_key_path()

    def get_mgmt_ip(self):
        """Returns the management interface's ip"""
        return self.mgmt_ip

    def configure_interface(self, link, link_idx):
        """Creates host test interface, adds it to the guest and configures IP address

        :param link: Configuration options for a link read from topo.json
        :type link: dict
        :param link_idx: Test interface index
        :type link_idx: int
        """
        tap = VmHandler._create_tap_intf()
        self.test_interfaces[tap] = link
        netdev, device = self.config.get_network_interface(tap)
        self.monitor_send_cmd(netdev)
        self.monitor_send_cmd(device)
        self.send_cmd("echo 1 > /sys/bus/pci/rescan")

        ip = self.config.host['options']['ip'].split('.')
        ip[3] = str(int(ip[3]) + link_idx)
        ipstr = ".".join(ip)
        # Add one because eth0 is the management interface
        intf_name = "eth" + str(link_idx + 1)

        self.send_cmd("ip a a " + ipstr + "/24 dev " + intf_name)
        self.send_cmd("ip link set " + intf_name + " up")

    def configure_interfaces(self):
        print(self.config.host)
        i = 0
        for link in self.config.host['links']:
            self.configure_interface(link, i)
            i = i + 1

    def clean_interfaces(self):
        for intf in self.test_interfaces:
            VmHandler._remove_tap_intf(intf)

    def monitor_send_cmd(self, command):
        path = "/tmp/" + self.config.vm_name + "/vm-monitor-console.socket"
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(path)
        sock.recv(128)
        sock.send(command + "\n")
        response = sock.recv(128)
        sock.close()
        return response

    @staticmethod
    def _create_tap_intf():
        """Create a TAP interface on host to be used inside VM
        :return: The name of the newly created TAP interface
        :rtype: str
        """
        p = subprocess.Popen(['tunctl', '-b'], stdout=subprocess.PIPE)
        output, err = p.communicate()
        return output[0:-1]

    @staticmethod
    def _remove_tap_intf(tap_name):
        """Remove the tap interface from host"""
        subprocess.call(['tunctl', '-d', tap_name])

    def _set_mgmt_tap_ip(self):
        """Sets ip on tap linked to management interface"""
        ip = '10.0.' + str(self.config.get_vm_index()) + '.1/24'
        subprocess.call(['ip', 'addr', 'add', ip, 'dev', self.tap])

    def _generate_mgmt_ip(self):
        """Generates the ip of the management interface"""
        return '10.0.' + str(self.config.get_vm_index()) + '.2'
