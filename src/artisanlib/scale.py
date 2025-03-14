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
from typing import Final, List, Tuple, Optional

try:
    from PyQt6.QtCore import QObject, pyqtSignal # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import QObject, pyqtSignal # type: ignore # @UnusedImport @Reimport  @UnresolvedImport


_log: Final[logging.Logger] = logging.getLogger(__name__)



#  tuples (model name, connection type) with connection type from {0: BT, 1: WiFi, 2: Serial}
SUPPORTED_SCALES:Final[List[Tuple[str,int]]] = [
    ('Acaia', 0) # 0
]

ScaleSpec = Tuple[str,str]
ScaleSpecs = List[ScaleSpec]


# NOTE: this class and all subclasses are not allowed to hold __slots__
class Scale(QObject): # pyright: ignore [reportGeneralTypeIssues] # Argument to class must be a base class

    weight_changed_signal = pyqtSignal(int)   # delivers new weight in g
    battery_changed_signal = pyqtSignal(int)  # delivers new batter level in %
    disconnected_signal = pyqtSignal()        # issued on disconnect

    def __init__(self) -> None:
        QObject.__init__(self)


    def connect(self) -> None:
        pass

    def disconnect(self) -> None:
        pass




class ScaleManager:

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
    def get_scale(model:int, address:str) -> Optional[Scale]:
        if model == 0:
            from artisanlib.acaia import Acaia
            scale = Acaia()
            scale.set_address(address)
            return scale
        return None
