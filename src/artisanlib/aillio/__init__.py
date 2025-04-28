#
# ABOUT
# Aillio support for Artisan

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

# AUTHOR27
# Rui Paulo, 2023
# mikefsq, r2 2025

from .aillio import AillioBase
from typing import Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.aillio.aillio_r1 import AillioR1
    from artisanlib.aillio.aillio_r2 import AillioR2

# Maintain backwards compatibility by using AillioR1 name
def Aillio(debug:bool=False) -> 'Optional[Union[AillioR1, AillioR2]]':
    return AillioBase.create(debug=debug)

__all__ = ['Aillio']
