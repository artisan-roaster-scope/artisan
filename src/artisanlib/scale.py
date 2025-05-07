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

import logging
from typing import Final, List, Tuple, Optional, Callable

try:
    from PyQt6.QtCore import pyqtSignal # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import pyqtSignal # type: ignore # @UnusedImport @Reimport  @UnresolvedImport


_log: Final[logging.Logger] = logging.getLogger(__name__)



#  tuples (model name, connection type) with connection type from {0: BT, 1: WiFi, 2: Serial}
SUPPORTED_SCALES:Final[List[Tuple[str,int]]] = [
    ('Acaia', 0) # 0
]

ScaleSpec = Tuple[str,str] # scale name, scale id (eg. ble address)
ScaleSpecs = List[ScaleSpec]


# NOTE: this class and all subclasses are not allowed to hold __slots__
class Scale:

    weight_changed_signal = pyqtSignal(int)   # delivers new weight in g
    battery_changed_signal = pyqtSignal(int)  # delivers new batter level in %
    disconnected_signal = pyqtSignal()        # issued on disconnect

    def __init__(self, model:int, ident:Optional[str], name:Optional[str]):
        self.model = model
        self.ident = ident
        self.name = name

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

    #---

    def set_connected_handler(self, connected_handler:Optional[Callable[[], None]]) -> None:
        pass

    def set_disconnected_handler(self, disconnected_handler:Optional[Callable[[], None]]) -> None:
        pass

    def connect_scale(self) -> None:
        pass

    def disconnect_scale(self) -> None:
        pass

    def tare_scale(self) -> None:
        pass



class ScaleManager:

    __slots__ = [ 'scale1', 'scale2' ]

    def __init__(self) -> None:
        self.scale1: Optional[Scale] = None
        self.scale2: Optional[Scale] = None

    # returns list of discovered devices as (name, address) tuples matching selected scale model
    @staticmethod
    def scan_for_scales(model:int) -> ScaleSpecs:
        if model == 0: # Acaia
            from artisanlib.ble_port import scan_ble
            devices = scan_ble()
            from artisanlib import acaia
            acaia_devices:ScaleSpecs = []
            # for Acaia scales we filter by name
            for d, a in devices:
                name = (a.local_name or d.name)
                if name:
                    match = next((f'{product_name} ({name})' for (name_prefix, product_name) in acaia.ACAIA_SCALE_NAMES
                                if name and name.startswith(name_prefix)), None)
                    if match is not None:
                        acaia_devices.append((match, d.address))
            return acaia_devices
        return []

    @staticmethod
    def get_scale(model:int, ident:str, name:str) -> Optional[Scale]:
        if model == 0:
            from artisanlib.acaia import Acaia
            return Acaia(model, ident, name)
        return None

    def set_scale1(self, scale:Optional[Scale]) -> None:
        if self.scale1 is not None:
            self.scale1.disconnect_scale()
        self.scale1 = scale

    def get_scale1(self) -> Optional[Scale]:
        return self.scale1

    def set_scale2(self, scale:Optional[Scale]) -> None:
        if self.scale2 is not None:
            self.scale2.disconnect_scale()
        self.scale2 = scale

    def get_scale2(self) -> Optional[Scale]:
        return self.scale2

    def disconnect_all(self) -> None:
        if self.scale1 is not None:
            self.scale1.disconnect_scale()
            self.scale1 = None
        if self.scale2 is not None:
            self.scale2.disconnect_scale()
            self.scale2 = None
