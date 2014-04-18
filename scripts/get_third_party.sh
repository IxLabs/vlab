#!/bin/bash

# Gets third party apps like Busybox and Dropbear and statically compiles them
# $1 - Target path for downloading and building apps

if [ -z "$1" ]
	then
	echo -e "Error: Target path not specified\n" \
		"Please specify a directory where to download and build apps. E.g \n" \
		"$0 /tmp"
	exit 1
fi

TARGET_DIR=$1
BUSYBOX_URL="http://www.busybox.net/downloads"
BUSYBOX="busybox-1.21.0"
DROPBEAR_URL="https://matt.ucc.asn.au/dropbear/releases"
DROPBEAR="dropbear-2014.63"
DROPBEAR_PROGRAMS="dropbear dbclient dropbearkey dropbearconvert scp"

# Downloads and extracts third party app
# $1 - name of the app. E.g.: busybox-1.21.0.tar.bz2
# $2 - base url to download the app
get_and_extract() {
	echo "Downloading $1 ..."
	wget -q "$2/$1"

	echo "Extracting $1 ..."
	tar -xf $1
	rm $1
}

# Download Busybox and Dropbear
cd ${TARGET_DIR}

get_and_extract "${BUSYBOX}.tar.bz2" ${BUSYBOX_URL}
get_and_extract "${DROPBEAR}.tar.bz2" ${DROPBEAR_URL}

# Build Busybox statically
cd ${TARGET_DIR}/${BUSYBOX}

echo "Building ${BUSYBOX} ..."
make defconfig &> /dev/null
echo "CONFIG_STATIC=y" >> .config
make &> /dev/null

# Build Dropbear statically
cd ${TARGET_DIR}/${DROPBEAR}

echo "Building ${DROPBEAR} ..."
./configure &> /dev/null
# If there's need for all-in-one binary, set MULTI=1 below and create symlinks
# like this: ln -s dropbearmulti dropbear; ln -s dropbearmulti dbclient; etc
make PROGRAMS="${DROPBEAR_PROGRAMS}" STATIC=1 &> /dev/null

echo "Busybox binary can be found at ${TARGET_DIR}/${BUSYBOX}/busybox"
echo -e "Dropbear binaries, namely ${DROPBEAR_PROGRAMS} can be found at\n\t" \
	"${TARGET_DIR}/${DROPBEAR}/\n"
