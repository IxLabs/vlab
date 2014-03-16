"""
Node objects for vLab

A Node can be seen as an abstraction for a node in a network topology. It can be
a Host, a Switch or something.
"""


class Node( object ):
    """A virtual network node is the abstraction of a network node."""

    def __init__( self ):
        pass

    def startVm( self ):
        pass

    def stopVm( self ):
        pass

    def cleanup( self ):
        pass

    def sendCmd( self ):
        pass


class Switch( Node ):
    """A switch is basically a bridge"""

    def __init__( self ):
        Node.__init__( self )
        pass


class Host( Node ):
    """A Host is actually a node that runs in a Qemu VM"""

    def __init__( self ):
        Node.__init__( self )
        pass
