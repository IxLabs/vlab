#!/bin/bash

# This script is passed to kernel init when a Qemu VM starts up. It basically
# sets up things like hostname, mounts the home directory and others.

SHELL=/bin/bash

# Print message in light blue color
info() {
	echo -e "\033[1;34m$@ \033[0m"
}

# Print message in light red color
error() {
	echo -e "\033[1;31m$@ \033[0m"
}

info "Running init script"

info "Index of VM is " $1
VM_INDEX=$1

info "Setting hostname as ${uts}"
hostname ${uts}

# Set path
export HOME=/root
info "Exported HOME: $HOME"
export PATH=$HOME/bin:/bin:/usr/local/bin:/usr/bin:/sbin:/usr/local/sbin:/usr/sbin
info "Exported PATH: $PATH"

# Set overlayfs
info 'Mounting tmpfs ...'
mount -t tmpfs tmpfs /tmp -o rw
info 'Mounting proc ...'
mount -n -t proc proc /proc
info 'Mounting sysfs ...'
mount -n -t sysfs sys /sys

info 'Mounting root overlayshare ...'
mkdir -p /tmp/vmroot
mount -t 9p overlayshare /tmp/vmroot -o trans=virtio,version=9p2000.L,access=0,rw

info 'Mounting home dir on /root ...'
# Mount home dir on /root
[ ! -d /tmp/vmroot/root ] && error 'root folder not found in vmrootfs.'
mount -o bind /tmp/vmroot/root /root

info 'Mounting /etc ...'
# Mount /etc
[ ! -d /tmp/vmroot/etc ] && error 'etc folder not found in vmrootfs.'
rm -f /tmp/vmroot/etc/mtab      # Make sure mtab file doesn't exist here
mount -t tmpfs tmpfs /etc -o rw
cp -r /tmp/vmroot/etc/* /etc/

info 'Mounting kernel modules ...'
# Mount kernel modules
mkdir -p /tmp/kernel
mount -t 9p kernelshare /tmp/kernel -o trans=virtio,version=9p2000.L,access=0,rw
mount -o bind /tmp/kernel/lib/modules /lib/modules

# Clean /tmp and /run
info "Clean out /tmp and /run directories..."
for fs in /run /var/run /var/tmp /var/log; do
	info "Mounting ${fs}"
	mount -t tmpfs tmpfs ${fs} -o rw,nosuid,nodev
done

info "Setup network interfaces ..."
for intf in /sys/class/net/*; do
	intf=$(basename ${intf})
	ip a s dev ${intf} &> /dev/null || continue
	case ${intf} in
		lo|eth*|dummy*)
			ip link set up dev ${intf}
			;;
	esac
done

# Mount devpts for remote logints
mkdir -p /dev/pts
mount -t devpts none /dev/pts

# Set ip address on management interface (it should always be eth0)
# The corresponding TAP on host machine should have ip 10.0.${VM_INDEX}.1/24
ip addr add 10.0.${VM_INDEX}.2/24 dev eth0

info "Starting dropbear server ..."
# Run dropbear with option -E to log errors to stderr
dropbear -E

# Notify host that we have finished booting
echo "$(hostname) booted!" | nc 10.0.${VM_INDEX}.1 20000

# Spawn a hell
while true; do
	info "Spawning ${SHELL}"
	cd ${HOME}
	${SHELL} -i
done
