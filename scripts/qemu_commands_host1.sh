PROG_NAME=$(readlink -f $0)
VM_NAME="host1"
KERNEL_DIR="/tmp/install"
KERNEL_IMAGE_NAME="linux"
TMP_DIR="/tmp/host1"
MON_PIPE="$TMP_DIR/vm-$VM_NAME-monitor.pipe"
MGMT_PIPE="$TMP_DIR/vm-$VM_NAME-mgmt-console.pipe"
VM_INIT=$(readlink -f "vm_init.sh")

rm -rf $TMP_DIR
mkdir $TMP_DIR

rm -rf "$PWD/vmrootfs"
mkdir "$PWD/vmrootfs"

qemu-system-x86_64 -m 384m \
    \
    -chardev socket,id=serial0,path=$MGMT_PIPE,server,nowait \
    -serial chardev:serial0 \
    \
    -chardev socket,id=monitor,path=$MON_PIPE,server,nowait \
    -mon chardev=monitor,mode=readline,default \
    \
    -fsdev local,security_model=passthrough,id=fsdev-root,path="/",readonly \
    -device virtio-9p-pci,id=fs-root,fsdev=fsdev-root,mount_tag=/dev/root \
    -fsdev local,security_model=none,id=fsdev-home,path="$PWD/vmrootfs" \
    -device virtio-9p-pci,id=fs-home,fsdev=fsdev-home,mount_tag=overlayshare \
    -fsdev local,security_model=none,id=fsdev-lab,path=$KERNEL_DIR \
    -device virtio-9p-pci,id=fs-lab,fsdev=fsdev-lab,mount_tag=kernelshare \
    \
    \
    \
    -kernel "${KERNEL_DIR}/${KERNEL_IMAGE_NAME}" \
    -append "init=${VM_INIT} console=tty0 console=ttyS0,115200n8 uts=$VM_NAME root=/dev/root rootflags=trans=virtio,version=9p2000.u ro rootfstype=9p"
