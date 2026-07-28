# ABOUT
# QR support for artisan scope
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

import qrcode
import qrcode.constants
from qrcode.main import QRCode
from qrcode.image.base import BaseImage

from typing import override, Any

from PyQt6.QtGui import QImage, QPixmap,QPainter
from PyQt6.QtCore import Qt

##########################################################################
#####################     QR Image   #####################################
##########################################################################

class QRImage(BaseImage):

    @override
    def new_image(self, **_kwargs:dict[Any,Any]) -> QImage:
        img = QImage(self.pixel_size, self.pixel_size, QImage.Format.Format_RGB16)
        img.fill(Qt.GlobalColor.white)
        return img

    def pixmap(self) -> QPixmap:
        return QPixmap.fromImage(self.get_image())

    @override
    def drawrect(self, row:int, col:int) -> None:
        painter = QPainter(self.get_image())
        painter.fillRect(
            (col + self.border) * self.box_size,
            (row + self.border) * self.box_size,
            self.box_size, self.box_size,
            Qt.GlobalColor.black)

    @override
    def save(self, stream:Any, kind:str|None = None) -> None:
        pass

    @override
    def process(self) -> None:
        pass

    @override
    def drawrect_context(self, row: int, col: int, qr: QRCode[Any]) -> None:
        pass

def QRlabel(url_str:str) -> QRCode[Any]:
    qr = QRCode(
        version=None, # 1,
        error_correction=qrcode.constants.ERROR_CORRECT_L, # pyright:ignore # pyright: "constants" is not a known member of module "qrcode"
        box_size=4,
        border=1,
        image_factory=QRImage)
    qr.add_data(url_str)
    qr.make(fit=True)
    return qr
