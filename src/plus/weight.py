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
    from PyQt6.QtCore import QObject, QSemaphore, pyqtSlot # @Reimport @UnresolvedImport @UnusedImport
except ImportError:
    from PyQt5.QtCore import QObject, QSemaphore, pyqtSlot # type: ignore[import-not-found,no-redef]  # @Reimport @UnresolvedImport @UnusedImport

from dataclasses import dataclass
from enum import IntEnum, unique
from statemachine import StateMachine, State
from typing import Optional, List, Tuple, Callable, Final

from artisanlib.scale import ScaleManager


_log: Final[logging.Logger] = logging.getLogger(__name__)



@unique
class PROCESS_STATE(IntEnum):
    DISCONNECTED = 0
    CONNECTED = 1
    WEIGHING = 2
    DONE = 3
    CANCELD = 4

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

    def show_item(self, item:WeightItem, state:PROCESS_STATE = PROCESS_STATE.DISCONNECTED, component:int = 0) -> None: # pylint: disable=unused-argument,no-self-use
        ...

class GreenDisplay(Display):
    ...

class RoastedDisplay(Display):
    ...


#------------


class GreenWeighingState(StateMachine):

    idle = State(initial=True)  # display_state = 0
    scale = State()             # scale available, display_state = 1
    item = State()              # current_item available, display_state = 0
    ready = State()             # display_state = 1

    current_item = (
        idle.to(item)
        | item.to(item)
        | ready.to(ready)
        | scale.to(ready)
    )

    clear_item = (
        idle.to(idle)
        | item.to(idle)
        | ready.to(scale)
    )

    available = (
        idle.to(scale)
        | item.to(ready)
    )

    unavailable = (
        scale.to(idle)
        | ready.to(item)
    )

    def __init__(self, displays:List[Display]) -> None:

        # list of displays control, incl. the display of the selected scale if any
        self.displays: List[Display] = displays

        # holds the WeightItem currently processed, if any
        self.current_weight_item:Optional[GreenWeightItem] = None
        self.process_state:PROCESS_STATE = PROCESS_STATE.DISCONNECTED
        self.component:int = 0 # component (of blend) currently processed (0 <= self.component < len(self.current_weight_item.descriptions))

        super().__init__(allow_event_without_transition=True) # no errors for events which do not lead to transitions

    def after_current_item(self, weight_item:GreenWeightItem) -> None:
        self.current_weight_item = weight_item
        self.update_displays()

    def after_clear_item(self) -> None:
        self.current_weight_item = None
        self.update_displays()

    def after_available(self) -> None:
        self.process_state = PROCESS_STATE.CONNECTED
        self.update_displays()

    def after_unavailable(self) -> None:
        self.process_state = PROCESS_STATE.DISCONNECTED
        self.update_displays()

#-

    def taskCompleted(self) -> None:
        if self.current_weight_item is not None:
            self.current_weight_item.callback(str(self.current_weight_item.uuid), float(self.current_weight_item.weight))

#-

    # render item on all active displays
    def update_displays(self) -> None:
        for display in self.displays:
            if self.current_weight_item is not None:
                display.show_item(self.current_weight_item, self.process_state, self.component)
            else:
                display.clear_green()

    # update weight to be displayed on all connected displays
    def update_weight(self) -> None:
        pass # to be implemented


class RoastedWeighingState(StateMachine):

    idle = State(initial=True)  # display_state = 0
    scale = State()             # scale available, display_state = 1
    item = State()              # current_item available, display_state = 0
    ready = State()             # display_state = 1

    current_item = (
        idle.to(item)
        | item.to(item)
        | ready.to(ready)
        | scale.to(ready)
    )

    clear_item = (
        idle.to(idle)
        | item.to(idle)
        | ready.to(scale)
    )

    available = (
        idle.to(scale)
        | item.to(ready)
    )

    unavailable = (
        scale.to(idle)
        | ready.to(item)
    )

    def __init__(self, displays:List[Display]) -> None:

        # list of displays control, incl. the display of the selected scale if any
        self.displays: List[Display] = displays

        # holds the WeightItem currently processed, if any
        self.current_weight_item:Optional[RoastedWeightItem] = None
        self.process_state:PROCESS_STATE = PROCESS_STATE.DISCONNECTED
        self.component:int = 0 # component (of blend) currently processed (0 <= self.component < len(self.current_weight_item.descriptions))

        super().__init__(allow_event_without_transition=True) # no errors for events which do not lead to transitions

    def after_current_item(self, weight_item:RoastedWeightItem) -> None:
        self.current_weight_item = weight_item
        # update displays
        self.update_displays()

    def after_clear_item(self) -> None:
        self.current_weight_item = None
        self.update_displays()

    def after_available(self) -> None:
        self.process_state = PROCESS_STATE.CONNECTED
        self.update_displays()

    def after_unavailable(self) -> None:
        self.process_state = PROCESS_STATE.DISCONNECTED
        self.update_displays()

