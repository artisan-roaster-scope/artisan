# -*- mode: python -*-

import os
from PyInstaller.utils.hooks import get_package_paths

block_cipher = None

# add snap7 libs
BINARIES = [(os.path.join(get_package_paths('snap7')[1], 'lib/libsnap7.so'), 'snap7/lib' )]
# add yocto libs
yocto_lib_path = os.path.join(get_package_paths('yoctopuce')[1], 'cdll')
BINARIES.extend([(os.path.join(yocto_lib_path, fn),'yoctopuce/cdll') for fn in os.listdir(yocto_lib_path) if fn.endswith('.so')])

path=os.environ['HOME'] + '/artisan-master/src'
if not os.path.isdir(path):
    path=os.environ['HOME'] + '/artisan/src'
# For Travis
if not os.path.isdir(path):
    path=os.getcwd()

hiddenimports_list=[
    'matplotlib.backends.backend_pdf',
    'matplotlib.backends.backend_svg'
]

a = Analysis(['artisan.py'],
    pathex=[path],
    binaries=BINARIES,
    datas=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    hiddenimports=hiddenimports_list,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher)



# exclude libs from the build
a.binaries -= TOC([
                  # excluding libwayland libs
                  # see
                  #   https://github.com/pyinstaller/pyinstaller/issues/7506
                  #   https://github.com/gridsync/gridsync/issues/631
                  #   https://stackoverflow.com/questions/57466637/how-to-exclude-unnecessary-qt-so-files-when-packaging-an-application
                  ('libwayland-client.so.0', None, None),
                  ('libwayland-cursor.so.0', None, None),
                  ('libwayland-egl.so.1', None, None),
                  ('libwayland-server.so.0', None, None) # RPi
])

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True, # should be True for onedir
          name='artisan',
          debug=False,
          strip=False,
          upx=True,
          console=True)

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='artisan')
