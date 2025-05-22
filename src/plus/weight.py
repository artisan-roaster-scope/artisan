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
from typing import Optional, List, Tuple, Callable, Final

from artisanlib.scale import ScaleManager


_log: Final[logging.Logger] = logging.getLogger(__name__)

@dataclass # creates an __eq__ method comparing objects by property values
class WeightItem:
    uuid:str                 # the UUID of the ScheduledItem or CompletedItem
    title:str                # the title (schedule item name of a ScheduledItem, or batch number and roast name of a CompletedItem
    blend_name:Optional[str] # None if item is a coffee, else the name of the blend
    description:str          # a HTML formatted string describing the weight item (used by the Scheduler task display tooltip popup)
    descriptions:List[Tuple[float,str]] # the descriptions of the green coffee or blend as non empty list of tuples <ratio>,<description>
                             # with ratio the component ratio in blends and description the coffee component name.
                             # A single coffee has just one tuple with ratio set to 1 (also for completed items).
                             # For roasted blend items this is always just the one element list [(1, '')]
    position:str             # the position string (like "2/5" for 2nd of 5 batches)
    weight:float             # target or suggested weight
    weight_unit_idx:int      # the weight unit, one of (0:'g', 1:'kg', 2:'lb', 3:'oz')
    callback:Callable[[str, float], None] # the function to be called with id:str and weight (in kg) on completion

@dataclass
class GreenWeightItem(WeightItem):
    ...

@dataclass
class RoastedWeightItem(WeightItem):
    ...

#WebDisplay protocol
#- id:str (schedule item position / roast batch nr)
#- title:str
#- subtitle:str
#- batchsize:str
#- weight:str
#- percent: float => always present
#- state:int (0:disconnected, 1:connected, 2:weighing, 3:done, 4:canceled)
#- bucket: int {0,1,2}
#- blend_percent: str # could be the empty string
#- total_percent: float => could be dropped
#- type:int (0:green, 1: roasted, 2:defects)


# Consider
#. if green: target weight (counts down)
#. if green: bean or blend name
#. if green: container recognized (or not) indicating container name
#. if roasted: batch number + roast name + green weight + weight loss
#. registered weight (so far)



class Display:

    __slots__ = [ 'active' ]

    def __init__(self) -> None:
        self.active:bool = True

    def clear_green(self) -> None: # pylint: disable=no-self-use
        ...

    def clear_roasted(self) -> None: # pylint: disable=no-self-use
        ...

    def show_item(self, item:WeightItem) -> None: # pylint: disable=unused-argument,no-self-use
        ...

class GreenDisplay(Display):
    ...

class RoastedDisplay(Display):
    ...





#class Scale:
#    __slots__ = [ 'display' ]
#
#    def __init__(self) -> None:
#        self.display:Optional[Display] = None
#
#    def get_display(self) -> Optional[Display]:
#        return self.display
#
#
#class PhidgetScale(Scale):
#    def __init__(self) -> None:
#        super().__init__()
#        self.display = Display()
#
#class AcaiaScale(Scale):
#    ...




