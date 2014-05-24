"""
Contains everything related to configs

A VmConfigLoader handles reading config files for VMs and for topologies.
A VmConfig is created by VmConfigLoader for the range specified in the config
file
"""

import json
import subprocess
import os
import shlex
import random
import binascii

class VmConfig(object):
    """Holds data necessary to start a VM"""

    def __init__(self, config_data, host_config, vm_index):
        """Creates VmConfig object.

        :param config_data: Dict containing the info from the vm config file
        :type config_data: dict
        :param vm_index: Index of this VmConfig object
        :type vm_index: int
        """
        self.vm_index = vm_index
        self.vm_name = config_data['base_name'] + str(self.vm_index)
        self.qemu_binary = config_data['qemu_binary']
        self.misc_params = config_data['misc_params']
        self.max_ram = config_data['max_ram']
        self.kernel_dir = config_data['kernel_image']['dir']
        self.kernel_image_name = config_data['kernel_image']['image_name']
        self.kernel_init_params = dict(
            config_data['kernel_image']['init_params'])
        self.properties = list(config_data['properties'])
        self.host = host_config
        self.home_dir = ""

    def get_commandline(self, mgmt_tap_name):
        """Gets the command line needed for starting up the VM

        :param mgmt_tap_name: The name of the TAP interface created on host
        :typmgmt_tap_nameme: str
        :return: the command line required to run Qemu as list of strings
        :rtype: list(str)
        """
        directory = '/tmp/' + self.vm_name
        if not os.path.exists(directory):
            os.makedirs(directory)
        return ([self.qemu_binary, '-m', str(self.max_ram)] +
                self._get_misc_params() +
                self._get_chardev_lines() + self._get_fsdev_lines() +
                self._get_kernel_line() + self._get_mgmt_intf_line(mgmt_tap_name))

    def get_vm_index(self):
        """Returns the index of this VM"""
        return self.vm_index

    def get_vm_name(self):
        """Returns the name of this VM"""
        return self.vm_name

    def get_home_dir(self):
        """Returns the path of this VM home directory"""
        return self.home_dir

    def get_ssh_key_path(self):
        """Returns the path of this VM's private SSH key"""
        return self.get_home_dir() + '/root/.ssh/id_rsa'

    def _get_misc_params(self):
        return shlex.split(self.misc_params)

    def _get_fsdev_lines(self):
        """Returns the lines corresponding to fsdevs"""
        fsdev_lines = []
        for prop in self.properties:
            if prop['dev'] != 'fsdev':
                continue

            path = prop['path']
            if prop['id'] == 'fsdev-home':
                if not os.path.exists(path):
                    raise IOError('Vmrootfs folder does not exist: %s' % path)
                self.home_dir = path

            security_model = 'none'
            readonly = ''
            if prop['id'] == 'fsdev-root':
                security_model = 'passthrough'
                readonly = ',readonly'

            fsdev_lines += ['-fsdev',
                            ('local,security_model=' + security_model +
                             ',id=' + prop['id'] + ',path=' + path + readonly)]
            fsdev_lines += ['-device',
                            (prop['device_type'] + ',fsdev=' + prop['id'] +
                             ',mount_tag=' + prop['mount_tag'])]
        return fsdev_lines

    def _get_chardev_lines(self):
        """Returns the lines corresponding to chardevs"""
        chardev_lines = []
        for prop in self.properties:
            if prop['dev'] != 'chardev':
                continue

            chardev_props = 'chardev'
            path = '/tmp/' + self.vm_name
            if prop['id'] == 'mgmt':
                chardev_props += ':mgmt'
                path += '/vm-mgmt-console.socket'
            elif prop['id'] == 'monitor':
                chardev_props += '=monitor,mode=readline,default'
                path += '/vm-monitor-console.socket'

            chardev_lines += ['-chardev',
                              ('socket,id=' + prop['id'] + ',path=' + path +
                               ',server,nowait'),
                              '-' + prop['type'],
                              chardev_props]
        return chardev_lines

    def _get_kernel_line(self):
        """Returns the kernel parameters line"""
        return ['-kernel',
                self.kernel_dir + '/' + self.kernel_image_name,
                '-append',
                ('init=' +
                 self._get_full_path(self.kernel_init_params['init']) +
                 ' console=tty0' +
                 ' console=' + self.kernel_init_params['console'] +
                 ' uts=' + self.vm_name +
                 ' root=/dev/root' +
                 self._get_root_flags() +
                 ' ' + self.kernel_init_params['mode'] +
                 ' rootfstype=' + self.kernel_init_params['rootfstype'] +
                 ' ' + self._get_init_script_args())]

    def _get_root_flags(self):
        """Returns the rootflags sent to kernel init"""
        rootflags = ' rootflags='
        for key in self.kernel_init_params['rootflags'].keys():
            rootflags += (key + '=' +
                          self.kernel_init_params['rootflags'][key] + ',')
        return rootflags[0:-1]  # strip last ','

    def _get_init_script_args(self):
        """Returns the arguments that will be transmitted to the init script"""
        return str(self.vm_index)

    def _get_mgmt_intf_line(self, mgmt_tap_name):
        """Returns the line corresponding with the management netdev
        interface"""
        # TODO: Use a MAC address from the config, if it is available
        mgmt_prop = next(
            (prop for prop in self.properties if prop['dev'] == 'netdev'),
            None)
        return ['-netdev',
                ('type=' + mgmt_prop['type'] + ',id=' +
                 mgmt_prop['id'] + ',ifname=' + mgmt_tap_name),
                '-device',
                mgmt_prop['device_type'] + ',netdev=' + mgmt_prop['id'] +
                ",mac=" + self._get_random_mac()]

    def get_network_interface(self, tap_name):
        net = next(
            (prop for prop in self.properties if prop['id'] == 'net'),
            None)
        # TODO: Use a MAC address from the config, if it is available
        netdev = net['id'] + tap_name
        return ["netdev_add " + net['type'] + ",id=" + netdev +
                ",ifname=" + tap_name,
                "device_add " + net['device_type'] + ",netdev=" + netdev +
                ",mac=" + self._get_random_mac()]

    @staticmethod
    def _get_full_path(file_name):
        p = subprocess.Popen(['readlink', '-f', file_name], stdout=subprocess
                             .PIPE)
        output, err = p.communicate()
        return output[0:-1]

    @staticmethod
    def _get_random_mac():
        values = [0, 1, 1] + [random.randint(0, 255) for i in range(3)]

        return ":".join([binascii.hexlify(chr(c)) for c in values])

