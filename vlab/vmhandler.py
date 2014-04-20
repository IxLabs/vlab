"""
VmHandler is used by Nodes for interacting with a Qemu VM.
"""

import subprocess

from vmconfig import VmConfig


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

    def startVm( self ):
        """Starts the VM. Handles the creation of tap interfaces as well"""
        self.tap = self._createTapIntf( )
        cmd = self.config.getCommandline( self.tap )
        print 'Running ' + cmd
        self.vmProcess = subprocess.Popen( cmd, shell=True )
        print 'Process is ' + str(self.vmProcess.pid)
        self.started = True

    def stopVm( self ):
        """Stops the VM. Also removes the created tap interfaces"""
        self.vmProcess.kill( )
        self._removeTapIntf( self.tap )
        self.tap = ''
        self.started = False

    def isStarted( self ):
        """Returns whether the VM is currently started or not"""
        return self.started

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
        p = subprocess.Popen( [ 'tunctl', '-b' ], stdout=subprocess
                              .PIPE )
        output, err = p.communicate( )
        return output[ 0:-1 ]

    @staticmethod
    def _removeTapIntf( tapName ):
        """Remove the tap interface from host"""
        subprocess.call( [ 'tunctl', '-d', tapName ] )
