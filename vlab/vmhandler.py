"""
VmHandler is used by Nodes for interacting with a Qemu VM.
"""


class VmHandler( object ):
    """A VmHandler provides primitives for handling a Qemu VM."""

    def __init__( self ):
        pass

    def startVm( self ):
        pass

    def stopVm( self ):
        pass

    def screenAttachMonitor( self ):
        pass

    def screenAttachGuestControl( self ):
        pass

    def screenDetach( self ):
        pass

    def quitVm( self ):
        pass