class VmConfigLoader(object):
    """Loads config from file and stores it in a dict to be used in VmHandler"""

    def __init__(self, vm_file='../configs/vm.json',
                 topo_file='../configs/topo.json'):
        """Create the VmConfigLoader given two config files

        :param vm_file: File where the configs related to Qemu are found
        :type vm_file: str
        :param topo_file: File where configs related to topology are found
        :type topo_file: str
        """
        self.vm_file = vm_file
        self.topo_file = topo_file
        self.vm_config_data = {}
        self.vm_configs = []
        self.topo_config_data = {}
        self.host_names = []
        self.switch_names = []
        self.links = {}

    def read_config(self):
        """Reads the config files and stores them accordingly"""
        with open(self.vm_file, 'r') as f:
            self.vm_config_data = json.load(f)
            print self.vm_config_data

        with open(self.topo_file, 'r') as f:
            self.topo_config_data = json.load(f)

        for host in self.topo_config_data['hosts']:
            self.host_names.append(host['opts']['hostname'])

        for switch in self.topo_config_data['switches']:
            self.switch_names.append(switch['opts']['hostname'])

    def create_vm_configs(self):
        """Generates the VmConfigs"""

        links = {}
        for link in self.topo_config_data['links']:
            src = link['src']
            dst = link['dest']
            if not src in links:
                links[src] = [link]
            else:
                links[src].append(link)

            if not dst in links:
                links[dst] = [link]
            else:
                links[dst].append(link)

        self.links = links

        for i in xrange(len(self.topo_config_data['hosts'])):
            host_data = self.topo_config_data['hosts'][i]
            hostname = host_data['opts']['hostname']
            host_config = {'options': host_data['opts'],
                           'links': links[hostname]}

            print(host_config)

            # TODO: Fix kernel bug that makes intf with ip 10.0.0.2 to be sent on lo
            # instead of eth0 (inside vm)
            config = VmConfig(self.vm_config_data, host_config, i + 1)
            self.vm_configs.append(config)

    def get_configs(self):
        """Gets the list of the VmConfigs. Note: create_vm_configs must be
        :return A list of VmConfigs
        :rtype list(VmConfig)
        """
        return self.vm_configs

    def get_topo_config(self):
        return self.topo_config_data

    def get_switch_names(self):
        return self.switch_names

    def get_host_names(self):
        return self.host_names

    def get_links(self):
        return self.links
