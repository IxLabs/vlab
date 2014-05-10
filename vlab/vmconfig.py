"""
Contains everything related to configs

A VmConfigLoader handles reading config files for VMs and for topologies.
A VmConfig is created by VmConfigLoader for the range specified in the config
file
"""

import json
import subprocess
import os
import shlex


class VmConfig( object ):
    """Holds data necessary to start a VM"""

    def __init__( self, configData, vmIndex ):
        """Creates VmConfig object.

        :param configData: Dict containing the info from the vm config file
        :type configData: dict
        :param vmIndex: Index of this VmConfig object
        :type vmIndex: int
        """
        self.vmIndex = vmIndex
        self.vmName = configData[ 'base_name' ] + str( self.vmIndex )
        self.qemuBinary = configData[ 'qemu_binary' ]
        self.miscParams = configData[ 'misc_params' ]
        self.maxRam = configData[ 'max_ram' ]
        self.kernelDir = configData[ 'kernel_image' ][ 'dir' ]
        self.kernelImageName = configData[ 'kernel_image' ][ 'image_name' ]
        self.kernelInitParams = dict(
            configData[ 'kernel_image' ][ 'init_params' ] )
        self.properties = list( configData[ 'properties' ] )

    def getCommandline( self, mgmtTapName ):
        """Gets the command line needed for starting up the VM

        :param mgmtTapName: The name of the TAP interface created on host
        :type mgmtTapName: str
        :return: the command line required to run Qemu as list of strings
        :rtype: list(str)
        """
        directory = '/tmp/' + self.vmName
        if not os.path.exists( directory ):
            os.makedirs( directory )
        return ([ self.qemuBinary, '-m', str( self.maxRam ) ] +
                self._getMiscParams( ) +
                self._getChardevLines( ) + self._getFsdevLines( ) +
                self._getKernelLine( ) + self._getMgmtIntfLine( mgmtTapName ))

    def getVmIndex( self ):
        """Returns the index of this VM"""
        return self.vmIndex

    def getVmName( self ):
        """Returns the name of this VM"""
        return self.vmName

    def _getMiscParams( self ):
        return shlex.split( self.miscParams )

    def _getFsdevLines( self ):
        """Returns the lines corresponding to fsdevs"""
        fsdevLines = [ ]
        for prop in self.properties:
            if prop[ 'dev' ] != 'fsdev':
                continue

            path = prop[ 'path' ]
            if prop[ 'id' ] == 'fsdev-home':
                if not os.path.exists( path ):
                    raise IOError( 'Vmrootfs folder does not exist: %s' % path )

            security_model = 'none'
            readonly = ''
            if prop[ 'id' ] == 'fsdev-root':
                security_model = 'passthrough'
                readonly = ',readonly'

            fsdevLines += [ '-fsdev',
                            ('local,security_model=' + security_model +
                             ',id=' + prop[ 'id' ] + ',path=' + path +
                             readonly) ]
            fsdevLines += [ '-device',
                            (prop[ 'device_type' ] + ',fsdev=' + prop[ 'id' ] +
                             ',mount_tag=' + prop[ 'mount_tag' ]) ]
        return fsdevLines

    def _getChardevLines( self ):
        """Returns the lines corresponding to chardevs"""
        chardevLines = [ ]
        for prop in self.properties:
            if prop[ 'dev' ] != 'chardev':
                continue

            chardevProps = 'chardev'
            path = '/tmp/' + self.vmName
            if prop[ 'id' ] == 'mgmt':
                chardevProps += ':mgmt'
                path += '/vm-mgmt-console.socket'
            elif prop[ 'id' ] == 'monitor':
                chardevProps += '=monitor,mode=readline,default'
                path += '/vm-monitor-console.socket'

            chardevLines += [ '-chardev',
                              ('socket,id=' + prop[ 'id' ] + ',path=' + path +
                               ',server,nowait'),
                              '-' + prop[ 'type' ],
                              chardevProps ]
        return chardevLines

    def _getKernelLine( self ):
        """Returns the kernel parameters line"""
        return [ '-kernel',
                 self.kernelDir + '/' + self.kernelImageName,
                 '-append',
                 ('init=' +
                  self._getFullPath( self.kernelInitParams[ 'init' ] ) +
                  ' console=tty0' +
                  ' console=' + self.kernelInitParams[ 'console' ] +
                  ' uts=' + self.vmName +
                  ' root=/dev/root' +
                  self._getRootFlags( ) +
                  ' ' + self.kernelInitParams[ 'mode' ] +
                  ' rootfstype=' + self.kernelInitParams[ 'rootfstype' ] +
                  ' ' + self._getInitScriptArgs( ) ) ]

    def _getRootFlags( self ):
        """Returns the rootflags sent to kernel init"""
        rootflags = ' rootflags='
        for key in self.kernelInitParams[ 'rootflags' ].keys( ):
            rootflags += (key + '=' +
                          self.kernelInitParams[ 'rootflags' ][ key ] + ',')
        return rootflags[ 0:-1 ]  # strip last ','

    def _getInitScriptArgs( self ):
        """Returns the arguments that will be transmitted to the init script"""
        return str( self.vmIndex )

    def _getMgmtIntfLine( self, mgmtTapName ):
        """Returns the line corresponding with the management netdev
        interface"""
        mgmtProp = next(
            (prop for prop in self.properties if prop[ 'dev' ] == 'netdev'),
            None )
        return [ '-netdev',
                 ('type=' + mgmtProp[ 'type' ] + ',id=' +
                  mgmtProp[ 'id' ] + ',ifname=' + mgmtTapName),
                 '-device',
                 mgmtProp[ 'device_type' ] + ',netdev=' + mgmtProp[ 'id' ] ]

    @staticmethod
    def _getFullPath( fileName ):
        p = subprocess.Popen( [ 'readlink', '-f', fileName ], stdout=subprocess
                              .PIPE )
        output, err = p.communicate( )
        return output[ 0:-1 ]


class VmConfigLoader( object ):
    """Loads config from file and stores it in a dict to be used in VmHandler"""

    def __init__( self, vmFile='../configs/vm.json',
                  topoFile='../configs/topo.json' ):
        """Create the VmConfigLoader given two config files

        :param vmFile: File where the configs related to Qemu are found
        :type vmFile: str
        :param topoFile: File where configs related to topology are found
        :type topoFile: str
        """
        self.vmFile = vmFile
        self.topoFile = topoFile
        self.vmConfigData = {}
        self.vmConfigs = [ ]
        self.topoConfigData = {}

    def readConfig( self ):
        """Reads the config files and stores them accordingly"""
        with open( self.vmFile, 'r' ) as f:
            self.vmConfigData = json.load( f )
            print self.vmConfigData

        with open( self.topoFile, 'r' ) as f:
            self.topoConfigData = json.load( f )

    def createVmConfigs( self ):
        """Generates the VmConfigs"""
        for i in xrange( self.vmConfigData[ 'range_low' ],
                         self.vmConfigData[ 'range_high' ] + 1 ):
            config = VmConfig( self.vmConfigData, i )
            self.vmConfigs.append( config )

    def getConfigs( self ):
        """Gets the list of the VmConfigs. Note: createVmConfigs must be
        :return A list of VmConfigs
        :rtype list(VmConfig)
        """
        return self.vmConfigs

    def getTopoConfig( self ):
        return self.topoConfigData
