# -*- mode: python -*-

block_cipher = None

import os

path=os.environ['HOME'] + '/artisan-master/src'
if not os.path.isdir(path):
    path=os.environ['HOME'] + '/artisan/src'
if not os.path.isdir(path):
    path=os.environ['HOME'] + '/Documents/Projects/Artisan/RepositoryGIT/src'
# For Travis
if not os.path.isdir(path):
    path=os.getcwd()
    
phidget="/Library/Frameworks/Phidget22.framework/Versions/Current/Phidget22"

a = Analysis(['artisan.py'],
             pathex=[path],
             binaries=[],
             datas=[],
             hiddenimports=['scipy._lib.messagestream', 'pkg_resources.py2_warn'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

# Remove pyi_rth_mplconfig.py useless because it makes our startup slow.
# This hook only applies to one-file distributions.
for s in a.scripts:
    if s[0] == 'pyi_rth_mplconfig':
        a.scripts.remove(s)
        break

a.binaries = [x for x in a.binaries if not x[0].startswith(phidget)]

pyz = PYZ(a.pure, a.zipped_data,cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          exclude_binaries=False,
          name='Artisan',
          debug=False,
          strip=True,
          upx=True,
          console=False )

# prepare Info.plist
import artisanlib
import string
import plistlib
VERSION = artisanlib.__version__
LICENSE = 'GNU General Public License (GPL)'
with open('Info.plist', 'r+b') as fp:
    plist = plistlib.load(fp)
    plist['CFBundleDisplayName'] = 'Artisan'
    plist['CFBundleGetInfoString'] = 'Artisan, Roast Logger'
    plist['CFBundleIdentifier'] = 'org.artisan-scope.artisan'
    plist['CFBundleShortVersionString'] = VERSION
    plist['CFBundleVersion'] = 'Artisan ' + VERSION
    plist['LSMinimumSystemVersion'] = '10.13'
    plist['LSMultipleInstancesProhibited'] = 'false'
    plist['LSPrefersPPC'] = False,
    plist['LSArchitecturePriority'] = 'x86_64',
    plist['NSHumanReadableCopyright'] = LICENSE
    fp.seek(0, os.SEEK_SET)
    fp.truncate()
    plistlib.dump(plist, fp)

app = BUNDLE(exe,
          name='Artisan.app',
          icon='artisan.icns',
          bundle_identifier='org.artisan-scope.artisan')


import os
os.system(r'rm dist/Artisan.app/Contents/Info.plist')

plistlib.writePlist(plist,r'dist/Artisan.app/Contents/Info.plist')
