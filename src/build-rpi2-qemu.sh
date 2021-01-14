#!/bin/bash

set -ex

# User configurable variables
KERNEL_IMAGE="kernel-qemu-4.9.59-stretch"
KERNEL_SHA1=bdba230db1d404b41485a002d60b0db4ba571f1d
DTB=versatile-pb.dtb
DTB_SHA1=ab13a35a2b0862ee769a9de20bc975104f4f244d
RASPBIAN_DATE="2018-04-18"
RASPBIAN_URL="http://director.downloads.raspberrypi.org/raspbian/images/raspbian-2018-04-19"
RASPBIAN_MIRROR_URL="http://ftp.jaist.ac.jp/pub/raspberrypi/raspbian/images/raspbian-2018-04-19"
RASPBIAN_ZIP_SHA1=f141331a5613c3d5d94ff60cdbf0a25097b3520a

SSH="ssh -p 2222 -o StrictHostKeyChecking=no"
SCP="scp -P 2222 -o StrictHostKeyChecking=no"
RASPBIAN_ZIP=${RASPBIAN_DATE}-raspbian-stretch.zip
RASPBIAN_IMAGE=${RASPBIAN_DATE}-raspbian-stretch.img

check_sha1()
{
    file=`mktemp`
    cat >> $file <<EOF
    ${KERNEL_SHA1} ${KERNEL_IMAGE}
    ${DTB_SHA1} ${DTB}
    ${RASPBIAN_ZIP_SHA1} ${RASPBIAN_ZIP}
EOF
    sha1sum -c $file
    rm $file
}

die()
{
    pkill -9 qemu-system-arm
    exit 1
}

ssh_control()
{
    set +ex
    while :; do
	${SSH} pi@localhost ls 2>&1 >/dev/null
	if [ $? -eq 0 ]; then
	    break
	fi
	sleep 1
    done
    set -ex
    cat <<EOF > script
    set -ex
    export ARTISAN_OS=rpi
    sudo apt remove -y python3-serial
    sudo apt install -y python3-pip python3-pyqt5 libusb-1.0 \
	    libblas-dev liblapack-dev libatlas-base-dev gfortran
    set +e
    sudo pip3 install --upgrade setuptools # prevents urlib3 error "TypeError: unsupported operand type(s) for -=: 'Retry' and 'int'" on pip3 retries
    while :; do
        pip3 install -r artisan/src/requirements.txt
	if [ \$? -eq 0 ]; then
	   break
	fi
    done
    while :; do
        pip3 install -r artisan/src/requirements-rpi.txt
	if [ \$? -eq 0 ]; then
	   break
	fi
    done
#    (cd Phidget22Python && sudo python3 setup.py install) # now installed via pip
    cd artisan
    cd src
    ./build-linux.sh
    ./build-rpi2-deb.sh
EOF
    ${SCP} script pi@localhost:
    trap die ERR
    ${SSH} pi@localhost bash script
    ${SCP} pi@localhost:artisan/src/\*.deb src
    pkill qemu-system-arm
}

ssh-keygen -R "[localhost]:2222"
if [ ! -f ${RASPBIAN_ZIP} ]; then
    (sleep 600; pgrep curl && pkill curl)&
    curl -L -O ${RASPBIAN_URL}/${RASPBIAN_ZIP} || curl -C - -L -O ${RASPBIAN_MIRROR_URL}/${RASPBIAN_ZIP}

fi
if [ ! -f ${RASPBIAN_IMAGE} ]; then
    unzip ${RASPBIAN_ZIP}
fi
if [ ! -f ${KERNEL_IMAGE} ]; then
    curl -L -O https://github.com/juokelis/qemu-rpi-kernel/raw/master/${KERNEL_IMAGE}
fi
if [ ! -f versatile-pb.dtb ]; then
    curl -L -O https://github.com/juokelis/qemu-rpi-kernel/raw/master/versatile-pb.dtb
fi
check_sha1
qemu-img resize -f raw ${RASPBIAN_IMAGE} +2G
LABEL_ID=`sfdisk -d ${RASPBIAN_IMAGE} | grep label-id | awk -F: '{ print $2 }'`
if [ -z $LABEL_ID ]; then
    echo unable to read label-id
    exit 1