#-

    def taskCompleted(self) -> None:
        if self.current_weight_item is not None:
            self.current_weight_item.callback(self.current_weight_item.uuid, self.current_weight_item.weight)

#-

    # render item on all active displays
    def update_displays(self) -> None:
        for display in self.displays:
            if self.current_weight_item is not None:
                display.show_item(self.current_weight_item, self.process_state, self.component)
            else:
                display.clear_roasted()

    # update weight to be displayed on all connected displays
    def update_weight(self) -> None:
        pass # to be implemented


class WeightManager(QObject): # pyright:ignore[reportGeneralTypeIssues] # error: Argument to class must be a base class

    __slots__ = [ 'displays', 'scale_manager', 'next_green_item',  'next_roasted_item',
                    'greenItemSemaphore', 'roastedItemSemaphore', 'green_sm' ]


    def __init__(self, displays:List[Display], scale_manager:ScaleManager) -> None:
        super().__init__()

        self.scale_manager = scale_manager

        # holds the next WeightItem waiting to be processed, if any
        self.next_green_item:Optional[GreenWeightItem] = None
        self.next_roasted_item:Optional[RoastedWeightItem] = None

        self.greenItemSemaphore = QSemaphore(1) # semaphore to protect access to next_green_item
        self.roastedItemSemaphore = QSemaphore(1) # semaphore to protect access to next_roasted_item

        self.sm_green = GreenWeighingState(displays)
        self.sm_roasted = RoastedWeighingState(displays)

        self.start() # connect to configured scales


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
            self.fetch_next_green()

    def clear_next_green(self) -> None:
        self.greenItemSemaphore.acquire(1)
        self.next_green_item = None
        self.greenItemSemaphore.release(1)
        self.fetch_next_green()

    # start processing the next green item if any
    def fetch_next_green(self) -> None:
        # if there is no scale, we fetch that item immediately and start "processing"
        # even if there is already a current one in "processing"
        if self.sm_green.process_state in {PROCESS_STATE.DISCONNECTED, PROCESS_STATE.CONNECTED}:
            self.greenItemSemaphore.acquire(1)
            try:
                if self.next_green_item is None:
                    self.sm_green.send('clear_item')
                else:
                    self.sm_green.current_item(self.next_green_item)
                    self.next_green_item = None
            finally:
                if self.greenItemSemaphore.available() < 1:
                    self.greenItemSemaphore.release(1)

    def greenTaskCompleted(self) -> None:
        self.sm_green.taskCompleted()


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
            self.fetch_next_roasted()

    def clear_next_roasted(self) -> None:
        self.roastedItemSemaphore.acquire(1)
        self.next_roasted_item = None
        self.roastedItemSemaphore.release(1)
        self.fetch_next_roasted()

    # start processing the next roasted item if any
    def fetch_next_roasted(self) -> None:
        # if there is no scale, we fetch that item immediately and start "processing"
        # even if there is already a current one in "processing"
        if self.sm_roasted.process_state in {PROCESS_STATE.DISCONNECTED, PROCESS_STATE.CONNECTED}:
            self.roastedItemSemaphore.acquire(1)
            try:
                if self.next_roasted_item is None:
                    self.sm_roasted.send('clear_item')
                else:
                    self.sm_roasted.current_item(self.next_roasted_item)
                    self.next_roasted_item = None
            finally:
                if self.roastedItemSemaphore.available() < 1:
                    self.roastedItemSemaphore.release(1)

    def roastedTaskCompleted(self) -> None:
        self.sm_roasted.taskCompleted()

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

    @pyqtSlot()
    def scales_available(self) -> None:
        self.sm_green.send('available')
        self.sm_roasted.send('available')

    @pyqtSlot()
    def scales_unavailable(self) -> None:
        self.sm_green.send('unavailable')
        self.sm_roasted.send('unavailable')

    def start(self) -> None:
        self.scale_manager.available_signal.connect(self.scales_available)
        self.scale_manager.unavailable_signal.connect(self.scales_unavailable)
        self.scale_manager.connect_all()

    def stop(self) -> None:
        self.reset()
        self.scale_manager.disconnect_all()
        self.scale_manager.available_signal.disconnect()
        self.scale_manager.unavailable_signal.disconnect()


# Container information
#aw.qmc.container_names
#container_weights
