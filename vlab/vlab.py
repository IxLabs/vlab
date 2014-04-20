"""
This is the main object of this app

It instantiates VmConfigLoader and creates the nodes that are then started
"""

from vmconfig import VmConfigLoader, VmConfig
from vmhandler import VmHandler


class Vlab( object ):
    """Network emulation with hosts spawned in Qemu"""

    def __init__( self ):
        self.vmConfigLoader = VmConfigLoader( )
        self.configs = [ ]
        self.vmHandlers = [ ]
        self.hosts = [ ]

        self.initConfigs( )

    def startAll( self ):
        """Start All the VMs"""
        for i in xrange( len( self.configs ) ):
            self.startVmAt( i )

    def stopAll( self ):
        """Stop All the VMs"""
        for i in xrange( len( self.configs ) ):
            self.stopVmAt( i )

    def initConfigs( self ):
        """Read and init the configs"""
        self.vmConfigLoader.readConfig( )
        self.vmConfigLoader.createVmConfigs( )
        self.configs = self.vmConfigLoader.getConfigs( )
        self._createVmHandlers( )

    def _createVmHandlers( self ):
        """Creates the VmHandler instances for each VmConfig"""
        for config in self.configs:
            self.vmHandlers.append( VmHandler( config ) )

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

