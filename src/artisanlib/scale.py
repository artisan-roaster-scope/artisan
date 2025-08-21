#
# ABOUT
# Scale support for Artisan

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

# AUTHOR
# Marko Luther, 2025

import math
import platform
import time as libtime
import logging
from enum import IntEnum, unique
from typing import Final, List, Tuple, Optional, Callable

try:
    from PyQt6.QtCore import Qt, QObject, pyqtSignal, pyqtSlot, QTimer # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import Qt, QObject, pyqtSignal, pyqtSlot, QTimer # type: ignore # @UnusedImport @Reimport  @UnresolvedImport

from artisanlib.util import toFloat

_log: Final[logging.Logger] = logging.getLogger(__name__)



#  tuples (model name, connection type) with connection type from {0: BT, 1: WiFi, 2: Serial}
SUPPORTED_SCALES:Final[List[Tuple[str,int]]] = (
[
    ('Acaia', 0) # 0
] if not (platform.system() == 'Windows' and math.floor(toFloat(platform.release())) < 10) else [])

ScaleSpec = Tuple[str,str] # scale name, scale id (eg. ble address)
ScaleSpecs = List[ScaleSpec]

# STABLE_TIMER_PERIOD should be >1sec if Acaia is reporting also non-stable readings, for stable readings a very short period is fine
STABLE_TIMER_PERIOD =350 # period to wait until new weight stabilized before forwarding the new reading via scale_stable_weight_changed signals (> then scale update period!)
MIN_STABLE_WEIGHT_CHANGE = 1 # The weight has to change for at least this amount (in g) to update the last stable weight



@unique
class STATE_ACTION(IntEnum):
    DISCONNECTED = 0        # scale got disconnected
    CONNECTED = 1           # scale got connected
    #
    RELEASED = 2            # scale got released from task
    ASSIGNED_GREEN = 3      # scale got assigned to the green weighing task
    ASSIGNED_ROASTED = 4    # scale got assigned to the roasted weighing task
    #
    ZONE_ENTER = 5          # scale weight entered target area with acceptable accuracy
    ZONE_EXIT = 6           # scale weight left target area with acceptable accuracy
    SWAP_ENTER = 7          # scale empty for bucket swap
    SWAP_EXIT = 8           # scale no longer empty after bucket swap
    TARGET_ENTER = 9        # scale weight entered the 100% target zone
    TARGET_EXIT = 10        # scale weight left the 100% target zone
    OK_ENTER = 11           # scale OK confirmation dialog started
    OK_EXIT = 12            # scale OK confirmation dialog successfully ended with task confirmation
    CANCEL_ENTER = 13       # scale CANCEL confirmation dialog started
    CANCEL_EXIT = 14        # scale CANCEL confirmation dialog successfully ended with task cancellation
    INTERRUPTED = 15        # scale operation interrupted by push-to-cancel guesture
    COMPONENT_CHANGED = 16  # weight items blend component changed
    #
    TARE = 17               # tare send from app



# NOTE: this class and all subclasses are not allowed to hold __slots__
class Scale(QObject):  # pyright:ignore[reportGeneralTypeIssues] # error: Argument to class must be a base class

    scanned_signal = pyqtSignal(list)               # delivers discovered device details
    weight_changed_signal = pyqtSignal(float, bool) # delivers new weight in g with decimals for accurate
                                                    #   conversion and flag indicating stable readings
    battery_changed_signal = pyqtSignal(int)        # delivers new battery level in %
    connected_signal = pyqtSignal()                 # issued on connect
    disconnected_signal = pyqtSignal()              # issued on disconnect

    def __init__(self, model:int, ident:Optional[str] = None, name:Optional[str] = None):
        super().__init__()
        self.model = model
        self.ident = ident
        self.name = name
        #-
        self._stable_only: bool = False # True if scale reports only stable readings
        self._assigned: bool = False

    def set_model(self, model:int) -> None:
        self.model = model

    def get_model(self) -> int:
        return self.model

    def set_ident(self, ident:Optional[str]) -> None:
        self.ident = ident

    def get_ident(self) -> Optional[str]:
        return self.ident

    def set_name(self, name:Optional[str]) -> None:
        self.name = name

    def get_name(self) -> Optional[str]:
        return self.name

    def set_assigned(self, assigned:bool) -> None:
        self._assigned = assigned

    def is_assigned(self) -> bool:
        return self._assigned

    def is_stable_only(self) -> bool:
        return self._stable_only

    #---

    def scan(self) -> None:
        pass

    def connect_scale(self, device_logging:bool) -> None:
        pass

    def disconnect_scale(self) -> None:
        pass

    def tare_scale(self) -> None:
        pass

    def is_connected(self) -> bool: # pylint: disable=no-self-use
        return False

    # weight in g
    def max_weight(self) -> float: # pylint: disable=no-self-use
        return 0

    # readability in g
    def readability(self) -> float: # pylint: disable=no-self-use
        return 0

    def signal_user(self, action:STATE_ACTION) -> None:
        pass


