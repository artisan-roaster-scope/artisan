# -*- mode: python -*-

block_cipher = None

additionalLibs = [] 
#additionalLibs.append( ("libGL.so.1", "/usr/lib64/libGL.so.1", 'BINARY') )

import os

path=os.environ['HOME'] + '/artisan-master/src'
if not os.path.isdir(path):
    path=os.environ['HOME'] + '/artisan/src'
# For Travis
if not os.path.isdir(path):
    path=os.getcwd()

a = Analysis(['artisan.py'],
             pathex=[path],
             binaries=[],
             datas=[],
             hiddenimports=['scipy._lib.messagestream'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='artisan',
          debug=False,
          strip=False,
          upx=True,
          console=True )

coll = COLLECT(exe,
               a.binaries + additionalLibs,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='artisan')
