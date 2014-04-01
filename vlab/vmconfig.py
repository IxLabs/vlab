"""
Contains everything related to configs

A VmConfigLoader handles reading config files for VMs and for topologies.
A VmConfig is created by VmConfigLoader for the range specified in the config
file
"""

import json
import subprocess
import os


class VmConfig( object ):
    """Holds data necessary to start a VM"""

    def __init__( self, configData, vmIndex ):
        """configData: Dict containing the info from the vm config file
           vmIndex: Index of this VmConfig object"""
        self.vmIndex = vmIndex
        self.vmName = configData[ 'base_name' ] + str( self.vmIndex )
        self.qemuBinary = configData[ 'qemu_binary' ]
        self.maxRam = configData[ 'max_ram' ]
        self.kernelDir = configData[ 'kernel_image' ][ 'dir' ]
        self.kernelImageName = configData[ 'kernel_image' ][ 'image_name' ]
        self.kernelInitParams = dict(
            configData[ 'kernel_image' ][ 'init_params' ] )
        self.properties = list( configData[ 'properties' ] )

    def getCommandline( self ):
        directory = '/tmp/' + self.vmName
        if not os.path.exists( directory ):
            os.makedirs( directory )
        return (self.qemuBinary + ' -m ' + self.maxRam +
                self._getChardevLines( ) + self._getFsdevLines( ) +
                self._getKernelLine( ))

    def _getFsdevLines( self ):
        """Returns the lines corresponding to fsdevs"""
        fsdevLines = ''
        for prop in self.properties:
            if prop[ 'dev' ] != 'fsdev':
                continue

            path = prop[ 'path' ]
            if prop[ 'id' ] == 'fsdev-home':
                path += '/' + self.vmName
                if not os.path.exists( path ):
                    os.makedirs( path )

            fsdevProps = (' -fsdev local,security_model=passthrough,id=' +
                          prop[ 'id' ] + ',path=' + prop[ 'path' ])
            deviceProps = (' -device ' + prop[ 'device_type' ] +
                           ',fsdev=' + prop['id'] +
                           ',mount_tag=' + prop[ 'mount_tag' ])
            if prop[ 'id' ] == 'fsdev-root':
                fsdevProps += ',readonly'
            fsdevLines += fsdevProps + deviceProps
        return fsdevLines


    def _getChardevLines( self ):
        """Returns the lines corresponding to chardevs"""
        chardevLines = ''
        for prop in self.properties:
            if prop[ 'dev' ] != 'chardev':
                continue

            chardevProps = ' chardev'
            path = '/tmp/' + self.vmName
            if prop[ 'id' ] == 'mgmt':
                chardevProps += ':mgmt'
                path += '/vm-mgmt-console.socket'
            elif prop[ 'id' ] == 'monitor':
                chardevProps += '=monitor,mode=readline,default'
                path += '/vm-monitor-console.socket'

            chardevLines += (' -chardev socket,id=' +
                             prop[ 'id' ] + ',path=' + path + ',server,nowait' +
                             ' -' + prop[ 'type' ] + chardevProps)
        return chardevLines

    def _getKernelLine( self ):
        """Returns the kernel parameters line"""
        return (' -kernel ' + self.kernelDir + '/' + self.kernelImageName +
                ' -append "init=' +
                self._getFullPath( self.kernelInitParams[ 'init' ] ) +
                ' console=tty0' +
                ' console=' + self.kernelInitParams[ 'console' ] +
                ' uts=' + self.vmName +
                ' root=/dev/root' +
                self._getRootFlags( ) +
                ' ' + self.kernelInitParams[ 'mode' ] +
                ' rootfstype=' + self.kernelInitParams[ 'rootfstype' ] +
                ' ' + self._getInitScriptArgs( ) + '"')

    def _getRootFlags( self ):
        """Returns the rootflags sent to kernel init"""
        rootflags = ' rootflags='
        for key in self.kernelInitParams[ 'rootflags' ].keys( ):
            rootflags += (key + '=' +
                          self.kernelInitParams[ 'rootflags' ][ key ] + ',')
        return rootflags[ 0:-1 ]  # strip last ','

    def _getInitScriptArgs( self ):
        """Returns the arguments that will be transmitted to the init script"""
        return ' ' + self.vmName

    @staticmethod
    def _getFullPath( fileName ):
        p = subprocess.Popen( [ 'readlink', '-f', fileName ], stdout=subprocess
                              .PIPE )
        output, err = p.communicate( )
        return output[ 0:-1 ]


class VmConfigLoader( object ):
    """Loads config from file and stores it in a dict to be used in VmHandler"""

    def __init__( self, vmFile='../configs/vm.json',
                  topoFile='../configs/simple.json' ):
        """vmFile: File where the configs related to Qemu are found
           topoFile: File where configs related to topology are found"""
        self.vmFile = vmFile
        self.topoFile = topoFile
        self.vmConfigData = {}
        self.vmConfigs = [ ]

    def readConfig( self ):
        with open( self.vmFile, 'r' ) as f:
            self.vmConfigData = json.load( f )
            print self.vmConfigData

    def _createVmConfigs( self ):
        for i in xrange( self.vmConfigData[ 'range_low' ],
                         self.vmConfigData[ 'range_high' ] ):
            config = VmConfig( self.vmConfigData, i )
            self.vmConfigs.append( config )

    def getConfigs( self ):
        return self.vmConfigs