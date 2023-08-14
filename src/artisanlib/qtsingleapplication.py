#

'''
Source: https://github.com/IARI/alsa_jack_gui
Author: https://github.com/IARI
Original Source: http://stackoverflow.com/questions/12712360/qtsingleapplication-for-pyside-or-pyqt
Original Author: user763305
Notes: Modified for PyQt5; further modified to remove blocking sockets remaining from died server
Updated to support QT6
'''

import sys
import multiprocessing as mp

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # pylint: disable=unused-import

try:
    from PyQt6.QtCore import pyqtSignal, QTextStream, Qt, pyqtSlot # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import QApplication # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtNetwork import QLocalSocket, QLocalServer # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import pyqtSignal, QTextStream, Qt, pyqtSlot # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import QApplication # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtNetwork import QLocalSocket, QLocalServer # type: ignore # @UnusedImport @Reimport  @UnresolvedImport


class QtSingleApplication(QApplication): # pyright: ignore [reportGeneralTypeIssues] # Argument to class must be a base class
    messageReceived = pyqtSignal(str)

    __slots__ = [ '_id', '_viewer_id', '_activationWindow', '_activateOnMessage', '_inSocket', '_outSocket', '_isRunning', '_server',
        '_isRunningViewer', '_outSocketViewer', '_inStream', '_outStream', '_outStreamViewer' ]

    def __init__(self, _id:str, _viewer_id:str, *argv) -> None:

        if sys.platform.startswith('darwin') and mp.current_process().name == 'WebLCDs':
            import AppKit # type: ignore # pylint: disable=import-error
            info = AppKit.NSBundle.mainBundle().infoDictionary()  # type:ignore # @UndefinedVariable # pylint: disable=maybe-no-member
            info['LSBackgroundOnly'] = '1'

        super().__init__(*argv)

        self._id:str = _id
        self._viewer_id:str = _viewer_id
        self._activationWindow:Optional['ApplicationWindow'] = None
        self._activateOnMessage:bool = False

        self._inSocket:Optional[QLocalSocket] = None
        self._outSocket:Optional[QLocalSocket] = None

        self._isRunning:bool = False
        self._isRunningViewer:bool = False

        self._server:Optional[QLocalServer] = None

        self._inStream:Optional[QTextStream] = None
        self._outStream:Optional[QTextStream] = None

        self._outSocketViewer: Optional[QLocalSocket] = None
        self._outStreamViewer:Optional[QTextStream] = None

        # we exclude the WebLCDs parallel process from participating any Artisan inter-app communication
        if mp.current_process().name != 'WebLCDs':
            # Is there another instance running?
            self._outSocket = QLocalSocket()
            self._outSocket.connectToServer(self._id)
            self._isRunning = self._outSocket.waitForConnected(-1)
            if self._isRunning:
                # Yes, there is.
                self._outStream = QTextStream(self._outSocket)
                try:
                    self._outStream.setCodec('UTF-8') # type: ignore # setCodec not available in PyQt6, but UTF-8 the default encoding
                except Exception: # pylint: disable=broad-except
                    pass
                # Is there another viewer running?
                self._outSocketViewer = QLocalSocket()
                self._outSocketViewer.connectToServer(self._viewer_id)
                self._isRunningViewer = self._outSocketViewer.waitForConnected(-1)
                if self._isRunningViewer:
                    self._outStreamViewer = QTextStream(self._outSocketViewer)
                    try:
                        self._outStreamViewer.setCodec('UTF-8') # type: ignore # setCodec not available in PyQt6, but UTF-8 the default encoding
                    except Exception: # pylint: disable=broad-except
                        pass
                else:
                    # app is running, we announce us as viewer app
                    # First we remove existing servers of that name that might not have been properly closed as the server died
                    QLocalServer.removeServer(self._viewer_id)
                    self._outSocketViewer = None
                    self._outStreamViewer = None
                    self._inSocket = None
                    self._inStream = None
                    self._server = QLocalServer()
                    self._server.listen(self._viewer_id)
                    self._server.newConnection.connect(self._onNewConnection)
            else:
                self._isRunningViewer = False
                # No, there isn't.
                # First we remove existing servers of that name that might not have been properly closed as the server died
                QLocalServer.removeServer(self._id)
                self._outSocket = None
                self._outStream = None
                self._inSocket = None
                self._inStream = None
                self._server = QLocalServer()
                self._server.listen(self._id)
                self._server.newConnection.connect(self._onNewConnection)

    def isRunning(self) -> bool:
        return self._isRunning

    def isRunningViewer(self) -> bool:
        return self._isRunningViewer

    def id(self) -> str: # noqa: A003
        return self._id

    def activationWindow(self) -> Optional['ApplicationWindow']:
        return self._activationWindow

    def setActivationWindow(self, activationWindow:'ApplicationWindow', activateOnMessage=True) -> None:
        self._activationWindow = activationWindow
        self._activateOnMessage = activateOnMessage

    def activateWindow(self) -> None:
        if not self._activationWindow:
            return

        self._activationWindow.show()
        self._activationWindow.setWindowState(
            self._activationWindow.windowState() & ~Qt.WindowState.WindowMinimized)
        self._activationWindow.raise_()
        self._activationWindow.activateWindow()

    def sendMessage(self, msg:str) -> bool:
        if self._outStream is None or self._outSocket is None:
            return False
        self._outStream << msg << '\n' # pylint: disable=pointless-statement # pyright: ignore [reportUnusedExpression] # warning: Expression value is unused
        self._outStream.flush()
        return self._outSocket.waitForBytesWritten()

    @pyqtSlot()
    def _onNewConnection(self) -> None:
        if self._inSocket is not None:
            self._inSocket.readyRead.disconnect(self._onReadyRead)
        if self._server is None:
            return
        self._inSocket = self._server.nextPendingConnection()
        self._inStream = QTextStream(self._inSocket)
        try:
            self._inStream.setCodec('UTF-8') # type: ignore # setCodec not available in PyQt6, but UTF-8 the default encoding
        except Exception: # pylint: disable=broad-except
            pass
        if self._inSocket is not None:
            self._inSocket.readyRead.connect(self._onReadyRead)
        if self._activateOnMessage and self._isRunning:
            self.activateWindow()

    @pyqtSlot()
    def _onReadyRead(self) -> None:
        while True:
            if self._inStream is None:
                break
            msg = self._inStream.readLine()
            if not msg:
                break
            self.messageReceived.emit(msg)