class WeightManager:

    __slots__ = [ 'displays', 'scale_manager', 'next_green_item',  'next_roasted_item',  'current_green_item', 'current_roasted_item',
                    'greenItemSemaphore', 'roastedItemSemaphore' ]


    def __init__(self, displays:List[Display], scale_manager:ScaleManager) -> None:

        self.scale_manager = scale_manager

        # list of displays control, incl. the display of the selected scale if any
        self.displays: List[Display] = displays

        # holds the next WeightItem waiting to be processed, if any
        self.next_green_item:Optional[GreenWeightItem] = None
        self.next_roasted_item:Optional[RoastedWeightItem] = None

        # holds the WeightItem currently processed, if any
        self.current_green_item:Optional[GreenWeightItem] = None
        self.current_roasted_item:Optional[RoastedWeightItem] = None

        self.greenItemSemaphore = QSemaphore(1) # semaphore to protect access to next_green_item and current_green_item
        self.roastedItemSemaphore = QSemaphore(1) # semaphore to protect access to next_roasted_item and current_roasted_item


    # queues a GreenWeightItem for processing
    # if item is None, the next green item is cleared
    # Note: the queue has size 1 and a newer incoming item overwrites an older already queued item
    def set_next_green(self, item:Optional[GreenWeightItem]) -> None:
        if item is None:
            self.clear_next_green()
        else:
            # if there is a scale, we add the item to the waiting list to be fetched once a
            # container is recognized on the scale and processing is started
            # older waiting (outdated) weight item just get overwritten

            self.greenItemSemaphore.acquire(1)
            self.next_green_item = item
            self.greenItemSemaphore.release(1)

            if True: # TODO: if green weighing process is not running
                # if there is no scale, we fetch that item immediately and start "processing"
                # even if there is already a current one in "processing"
                self.fetch_next_green()

    def clear_next_green(self) -> None:
        self.greenItemSemaphore.acquire(1)
        self.next_green_item = None
        self.greenItemSemaphore.release(1)
        self.clear_displays(green=True)

    # start processing the next green item if any
    def fetch_next_green(self) -> None:
        self.greenItemSemaphore.acquire(1)
        try:
            if self.next_green_item is None:
                self.current_roasted_item = None
                self.clear_displays(green=True)
            else:
                self.current_green_item = self.next_green_item
                self.next_green_item = None
                # update displays
                self.update_displays(self.current_green_item)
        finally:
            if self.greenItemSemaphore.available() < 1:
                self.greenItemSemaphore.release(1)

    def greenTaskCompleted(self) -> None:
        if self.current_green_item is not None:
            self.current_green_item.callback(self.current_green_item.uuid, self.current_green_item.weight)

#--

    # queues a RoastedWeightItem for processing
    # if item is None, the next roasted item is cleared
    # Note: the queue has size 1 and a newer incoming item overwrites an older already queued item
    def set_next_roasted(self, item:Optional[RoastedWeightItem]) -> None:
        if item is None:
            self.clear_next_roasted()
        else:
            # if there is a scale, we add the item to the waiting list to be fetched once a
            # container is recognized on the scale and processing is started
            # older waiting (outdated) weight item just get overwritten

            self.roastedItemSemaphore.acquire(1)
            self.next_roasted_item = item
            self.roastedItemSemaphore.release(1)

            if True: # TODO: if roasted weighing process is not running
                # if there is no scale, we fetch that item immediately and start "processing"
                # even if there is already a current one in "processing"
                self.fetch_next_roasted()

    def clear_next_roasted(self) -> None:
        self.roastedItemSemaphore.acquire(1)
        self.next_roasted_item = None
        self.roastedItemSemaphore.release(1)
        self.clear_displays(roasted=True)

    # start processing the next roasted item if any
    def fetch_next_roasted(self) -> None:
        self.roastedItemSemaphore.acquire(1)
        try:
            if self.next_roasted_item is None:
                self.current_roasted_item = None
                self.clear_displays(roasted=True)
            else:
                self.current_roasted_item = self.next_roasted_item
                self.next_roasted_item = None
                # update displays
                self.update_displays(self.current_roasted_item)
        finally:
            if self.roastedItemSemaphore.available() < 1:
                self.roastedItemSemaphore.release(1)

    def roastedTaskCompleted(self) -> None:
        if self.current_roasted_item is not None:
            self.current_roasted_item.callback(self.current_roasted_item.uuid, self.current_roasted_item.weight)

#--

    def clear_next(self) -> None:
        self.clear_next_green()
        self.clear_next_roasted()

    def fetch_next(self) -> None:
        self.fetch_next_green()
        self.fetch_next_roasted()

    def reset(self) -> None:
        self.clear_next()
        self.fetch_next()


    # render item on all active displays
    def update_displays(self, item:WeightItem) -> None:
        for display in self.displays:
            display.show_item(item)

    # update weight to be displayed on all connected displays
    def update_weight(self) -> None:
        pass # to be implemented

    # if green and roasted are False, all displays are cleared
    def clear_displays(self, green:bool = False, roasted:bool = False) -> None:
        for display in self.displays:
            if (green and not roasted) or not (green or roasted):
                display.clear_green()
            if roasted or not (green or roasted):
                display.clear_roasted()

# Container information
#aw.qmc.container_names
#container_weights