class ScaleManager(QObject): # pyright:ignore[reportGeneralTypeIssues] # error: Argument to class must be a base class

    # triggered from clients:

    scan_scale1_signal = pyqtSignal(int)
    # use model=-1 to reset the scale (unused)
    # scales marked assigned (in use) cannot be set nor disconnected
    # note set setting a scale to a new configuration will disconnect from a previously connected scale
    set_scale1_signal = pyqtSignal(int, str, str) # set scale1 to model, ident and name
    connect_scale1_signal = pyqtSignal(bool) # if argument is True, device logging is activated for scale 1
    disconnect_scale1_signal = pyqtSignal()
    tare_scale1_signal = pyqtSignal()
    signal_user_scale1_signal = pyqtSignal(int)
    reserve_scale1_signal = pyqtSignal()
    release_scale1_signal = pyqtSignal()

    scan_scale2_signal = pyqtSignal(int)
    # use model=-1 to reset the scale (unused)
    # scales marked assigned (in use) cannot be set nor disconnected
    # note set setting a scale to a new configuration will disconnect from a previously connected scale
    set_scale2_signal = pyqtSignal(int, str, str) # set scale2 to model, ident and name
    connect_scale2_signal = pyqtSignal(bool) # if argument is True, device logging is activated for scale 1
    disconnect_scale2_signal = pyqtSignal()
    tare_scale2_signal = pyqtSignal()
    signal_user_scale2_signal = pyqtSignal(int)
    reserve_scale2_signal = pyqtSignal()
    release_scale2_signal = pyqtSignal()

    disconnect_all_signal = pyqtSignal()
    connect_all_signal = pyqtSignal(bool) # if argument is True, device logging is activated for scales


    # subscribed by clients:

    scale1_scanned_signal = pyqtSignal(list) # ScaleSpecs
    scale1_connected_signal = pyqtSignal()
    scale1_disconnected_signal = pyqtSignal()
    scale1_weight_changed_signal = pyqtSignal(int)         # in g
    scale1_stable_weight_changed_signal = pyqtSignal(int)  # in g

    scale2_scanned_signal = pyqtSignal(list) # ScaleSpecs
    scale2_connected_signal = pyqtSignal()
    scale2_disconnected_signal = pyqtSignal()
    scale2_weight_changed_signal = pyqtSignal(int)         # in g
    scale2_stable_weight_changed_signal = pyqtSignal(int)  # in g

    available_signal = pyqtSignal()    # issued if the first scale freshly connects or an already connected but assigned scale gets released from its assignment
    unavailable_signal = pyqtSignal()  # issued if the last available scale disconnects or gets assigned


    # NOTE: scale_manager and especially the scale1/scale2 objects need to be allocated in the main event loop (allocated in the app, never in a QDialog)!

    def __init__(self, connected_handler:Callable[[str, str], None], disconnected_handler:Callable[[str, str], None]) -> None:
        super().__init__()
        self.connected_handler = connected_handler
        self.disconnected_handler = disconnected_handler
        self.scale1: Optional[Scale] = None
        self.scale2: Optional[Scale] = None
        self.available:bool = False # true if any of the both scales is connected but not assigned

        self.scan_scale1_signal.connect(self.scan_scale1_slot, type=Qt.ConnectionType.QueuedConnection) # type: ignore
        self.set_scale1_signal.connect(self.set_scale1_slot, type=Qt.ConnectionType.QueuedConnection) # type: ignore
        self.connect_scale1_signal.connect(self.connect_scale1_slot, type=Qt.ConnectionType.QueuedConnection) # type: ignore
        self.disconnect_scale1_signal.connect(self.disconnect_scale1_slot, type=Qt.ConnectionType.QueuedConnection) # type: ignore
        self.tare_scale1_signal.connect(self.tare_scale1_slot, type=Qt.ConnectionType.QueuedConnection) # type: ignore
        self.signal_user_scale1_signal.connect(self.signal_user_scale1_slot, type=Qt.ConnectionType.QueuedConnection) # type: ignore
        self.reserve_scale1_signal.connect(self.reserve_scale1_slot, type=Qt.ConnectionType.QueuedConnection) # type: ignore
        self.release_scale1_signal.connect(self.release_scale1_slot, type=Qt.ConnectionType.QueuedConnection) # type: ignore

        self.scan_scale2_signal.connect(self.scan_scale2_slot, type=Qt.ConnectionType.QueuedConnection) # type: ignore
        self.set_scale2_signal.connect(self.set_scale2_slot, type=Qt.ConnectionType.QueuedConnection) # type: ignore
        self.connect_scale2_signal.connect(self.connect_scale2_slot, type=Qt.ConnectionType.QueuedConnection) # type: ignore
        self.disconnect_scale2_signal.connect(self.disconnect_scale2_slot, type=Qt.ConnectionType.QueuedConnection) # type: ignore
        self.tare_scale2_signal.connect(self.tare_scale2_slot, type=Qt.ConnectionType.QueuedConnection) # type: ignore
        self.signal_user_scale2_signal.connect(self.signal_user_scale2_slot, type=Qt.ConnectionType.QueuedConnection) # type: ignore
        self.reserve_scale2_signal.connect(self.reserve_scale2_slot, type=Qt.ConnectionType.QueuedConnection) # type: ignore
        self.release_scale2_signal.connect(self.release_scale2_slot, type=Qt.ConnectionType.QueuedConnection) # type: ignore

        self.disconnect_all_signal.connect(self.disconnect_all_slot, type=Qt.ConnectionType.QueuedConnection) # type: ignore
        self.connect_all_signal.connect(self.connect_all_slot, type=Qt.ConnectionType.QueuedConnection) # type: ignore

        self.scale1_last_weight:Optional[int] = None    # in g; cleared by arrival of fresh stable weights
        self.scale1_stable_reading_timer = QTimer()
        self.scale1_stable_reading_timer.setSingleShot(True)
        self.scale1_stable_reading_timer.timeout.connect(self.scale1_stable_reading_timer_slot)

        self.scale2_last_weight:Optional[int] = None    # in g; cleared by arrival of fresh stable weights
        self.scale2_stable_reading_timer = QTimer()
        self.scale2_stable_reading_timer.setSingleShot(True)
        self.scale2_stable_reading_timer.timeout.connect(self.scale2_stable_reading_timer_slot)


    def _get_scale(self, model:int, ident:str, name:str) -> Optional[Scale]:
        if model == 0:
            from artisanlib.acaia import Acaia
            return Acaia(model, ident, name, lambda : self.connected_handler(ident, name), lambda : self.disconnected_handler(ident, name),
                stable_only=False, decimals=0)
        return None

    # returns readability of the connected scale_nr (0 or 1) if connected and otherwise 0
    def readability(self, scale_nr:int) -> float:
        if scale_nr == 1 and self.scale1 is not None:
            return self.scale1.readability()
        if scale_nr == 2 and self.scale2 is not None:
            return self.scale2.readability()
        return 0

