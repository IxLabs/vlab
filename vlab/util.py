"""Utility functions for vLab"""

from subprocess import call

def run( cmd ):
    """Simple interface to subprocess.call()
    :param cmd: list of command params
    """
    return call( cmd.split( ' ' ) )
