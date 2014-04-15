"""
This is the main object of this app

It instantiates VmConfigLoader and creates the nodes that are then started
"""

import subprocess

from vmconfig import VmConfigLoader, VmConfig


class Vlab( object ):
    """Network emulation with hosts spawned in Qemu"""

    def __init__( self ):
        self.vmConfigLoader = VmConfigLoader( )
        self.configs = [ ]
        self.hosts = [ ]

        self.initConfigs( )

    def startAll( self ):
        for i in xrange( len( self.configs ) ):
            self.startOne( i )

    def initConfigs( self ):
        self.vmConfigLoader.readConfig( )
        self.vmConfigLoader.createVmConfigs( )
        self.configs = self.vmConfigLoader.getConfigs( )

    def startOne( self, index ):
        args = self.configs[ index ].getCommandline( )
        print args
        subprocess.Popen( args, shell=True )
