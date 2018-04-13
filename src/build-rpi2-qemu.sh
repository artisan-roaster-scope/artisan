#!/bin/bash

set -exm

# User configurable variables
KERNEL_IMAGE="kernel-qemu-4.9.59-stretch"
RASPBIAN_DATE="2018-03-13"
RASPBIAN_URL="http://director.downloads.raspberrypi.org/raspbian/images/raspbian-2018-03-14"
#RASPBIAN_URL="http://ftp.jaist.ac.jp/pub/raspberrypi/raspbian/images/raspbian-2018-03-14"

SSH="ssh -p 2222 -o StrictHostKeyChecking=no"
SCP="scp -P 2222 -o StrictHostKeyChecking=no"
RASPBIAN_ZIP=${RASPBIAN_DATE}-raspbian-stretch.zip
RASPBIAN_IMAGE=${RASPBIAN_DATE}-raspbian-stretch.img

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
    set -x
    sudo apt install -y python3-pip python3-pyqt5 libusb-1.0 \
	    libblas-dev liblapack-dev libatlas-base-dev gfortran
    while :; do
        pip3 install -r artisan/src/requirements.txt
	if [ $? -eq 0 ]; then
	   break
	fi
    done
    set -e
    cd artisan
    .travis/install-phidgets.sh
    .travis/install-pymodbus.sh
    cd src
    ./build-linux.sh
    ./build-rpi2-deb.sh
EOF
    ${SCP} script pi@localhost:
    trap die ERR
    ${SSH} pi@localhost sh script
    ${SCP} pi@localhost:artisan/src/\*.deb src
    pkill qemu-system-arm
}

ssh-keygen -R "[localhost]:2222"
curl -L -O ${RASPBIAN_URL}/${RASPBIAN_ZIP}
unzip ${RASPBIAN_ZIP}
curl -L -O https://github.com/juokelis/qemu-rpi-kernel/raw/master/${KERNEL_IMAGE}
curl -L -O https://github.com/juokelis/qemu-rpi-kernel/raw/master/versatile-pb.dtb
qemu-img resize ${RASPBIAN_IMAGE} +2G
partitions=`mktemp`
cat <<EOF > $partitions
label: dos
label-id: 0x15ca46a5
device: 2018-03-14-raspbian-stretch.img
unit: sectors

2018-03-14-raspbian-stretch.img1 : start=        8192, size=       85611, type=c
2018-03-14-raspbian-stretch.img2 : start=       98304, size=    13860863, type=83
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
sudo mkdir $mountpoint/home/pi/.ssh
sudo chown 1000  $mountpoint/home/pi/.ssh
sudo chmod go-rwx $mountpoint/home/pi/.ssh
cat /dev/zero | ssh-keygen -q -N "" || true
sudo cp $HOME/.ssh/id_rsa.pub $mountpoint/home/pi/.ssh/authorized_keys
sudo mkdir $mountpoint/home/pi/artisan
if [ -d src ]; then
    sudo cp -R ../artisan/.travis $mountpoint/home/pi/artisan
    sudo cp -R ../artisan/src $mountpoint/home/pi/artisan
    sudo cp -R ../artisan/LICENSE $mountpoint/home/pi/artisan
elif [ -f artisan.py ]; then
    sudo cp -R ../../artisan/.travis $mountpoint/home/pi/artisan
    sudo cp -R ../../artisan/src $mountpoint/home/pi/artisan
    sudo cp -R ../../artisan/LICENSE $mountpoint/home/pi/artisan
fi
cd $mountpoint/home/pi
sudo curl -L -O https://dl.bintray.com/artisan/artisan-cache/libsnap.tar.gz
sudo tar -C $mountpoint/usr/lib -xzf libsnap.tar.gz
sudo curl -L -O https://dl.bintray.com/artisan/artisan-cache/pip-cache.tar.gz   
sudo tar -xzpf pip-cache.tar.gz
sudo rm pip-cache.tar.gz
sudo chown -R 1000 .
sudo curl -L -O https://dl.bintray.com/artisan/artisan-cache/apt-cache.tar.gz
sudo tar -C $mountpoint -xzpf apt-cache.tar.gz
sudo rm apt-cache.tar.gz
cd -
sudo umount $mountpoint
sudo losetup -d /dev/loop0
rmdir $mountpoint

ssh_control &
qemu-system-arm -kernel ${KERNEL_IMAGE} -dtb versatile-pb.dtb -cpu arm1176 -m 256 -M versatilepb -no-reboot -nographic -append "root=/dev/sda2 panic=1 rootfstype=ext4 rw" -hda ${RASPBIAN_IMAGE} -redir tcp:2222::22
