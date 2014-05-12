"""Utility functions for vLab"""

from subprocess import call
from paramiko import SSHClient, AutoAddPolicy


def run(cmd):
    """Simple interface to subprocess.call()
    :param cmd: list of command params
    """
    return call(cmd.split(' '))


def ssh_setup():
    """Returns a new SSHClient that doesn't require known_hosts"""
    c = SSHClient()
    c.set_missing_host_key_policy(AutoAddPolicy())
    return c
