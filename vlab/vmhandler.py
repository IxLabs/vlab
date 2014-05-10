"""
VmHandler is used by Nodes for interacting with a Qemu VM.
"""

import subprocess
import socket
from vmconfig import VmConfig
from util import ssh_setup

class VmHandler( object ):
    """A VmHandler provides primitives for handling a Qemu VM."""

    def __init__( self, config ):
        """Create VMHandler object

        :param config: VmConfig object corresponding to this VM
        :type config: VmConfig
        """
        self.config = config

        self.tap = ''
        self.started = False
        self.vmProcess = None
        self.mgmtIp = self._generateMgmtIp( )
        self.testInterfaces = {}

    def startVm( self ):
        """Starts the VM. Handles the creation of tap interfaces as well"""
        self.tap = self._createTapIntf( )
        self._setMgmtTapIp( )

        cmd = self.config.getCommandline( self.tap )
        print 'DEBUG: cmd=' + str( cmd )
        print 'Running ' + ' '.join( cmd )
        self.vmProcess = subprocess.Popen( cmd )
        print 'Process is ' + str( self.vmProcess.pid )
        self.started = True

    def stopVm( self ):
        """Stops the VM. Also removes the created tap interfaces"""
        self.vmProcess.terminate( )
        self.vmProcess.wait( )
        self._removeTapIntf( self.tap )
        self.tap = ''
        self.started = False
        self.cleanInterfaces()

    def isStarted( self ):
        """Returns whether the VM is currently started or not"""
        return self.started

    def getVmName(self):
        return self.config.vmName

    def sendCmd( self, line ):
        """Sends a command to host to be executed"""
        c = ssh_setup( )
        c.connect( self.mgmtIp, username='root' )
        line = 'source ~/.bashrc; ' + line
        stdin, stdout, stderr = c.exec_command( line )
        out_lines = stdout.readlines( )
        err_lines = stderr.readlines( )
        c.close( )
        return out_lines, err_lines


    def getMgmtIp( self ):
        """Returns the management interface's ip"""
        return self.mgmtIp

    def configureInterface( self, link ):
        tap = VmHandler._createTapIntf()
        self.testInterfaces[ tap ] = link
        netdev, device = self.config.getNetworkInterface(tap)
        self.monitorSendCmd(netdev)
        self.monitorSendCmd(device)
        self.sendCmd("echo 1 > /sys/bus/pci/rescan")
        # TODO: set IP in guest

    def configure( self ):
        print(self.config.host)
        for link in self.config.host[ 'links' ]:
            self.configureInterface(link)

    def cleanInterfaces(self):
        for intf in self.testInterfaces:
            VmHandler._removeTapIntf(intf)

    def monitorSendCmd(self, Command):
        path = "/tmp/" + self.config.vmName + "/vm-monitor-console.socket"
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(path)
        sock.recv(128)
        sock.send(Command + "\n")
        response = sock.recv(128)
        sock.close()
        return response

    def screenAttachMonitor( self ):
        pass

    def screenAttachGuestControl( self ):
        pass

    def screenDetach( self ):
        pass

    def quitVm( self ):
        pass

    @staticmethod
    def _createTapIntf( ):
        """Create a TAP interface on host to be used inside VM
        :return: The name of the newly created TAP interface
        :rtype: str
        """
        p = subprocess.Popen( [ 'tunctl', '-b' ], stdout=subprocess.PIPE )
        output, err = p.communicate( )
        return output[ 0:-1 ]

    @staticmethod
    def _removeTapIntf( tapName ):
        """Remove the tap interface from host"""
        subprocess.call( [ 'tunctl', '-d', tapName ] )

    def _setMgmtTapIp( self ):
        """Sets ip on tap linked to management interface"""
        ip = '10.0.' + str( self.config.getVmIndex( ) ) + '.1/24'
        subprocess.call( [ 'ip', 'addr', 'add', ip, 'dev', self.tap ] )

    def _generateMgmtIp( self ):
        """Generates the ip of the management interface"""
        return '10.0.' + str( self.config.getVmIndex( ) ) + '.2'
