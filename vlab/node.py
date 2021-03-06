"""
Node objects for vLab

A Node can be seen as an abstraction for a node in a network topology. It can be
a Host, a Switch or something.
"""
from util import run
from vmhandler import VmHandler


class Node(object):
    """A virtual network node is the abstraction of a network node."""

    def __init__(self):
        pass

    def start(self):
        """Starts a Node if it is not already running"""
        pass

    def stop(self):
        """Stops a Node if it is already running"""
        pass

    def exec_cmd(self, line):
        """Runs a cmd on this Host
        :param line: The line of the command to be executed
        :type line: str
        :return A tuple containing out lines and err lines
        :rtype tuple
        """
        pass

    def is_started(self):
        """Returns whether this node is started or not"""
        pass

    def get_hostname(self):
        """Gets the hostname of this Node
        :return The hostname corresponding tho this Node
        :rtype str
        """
        pass


class Switch(Node):
    """A switch is basically a bridge"""

    def __init__(self, s, l):
        Node.__init__(self)
        self.switch = s
        self.links = l
        self.started = False

    def get_hostname(self):
        return self.switch['opts']['hostname']

    def start(self):
        if self.is_started():
            print("%s already started" % (self.get_hostname()))
            return
        print 'Starting switch ' + self.get_hostname()
        cmd = "brctl addbr " + self.get_hostname()
        run(cmd)
        self.started = True

    def stop(self):
        if not self.is_started():
            print("%s already stopped" % (self.get_hostname()))
            return
        print 'Stopping switch ' + self.get_hostname()
        cmd = "brctl delbr " + self.get_hostname()
        run(cmd)
        self.started = False

    def is_started(self):
        return self.started

    def add_intf(self, intf):
        print "Adding interface " + intf
        cmd = "brctl addif " + self.get_hostname() + " " + intf
        run(cmd)

    def del_intf(self, intf):
        print "Deleting interface " + self.int
        cmd = "brctl delif " + self.get_hostname() + " " + intf
        run(cmd)

    #TODO: reduce duplicate code
    def add_links(self):
        print "Adding Links :"
        for link in self.links:
            src = link['src']
            dst = link['dest']

            if self.get_hostname() == src:
                peer = dst
            else:
                peer = src
            self.add_intf("tap" + "." + peer)

    def del_links(self):
        for link in self.links:
            src = link['src']
            dst = link['dest']

            if self.get_hostname() == src:
                peer = dst
            else:
                peer = src
            self.del_intf("tap" + "." + peer)

class Host(Node):
    """A Host is actually a node that runs in a Qemu VM"""

    def __init__(self, vmhandler):
        """Creates a Host given a VmHandler
        :param vmhandler: The VmHandler corresponding to this Host
        :type vmhandler: VmHandler
        """
        Node.__init__(self)
        self.vmhandler = vmhandler

    def start(self):
        if not self.vmhandler.is_started():
            self.vmhandler.start_vm()

    def stop(self):
        if self.vmhandler.is_started():
            self.vmhandler.stop_vm()

    def exec_cmd(self, line):
        return self.vmhandler.send_cmd(line)

    def get_hostname(self):
        return self.vmhandler.get_vm_name()

    def is_started(self):
        return self.vmhandler.is_started()

    def configure_interfaces(self):
        return self.vmhandler.configure_interfaces()

    def run_xterm(self):
        return self.vmhandler.run_xterm()

    def get_mgmt_ip(self):
        return self.vmhandler.get_mgmt_ip()
