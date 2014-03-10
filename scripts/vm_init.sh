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

hostname ${uts}
# Set path
export TERM=screen
export HOME=/root
export PATH=/bin:/usr/local/bin:/usr/bin:/sbin:/usr/local/sbin:/usr/sbin:$HOME/bin

# Set overlayfs
mount -t tmpfs tmpfs /tmp -o rw
mount -n -t proc proc /proc
mount -n -t sysfs sys /sys

mkdir /tmp/vmroot
mount -t 9p overlayshare /tmp/vmroot -o trans=virtio,version=9p2000.L,access=0,rw

# Mount home dir on /root
mkdir /tmp/vmroot/root
mount -o bind /tmp/vmroot/root /root

# Mount /etc
mkdir /tmp/vmroot/etc
mount -o bind /tmp/vmroot/etc /etc

# Mount kernel modules
mkdir /tmp/kernel
mount -t 9p kernelshare /tmp/kernel -o trans=virtio,version=9p2000.L,access=0,rw
mount -o bind /tmp/kernel/lib/modules /lib/modules

# Clean /tmp and /run
for fs in /run /var/run /var/tmp /var/log; do
	mount -t tmpfs tmpfs $fs -o rw,nosuid,nodev
done

# Execute shell
info "Executing ${SHELL}"
exec ${SHELL}
