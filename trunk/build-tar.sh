#!/bin/sh

VERSION=$(python3 -c 'import artisanlib; print(artisanlib.__version__)')
NAME=artisan-${VERSION}
TMPDIR=/tmp/$NAME

# cleanup distribution
rm -rf $TMPDIR > /dev/null 2>&1
mkdir $TMPDIR
cd /tmp && svn co http://artisan.googlecode.com/svn/trunk/ $TMPDIR && cd - > /dev/null 2>&1
rm -rf $TMPDIR/build $TMPDIR/dist
rm -f $TMPDIR/screenshots
rm -f $TMPDIR/*.dmg
rm -f $TMPDIR/*.tar
rm -f $TMPDIR/*.tar.gz
rm -f $TMPDIR/*.deb
rm -f $TMPDIR/*.rpm
find $TMPDIR -name .svn -exec rm -rf {} \; > /dev/null 2>&1
find $TMPDIR -name \*.pyc -exec rm -f {} \; > /dev/null 2>&1
find $TMPDIR -name \*.DS_Store -exec rm -f {} \; > /dev/null 2>&1

# create tar
cd /tmp && tar -cf $NAME.tar $NAME && cd - > /dev/null 2>&1
gzip $TMPDIR.tar
cp $TMPDIR.tar.gz .
rm $TMPDIR.tar.gz
rm -rf $TMPDIR
