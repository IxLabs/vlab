"""
A simple command-line interface for vLab

This CLI permits simple commands like:

vlab> h2 ip a s
"""

from cmd import Cmd, IDENTCHARS
from os import isatty
import sys
import os
import atexit

from util import run


class CLI(Cmd):
    """Simple Command-line interface to communicate with nodes."""

    prompt = 'vLab> '
    identchars = IDENTCHARS + '-'

    def __init__(self, vlab, stdin=sys.stdin):
        """Instantiates a CLI object
        :param vlab: Vlab class to be run"""
        self.stdin = stdin
        self.vlab = vlab
        Cmd.__init__(self)
        print('Starting CLI:\n')

        # Setup history if readline is available
        try:
            import readline
        except ImportError:
            pass
        else:
            history_path = os.path.expanduser('~/.vlab_history')
            if os.path.isfile(history_path):
                readline.read_history_file(history_path)
            atexit.register(
                lambda: readline.write_history_file(history_path))

        while True:
            try:
                if self.isatty():
                    run('stty sane')
                self.cmdloop()
                break
            except KeyboardInterrupt:
                print('\nInterrupt\n')

    def emptyline(self):
        """Don't repeat last command when you hit return."""
        pass

    # Disable pylint "Unused argument: 'arg's'" messages, as well as
    # "method could be a function" warning, since each CLI function
    # must have the same interface
    # pylint: disable-msg=R0201

    help_str = (
        'You may also send a command to a node using:\n'
        '  <node> command {args}\n'
        'For example:\n'
        '  vLab> h1 ifconfig\n'
        '\n'
    )

    def do_help(self, line):
        """Describe available CLI commands."""
        Cmd.do_help(self, line)
        if line is '':
            print(self.help_str)

    def isatty(self):
        """Is our standard input a tty?"""
        return isatty(self.stdin.fileno())

    def do_exit(self, _line):
        """Exit"""
        self.vlab.stop_all()
        return 'Exited by user input'

    def do_quit(self, line):
        """Exit"""
        return self.do_exit(line)

    def do_EOF(self, line):
        """Exit"""
        print ('\n')
        return self.do_exit(line)

    def do_start_all(self, line):
        """Start All VMs"""
        self.vlab.start_all()
        print('Starting all\n')

    def do_stop_all(self, line):
        """Stop All VMs"""
        self.vlab.stop_all()
        print('Stopping all\n')

    def do_start_vm_at(self, line):
        """Starts one VM"""
        try:
            index = int(line) - 1
            if not self.vlab.index_in_bounds(index):
                print('VM Index out of bounds')
                return
            self.vlab.start_vm_at(index)
        except ValueError, arg:
            print "The argument does not contain numbers\n", arg

    def do_stop_vm_at(self, line):
        """Stops one VM"""
        try:
            index = int(line) - 1
            if not self.vlab.index_in_bounds(index):
                print('VM Index out of bounds')
                return
            self.vlab.stop_vm_at(index)
        except ValueError, arg:
            print "The argument does not contain numbers\n", arg

    def do_xterm(self, line):
        """ Run an xterm with a SSH connection to a host"""
        first, args, line = self.parseline(line)

        self.vlab.xterm(first)

    def default(self, line):
        """Called on an input line when the command prefix is not recognized.
        Overridden to run shell commands when a node is the first CLI argument.
        """

        first, args, line = self.parseline(line)

        print("DEBUG: first: %s args: %s " % (first, args))

        if not first in self.vlab.get_vm_names():
            print('*** Unknown command: %s\n' % line)
        else:
            if not args:
                print "*** Enter a command for node: %s <cmd>" % first

            node = self.vlab.get_host_by_name(first)

            # Substitute IP addresses for node names in command
            rest = args.split(' ')
            rest = [self.vlab.get_host_by_name(arg).get_mgmt_ip()
                    if arg in self.vlab.get_vm_names() else arg
                    for arg in rest]
            rest = ' '.join(rest)

            out_lines, err_lines = node.exec_cmd(rest)
            for ln in out_lines:
                print ln,
            for ln in err_lines:
                print ln,
