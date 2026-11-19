#!/bin/sh
# ABOUT
# CI install shell script for Artisan macOS builds
#
# COPYRIGHT (C) 2010-2026 The Artisan team represented by
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
# AUTHOR
# Dave Baxter, Marko Luther 2025

#set -ex # increased logging
set -e # reduced logging

echo "** Running install-macos.sh"
#.ci/silence.sh brew update # this seems to help to work around some homebrew issues; and fails on others

hash -r
uname -srv
which python3
python3 --version
openssl version -a

# to work around a wget open ssl issue: dyld: Library not loaded: /usr/local/opt/openssl/lib/libssl.1.0.0.dylib
# however for now we settled to use curl instead to download the upload script
#brew uninstall wget
#brew install wget


#brew install p7zip

python -m pip install --upgrade pip
sudo -H python -m pip install --root-user-action=ignore -r src/requirements.txt | sed '/^Ignoring/d'

# patch google packages to help out py2app
sudo -H touch ${PYTHONSITEPKGS}/google/__init__.py
sudo -H touch ${PYTHONSITEPKGS}/google/_upb/__init__.py
sudo -H touch ${PYTHONSITEPKGS}/google/protobuf/__init__.py
sudo -H touch ${PYTHONSITEPKGS}/google/protobuf/internal/__init__.py


# show set of libraries are installed
echo "**** pip freeze ****"
python3 -m pip freeze