#- scale 1

    def is_scale1_configured(self) -> bool:
        return self.scale1 is not None

    def is_scale1_connected(self) -> bool:
        return self.scale1 is not None and self.scale1.is_connected()

    def reset_scale1(self) -> None:
        if self.scale1 is not None:
            if self.scale1.is_assigned():
                return
            try:
                self.scale1.scanned_signal.disconnect(self.scale1_scanned_slot)
                self.scale1.connected_signal.disconnect(self.scale1_connected_slot)
                self.scale1.disconnected_signal.disconnect(self.scale1_disconnected_slot)
                self.scale1.weight_changed_signal.disconnect(self.scale1_weight_changed_slot)
                #-
                self.scale1.connected_signal.disconnect(self.update_availability)
                self.scale1.disconnected_signal.disconnect(self.update_availability)
            except Exception as e: # pylint: disable=broad-except
                _log.error(e)
            self.disconnect_scale(self.scale1)
            self.scale1 = None

    @pyqtSlot(int,str,str)
    def set_scale1_slot(self, model:int, ident:str, name:str) -> None:
        if self.scale1 is not None:
            if self.scale1.is_assigned(): # scale in use
                return
            self.reset_scale1()
        self.scale1 = self._get_scale(model, ident, name)
        if self.scale1 is not None:
            self.scale1_last_weight = None
            #-
            self.scale1.scanned_signal.connect(self.scale1_scanned_slot)
            self.scale1.connected_signal.connect(self.scale1_connected_slot)
            self.scale1.disconnected_signal.connect(self.scale1_disconnected_slot)
            self.scale1.weight_changed_signal.connect(self.scale1_weight_changed_slot)
            #-
            self.scale1.connected_signal.connect(self.update_availability)
            self.scale1.disconnected_signal.connect(self.update_availability)


    @pyqtSlot(int)
    def scan_scale1_slot(self, model:int) -> None:
        if model == 0: # Acaia
            self.set_scale1_slot(0,'', '')
            if self.scale1 is not None:
                self.scale1.scan()

    @pyqtSlot(bool)
    def connect_scale1_slot(self, device_logging:bool) -> None:
        if self.scale1 is not None:
            self.scale1.connect_scale(device_logging)

    @pyqtSlot()
    def disconnect_scale1_slot(self) -> None:
        if self.scale1 is not None and not self.scale1.is_assigned():
            self.disconnect_scale(self.scale1)


    @pyqtSlot()
    def tare_scale1_slot(self) -> None:
        if self.scale1 is not None:
            self.scale1.tare_scale()
            self.scale1.signal_user(STATE_ACTION.TARE)

    @pyqtSlot(int)
    def signal_user_scale1_slot(self, action:STATE_ACTION) -> None:
        if self.scale1 is not None:
            self.scale1.signal_user(action)

    @pyqtSlot()
    def reserve_scale1_slot(self) -> None:
        if self.scale1 is not None:
            self.scale1.set_assigned(True)
            self.update_availability()

    @pyqtSlot()
    def release_scale1_slot(self) -> None:
        if self.scale1 is not None:
            self.scale1.set_assigned(False)
            self.update_availability()


    @pyqtSlot(list)
    def scale1_scanned_slot(self, scales:ScaleSpecs) -> None:
        self.scale1_scanned_signal.emit(scales)

    @pyqtSlot()
    def scale1_connected_slot(self) -> None:
        self.scale1_connected_signal.emit()
        if self.scale1 is not None:
            self.scale1.signal_user(STATE_ACTION.CONNECTED)

    @pyqtSlot()
    def scale1_disconnected_slot(self) -> None:
        self.scale1_disconnected_signal.emit()

    ## try to catch a last non weight change and send as stable state
    # weight in g
    @pyqtSlot(float, bool)
    def scale1_weight_changed_slot(self, weight:float, stable:bool) -> None:
        weight = int(round(weight))
        if stable:
            self.scale1_last_weight = None # prevent earlier non-stable weights to be send delayed as stable via the timer
            # weights marked as stable by the scale are immediately forwarded as stable weights
            self.scale1_stable_weight_changed_signal.emit(weight)
        else:
            self.scale1_last_weight = weight
            # fed into our stable weight timer system to ensure that the "last one" is also emitted as stable weight
            self.scale1_stable_reading_timer.start(STABLE_TIMER_PERIOD) # start/restart stable weight timer
            # non-stable weights are immediately forwarded as regular weight updates to keep the display fluid
            self.scale1_weight_changed_signal.emit(weight)

    @pyqtSlot()
    def scale1_stable_reading_timer_slot(self) -> None:
        if self.scale1_last_weight is not None:
            self.scale1_stable_weight_changed_signal.emit(self.scale1_last_weight)