fi
partitions=`mktemp`
cat <<EOF > $partitions
label: dos
label-id: ${LABEL_ID}
device: ${RASPBIAN_IMAGE}
unit: sectors

${RASPBIAN_IMAGE}1 : start=        8192, size=       85611, type=c
${RASPBIAN_IMAGE}2 : start=       98304, size=    13869055, type=83
EOF
sfdisk  ${RASPBIAN_IMAGE} < $partitions
rm $partitions
sudo losetup -o $((98304*512)) /dev/loop0 ${RASPBIAN_IMAGE}
sudo e2fsck -fy /dev/loop0 || true
sudo resize2fs /dev/loop0
mountpoint=`mktemp -d`
sudo mount /dev/loop0 $mountpoint
sudo sed -i'' -e 's/exit 0/\/etc\/init.d\/ssh start/' $mountpoint/etc/rc.local
sudo sh -c "echo 'systemctl set-default multi-user.target --force' >> $mountpoint/etc/rc.local"
sudo sh -c "echo 'systemctl stop lightdm.service --force' >> $mountpoint/etc/rc.local"
sudo sh -c "echo 'systemctl stop graphical.target --force' >> $mountpoint/etc/rc.local"
sudo sh -c "echo 'systemctl stop plymouth.service --force' >> $mountpoint/etc/rc.local"
# HACK to work around piwheels.org DNS problems
sudo sh -c "echo '93.93.129.174 proxy.mythic-beasts.com piwheels.org www.piwheels.org' >> $mountpoint/etc/hosts"
sudo rm $mountpoint/etc/ld.so.preload
sudo mkdir $mountpoint/home/pi/.ssh
sudo chown 1000  $mountpoint/home/pi/.ssh
sudo chmod go-rwx $mountpoint/home/pi/.ssh
cat /dev/zero | ssh-keygen -q -N "" || true
sudo cp $HOME/.ssh/id_rsa.pub $mountpoint/home/pi/.ssh/authorized_keys
sudo mkdir $mountpoint/home/pi/artisan
#dave
pwd
if [ -d src ]; then
    sudo cp -R ./.ci $mountpoint/home/pi/artisan
    sudo cp -R ./src $mountpoint/home/pi/artisan
    sudo cp -R ./LICENSE $mountpoint/home/pi/artisan
#if [ -d src ]; then
#    sudo cp -R ../artisan/.ci $mountpoint/home/pi/artisan
#    sudo cp -R ../artisan/src $mountpoint/home/pi/artisan
#    sudo cp -R ../artisan/LICENSE $mountpoint/home/pi/artisan
elif [ -f artisan.py ]; then
    sudo cp -R ../../artisan/.ci $mountpoint/home/pi/artisan
    sudo cp -R ../../artisan/src $mountpoint/home/pi/artisan
    sudo cp -R ../../artisan/LICENSE $mountpoint/home/pi/artisan
fi
cd $mountpoint/home/pi
sudo curl -L -O https://dl.bintray.com/artisan/artisan-cache/libsnap.tar.gz
sudo tar -C $mountpoint/usr/lib -xzf libsnap.tar.gz
sudo curl -L -O https://dl.bintray.com/artisan/artisan-cache/libphidget22.tar.gz
sudo tar -C $mountpoint/usr/lib -xzf libphidget22.tar.gz
#sudo curl -L -O https://www.phidgets.com/downloads/phidget22/libraries/any/Phidget22Python.zip # Phidget Python lib now installed via pip
#sudo unzip -q Phidget22Python.zip
sudo chown -R 1000 .
sudo curl -L -O https://dl.bintray.com/artisan/artisan-cache/apt-cache.tar.gz
sudo tar -C $mountpoint -xzpf apt-cache.tar.gz
sudo rm apt-cache.tar.gz
cd -
sudo umount $mountpoint
sudo losetup -d /dev/loop0
rmdir $mountpoint

ssh_control &
qemu-system-arm -kernel ${KERNEL_IMAGE} -dtb versatile-pb.dtb -cpu arm1176 -m 256 -M versatilepb -no-reboot -nographic -append "root=/dev/sda2 panic=1 rootfstype=ext4 rw" -drive file=${RASPBIAN_IMAGE},format=raw -redir tcp:2222::22


