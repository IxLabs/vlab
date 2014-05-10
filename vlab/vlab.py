"""
This is the main object of this app

It instantiates VmConfigLoader and creates the nodes that are then started
"""

from vmconfig import VmConfigLoader, VmConfig
from vmhandler import VmHandler
from node import Switch

import socket

class Vlab( object ):
    """Network emulation with hosts spawned in Qemu"""
    LISTEN_PORT = 20000
    BACKLOG = 10

    def __init__( self ):
        self.vmConfigLoader = VmConfigLoader( )
        self.configs = [ ]
        self.vmHandlers = [ ]
        self.hosts = [ ]
        self.switches = [ ]

        self.startBootListener()
        self.initConfigs( )

    def startBootListener( self ):
        self.notifysocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.notifysocket.bind(('0.0.0.0', Vlab.LISTEN_PORT))
        self.notifysocket.listen(Vlab.BACKLOG)

    def startAll( self ):
        """Start All the VMs"""
        for i in xrange( len( self.configs ) ):
            self.startVmAt( i )
        for s in self.switches:
            s.startVm()

        booted = 0
        while booted < len( self.configs ):
            client, addr = self.notifysocket.accept()
            booted = booted + 1

            message = client.recv(128)
            client.close()

            print message,

    def stopAll( self ):
        """Stop All the VMs"""
        for i in xrange( len( self.configs ) ):
            self.stopVmAt( i )
        for s in self.switches:
            s.stopVm()

    def initConfigs( self ):
        """Read and init the configs"""
        self.vmConfigLoader.readConfig( )
        self.vmConfigLoader.createVmConfigs( )
        self.configs = self.vmConfigLoader.getConfigs( )
        self.topo = self.vmConfigLoader.getTopoConfig()
        self._createVmHandlers( )
        self._createSwitches()

    def _createVmHandlers( self ):
        """Creates the VmHandler instances for each VmConfig"""
        for config in self.configs:
            self.vmHandlers.append( VmHandler( config ) )

    def _createSwitches(self):
        for s in self.topo['switches']:
            switch = Switch(s)
            self.switches.append(switch)

    def startVmAt( self, index ):
        """Starts the VM number index
        :param index: The index of the VM to be started
        :type index: int
        """
        if not self.vmHandlers[ index ].isStarted( ):
            self.vmHandlers[ index ].startVm( )


    def stopVmAt( self, index ):
        """Stops the VM number index
        :param index: The index of the VM to be started
        :type index: int
        """
        if self.vmHandlers[ index ].isStarted( ):
            self.vmHandlers[ index ].stopVm( )