#- scale 2

    def is_scale2_connected(self) -> bool:
        return self.scale2 is not None and self.scale2.is_connected()

    def reset_scale2(self) -> None:
        if self.scale2 is not None:
            if self.scale2.is_assigned():
                return
            try:
                self.scale2.scanned_signal.disconnect(self.scale2_scanned_slot)
                self.scale2.connected_signal.disconnect(self.scale2_connected_slot)
                self.scale2.disconnected_signal.disconnect(self.scale2_disconnected_slot)
                self.scale2.weight_changed_signal.disconnect(self.scale2_weight_changed_slot)
                #-
                self.scale2.connected_signal.disconnect(self.update_availability)
                self.scale2.disconnected_signal.disconnect(self.update_availability)
            except Exception as e: # pylint: disable=broad-except
                _log.error(e)
            self.disconnect_scale(self.scale2)
            self.scale2 = None

    @pyqtSlot(int,str,str)
    def set_scale2_slot(self, model:int, ident:str, name:str) -> None:
        if self.scale2 is not None:
            if self.scale2.is_assigned(): # scale in use
                return
            self.reset_scale2()
        self.scale2= self._get_scale(model, ident, name)
        if self.scale2 is not None:
            self.scale2_last_weight = None
            #-
            self.scale2.scanned_signal.connect(self.scale2_scanned_slot)
            self.scale2.connected_signal.connect(self.scale2_connected_slot)
            self.scale2.disconnected_signal.connect(self.scale2_disconnected_slot)
            self.scale2.weight_changed_signal.connect(self.scale2_weight_changed_slot)
            #-
            self.scale2.connected_signal.connect(self.update_availability)
            self.scale2.disconnected_signal.connect(self.update_availability)

    @pyqtSlot(int)
    def scan_scale2_slot(self, model:int) -> None:
        if model == 0: # Acaia
            self.set_scale2_slot(0,'', '')
            if self.scale2 is not None:
                self.scale2.scan()

    @pyqtSlot()
    def connect_scale2_slot(self, device_logging:bool) -> None:
        if self.scale2 is not None:
            self.scale2.connect_scale(device_logging)

    @pyqtSlot()
    def disconnect_scale2_slot(self) -> None:
        if self.scale2 is not None and not self.scale2.is_assigned():
            self.scale2.signal_user(STATE_ACTION.DISCONNECTED)
            libtime.sleep(0.2) # wait a moment to have the disconnect signal being sent to the user
            self.scale2.disconnect_scale()

    @pyqtSlot()
    def tare_scale2_slot(self) -> None:
        if self.scale2 is not None:
            self.scale2.tare_scale()
            self.scale2.signal_user(STATE_ACTION.TARE)

    @pyqtSlot(int)
    def signal_user_scale2_slot(self, action:STATE_ACTION) -> None:
        if self.scale2 is not None:
            self.scale2.signal_user(action)

    @pyqtSlot()
    def reserve_scale2_slot(self) -> None:
        if self.scale2 is not None:
            self.scale2.set_assigned(True)
            self.update_availability()

    @pyqtSlot()
    def release_scale2_slot(self) -> None:
        if self.scale2 is not None:
            self.scale2.set_assigned(False)
            self.update_availability()


    @pyqtSlot(list)
    def scale2_scanned_slot(self, scales:ScaleSpecs) -> None:
        self.scale2_scanned_signal.emit(scales)

    @pyqtSlot()
    def scale2_connected_slot(self) -> None:
        self.scale2_connected_signal.emit()
        if self.scale2 is not None:
            self.scale2.signal_user(STATE_ACTION.CONNECTED)

    @pyqtSlot()
    def scale2_disconnected_slot(self) -> None:
        self.scale2_disconnected_signal.emit()

    ## try to catch a last non weight change and send as stable state
    # weight in g
    @pyqtSlot(float, bool)
    def scale2_weight_changed_slot(self, weight:float, stable:bool) -> None:
        weight = int(round(weight))
        if stable:
            self.scale2_last_weight = None # prevent earlier non-stable weights to be send delayed as stable via the timer
            # weights marked as stable by the scale are immediately forwarded as stable weights
            self.scale2_stable_weight_changed_signal.emit(weight)
        else:
            self.scale2_last_weight = weight
            # fed into our stable weight timer system to ensure that the "last one" is also emitted as stable weight
            self.scale2_stable_reading_timer.start(STABLE_TIMER_PERIOD) # start/restart stable weight timer
            # non-stable weights are immediately forwarded as regular weight updates to keep the display fluid
            self.scale2_weight_changed_signal.emit(weight)

    @pyqtSlot()
    def scale2_stable_reading_timer_slot(self) -> None:
        if self.scale2_last_weight is not None:
            self.scale2_stable_weight_changed_signal.emit(self.scale2_last_weight)

