"""
VmHandler is used by Nodes for interacting with a Qemu VM.
"""

import subprocess
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

    def get_ssh_key_path(self):
        """Returns the path of this VM's private SSH key"""
        return self.config.get_ssh_key_path()

    def get_mgmt_ip(self):
        """Returns the management interface's ip"""
        return self.mgmt_ip

    def configure_interface(self, link):
        tap = VmHandler._create_tap_intf()
        self.test_interfaces[tap] = link
        netdev, device = self.config.get_network_interface(tap)
        self.monitor_send_cmd(netdev)
        self.monitor_send_cmd(device)
        self.send_cmd("echo 1 > /sys/bus/pci/rescan")
        # TODO: set IP in guest

    def configure(self):
        print(self.config.host)
        for link in self.config.host['links']:
            self.configure_interface(link)

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

    def screen_attach_monitor(self):
        pass

    def screen_attach_guest_control(self):
        pass

    def screen_detach(self):
        pass

    def quit_vm(self):
        pass

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
