"""
Node objects for vLab

A Node can be seen as an abstraction for a node in a network topology. It can be
a Host, a Switch or something.
"""
from util import run


class Node( object ):
    """A virtual network node is the abstraction of a network node."""

    def __init__( self ):
        pass

    def start( self ):
        pass

    def stop( self ):
        pass

    def cleanup( self ):
        pass

    def sendCmd( self ):
        pass


class Switch( Node ):
    """A switch is basically a bridge"""

    def __init__( self, s ):
        Node.__init__( self )
        self.switch = s

    def getHostname( self ):
        return self.switch[ 'opts' ][ 'hostname' ]

    def start( self ):
        print 'Starting switch ' + self.getHostname( )
        cmd = "brctl addbr " + self.getHostname( )
        run( cmd )

    def stop( self ):
        print 'Stopping switch ' + self.getHostname( )
        cmd = "brctl delbr " + self.getHostname( )
        run( cmd )


class Host( Node ):
    """A Host is actually a node that runs in a Qemu VM"""

    def __init__( self ):
        Node.__init__( self )
        pass
