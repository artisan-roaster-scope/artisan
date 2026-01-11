#
"""qtsingleapplication.py
Source: https://github.com/IARI/alsa_jack_gui
Author: https://github.com/IARI
Original Source: http://stackoverflow.com/questions/12712360/qtsingleapplication-for-pyside-or-pyqt
Original Author: user763305
Notes: modified to remove blocking sockets remaining from died server; Updated to support Qt6
"""

import sys
import multiprocessing as mp

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # pylint: disable=unused-import

from PyQt6.QtCore import pyqtSignal, QTextStream, Qt, pyqtSlot
from PyQt6.QtWidgets import QApplication
from PyQt6.QtNetwork import QLocalSocket, QLocalServer


class QtSingleApplication(QApplication):
    messageReceived = pyqtSignal(str)

    activateWindowSignal = pyqtSignal()

    __slots__ = [ '_id', '_viewer_id', '_activationWindow', '_activateOnMessage', '_inSocket', '_outSocket', '_isRunning', '_server',
        '_isRunningViewer', '_outSocketViewer', '_inStream', '_outStream', '_outStreamViewer' ]

    def __init__(self, _id:str, _viewer_id:str, *argv: Any) -> None:

        if sys.platform.startswith('darwin') and mp.current_process().name == 'WebLCDs':
            import AppKit # type: ignore[import-untyped] # ty:ignore[ignore] # pylint: disable=import-error
            info = AppKit.NSBundle.mainBundle().infoDictionary()  # type:ignore[unused-ignore] # @UndefinedVariable # pylint: disable=maybe-no-member
            info['LSBackgroundOnly'] = '1'

        super().__init__(*argv)

        self.activateWindowSignal.connect(self.activateWindow, type=Qt.ConnectionType.QueuedConnection)  # type: ignore[call-arg]

        self._id:str = _id
        self._viewer_id:str = _viewer_id
        self._activationWindow:ApplicationWindow|None = None
        self._activateOnMessage:bool = False

        self._inSocket:QLocalSocket|None = None
        self._outSocket:QLocalSocket|None = None

        self._isRunning:bool = False
        self._isRunningViewer:bool = False

        self._server:QLocalServer|None = None

        self._inStream:QTextStream|None = None
        self._outStream:QTextStream|None = None

        self._outSocketViewer: QLocalSocket|None = None
        self._outStreamViewer:QTextStream|None = None

        # Is there another instance running?
        self._outSocket = QLocalSocket()
        self._outSocket.connectToServer(self._id)
        self._isRunning = self._outSocket.waitForConnected(-1)
        if self._isRunning:
            # Yes, there is.
            self._outStream = QTextStream(self._outSocket)
            # Is there another viewer running?
            self._outSocketViewer = QLocalSocket()
            self._outSocketViewer.connectToServer(self._viewer_id)
            self._isRunningViewer = self._outSocketViewer.waitForConnected(-1)
            if self._isRunningViewer:
                self._outStreamViewer = QTextStream(self._outSocketViewer)
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

    def activationWindow(self) -> 'ApplicationWindow|None':
        return self._activationWindow

    def setActivationWindow(self, activationWindow:'ApplicationWindow', activateOnMessage:bool = True) -> None:
        self._activationWindow = activationWindow
        self._activateOnMessage = activateOnMessage

    @pyqtSlot()
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
