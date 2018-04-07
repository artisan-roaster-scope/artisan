#!/bin/sh

set -exm

# User configurable variables
KERNEL_IMAGE="kernel-qemu-4.9.59-stretch"
RASPIAN_DATE="2018-03-13"
RASPIAN_URL="http://director.downloads.raspberrypi.org/raspbian_lite/images/raspbian_lite-2018-03-14"

SSH="ssh -p 2222 -o StrictHostKeyChecking=no"
SCP="scp -P 2222 -o StrictHostKeyChecking=no"
RASPIAN_ZIP=${RASPIAN_DATE}-raspbian-stretch-lite.zip
RASPIAN_IMAGE=${RASPIAN_DATE}-raspbian-stretch-lite.img


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
    # Avoid copying the .git directory
    ${SSH} pi@localhost mkdir artisan
    cat <<EOF > script
    set -ex
    sudo apt install -y python3-pip python3-pyqt5 libusb-1.0 \
	    libblas-dev liblapack-dev libatlas-base-dev gfortran p7zip-full
    # Sometimes pip3 fails
    pip3 install -r artisan/src/requirements.txt || pip3 install -r artisan/src/requirements.txt
    (cd snap7-full-1.4.2/build/unix && make -f arm_v6_linux.mk all && sudo make -f arm_v6_linux.mk install);
    (cd libphidget22-* && ./configure --prefix=/usr && make && sudo make install && cp plat/linux/udev/* ../artisan/src/debian/etc/udev/rules.d)
    curl -L -O https://www.phidgets.com/downloads/phidget22/libraries/any/Phidget22Python.zip
    unzip Phidget22Python.zip
    (cd Phidget22Python && sudo python3 setup.py install)
    cd artisan/src
    ./build-centos-pi.sh
    ./build-rpi2-deb.sh
EOF
    ${SCP} script pi@localhost:
    ${SSH} pi@localhost sh script
    ${SCP} pi@localhost:artisan/src/\*.deb .
    pkill qemu-system-arm
}

ssh-keygen -R "[localhost]:2222"
curl -L -O ${RASPIAN_URL}/${RASPIAN_ZIP}
unzip ${RASPIAN_ZIP}
curl -L -O https://github.com/juokelis/qemu-rpi-kernel/raw/master/${KERNEL_IMAGE}
curl -L -O https://github.com/juokelis/qemu-rpi-kernel/raw/master/versatile-pb.dtb
qemu-img resize ${RASPIAN_IMAGE} +2G
parted -s ${RASPIAN_IMAGE} "resizepart 2 4006MB"
sudo losetup -o $((98304*512)) /dev/loop0 ${RASPIAN_IMAGE}
sudo e2fsck -fy /dev/loop0 || true
sudo resize2fs /dev/loop0
mountpoint=`mktemp -d`
sudo mount /dev/loop0 $mountpoint
sudo sed -i'' -e 's/exit 0/\/etc\/init.d\/ssh start/' $mountpoint/etc/rc.local
sudo mkdir $mountpoint/home/pi/.ssh
sudo chown 1000  $mountpoint/home/pi/.ssh
sudo chmod go-rwx $mountpoint/home/pi/.ssh
cat /dev/zero | ssh-keygen -q -N "" || true
sudo cp $HOME/.ssh/id_rsa.pub $mountpoint/home/pi/.ssh/authorized_keys
sudo mkdir $mountpoint/home/pi/artisan
if [ -d src ]; then
    sudo cp -R ../artisan/src $mountpoint/home/pi/artisan
    sudo cp -R ../artisan/LICENSE $mountpoint/home/pi/artisan
elif [ -f artisan.py ]; then
    sudo cp -R ../../artisan/src $mountpoint/home/pi/artisan
    sudo cp -R ../../artisan/LICENSE $mountpoint/home/pi/artisan
fi
cd $mountpoint/home/pi
sudo curl -L -O https://astuteinternet.dl.sourceforge.net/project/snap7/1.4.2/snap7-full-1.4.2.7z
sudo 7z x snap7-full-1.4.2.7z
sudo curl -L -O https://www.phidgets.com/downloads/phidget22/libraries/linux/libphidget22.tar.gz
sudo tar -xzf libphidget22.tar.gz
sudo curl -L -O https://www.phidgets.com/downloads/phidget22/libraries/any/Phidget22Python.zip
sudo unzip Phidget22Python.zip
cd -
sudo umount $mountpoint
sudo losetup -d /dev/loop0
losetup -l
rmdir $mountpoint

ssh_control &
qemu-system-arm -kernel ${KERNEL_IMAGE} -dtb versatile-pb.dtb -cpu arm1176 -m 256 -M versatilepb -no-reboot -nographic -append "root=/dev/sda2 panic=1 rootfstype=ext4" -hda ${RASPIAN_IMAGE} -redir tcp:2222::22
