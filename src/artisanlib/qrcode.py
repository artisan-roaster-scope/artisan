#

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
