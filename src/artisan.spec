# -*- mode: python -*-

block_cipher = None

import os
if os.environ.get('TRAVIS'):
    path=['/Users/travis/build/artisan-roaster-scope/artisan/src']
else:
    path=['/Users/luther/Documents/Projects/Artisan/RepositoryGIT/src']
    
phidget="/Library/Frameworks/Phidget22.framework/Versions/Current/Phidget22"

a = Analysis(['artisan.py'],
             pathex=path,
             binaries=[],
             datas=[],
             hiddenimports=['scipy._lib.messagestream'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

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
    plist['CFBundleIdentifier'] = 'com.google.code.p.Artisan'
    plist['CFBundleShortVersionString'] = VERSION
    plist['CFBundleVersion'] = 'Artisan ' + VERSION
    plist['LSMinimumSystemVersion'] = '10.13'
    plist['LSMultipleInstancesProhibited'] = 'false'
    plist['LSPrefersPPC'] = False,
    plist['LSArchitecturePriority'] = 'x86_64',
    plist['NSHumanReadableCopyright'] = LICENSE
    plistlib.dump(plist, fp)

app = BUNDLE(exe,
          name='Artisan.app',
          icon='artisan.icns',
          bundle_identifier='com.google.code.p.Artisan')


import os
os.system(r'rm dist/Artisan.app/Contents/Info.plist')

plist.write(r'dist/Artisan.app/Contents/Info.plist')
