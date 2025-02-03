#
# weight.py
#
# Copyright (c) 2024, Paul Holleis, Marko Luther
# All rights reserved.
#
#
# ABOUT
# This module connects to the artisan.plus inventory management service

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging

try:
    from PyQt6.QtCore import QSemaphore # @Reimport @UnresolvedImport @UnusedImport
except ImportError:
    from PyQt5.QtCore import QSemaphore # type: ignore[import-not-found,no-redef]  # @Reimport @UnresolvedImport @UnusedImport

from dataclasses import dataclass
from typing import Optional, List, Callable, Final


_log: Final[logging.Logger] = logging.getLogger(__name__)

@dataclass
class WeightItem:
    uuid:str         # the UUID of the ScheduledItem or CompletedItem
    title:str        # the title (schedule item name of a ScheduledItem, or batch number and roast name of a CompletedItem
    description:str  # the description (the coffee name or blend ingredients of a ScheduleItem or the roast date of a CompletedItem)
    position:str     # the position string (like "2/5" for 2nd of 5 batches)
    weight:float     # target or suggested weight
    weight_unit_idx:int  # the weight unit, one of (0:'g', 1:'kg', 2:'lb', 3:'oz')
    call_back:Callable[[str, float], None] # the function to be called with id:str and weight (in kg) on completion

@dataclass
class GreenWeightItem(WeightItem):
    ...

@dataclass
class RoastedWeightItem(WeightItem):
    ...

# Consider
#. if green: target weight (counts down)
#. if green: bean or blend name
#. if green: container recognized (or not) indicating container name
#. if roasted: batch number + roast name + green weight
#. registered weight (so far)



class Display:

    __slots__ = [ 'active' ]

    def __init__(self) -> None:
        self.active:bool = True
        self.clear()

    def clear(self) -> None: # pylint: disable=no-self-use
        ...

    def show_item(self, item:WeightItem) -> None: # pylint: disable=unused-argument,no-self-use
        ...


class PhidgetScaleDisplay(Display):
#    def __init__(self) -> None:
#        super().__init__()

    def show_item(self, item:WeightItem) -> None:
        if self.active:
            print(item)

class DialogDisplay(Display):
#    def __init__(self) -> None:
#        super().__init__()

    def show_item(self, item:WeightItem) -> None:
        pass

class WebDisplay(Display):
    __slots__ = [ 'url', 'qr_code' ]
#    def __init__(self) -> None:
#        super().__init__()



class Scale:
    __slots__ = [ 'display' ]

    def __init__(self) -> None:
        self.display:Optional[Display] = None

    def get_display(self) -> Optional[Display]:
        return self.display


class PhidgetScale(Scale):
    def __init__(self) -> None:
        super().__init__()
        self.display = Display()

class AcaiaScale(Scale):
    ...




class WeightManager:

    __slots__ = [ 'displays', 'scale', 'next_item', 'current_item', 'itemSemaphore' ]


    def __init__(self, displays:List[Display], scale:Optional[Scale] = None) -> None:

        # optional selected scale; may contain a display which is controlled by this object
        self.scale: Optional[Scale] = scale

        # list of displays control, incl. the display of the selected scale if any
        self.displays: List[Display] = displays
        if self.scale is not None:
            scale_display = self.scale.get_display()
            if scale_display is not None:
                self.displays.append(scale_display)

        # holds the next WeightItem waiting to be processed, if any
        self.next_item:Optional[WeightItem] = None

        # holds the WeightItem currently processed, if any
        self.current_item:Optional[WeightItem] = None

        self.itemSemaphore = QSemaphore(1) # semaphore to protect access to next_item and current_item


    # queues a WeightItem for processing
    # Note: the queue has size 1 and a newer incoming item overwrites an older already queued item
    def set_next(self, item:Optional[WeightItem]) -> None:
        if item is None:
            self.clear_next()
        else:
            # if there is a scale, we add the item to the waiting list to be fetched once a
            # container is recognized on the scale and processing is started
            # older waiting (outdated) weight item just get overwritten

            self.itemSemaphore.acquire(1)
            self.next_item = item
            self.itemSemaphore.release(1)

            if self.scale is None:
                # if there is no scale, we fetch that item immediately and start "processing"
                # even if there is already a current one in "processing"
                self.fetch_next()

    def clear_next(self) -> None:
        self.itemSemaphore.acquire(1)
        self.next_item = None
        self.itemSemaphore.release(1)
        self.clear_displays()

    def reset(self) -> None:
        self.clear_next()
        self.fetch_next()

    # start processing the next item if any
    def fetch_next(self) -> None:
        self.itemSemaphore.acquire(1)
        try:
            if self.next_item is None:
                self.current_item = None
                self.clear_displays()
            else:
                self.current_item = self.next_item
                self.next_item = None
                # update displays
                self.update_displays(self.current_item)
        finally:
            if self.itemSemaphore.available() < 1:
                self.itemSemaphore.release(1)

    def taskCompleted(self) -> None:
        if self.current_item is not None:
            self.current_item.call_back(self.current_item.uuid, self.current_item.weight)


    # render item on all active displays
    def update_displays(self, item:WeightItem) -> None:
        for display in self.displays:
            display.show_item(item)

    # update weight to be displayed on all connected displays
    def update_weight(self) -> None:
        pass # to be implemented

    def clear_displays(self) -> None:
        for display in self.displays:
            display.clear()

# Container information
#aw.qmc.container_names
#container_weights
