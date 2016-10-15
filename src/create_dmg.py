#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# create_dmg.py
#
# Copyright (c) 2016, Paul Holleis, Marko Luther
# All rights reserved.
# 
# 
# LICENSE
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import artisanlib

# current version
VERSION = artisanlib.__version__

dist_name = r"artisan-mac-" + VERSION + r".dmg"
os.system(r"rm " + dist_name)
os.system(r'hdiutil create ' + dist_name + r' -volname "Artisan" -fs HFS+ -srcfolder "dist"')