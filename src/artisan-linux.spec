# -*- mode: python -*-
#
# ABOUT
# artisan-linux.spec script for artisan linux builds using pyinstaller
#
# COPYRIGHT (C) 2010-2026 The artisan team represented by
#   Marko Luther <marko.luther@gmx.net> (maintainer) and all contributors
#
# LICENSE
# This program or module is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# MAINTAINER
# Marko Luther, 2026

import os
from PyInstaller.utils.hooks import get_package_paths, collect_submodules

block_cipher = None

# add snap7 libs
BINARIES = [(os.path.join(get_package_paths('snap7')[1], 'lib/libsnap7.so'), 'snap7/lib' )]
# add yocto libs
yocto_lib_path = os.path.join(get_package_paths('yoctopuce')[1], 'cdll')
BINARIES.extend([(os.path.join(yocto_lib_path, fn),'yoctopuce/cdll') for fn in os.listdir(yocto_lib_path) if fn.endswith('.so')])
# add phidgets libs
phidgets_lib_path = os.path.join(get_package_paths('Phidget22')[1], '.libs')
BINARIES.extend([(os.path.join(phidgets_lib_path, fn),'Phidget22/.libs') for fn in os.listdir(phidgets_lib_path) if fn.endswith('.so')])

path=os.environ['HOME'] + '/artisan-master/src'
if not os.path.isdir(path):
    path=os.environ['HOME'] + '/artisan/src'
# For Travis
if not os.path.isdir(path):
    path=os.getcwd()

hiddenimports_list=[
    'matplotlib.backends.backend_pdf',
    'matplotlib.backends.backend_svg',
    'babel.numbers'  # should not be needed as it got fixed in pyinstaller 6.11
] + collect_submodules('dbus_fast')

EXCLUDES = [
    'tkinter',
    'mypy',
    'hypothesis',
    'tornado',
    'pkg_resources',
    'setuptools',
    'curses',
    'matplotlib.tests',
    'numpy.tests',
    'scipy.tests',
    'numpy.lib.tests',
    'numpy.ma.tests',
    'numpy.matrixlib.tests',
    'numpy.polynomial.tests',
    'numpy.random.tests',
    'numpy.testing.tests',
    'numpy.typing.tests',
    'scipy._lib.tests',
    'scipy.constants.tests',
    'scipy.datasets.tests',
    'scipy.fft.tests',
    'scipy.fftpack.tests',
    'scipy.integrate._ivp.tests',
    'scipy.interpolate.tests',
    'scipy.io._harwell_boeing.tests',
    'scipy.io.arff.tests',
    'scipy.io.matlab.tests',
    'scipy.io.tests',
    'scipy.linalg.tests',
    'scipy.ndimage.tests',
    'scipy.odr.tests',
    'scipy.optimize.tests',
    'scipy.signal.tests',
    'scipy.sparse.linalg._isolve.tests',
    'scipy.sparse.linalg.tests',
    'scipy.sparse.tests',
    'scipy.spatial.tests',
    'scipy.spatial.transform.tests',
    'scipy.special.tests',
    'scipy.stats.tests',
    'PyQt5',
    'PyQt6.Multimedia',
    'PyQt6.Network',
    'PyQt6.PrintSupport',
    'PyQt6.QtRemoteObjects',
    'PyQt6.QtSensors',
    'PyQt6.QtSerialPort',
    'PyQt6.QtSpatialAudio',
    'PyQt6.QtTest',
    'PyQt6.QtTextToSpeech',
# the following are required by QtWebEngineWidgets and thus by QtWebEngine for the HTML2PDF export
    'PyQt6.QtQuick',
    'PyQt6.QtQml',
    'PyQt6.QtQmlMeta',
    'PyQt6.QtQmlModels',
    'PyQt6.QtQmlWorkerScript',
    'PyQt6.OpenGL',
    'PyQt6.QtWebChannel',
    'PyQt6.QtPositioning',
    'PyQt6.QtWebEngineQuick'
]


DATA_FILES = [
#    (os.path.join(get_package_paths('PyQt6')[1], 'Qt6/translations/qtwebengine_locales/en-US.pak'), 'PyQt6/Qt6/translations/qtwebengine_locales')
]

a = Analysis(['artisan.py'],
    pathex=[path],
    binaries=BINARIES,
    datas=DATA_FILES,
    hookspath=[],
    runtime_hooks=['./pyinstaller_hooks/rthooks/pyi_rth_mplconfig.py'], # overwrites default MPL runtime hook which keeps loading font cache from (new) temp directory
    excludes=EXCLUDES,
    hiddenimports=hiddenimports_list,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    optimize=2,
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
          strip=False, # builds fails to start with strip=True with some "address/offset not page-aligned" (scipy/blas)
          upx=True,
          console=True)

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False, # builds fails to start with strip=True with some "address/offset not page-aligned" (scipy/blas)
               upx=True,
               name='artisan')
