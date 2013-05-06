#!/bin/sh

NAME=artisan-0.6.0
TMPDIR=/tmp/$NAME

# cleanup distribution
rm -rf $TMPDIR > /dev/null 2>&1
mkdir $TMPDIR
cp -R * $TMPDIR
rm -rf $TMPDIR/build $TMPDIR/dist
rm -f $TMPDIR/*.dmg
rm -f $TMPDIR/*.tar
rm -f $TMPDIR/*.tar.gz
rm -f $TMPDIR/*.deb
rm -f $TMPDIR/*.rpm
find $TMPDIR -name .svn -exec rm -rf {} \; > /dev/null 2>&1
find $TMPDIR -name \*.pyc -exec rm -f {} \; > /dev/null 2>&1
find $TMPDIR -name \*.DS_Store -exec rm -f {} \; > /dev/null 2>&1

# create tar
cd /tmp && tar -cf $NAME.tar $NAME && cd -
gzip $TMPDIR.tar
rm $TMPDIR.tar.gz
cp $TMPDIR.tar.gz .
