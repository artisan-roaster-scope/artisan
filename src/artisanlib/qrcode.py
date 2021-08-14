import qrcode
from PyQt5.QtGui import QImage, QPixmap,QPainter
from PyQt5.QtCore import Qt

##########################################################################
#####################     QR Image   #####################################
##########################################################################

class QRImage(qrcode.image.base.BaseImage):

    def new_image(self, **_kwargs):
        img = QImage(self.pixel_size, self.pixel_size, QImage.Format_RGB16)
        img.fill(Qt.white)
        return img

    def pixmap(self):
        return QPixmap.fromImage(self.get_image())

    def drawrect(self, row, col):
        painter = QPainter(self.get_image())
        painter.fillRect(
            (col + self.border) * self.box_size,
            (row + self.border) * self.box_size,
            self.box_size, self.box_size,
            Qt.black)

    def save(self, stream, kind=None):
        pass
    
    def process(self):
        pass

    def drawrect_context(self, row, col, active, context):
        pass

def QRlabel(url_str):
    qr = qrcode.QRCode(
        version=None, # 1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=4,
        border=1,
        image_factory=QRImage)
    qr.add_data(url_str)
    qr.make(fit=True)
    return qr