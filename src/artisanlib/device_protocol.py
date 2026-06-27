#
# ABOUT
# Device Protocols for Artisan

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later versison. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.


from typing import Protocol


class RoasterProtocol(Protocol):
    """Structural protocol for roaster machine drivers.

    Defines the common interface expected of Artisan roaster drivers
    (e.g. KaleidoPort, Santoker, Orbiter). This is a structural
    Protocol — implementing classes satisfy it implicitly through
    compatible method signatures, without explicit inheritance.

    Not runtime_checkable. Static analysis only.
    """

    def start(self, connect_timeout: float = 30.0) -> None: ...
    def stop(self) -> None: ...
    def getBTET(self) -> tuple[float, float, int]: ...
    def setLogging(self, b: bool) -> None: ...
    def resetReadings(self) -> None: ...


class ScaleProtocol(Protocol):
    """Structural protocol for scale drivers (e.g. Acaia).

    Defines the common interface for scale communication.
    Structural subtyping — no explicit inheritance required.
    """

    def getWeight(self) -> float: ...
    def tare(self) -> None: ...
    def setLogging(self, b: bool) -> None: ...
