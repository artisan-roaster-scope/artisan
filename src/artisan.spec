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
from plistlib import Plist
VERSION = artisanlib.__version__
LICENSE = 'GNU General Public License (GPL)'
plist = Plist.fromFile('Info.plist')
plist.update({ 'CFBundleDisplayName': 'Artisan',
                    'CFBundleGetInfoString': 'Artisan, Roast Logger',
                    'CFBundleIdentifier': 'com.google.code.p.Artisan',
                    'CFBundleShortVersionString': VERSION,
                    'CFBundleVersion': 'Artisan ' + VERSION,
                    'LSMinimumSystemVersion': '10.11',
                    'LSMultipleInstancesProhibited': 'false',
                    'LSPrefersPPC': False,
                    'LSArchitecturePriority': 'x86_64',
                    'NSHumanReadableCopyright': LICENSE,
                })


app = BUNDLE(exe,
          name='Artisan.app',
          icon='artisan.icns',
          bundle_identifier='com.google.code.p.Artisan')


import os
os.system(r'rm dist/Artisan.app/Contents/Info.plist')

plist.write(r'dist/Artisan.app/Contents/Info.plist')