#--


    def is_available(self) -> bool:
        return self.available

    # if force is True, available/unavailable signals are also emitted if availability did not change to inform new/updated components
    def update_availability(self, force:bool = False) -> None:
        availability = ((self.scale1 is not None and self.scale1.is_connected() and not self.scale1.is_assigned()) or
            (self.scale2 is not None and self.scale2.is_connected() and not self.scale2.is_assigned()))
        if (force or self.available) and  not availability:
            self.unavailable_signal.emit()
        elif (force or not self.available) and availability:
            self.available_signal.emit()
        self.available = availability

    @pyqtSlot()
    def update_availability_slot(self) -> None:
        self.update_availability()

    @staticmethod
    def disconnect_scale(scale:Scale) -> None:
        scale.signal_user(STATE_ACTION.DISCONNECTED)
        libtime.sleep(0.2) # wait a moment to have the disconnect signal being sent to the user
        scale.disconnect_scale()

    @pyqtSlot()
    def disconnect_all_slot(self) -> None:
        for scale in (self.scale1, self.scale2):
            if scale is not None:
                self.disconnect_scale(scale)

    @pyqtSlot(bool)
    def connect_all_slot(self, device_logging:bool) -> None:
        self.connect_scale1_slot(device_logging)
        libtime.sleep(0.1)
        self.connect_scale2_slot(device_logging)
