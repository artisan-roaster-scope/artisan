#
# weight.py
#
# Copyright (c) 2025, Paul Holleis, Marko Luther
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
    from PyQt6.QtCore import QObject, QTimer, QSemaphore, pyqtSlot # @Reimport @UnresolvedImport @UnusedImport
except ImportError:
    from PyQt5.QtCore import QObject, QTimer, QSemaphore, pyqtSlot # type: ignore[import-not-found,no-redef]  # @Reimport @UnresolvedImport @UnusedImport

from dataclasses import dataclass
from enum import IntEnum, unique
from statemachine import StateMachine, State
from typing import Optional, List, Tuple, Callable, Final, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # noqa: F401 # pylint: disable=unused-import

from artisanlib.scale import ScaleManager, STATE_ACTION


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
    weight:float             # batch size (target weight for GreenWeightItem) in kg
    weight_estimate: float   # expected yield in kg (only valid for RoastedWeightItems!)
    weight_unit_idx:int      # the weight unit, one of (0:'g', 1:'kg', 2:'lb', 3:'oz')
    callback:Callable[[str, float], None] # the function to be called with id:str and weight (in kg) on completion

@dataclass
class GreenWeightItem(WeightItem):
    ...

@dataclass
class RoastedWeightItem(WeightItem):
    ...


class Display:

    __slots__ = [ #'active'
        'cancel_timer_timeout', 'done_timer_timeout', 'accuracy'
        ]

    def __init__(self) -> None:
#        self.active:bool = True
        self.cancel_timer_timeout:int = 0 # timeout of the cancel state in seconds; if 0, timer is disabled
        self.done_timer_timeout:int = 0   # timeout of the cancel state in seconds; if 0, timer is disabled
        self.accuracy:float = 0.          # accuracy deciding when to enter/leave zoom mode (zoom mode off if 0)

    def clear_green(self) -> None: # pylint: disable=no-self-use
        ...

    def clear_roasted(self) -> None: # pylint: disable=no-self-use
        ...

    def set_accuracy(self, value:float) -> None:
        self.accuracy = value

    # set the displays CANCEL timer timeout in seconds
    def set_cancel_timer_timeout(self, timeout:int) -> None:
        self.cancel_timer_timeout = timeout

    # set the displays DONE timer timeout in seconds
    def set_done_timer_timeout(self, timeout:int) -> None:
        self.done_timer_timeout = timeout

    # show task
    # task_type 0:green, 1:roasted, 2:defect
    def show_item(self, task_type:int, item:Optional[WeightItem], state:PROCESS_STATE = PROCESS_STATE.DISCONNECTED, component:int = 0, final_weight:Optional[int] = None) -> None: # pylint: disable=unused-argument,no-self-use
        ...

    # show progress of the green weighing process
    # task_type 0:green, 1:roasted, 2:defect
    def show_progress(self, task_type:int, item:Optional[WeightItem], state:PROCESS_STATE, component:int, bucket:int, current_weight:int) -> None: # pylint: disable=unused-argument,no-self-use
        ...

    # show progress of the roasted weighing process
    # task_type 0:green, 1:roasted, 2:defect
    def show_result(self, task_type:int, item:WeightItem, state:PROCESS_STATE, current_weight:int) -> None: # pylint: disable=unused-argument,no-self-use
        ...

class GreenDisplay(Display):
    ...

class RoastedDisplay(Display):
    ...


#------------


class GreenWeighingState(StateMachine):

    CONNECTION_LOSS_TIMEOUT:Final[int] = 60*1000    # 1min; time in milliseconds before disconnect state is terminated by a 'reset'
    EMPTY_TIMEOUT:Final[int] = 2*60*1000            # 2min; time in milliseconds before EMPTY stated is terminated by a 'reset'

    idle = State(initial=True)  # display_state = 0
    scale = State()             # scale available, display_state = 1
    item = State()              # current_item available, display_state = 0
    ready = State()             # display_state = 1
    weighing1 = State()         # weighing into first container
    empty = State()             # first container removed, platform empty awaiting second container
    weighing2 = State()         # weighing into second container
    cancel_weighing1 = State()  # cancel weighing1 if filled bucket is not put back within some seconds
    cancel_weighing2 = State()  # cancel weighing2 if filled bucket is not put back within some seconds
    done_weighing1 = State()    # weighing done
    done_weighing2 = State()    # weighing done

    reset = (
        idle.to(idle)
        | scale.to(scale)
        | item.to(item)
        | ready.to(ready)
        | weighing1.to(ready)
        | empty.to(ready)
        | weighing2.to(ready)
        | cancel_weighing1.to(ready)
        | cancel_weighing2.to(ready)
        | done_weighing1.to(ready)
        | done_weighing2.to(ready)
    )

    current_item = (
        idle.to(item)
        | scale.to(ready)
        | item.to(item)    # needed for updating displays to new current_item!
        | ready.to(ready, internal=True) # needed for updating displays to new current_item, no entry/exist actions triggered!
#        | empty.to(empty) # we don't allow to change current_item while swapping containers
        | done_weighing1.to(done_weighing1)
        | done_weighing2.to(done_weighing2)
    )

    clear_item = (
        ready.to(scale)
        | item.to(idle)
        | idle.to(idle) # ensure that internal display is cleared on scheduler tab switch in any case
    )

    available = (
        idle.to(scale)
        | item.to(ready)
    )

    unavailable = (
        scale.to(idle)
        | ready.to(item)
    )

    bucket_placed = (
        ready.to(weighing1)
        | empty.to(weighing2)
    )

    # empty bucket removed
    bucket_removed = (
        weighing1.to(ready)
        | weighing2.to(empty)
    )

    # as bucket removed, but expecting a second bucket
    bucket_swapped = (
        weighing1.to(empty)
    )

    bucket_put_back = (
        cancel_weighing1.to(weighing1)
        | cancel_weighing2.to(weighing2)
    )

    bucket_put_back_done = (
        done_weighing1.to(weighing1)
        | done_weighing2.to(weighing2)
    )

    bucket_put_back_swapped = (
        empty.to(weighing1)
    )

    task_completed = (
        weighing1.to(done_weighing1)
        | weighing2.to(done_weighing2)
    )

    fill = (
        weighing1.to(weighing1)
        | weighing2.to(weighing2)
    )

    task_canceled = (
        weighing1.to(cancel_weighing1)
        | weighing2.to(cancel_weighing2)
    )

    end = (
        done_weighing1.to(ready)
        | done_weighing2.to(ready)
    )

    cancel = (
        cancel_weighing1.to(ready)
        | cancel_weighing2.to(ready)
    )

    connection_lost = (
        weighing1.to(weighing1)
        | weighing2.to(weighing2)
        | cancel_weighing1.to(cancel_weighing1)
        | cancel_weighing2.to(cancel_weighing2)
        | done_weighing1.to(done_weighing1)
        | done_weighing2.to(done_weighing2)
        | empty.to(empty)
    )

    connection_restored = (
        weighing1.to(weighing1)
        | weighing2.to(weighing2)
        | cancel_weighing1.to(cancel_weighing1)
        | cancel_weighing2.to(cancel_weighing2)
        | done_weighing1.to(done_weighing1)
        | done_weighing2.to(done_weighing2)
        | empty.to(empty)
    )

    def __init__(self, displays:List[Display], release_scale:Callable[[],None]) -> None:

        # list of displays control, incl. the display of the selected scale if any
        self.displays: List[Display] = displays
        # release scale after weighing is done
        self.release_scale = release_scale
        self.scale_release_blocked = False #  if True, the scale is not released on entering READY (this is set on canceling a CANCEL/DONE timer by placing an empty container)

        # holds the WeightItem currently processed, if any
        self.current_weight_item:Optional[GreenWeightItem] = None
        self.process_state:PROCESS_STATE = PROCESS_STATE.DISCONNECTED
        self.process_state_before_connection_loss:PROCESS_STATE = PROCESS_STATE.DISCONNECTED
        self.component:int = 0 # component (of blend) currently processed (0 <= self.component < len(self.current_weight_item.descriptions))
        self.bucket:int = 0 # from {0,1,2}
        self.current_weight:int = 0 # in g # the current total (potentially over several containers) weight of the filled green coffee (without the weight of any bucket)

        # timers
        self.connection_loss_reset_timer = QTimer()
        self.connection_loss_reset_timer.setSingleShot(True)
        self.connection_loss_reset_timer.timeout.connect(lambda : self.send('reset'))
        self.empty_state_reset_timer = QTimer()
        self.empty_state_reset_timer.setSingleShot(True)
        self.empty_state_reset_timer.timeout.connect(lambda : self.send('reset'))

        super().__init__(allow_event_without_transition=True) # no errors for events which do not lead to transitions

    def set_accuracy(self, value:float) -> None:
        for display in self.displays:
            display.set_accuracy(value)

    def on_enter_ready(self) -> None:
        if not self.scale_release_blocked:
            self.release_scale()
        self.scale_release_blocked = False

    def on_enter_empty(self) -> None:
        self.empty_state_reset_timer.start(self.EMPTY_TIMEOUT)

    def on_exit_empty(self) -> None:
        self.empty_state_reset_timer.stop()

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

    def after_bucket_placed(self) -> None:
        self.process_state = PROCESS_STATE.WEIGHING
        if self.bucket == 1: # if we just swapped buckets
            self.bucket = 2  # we indicate the bucket recognition with a second bucket
        self.update_displays(progress=True)

    def after_bucket_removed(self) -> None:
        if self.bucket == 2:
            self.bucket = 1
        else:
            self.process_state = PROCESS_STATE.CONNECTED
            self.bucket = 0
            self.component = 0
            self.current_weight = 0
        self.update_displays(progress=True)

    def after_bucket_swapped(self) -> None:
        self.bucket = 1
        self.update_displays(progress=True)

    # final weight in g
    def after_task_completed(self, weight:int) -> None:
        self.process_state = PROCESS_STATE.DONE
        self.update_displays(final_weight = weight)

    def before_end(self, weight:int, block_scale_release:bool=False) -> None:
        del weight
        self.scale_release_blocked = block_scale_release

    # weight in g
    def after_end(self, weight:int) -> None:
        self.process_state = PROCESS_STATE.CONNECTED
        self.taskCompleted(weight/1000)
        self.component = 0
        self.bucket = 0
        self.current_weight = 0

    def after_task_canceled(self) -> None:
        self.process_state = PROCESS_STATE.CANCELD
        self.update_displays()

    def before_cancel(self, block_scale_release:bool=False) -> None:
        self.scale_release_blocked = block_scale_release

    def after_cancel(self) -> None:
        self.process_state = PROCESS_STATE.CONNECTED
        self.component = 0
        self.bucket = 0
        self.current_weight = 0
        self.update_displays()

    def after_bucket_put_back(self) -> None:
        self.process_state = PROCESS_STATE.WEIGHING
        self.update_displays(progress=True)

    def after_bucket_put_back_done(self) -> None:
        self.process_state = PROCESS_STATE.WEIGHING
        self.update_displays(progress=True)

    def after_bucket_put_back_swapped(self) -> None:
        self.process_state = PROCESS_STATE.WEIGHING
        self.bucket = 0
        self.update_displays(progress=True)

    def after_connection_lost(self) -> None:
        self.process_state_before_connection_loss = self.process_state
        self.process_state = PROCESS_STATE.DISCONNECTED
        self.update_displays()
        self.connection_loss_reset_timer.start(self.CONNECTION_LOSS_TIMEOUT)

    def after_connection_restored(self) -> None:
        self.connection_loss_reset_timer.stop()
        self.process_state = self.process_state_before_connection_loss
        self.update_displays()
        self.update_displays(progress=True)


    # new_weight is the new total weight of the measured greens without the bucket
    # if force_update is True, the display is update in any case, if not, the display is only update on increasing weights
    def after_fill(self, new_weight:int, force_update:bool) -> None:
        if self.current_weight_item is not None:# and self.current_weight != new_weight:
            # if there is another component, we check if we are done with the current one and can step to the next
            target = self.current_weight_item.weight * 1000 # target in g
            component_target_ratio = sum(component[0] for component in self.current_weight_item.descriptions[:self.component+1])
            component_target = component_target_ratio * target
            if new_weight >= component_target and len(self.current_weight_item.descriptions)>self.component+1:
                self.component += 1
            elif self.component > 0:
                # check if we should track back to the previous
                prev_component_target_ratio = sum(component[0] for component in self.current_weight_item.descriptions[:self.component])
                if new_weight < prev_component_target_ratio * target:
                    self.component -= 1
            increased = self.current_weight <= new_weight
            self.current_weight = new_weight
            if increased or force_update:
                self.update_displays(progress=True)

    def after_reset(self) -> None:
        self.release_scale()
        if self.process_state != PROCESS_STATE.DISCONNECTED:
            self.process_state = PROCESS_STATE.CONNECTED
        self.component = 0
        self.bucket = 0
        self.current_weight = 0
        self.update_displays()

# TESTING
#    # from statemachine import Event
#    @staticmethod
#    def on_transition(event_data, event: 'Event') -> None: # type:ignore
#        # The `event` parameter can be declared as `str` or `Event`, since `Event` is a subclass of `str`
#        # Note also that in this example, we're using `on_transition` instead of `on_cycle`, as this
#        # binds the action to run for every transition instead of a specific event ID.
#        assert event_data.event == event
#        _log.debug("GREEN_SM: Running %s from %s to %s", event.name, event_data.transition.source.id, event_data.transition.target.id)

    # weight in kg; if weight is None, the nominal weight from the ScheduleItem/WeightItem is used
    def taskCompleted(self, weight:Optional[float] = None) -> None:
        if self.current_weight_item is not None:
            if weight is None:
                weight = self.current_weight_item.weight
            _log.debug('BatchManager: green weighing task completed => %s', weight)
            self.current_weight_item.callback(str(self.current_weight_item.uuid), weight) # register weight in weight_item as prepared


#-
    # render current item and state on all active displays
    # if progress is True, the current weighing progress is displayed
    # final_weight in g if given
    def update_displays(self, progress:bool=False, final_weight:Optional[int] = None) -> None:
        for display in self.displays:
            if progress and self.current_weight_item is not None:
                display.show_progress(0, self.current_weight_item, self.process_state, self.component, self.bucket, self.current_weight)
            else:
                display.show_item(0, self.current_weight_item, self.process_state, component=self.component, final_weight=final_weight)

class RoastedWeighingState(StateMachine):

    CONNECTION_LOSS_TIMEOUT:Final[int] = 60*1000    # 1min; time in milliseconds before disconnect state is terminated by a 'reset'

    idle = State(initial=True)  # display_state = 0
    scale = State()             # scale available, display_state = 1
    prepared = State()          # empty bucket on scale, but no current_item available yet
    item = State()              # current_item available, display_state = 0
    ready = State()             # display_state = 1
    weighing = State()          # weighing a filled bucket
    filling = State()           # weighing starting from an empty bucket
    done = State()              # weighing done
    done_filling = State()      # filling done
    cancel_filling = State()    # cancel filling if filled bucket is not put back within some seconds

    reset = (
        idle.to(idle)
        | scale.to(scale)
        | prepared.to(scale)
        | item.to(item)
        | ready.to(ready)
        | weighing.to(ready)
        | filling.to(ready)
        | done.to(ready)
        | done_filling.to(ready)
        | cancel_filling.to(ready)
    )

    current_item = (
        idle.to(item)
        | item.to(item)                   # needed for updating displays to new current_item!
        | ready.to(ready, internal=True)  # needed for updating displays to new current_item, no entry/exist actions triggered!
        | scale.to(ready)
        | prepared.to(filling)
        | done_filling.to(done_filling)
    )

    clear_item = (
        ready.to(scale)
        | item.to(idle)
        | idle.to(idle) # ensure that internal display is cleared on scheduler tab switch in any case
    )

    available = (
        idle.to(scale)
        | item.to(ready)
    )

    unavailable = (
        scale.to(idle)
        | ready.to(item)
    )

    bucket_placed = (
        ready.to(weighing)
    )

    empty_bucket_placed = (
        scale.to(prepared)
        | ready.to(filling)
    )

    # empty bucket removed
    bucket_removed = (
        filling.to(ready)
    )

    update = (
        weighing.to(weighing)
    )

    bucket_put_back = (
        cancel_filling.to(filling)
    )

    bucket_put_back_done = (
        done_filling.to(filling)
    )

    fill = (
        filling.to(filling)
    )

    task_canceled = (
        filling.to(cancel_filling)
    )

    task_completed = (
        weighing.to(done)
        | filling.to(done_filling)
    )

    end = (
        done.to(ready)
        | done_filling.to(ready)
    )

    cancel = (
        cancel_filling.to(ready)
    )

    connection_lost = (
        weighing.to(weighing)
        | prepared.to(prepared)
        | filling.to(filling)
        | cancel_filling.to(cancel_filling)
        | done.to(done)
        | done_filling.to(done_filling)
    )

    connection_restored = (
        weighing.to(weighing)
        | prepared.to(prepared)
        | filling.to(filling)
        | cancel_filling.to(cancel_filling)
        | done.to(done)
        | done_filling.to(done_filling)
    )

    def __init__(self, displays:List[Display], release_scale:Callable[[],None]) -> None:

        # list of displays control, incl. the display of the selected scale if any
        self.displays: List[Display] = displays
        # release scale after weighing is done
        self.release_scale = release_scale

        # holds the WeightItem currently processed, if any
        self.current_weight_item:Optional[RoastedWeightItem] = None
        self.process_state:PROCESS_STATE = PROCESS_STATE.DISCONNECTED
        self.process_state_before_connection_loss:PROCESS_STATE = PROCESS_STATE.DISCONNECTED
        self.current_weight:int = 0 # in g # the current total weight of the roasted coffee (without the weight of the bucket)

        # timers
        self.connection_loss_reset_timer = QTimer()
        self.connection_loss_reset_timer.setSingleShot(True)
        self.connection_loss_reset_timer.timeout.connect(lambda : self.send('reset'))

        super().__init__(allow_event_without_transition=True) # no errors for events which do not lead to transitions

    def set_accuracy(self, value:float) -> None:
        for display in self.displays:
            display.set_accuracy(value)

    def on_enter_ready(self) -> None:
        self.release_scale()

    def after_current_item(self, weight_item:RoastedWeightItem, source:State) -> None:
        self.current_weight_item = weight_item
        # update displays
        if source == self.prepared and self.process_state == PROCESS_STATE.WEIGHING:
            # if we are coming from PREPARED, we reset the PROCESS_STATE back from the temporary WEIGHING to CONNECTED to ensure
            # that DISPLAY.show_item() sets the self.last_process_state correctly for the DISPLAY.show_progress() below to be effective
            self.process_state = PROCESS_STATE.CONNECTED
        self.update_displays()
        if source == self.prepared:
            self.process_state = PROCESS_STATE.WEIGHING
            self.update_displays(progress=True) # from PREPARED to FILLING we need to ensure that 'weight' gets calculated and set in the displays

    def after_clear_item(self) -> None:
        self.current_weight_item = None
        self.update_displays()

    def after_available(self) -> None:
        self.process_state = PROCESS_STATE.CONNECTED
        self.update_displays()

    def after_unavailable(self) -> None:
        self.process_state = PROCESS_STATE.DISCONNECTED
        self.update_displays()

    # weight is yield in g
    def after_bucket_placed(self, weight:int) -> None:
        self.current_weight = weight
        self.process_state = PROCESS_STATE.WEIGHING
        self.update_displays(result=True)

    # weight is yield in g
    def after_empty_bucket_placed(self) -> None:
        self.process_state = PROCESS_STATE.WEIGHING
        self.update_displays(progress=True)

    def after_bucket_removed(self) -> None:
        self.process_state = PROCESS_STATE.CONNECTED
        self.current_weight = 0
        self.update_displays(progress=True)

    def after_update(self, weight:int) -> None:
        self.current_weight = weight
        self.update_displays(result=True)

    # final weight in g
    def after_task_completed(self, weight:int) -> None:
        self.process_state = PROCESS_STATE.DONE
        self.update_displays(final_weight = weight)

    # weight in g
    def after_end(self, weight:int) -> None:
        self.process_state = PROCESS_STATE.CONNECTED
        self.taskCompleted(weight/1000)

    def after_task_canceled(self) -> None:
        self.process_state = PROCESS_STATE.CANCELD
        self.update_displays()

    def after_cancel(self) -> None:
        self.process_state = PROCESS_STATE.CONNECTED
        self.current_weight = 0
        self.update_displays()

    def after_bucket_put_back(self) -> None:
        self.process_state = PROCESS_STATE.WEIGHING
        self.update_displays(progress=True)

    def after_bucket_put_back_done(self) -> None:
        self.process_state = PROCESS_STATE.WEIGHING
        self.update_displays(progress=True)

    def after_connection_lost(self) -> None:
        self.process_state_before_connection_loss = self.process_state
        self.process_state = PROCESS_STATE.DISCONNECTED
        self.update_displays()
        self.connection_loss_reset_timer.start(self.CONNECTION_LOSS_TIMEOUT)

    def after_connection_restored(self) -> None:
        self.connection_loss_reset_timer.stop()
        self.process_state = self.process_state_before_connection_loss
        self.update_displays()
        self.update_displays(progress=True)

    # new_weight is the new total weight of the measured greens without the bucket
    # if force_update is True, the display is update in any case, if not, the display is only update on increasing weights
    def after_fill(self, new_weight:int, force_update:bool) -> None:
        increased = self.current_weight <= new_weight
        self.current_weight = new_weight
        if increased or force_update:
            self.update_displays(progress=True)

    def after_reset(self) -> None:
        self.release_scale()
        if self.process_state != PROCESS_STATE.DISCONNECTED:
            self.process_state = PROCESS_STATE.CONNECTED
        self.update_displays()



# TESTING
#    @staticmethod
#    def on_transition(event_data, event: 'Event') -> None: # type:ignore
#        # The `event` parameter can be declared as `str` or `Event`, since `Event` is a subclass of `str`
#        # Note also that in this example, we're using `on_transition` instead of `on_cycle`, as this
#        # binds the action to run for every transition instead of a specific event ID.
#        assert event_data.event == event
#        _log.debug("ROASTED_SM: Running %s from %s to %s", event.name, event_data.transition.source.id, event_data.transition.target.id)


    # weight in kg; if weight is None, the estimated weight from the ScheduleItem/WeightItem is used
    def taskCompleted(self, weight:Optional[float] = None) -> None:
        if self.current_weight_item is not None:
            if weight is None:
                weight = self.current_weight_item.weight_estimate
            _log.debug('BatchManager: roasted weighing task completed => %s', weight)
            self.current_weight_item.callback(str(self.current_weight_item.uuid), weight) # register weight in weight_item as prepared



    # render current item and state on all active displays
    # if result is True, the current weighing result is displayed
    # final_weight in g if given
    def update_displays(self, result:bool=False, final_weight:Optional[int] = None,  progress:bool=False) -> None:
        for display in self.displays:
            if result and self.current_weight_item is not None:
                display.show_result(1, self.current_weight_item, self.process_state, self.current_weight)
            elif progress:
                display.show_progress(1, self.current_weight_item, self.process_state, 1, 1, self.current_weight)
            else:
                display.show_item(1, self.current_weight_item, self.process_state, final_weight=final_weight)



class WeightManager(QObject): # pyright:ignore[reportGeneralTypeIssues] # pyrefly: ignore [invalid-inheritance] # error: Argument to class must be a base class

    __slots__ = [ 'displays', 'scale_manager', 'next_green_item',  'next_roasted_item',
                    'greenItemSemaphore', 'roastedItemSemaphore', 'green_sm' ]

    MIN_STABLE_WIGHT_CHANGE:Final[int] = 2                  # minimum stable weight changes being recognized in g
    MIN_CUSTOM_EMPTY_BUCKET_WEIGHT:Final[int] = 15          # minimum custom empty bucket weight recognized in g
    MIN_EMPTY_BUCKET_WEIGHT:Final[int] = 200                # minimum empty bucket weight recognized in g
    MAX_EMPTY_BUCKET_WEIGHT:Final[int] = 4000               # maximum empty bucket weight recognized in g
    MIN_EMPTY_BUCKET_WEIGHT_BATCH_PERECENT:Final[int] = 5   # minimum empty bucket weight percentage of batch size in %
    MAX_EMPTY_BUCKET_WEIGHT_BATCH_PERECENT:Final[int] = 25  # maximum empty bucket weight percentage of batch size in %
    MIN_EMPTY_BUCKET_RECOGNITION_TOLERANCE:Final[int] = 10  # +- minimal tolerance to recognize empty green bucket in g
    EMPTY_BUCKET_RECOGNITION_TOLERANCE_PERCENT:Final[float] = 5     # +- tolerance to recognize empty green bucket in % of bucket weight
    #-
    EMPTY_SCALE_RECOGNITION_TOLERANCE_TIGHT:Final[int] = 25 # +- tight tolerance to recognize empty scale in g for scale.readability() < 1g
    EMPTY_SCALE_RECOGNITION_TOLERANCE_LOOSE:Final[int] = 60 # +- loose tolerance to recognize empty scale in g for scale.readability() >= 1g
    CANCELED_STEP_RECOGNITION_TOLERANCE:Final[int] = 15     # +- tolerance to recognize a previous 'task_cancel' step to restart via 'bucket_put_back' in g
    DONE_STEP_RECOGNITION_TOLERANCE:Final[int] = 15         # +- tolerance to recognize a previous 'task_completed' step to restart via 'bucket_put_back_done' in g
    SWAP_STEP_RECOGNITION_TOLERANCE:Final[int] = 15         # +- tolerance to recognize a previous 'bucket_swapped' step to restart via 'bucket_put_back_swapped' in g
    ROASTED_BUCKET_TOLERANCE:Final[int] = 15                # +- tolerance to recognize filled roasted container in % w.r.t. the estimated weight
                                                            # (weight loss defaults to 15% if no template is given)
    ROASTED_BUCKET_REMOVALE_TOLERANCE:Final[int] = 15       # +- tolerance to recognize roasted bucket removal in g
    TAP_CANCEL_THRESHOLD = 100                              # threshold in g the measured weight has to exceed the empty scale weight for a tap-cancel action to be recognized
    TAP_CANCEL_PERIOD = 400                                 # time in ms after which the weight has to fall back to the empty scale weight for a tap-cancel action to be recognized

    WAIT_BEFORE_CANCEL:Final[int] = 5000  # time in milliseconds to display the CANCEL message before returning to READY
    WAIT_BEFORE_DONE:Final[int] = 5000    # time in milliseconds to display the DONE message before returning to READY

    def __init__(self, aw:'ApplicationWindow', displays:List[Display], scale_manager:ScaleManager) -> None:
        super().__init__()

        self.aw = aw # the Artisan application window

        self.scale_manager = scale_manager

        # set display done/cancel timer values
        for display in displays:
            display.set_cancel_timer_timeout(int(round(self.WAIT_BEFORE_CANCEL/1000)))
            display.set_done_timer_timeout(int(round(self.WAIT_BEFORE_DONE/1000)))

        # holds the next WeightItem waiting to be processed, if any
        self.next_green_item:Optional[GreenWeightItem] = None
        self.next_roasted_item:Optional[RoastedWeightItem] = None

        self.greenItemSemaphore = QSemaphore(1) # semaphore to protect access to next_green_item
        self.roastedItemSemaphore = QSemaphore(1) # semaphore to protect access to next_roasted_item

        self.sm_green = GreenWeighingState(displays, self.release_green_task_scale)
# write request to log to generate an SVG graph of the self.sm_green Statemachine
#        from urllib.parse import quote
#        _log.debug("PRINT sm_green: %s", f"https://quickchart.io/graphviz?graph={quote(self.sm_green._graph().to_string())}")

        self.sm_roasted = RoastedWeighingState(displays, self.release_roasted_task_scale)
# write request to log to generate an SVG graph of the self.sm_green Statemachine
#        from urllib.parse import quote
#        _log.debug("PRINT sm_roasted: %s", f"https://quickchart.io/graphviz?graph={quote(self.sm_roasted._graph().to_string())}")

        # last stable weights the scales reported
        self.scale1_last_stable_weight:int = 0 # in g
        self.scale2_last_stable_weight:int = 0 # in g

        self.last_nonstable_green_weight:int = 0 # in g
        self.last_nonstable_roasted_weight:int = 0 # in g

        # scale assignment => 0:no scale assigned, 1: scale1 assigned, 2: scale2 assigned
        self.green_task_scale:int = 0
        self.roasted_task_scale:int = 0

        # Weighing State.
        self.green_task_empty_scale_weight:int = 0            # weight of the empty scale
        self.green_task_scale_tare_weight:int = 0             # last stable weight after placing the empty bucket (green)
        self.roasted_task_scale_tare_weight:int = 0           # last stable weight after placing the empty bucket (roasted)
        self.green_task_container1_registered_weight:int = 0  # holds the green fill weight of the first container after container swap
        self.green_task_stable_weight_before_connection_loss = 0 # holds the green weight before the connection to the assigned scale got lost
        self.roasted_task_stable_weight_before_connection_loss = 0 # holds the roasted weight before the connection to the assigned scale got lost
        self.task_canceled_step:int = 0                       # remember step (in g) that did lead to "task_cancel" allowing for a restart via "bucket_put_back" on recognizing the inverse step
        self.task_done_step:int = 0                           # remember step (in g) that did lead to "task_completed" allowing for a restart via "bucket_put_back_done" on recognizing the
        self.task_swapped_step:int = 0                        # remember step (in g) that did lead to "task_swapped" allowing for a restart via "bucket_put_back_swapped" on recognizing the
        self.task_done_weight:int = 0                         # remember weight (in g) that did lead to "task_completed" allowing to complete this task
        #-
        self.roasted_task_empty_scale_weight:int = 0          # weight of the empty scale (tare weight)
        self.roasted_task_scale_total_weight:int = 0          # the reading of the scale with the full roasted bucket placed minus the tare (includes the bucket weight)

        self.roasted_task_canceled_step:int = 0               # remember step (in g) that did lead to "task_cancel" allowing for a restart via "bucket_put_back" on recognizing the inverse step
        self.roasted_task_done_step:int = 0                   # remember step (in g) that did lead to "task_completed" allowing for a restart via "bucket_put_back_done" on recognizing the

        self.roasted_task_done_weight:int =0                  # remember weight (in g) that did lead to roasted task_completed allowing to complete this task

        # Timers
        self.cancel_green_task_timer = QTimer()
        self.cancel_green_task_timer.setSingleShot(True)
        self.cancel_green_task_timer.timeout.connect(self.cancel_green_task_slot)

        self.cancel_roasted_task_timer = QTimer()
        self.cancel_roasted_task_timer.setSingleShot(True)
        self.cancel_roasted_task_timer.timeout.connect(self.cancel_roasted_task_slot)

        self.done_green_task_timer = QTimer()
        self.done_green_task_timer.setSingleShot(True)
        self.done_green_task_timer.timeout.connect(self.done_green_task_slot)

        self.done_roasted_task_timer = QTimer()
        self.done_roasted_task_timer.setSingleShot(True)
        self.done_roasted_task_timer.timeout.connect(self.done_roasted_task_slot)

        self.tap_cancel_green_task_timer = QTimer()
        self.tap_cancel_green_task_timer.setSingleShot(True)
        self.tap_cancel_green_task_timer.timeout.connect(self.tap_cancel_green_task_slot)

        self.tap_cancel_roasted_task_timer = QTimer()
        self.tap_cancel_roasted_task_timer.setSingleShot(True)
        self.tap_cancel_roasted_task_timer.timeout.connect(self.tap_cancel_roasted_task_slot)

        self.start() # connect to configured scales


    # queues a GreenWeightItem for processing
    # if item is None, the next green item is cleared
    # Note: the queue has size 1 and a newer incoming item overwrites an older already queued item
    def set_next_green(self, item:Optional[GreenWeightItem]) -> None:
        if item is None:
            self.clear_next_green()
        else:
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
        if self.sm_green.process_state != PROCESS_STATE.WEIGHING:
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

    # called from Scheduler on click of the Scheduler Task Display or on task completion
    # weight in kg
    def greenTaskCompleted(self, weight:Optional[float] = None) -> None:
        self.sm_green.taskCompleted(weight)


#--

    # queues a RoastedWeightItem for processing
    # if item is None, the next roasted item is cleared
    # Note: the queue has size 1 and a newer incoming item overwrites an older already queued item
    @pyqtSlot()
    def set_next_roasted(self, item:Optional[RoastedWeightItem]) -> None:
        if item is None:
            self.clear_next_roasted()
        else:
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
        # if there is no current_item and PROCESS_STATE.WEIGHING (PREPARED state waiting for an item, but connected to scale) or
        # if there is no scale, we fetch that item immediately and start "processing"
        # even if there is already a current one in "processing"
        if ((self.sm_roasted.current_weight_item is None and self.sm_roasted.process_state == PROCESS_STATE.WEIGHING) or
            self.sm_roasted.process_state in {PROCESS_STATE.DISCONNECTED, PROCESS_STATE.CONNECTED}):
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

    # called from Scheduler on click of the Scheduler Task Display
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
        if self.aw.taskWebDisplayGreenActive:
            self.sm_green.send('available')
        else:
            self.sm_green.send('unavailable')
        if self.aw.taskWebDisplayRoastedActive:
            self.sm_roasted.send('available')
        else:
            self.sm_roasted.send('unavailable')

    @pyqtSlot()
    def scales_unavailable(self) -> None:
        self.sm_green.send('unavailable')
        self.sm_roasted.send('unavailable')

    # returns roasted container weight in g if one is set
    def roasted_container_weight(self) -> Optional[int]:
        if 0 <= self.aw.container2_idx < len(self.aw.qmc.container_weights):
            return int(round(self.aw.qmc.container_weights[self.aw.container2_idx])) # in g
        return None

    # returns the expected total weight (bucket + roasted coffee) in g of the roasted current_weight_item if any
    # or None if there is no current_weight_item
    def expected_roasted_weight(self) -> Optional[int]:
        roasted_container_weight:Optional[int] = self.roasted_container_weight()
        if self.sm_roasted.current_weight_item is None or roasted_container_weight is None:
            return None
        # current_weight_item.weight holds the weight estimate for the roasted batch in kg
        # either taken from the template or assuming a default loss (15%)
        return int(round(self.sm_roasted.current_weight_item.weight * 1000 + roasted_container_weight))


    # estimated_roasted_weight in kg
    # roasted_bucket_weight in g
    # returns the estimated minimal weight (incl. the  WeightManager.ROASTED_BUCKET_TOLERANCE used by filled_roasted_container_placed)
    # of the filled roasted bucket in g
    @staticmethod
    def filled_roasted_bucket_estimated_minimal_weight(estimated_roasted_weight:float, roasted_bucket_weight:float) -> float:
        estimated_weight = estimated_roasted_weight*1000 + roasted_bucket_weight # in g
        return estimated_weight - (estimated_weight * WeightManager.ROASTED_BUCKET_TOLERANCE/100)

    # filled_container_weight in g
    # estimated_roasted_weight in kg
    # roasted_bucket_weight in g
    # returns True if the roasted coffee weight (filled_container_weight - roasted_bucket_weight) is within estimated_roasted_weight +- self.ROASTED_BUCKET_TOLERANCE (in %)
    @staticmethod
    def filled_roasted_container_placed(filled_container_weight:int, estimated_roasted_weight:float, roasted_bucket_weight:float) -> bool:
#        _log.debug("PRINT filled_roasted_container_placed(%s,%s,%s)",filled_container_weight,estimated_roasted_weight,roasted_bucket_weight)
        estimated_roasted_weight_g = estimated_roasted_weight*1000
        return abs(estimated_roasted_weight_g - (filled_container_weight - roasted_bucket_weight)) < (estimated_roasted_weight_g * WeightManager.ROASTED_BUCKET_TOLERANCE/100)

    # step in g
    # batchsize in kg
    #--
    # empty bucket weight needs in any case to be larger than WeightManager.MIN_CUSTOM_EMPTY_BUCKET_WEIGHT and smaller than roasted total weight of filled roasted bucket
    # recognition tolerance is at least +-MIN_EMPTY_BUCKET_RECOGNITION_TOLERANCE and otherwise +-EMPTY_BUCKET_RECOGNITION_TOLERANCE_PERCENT percent of the
    #   selected bucket or (-EMPTY_BUCKET_RECOGNITION_TOLERANCE percent of the min_bucket_weight and EMPTY_BUCKET_RECOGNITION_TOLERANCE of the max_bucket weight)
    # the bucket weight has to be
    #   +-WeightManager.MIN_EMPTY_BUCKET_RECOGNITION_TOLERANCE of the set green bucket weight if available
    #   +-WeightManager.MIN_EMPTY_BUCKET_RECOGNITION_TOLERANCE of the defined bucket weights if available (an no green bucket is set)
    #   between WeightManager.MIN_EMPTY_BUCKET_WEIGHT_BATCH_PERECENT and WeightManager.MAX_EMPTY_BUCKET_WEIGHT_BATCH_PERECENT of the batchsize (if given)
    #     but not smaller than WeightManager.MIN_EMPTY_BUCKET_WEIGHT and WeightManager.MAX_EMPTY_BUCKET_WEIGHT
    # if green is True we check for an empty bucket to weigh greens otherwise to weigh roasted
    def empty_bucket_placed(self, step:int, batchsize:Optional[float], green:bool=True) -> bool:
        # the empty bucket weight must be lighter than the total weight of a filled roasted bucket
        # to avoid overlapping recognition
        # NOTE: a very light roasting task can block the recognition of the placement of empty green buckets
        #       Thus, this is rather unlikely as the roasted task contains already the weight of a bucket
        if (self.sm_roasted.current_weight_item is not None and                        # there is a current roasting task
                self.roasted_task_scale == 0 and                                       # there is no scale yet assigned to the roasted task
                0 <= self.aw.container2_idx <= len(self.aw.qmc.container_weights) and  # there is a roasted container weight specified
                step >= self.filled_roasted_bucket_estimated_minimal_weight(
                            self.sm_roasted.current_weight_item.weight_estimate, self.aw.qmc.container_weights[self.aw.container2_idx])):
            return False

        # bucket smaller than the total weight of the filled roasted bucket

        if step > WeightManager.MIN_CUSTOM_EMPTY_BUCKET_WEIGHT:
            # larger than absolute minimum bucket weight

            if green and 0 <= self.aw.container1_idx < len(self.aw.qmc.container_weights):
                # if green bucket is set, step should be about the weight of the user defined green bucket
                selected_container_weight = self.aw.qmc.container_weights[self.aw.container1_idx]
                return abs(selected_container_weight - step) <= max(float(WeightManager.MIN_EMPTY_BUCKET_RECOGNITION_TOLERANCE),
                    selected_container_weight*WeightManager.EMPTY_BUCKET_RECOGNITION_TOLERANCE_PERCENT/100)
            if not green and 0 <= self.aw.container2_idx < len(self.aw.qmc.container_weights):
                # if roasted bucket is set, step should be about the weight of the user defined roasted bucket
                selected_container_weight = self.aw.qmc.container_weights[self.aw.container2_idx]
                return abs(selected_container_weight - step) <= max(float(WeightManager.MIN_EMPTY_BUCKET_RECOGNITION_TOLERANCE),
                    selected_container_weight*WeightManager.EMPTY_BUCKET_RECOGNITION_TOLERANCE_PERCENT/100)

            # default min/max limits between 5% and 25% of batchsize in g, with absolute min. of 300g and max. of 4000g
            min_bucket_weight:float
            max_bucket_weight:float
            if batchsize is None:
                min_bucket_weight = float(WeightManager.MIN_EMPTY_BUCKET_WEIGHT)
                max_bucket_weight = float(WeightManager.MAX_EMPTY_BUCKET_WEIGHT)
            else:
                min_bucket_weight = max(float(WeightManager.MIN_EMPTY_BUCKET_WEIGHT), batchsize*1000*WeightManager.MIN_EMPTY_BUCKET_WEIGHT_BATCH_PERECENT/100)
                max_bucket_weight = min(float(WeightManager.MAX_EMPTY_BUCKET_WEIGHT), batchsize*1000*WeightManager.MAX_EMPTY_BUCKET_WEIGHT_BATCH_PERECENT/100)

            if len(self.aw.qmc.container_weights) > 0:
                # if custom containers  are defined we use the min/max limits over all user defined container weights
                min_bucket_weight = min(self.aw.qmc.container_weights)
                max_bucket_weight = max(self.aw.qmc.container_weights)

            min_tolerance = max(float(WeightManager.MIN_EMPTY_BUCKET_RECOGNITION_TOLERANCE),
                                min_bucket_weight*WeightManager.EMPTY_BUCKET_RECOGNITION_TOLERANCE_PERCENT/100)
            max_tolerance = max(float(WeightManager.MIN_EMPTY_BUCKET_RECOGNITION_TOLERANCE),
                                max_bucket_weight*WeightManager.EMPTY_BUCKET_RECOGNITION_TOLERANCE_PERCENT/100)
            return min_bucket_weight - min_tolerance <= step <= max_bucket_weight + max_tolerance

        return False

    def empty_scale_tolerance(self, scale_nr:int) -> int:
        return (WeightManager.EMPTY_SCALE_RECOGNITION_TOLERANCE_LOOSE if self.scale_manager.readability(scale_nr) >= 1 else WeightManager.EMPTY_SCALE_RECOGNITION_TOLERANCE_TIGHT)

    # tare_weight and current_weight in g
    def scale_empty(self, scale_nr:int, empty_weight:int, current_weight:int) -> bool:
        return bool(abs(empty_weight - current_weight) <= self.empty_scale_tolerance(scale_nr))

    # scale_nr: 1 or 2
    def scale_stable_weight_changed(self, scale_nr:int, stable_weight:int) -> None:

        step = stable_weight - (self.scale1_last_stable_weight if scale_nr == 1 else self.scale2_last_stable_weight)

#        _log.debug("PRINT self.scale1_last_stable_weight: %s",self.scale1_last_stable_weight)
#        _log.debug("PRINT self.scale2_last_stable_weight: %s",self.scale2_last_stable_weight)
#        _log.debug('PRINT scale_stable_weight_changed(%s,%s) => step: %s', scale_nr, stable_weight, step)

        if abs(step) <= self.MIN_STABLE_WIGHT_CHANGE:
            return

        if step > 0:

            # weight added

            # 1. Cancel Green Cancel
            if (self.green_task_scale == scale_nr and
                    self.sm_green.current_state in {GreenWeighingState.cancel_weighing1, GreenWeighingState.cancel_weighing2} and
                    self.task_canceled_step < 0 and abs(step + self.task_canceled_step) < self.CANCELED_STEP_RECOGNITION_TOLERANCE):
                # Cancel of the cancel operation; we restart at the canceled state
                self.signal_green_task_scale(STATE_ACTION.INTERRUPTED)
                self.cancel_green_task_timer.stop()
                self.task_canceled_step = 0
                self.sm_green.send('bucket_put_back')

            # 2. Cancel Green Done
            elif (self.green_task_scale == scale_nr and
                    self.sm_green.current_state in {GreenWeighingState.done_weighing1, GreenWeighingState.done_weighing2} and
                    self.task_done_step < 0 and abs(step + self.task_done_step) < self.DONE_STEP_RECOGNITION_TOLERANCE):
                # Cancel of the done operation; we restart at the done state
                self.done_green_task_timer.stop()
                self.signal_green_task_scale(STATE_ACTION.INTERRUPTED)
                self.task_done_step = 0
                self.task_done_weight = 0
                self.sm_green.send('bucket_put_back_done')


            # 3. Cancel Roasted Cancel
            if (self.roasted_task_scale == scale_nr and
                    self.sm_roasted.current_state == RoastedWeighingState.cancel_filling and
                    self.roasted_task_canceled_step < 0 and abs(step + self.roasted_task_canceled_step) < self.CANCELED_STEP_RECOGNITION_TOLERANCE):
                # Cancel of the cancel operation; we restart at the canceled state
                self.signal_roasted_task_scale(STATE_ACTION.INTERRUPTED)
                self.cancel_roasted_task_timer.stop()
                self.roasted_task_canceled_step = 0
                self.sm_roasted.send('bucket_put_back')

            # 4. Cancel Roasted Done
            elif (self.roasted_task_scale == scale_nr and
                    self.sm_roasted.current_state == RoastedWeighingState.done_filling and
                    self.roasted_task_done_step < 0 and abs(step + self.roasted_task_done_step) < self.DONE_STEP_RECOGNITION_TOLERANCE):
                # Cancel of the done operation; we restart at the done state
                self.done_roasted_task_timer.stop()
                self.signal_roasted_task_scale(STATE_ACTION.INTERRUPTED)
                self.roasted_task_done_step = 0
                self.roasted_task_done_weight = 0
                self.sm_roasted.send('bucket_put_back_done')


            # 5. Cancel Container Swap (from EMPTY TO WEIHING1; bucket_put_back_swapped
            elif (self.green_task_scale == scale_nr and
                    self.sm_green.current_state == GreenWeighingState.empty and
                    self.task_swapped_step < 0 and abs(step + self.task_swapped_step) < self.SWAP_STEP_RECOGNITION_TOLERANCE):
                # Cancel of the done operation; we restart at the done state
                self.task_swapped_step = 0
                self.green_task_container1_registered_weight = 0
                self.sm_green.send('bucket_put_back_swapped')
                self.signal_green_task_scale(STATE_ACTION.INTERRUPTED)

            # 6. Place Empty Green Bucket (gets priority over placing an empty roasted bucket in the next clause!)
            elif (self.aw.taskWebDisplayGreenActive and                                        # only if Task Display Green is active
                    self.sm_green.current_weight_item is not None and                          # current green weight item is established
                    (((self.sm_green.current_state in
                        {GreenWeighingState.ready, GreenWeighingState.empty}) and              # green State Machine is in READY or EMPTY state
                        (self.green_task_scale == 0 or
                          self.green_task_container1_registered_weight != 0)) or               # no scale yet assigned to the green task or we are swapping containers
                     (self.sm_green.current_state in
                        {GreenWeighingState.cancel_weighing1,                                  # shortcut the cancel/done timer by placing an empty bucket
                        GreenWeighingState.cancel_weighing2,
                        GreenWeighingState.done_weighing1,
                        GreenWeighingState.done_weighing2} and
                        self.green_task_scale == scale_nr)) and                                # step received on currently assigned scale
                    self.empty_bucket_placed(step, self.sm_green.current_weight_item.weight)): # empty green bucket recognized

                self.sm_green.set_accuracy(self.aw.green_task_precision) # update the GreenStateMachine/Display accuracy

                if self.sm_green.current_state in {GreenWeighingState.cancel_weighing1,GreenWeighingState.cancel_weighing2}:
                    # if task got canceled and cancel timer is still running we stop it here
#                    self.signal_green_task_scale(STATE_ACTION.CANCEL_EXIT) # not needed as new reservation is immediately following with corresponding signalling
                    self.cancel_green_task_timer.stop()
                    self.task_canceled_step = 0
                    self.sm_green.send('cancel', block_scale_release=True)
                    self.sm_green.current_weight_item.callback('', 0) # trigger an refresh of the next weight_item, a previous fetch_next_green update might have been blocked while processing
                elif self.sm_green.current_state in {GreenWeighingState.done_weighing1,GreenWeighingState.done_weighing2}:
                    # if task got completed and done timer is still running we stop it here
#                    self.signal_green_task_scale(STATE_ACTION.OK_EXIT) # not needed as new reservation is immediately following with corresponding signalling
                    self.done_green_task_timer.stop()
                    self.sm_green.send('end', self.task_done_weight, block_scale_release=True)
                    self.task_done_step = 0
                    self.task_done_weight = 0
                    self.green_task_container1_registered_weight = 0

                # reserve scale for the green task
                if scale_nr == 1:
                    self.green_task_scale = scale_nr
                    self.green_task_scale_tare_weight = stable_weight # the reading of the scale with the empty bucket placed
                    self.green_task_empty_scale_weight = self.scale1_last_stable_weight
                    self.scale_manager.scale1_connected_signal.connect(self.scale1_connected_slot)
                    self.scale_manager.scale1_disconnected_signal.connect(self.scale1_disconnected_slot)
                    self.scale_manager.reserve_scale1_signal.emit()
                    if self.green_task_container1_registered_weight > 0:
                        # bucket swapped
                        self.scale_manager.signal_user_scale1_signal.emit(STATE_ACTION.SWAP_EXIT)
                        _log.debug('BatchManager: bucket placed on scale 1: bucket swapped')
                    else:
                        self.scale_manager.signal_user_scale1_signal.emit(STATE_ACTION.ASSIGNED_GREEN)
                        _log.debug('BatchManager: bucket placed on scale 1: %s',self.green_task_container1_registered_weight)
                    # make state transition (which then triggers the display update)
                    self.sm_green.send('bucket_placed')
                elif scale_nr == 2:
                    self.green_task_scale = scale_nr
                    self.green_task_scale_tare_weight = stable_weight # the reading of the scale with the empty bucket placed
                    self.green_task_empty_scale_weight = self.scale2_last_stable_weight
                    self.scale_manager.scale2_connected_signal.connect(self.scale2_connected_slot)
                    self.scale_manager.scale2_disconnected_signal.connect(self.scale2_disconnected_slot)
                    self.scale_manager.reserve_scale2_signal.emit()
                    if self.green_task_container1_registered_weight > 0:
                        # bucket swapped
                        self.scale_manager.signal_user_scale2_signal.emit(STATE_ACTION.SWAP_EXIT)
                        _log.debug('BatchManager: bucket placed on scale 2: bucket swapped')
                    else:
                        self.scale_manager.signal_user_scale2_signal.emit(STATE_ACTION.ASSIGNED_GREEN)
                        _log.debug('BatchManager: bucket placed on scale 2: %s',self.green_task_container1_registered_weight)
                    # make state transition (which then triggers the display update)
                    self.sm_green.send('bucket_placed')

            # 7. Place Empty Roasted Bucket (only if empty green bucket not recognized)
            elif ((self.aw.taskWebDisplayRoastedActive or (self.aw.schedule_window is not None and self.aw.schedule_window.TabWidget.currentIndex() == 1)) and
                        # only if Task Display Roasted is active; strictly not necessary,
                        #   but this way it allows to deactivate the mechanism
                    self.roasted_task_scale == 0 and                                       # no scale yet assigned to the roasted task
                    # either there is no current roasted weight item or there is a single one
                    (self.sm_roasted.current_weight_item is None or
                        # the current weight item is the only non-completed one (first and last uncompleted):
                        (self.aw.schedule_window is not None and
                         self.aw.schedule_window.is_only_not_completed_item(self.sm_roasted.current_weight_item.uuid))) and
                    self.empty_bucket_placed(step, (None if self.sm_roasted.current_weight_item is None else self.sm_roasted.current_weight_item.weight), False)): # empty roasted bucket recognized

                self.sm_roasted.set_accuracy(0)

                if self.sm_roasted.current_weight_item is not None:
                    if self.sm_roasted.current_state == RoastedWeighingState.cancel_filling:
                        # if task got canceled and cancel timer is still running we stop it here
                        self.cancel_roasted_task_timer.stop()
                        self.roasted_task_canceled_step = 0
                        self.sm_roasted.send('cancel', block_scale_release=True)
                        self.sm_roasted.current_weight_item.callback('', 0) # trigger an refresh of the next weight_item, a previous fetch_next_roasted update might have been blocked while processing
                    elif self.sm_roasted.current_state == RoastedWeighingState.done_filling:
                        # if task got completed and done timer is still running we stop it here
                        self.done_roasted_task_timer.stop()
                        self.sm_roasted.send('end', self.roasted_task_done_weight, block_scale_release=True)
                        self.roasted_task_done_step = 0
                        self.roasted_task_done_weight = 0

                # reserve scale for the roasted task
                if scale_nr == 1:
                    self.roasted_task_scale = scale_nr
                    self.roasted_task_scale_tare_weight = stable_weight  # the reading of the scale with the empty bucket placed
                    self.roasted_task_empty_scale_weight = self.scale1_last_stable_weight
                    self.scale_manager.scale1_connected_signal.connect(self.scale1_connected_slot)
                    self.scale_manager.scale1_disconnected_signal.connect(self.scale1_disconnected_slot)
                    self.scale_manager.reserve_scale1_signal.emit()
                    self.scale_manager.signal_user_scale1_signal.emit(STATE_ACTION.ASSIGNED_ROASTED)
                elif scale_nr == 2:
                    self.roasted_task_scale = scale_nr
                    self.roasted_task_scale_tare_weight = stable_weight  # the reading of the scale with the empty bucket placed
                    self.roasted_task_empty_scale_weight = self.scale2_last_stable_weight
                    self.scale_manager.scale2_connected_signal.connect(self.scale2_connected_slot)
                    self.scale_manager.scale2_disconnected_signal.connect(self.scale2_disconnected_slot)
                    self.scale_manager.reserve_scale2_signal.emit()
                    self.scale_manager.signal_user_scale2_signal.emit(STATE_ACTION.ASSIGNED_ROASTED)
                self.sm_roasted.send('empty_bucket_placed')


            # 8. Place Full Roasted Bucket
            elif (self.aw.taskWebDisplayRoastedActive and                                  # only if Task Display Roasted is active
                    self.sm_roasted.current_weight_item is not None and                    # current roasted weight item is established
                    self.sm_roasted.current_state == RoastedWeighingState.ready and        # roasted State Machine is in READY state
                    self.roasted_task_scale == 0 and                                       # no scale yet assigned to the roasted task
                    0 <= self.aw.container2_idx <= len(self.aw.qmc.container_weights) and  # a roasted container is set
                    self.filled_roasted_container_placed(
                        step,
                        self.sm_roasted.current_weight_item.weight_estimate,
                        self.aw.qmc.container_weights[self.aw.container2_idx])):            # filled container of expected weight

                # reserve scale for the roasted task
                if scale_nr == 1:
                    self.roasted_task_scale = scale_nr
                    self.roasted_task_empty_scale_weight = self.scale1_last_stable_weight
                    self.roasted_task_scale_total_weight = stable_weight - self.roasted_task_empty_scale_weight # the reading of the scale with the full roasted bucket placed minus the tare (includes the bucket weight!)
                    self.scale_manager.scale1_connected_signal.connect(self.scale1_connected_slot)
                    self.scale_manager.scale1_disconnected_signal.connect(self.scale1_disconnected_slot)
                    self.scale_manager.reserve_scale1_signal.emit()
                    self.scale_manager.signal_user_scale1_signal.emit(STATE_ACTION.ASSIGNED_ROASTED)
                elif scale_nr == 2:
                    self.roasted_task_scale = scale_nr
                    self.roasted_task_empty_scale_weight = self.scale2_last_stable_weight
                    self.roasted_task_scale_total_weight = stable_weight - self.roasted_task_empty_scale_weight # the reading of the scale with the full roasted bucket placed minus the tare
                    self.scale_manager.scale2_connected_signal.connect(self.scale2_connected_slot)
                    self.scale_manager.scale2_disconnected_signal.connect(self.scale2_disconnected_slot)
                    self.scale_manager.reserve_scale2_signal.emit()
                    self.scale_manager.signal_user_scale2_signal.emit(STATE_ACTION.ASSIGNED_ROASTED)
                self.sm_roasted.send('bucket_placed', int(round(self.roasted_task_scale_total_weight - self.aw.qmc.container_weights[self.aw.container2_idx])))


        # step < 0

        ## green task
        elif (self.sm_green.current_weight_item is not None and self.green_task_scale == scale_nr and
                    self.scale_empty(scale_nr, self.green_task_empty_scale_weight, stable_weight)):

            # weight removed completely, scale empty now

            batchsize = self.sm_green.current_weight_item.weight * 1000 # batch size in g
            weight = ((self.scale1_last_stable_weight if scale_nr == 1 else self.scale2_last_stable_weight)
                - self.green_task_scale_tare_weight             # remove tare weight
                + self.green_task_container1_registered_weight) # add already registered green weight filled in container 1

            if (self.aw.two_bucket_mode and weight < batchsize * 1/3) or (not self.aw.two_bucket_mode and weight < batchsize * 0.5):
                # case 1: bucket was almost empty (less than 1/3, in two-bucket-mode, or less than 50% in one-bucket-mode)
                _log.debug(r'BatchManager: green bucket removed at <50 percent or 1/3')
                self.sm_green.send('bucket_removed')
                # trigger an refresh of the next weight_item, a previous fetch_next_green update might have been blocked while processing
                self.sm_green.current_weight_item.callback('', 0)
            elif self.green_task_container1_registered_weight == 0 and self.aw.two_bucket_mode and batchsize * 1/3 <= weight < batchsize * 2/3:
                # case 2: bucket filled between 1/3 and 2/3 (only in two-bucket-mode)
                # buckets not yet swapped
                # we register the already weighted greens
                self.green_task_container1_registered_weight = weight
                self.task_swapped_step = step
                self.sm_green.send('fill', weight, True) # update widget after registered weight of container 1 has been set
                self.sm_green.send('bucket_swapped')
                self.signal_green_task_scale(STATE_ACTION.SWAP_ENTER)

            elif self.green_task_container1_registered_weight != 0 and abs(weight - self.green_task_container1_registered_weight) < self.empty_scale_tolerance(scale_nr):
                # case 3: second green bucket removed while still empty
                _log.debug('BatchManager: second green bucket removed empty')
                self.sm_green.send('bucket_removed')

            elif (
                    # case 4: bucket completely filled (precision deactivated) => done
                    # precision is deactivated; all weights are accepted (overloading/underloading outside of target range); canceling deactivated
                    self.aw.green_task_precision <= 0 or

                    # case 5: bucket completely filled (precision activated) => done
                    # if weight is in target zone (batchsize - green_task_precision% <= weight <= batchsize + green_task_precision%) the task is completed
                    (self.aw.green_task_precision > 0 and
                    (batchsize - (self.aw.green_task_precision/100 * batchsize)) <= weight <= (batchsize + (self.aw.green_task_precision/100 * batchsize)))):

                self.task_done_step = step
                self.task_done_weight = weight
                self.done_green_task_timer.start(self.WAIT_BEFORE_DONE)
                self.sm_green.send('task_completed', self.task_done_weight)
                self.signal_green_task_scale(STATE_ACTION.OK_ENTER)

            else:
                # task canceled
                _log.debug('BatchManager: green bucket removed while weight %s out of accuracy +-%s. Task canceled.', weight, self.aw.green_task_precision/100 * batchsize)
                _log.debug('BatchManager: not %s <= %s <= %s', weight, batchsize - (self.aw.green_task_precision/100 * batchsize), batchsize + (self.aw.green_task_precision/100 * batchsize))
                self.task_canceled_step = step
                self.cancel_green_task_timer.start(self.WAIT_BEFORE_CANCEL)
                self.sm_green.send('task_canceled')
                self.signal_green_task_scale(STATE_ACTION.CANCEL_ENTER)


        ## roasted task (item set)
        elif (self.scale_empty(scale_nr, self.roasted_task_empty_scale_weight, stable_weight) and
                self.roasted_task_scale == scale_nr):
            # weight removed completely, scale empty now

            if self.sm_roasted.current_weight_item is None and self.sm_roasted.current_state == RoastedWeighingState.prepared:
                # no weight item set yet, but empty bucket removed
                self.sm_roasted.send('reset')
            if self.sm_roasted.current_weight_item is not None:
                batchsize = self.sm_roasted.current_weight_item.weight * 1000 # batch size in g
                weight = ((self.scale1_last_stable_weight if scale_nr == 1 else self.scale2_last_stable_weight)
                    - self.roasted_task_scale_tare_weight)             # remove tare weight

                if self.sm_roasted.current_state == RoastedWeighingState.weighing and abs(self.roasted_task_scale_total_weight + step) < self.ROASTED_BUCKET_REMOVALE_TOLERANCE:
                    # 1. full roasted bucket weighing finished:
                    weight = int(round(self.roasted_task_scale_total_weight - self.aw.qmc.container_weights[self.aw.container2_idx]))
                    self.roasted_task_done_weight = weight
                    self.roasted_task_done_step = step
                    self.sm_roasted.send('task_completed', self.roasted_task_done_weight)
                    self.signal_roasted_task_scale(STATE_ACTION.OK_ENTER)
                    self.done_roasted_task_timer.start(self.WAIT_BEFORE_DONE)
                elif (self.sm_roasted.current_state == RoastedWeighingState.filling and
                        # weight > estimated minimal weight based on
                        weight > self.filled_roasted_bucket_estimated_minimal_weight(self.sm_roasted.current_weight_item.weight_estimate, 0) < weight):
                    # 2. roasted bucket filling finished:
                    self.roasted_task_done_weight = weight
                    self.roasted_task_done_step = step
                    self.sm_roasted.send('task_completed', self.roasted_task_done_weight)
                    self.signal_roasted_task_scale(STATE_ACTION.OK_ENTER)
                    self.done_roasted_task_timer.start(self.WAIT_BEFORE_DONE)
                elif self.sm_roasted.current_state == RoastedWeighingState.filling and weight >= batchsize * 0.5:
                    # 3. roasted bucket filling canceled at a fill weight >= 50% of the batch size, but below the estimated minimal weight
                    _log.debug(r'BatchManager: roasted bucket removed at >50 percent of the batch size, but lower then the estimated minimal weight. Roasted weighing task canceled.')
                    self.roasted_task_canceled_step = step
                    self.cancel_roasted_task_timer.start(self.WAIT_BEFORE_CANCEL)
                    self.sm_roasted.send('task_canceled')
                    self.signal_roasted_task_scale(STATE_ACTION.CANCEL_ENTER)
                elif self.sm_roasted.current_state == RoastedWeighingState.filling and weight < batchsize * 0.5:
                    # 4. roasted bucket filling removed at fill weight < 50% of the batch size
                    _log.debug(r'BatchManager: roasted bucket removed at <50 percent of the batch size')
                    self.sm_roasted.send('bucket_removed')
                    # trigger an refresh of the next weight_item, a previous fetch_next_green update might have been blocked while processing
                    self.sm_roasted.current_weight_item.callback('', 0)
                else:
                    # this does nothing!
                    # cancel on tap while DONE
                    self.sm_roasted.send('cancel')
                    self.sm_roasted.current_weight_item.callback('', 0) # trigger an refresh of the next weight_item, a previous fetch_next_roasted update might have been blocked while processing, update now to the latest

        # independent on the step direction do always update the roasting weight while weighing the roasted container
        if self.roasted_task_done_weight == 0 and self.roasted_task_scale == scale_nr and self.sm_roasted.current_state == RoastedWeighingState.weighing:
            # while roasting scale is in weighing state, we updated the
            self.roasted_task_scale_total_weight = stable_weight - self.roasted_task_empty_scale_weight
            self.sm_roasted.send('update',int(round(self.roasted_task_scale_total_weight - self.aw.qmc.container_weights[self.aw.container2_idx])))

        # update stable weight
        if scale_nr == 1:
            self.scale1_last_stable_weight = stable_weight
        elif scale_nr == 2:
            self.scale2_last_stable_weight = stable_weight

    #-

    def green_task_scale_discconnect(self, last_stable_weight:int) -> None:
        # remember the current scale1 stable weight to be applied as offset after reconnect
        self.green_task_stable_weight_before_connection_loss = last_stable_weight
        self.sm_green.send('connection_lost')

    def green_task_scale_reconnect(self) -> None:
        self.sm_green.send('connection_restored')

    #-

    def roasted_task_scale_discconnect(self, last_stable_weight:int) -> None:
        # remember the current scale1 stable weight to be applied as offset after reconnect
        self.roasted_task_stable_weight_before_connection_loss = last_stable_weight
        self.sm_roasted.send('connection_lost')

    def roasted_task_scale_reconnect(self) -> None:
        self.sm_roasted.send('connection_restored')

    #-

    @pyqtSlot()
    def scale1_connected_slot(self) -> None:
        if self.green_task_scale == 1:
            self.green_task_scale_reconnect()
        elif self.roasted_task_scale == 1:
            self.roasted_task_scale_reconnect()

    @pyqtSlot()
    def scale1_disconnected_slot(self) -> None:
        if self.green_task_scale == 1:
            self.green_task_scale_discconnect(self.scale1_last_stable_weight)
        elif self.roasted_task_scale == 1:
            self.roasted_task_scale_discconnect(self.scale1_last_stable_weight)

    @pyqtSlot()
    def scale2_connected_slot(self) -> None:
        if self.green_task_scale == 2:
            self.green_task_scale_reconnect()
        elif self.roasted_task_scale == 2:
            self.roasted_task_scale_reconnect()

    @pyqtSlot()
    def scale2_disconnected_slot(self) -> None:
        if self.green_task_scale == 2:
            self.green_task_scale_discconnect(self.scale2_last_stable_weight)
        elif self.roasted_task_scale == 2:
            self.roasted_task_scale_discconnect(self.scale2_last_stable_weight)

    def release_green_task_scale(self) -> None:
        self.green_task_container1_registered_weight = 0  # clear container1 weight
        self.task_done_step = 0
        self.task_done_weight = 0
        self.done_green_task_timer.stop()
        self.cancel_green_task_timer.stop()
        if self.green_task_scale == 1:
            self.scale_manager.scale1_connected_signal.disconnect(self.scale1_connected_slot)
            self.scale_manager.scale1_disconnected_signal.disconnect(self.scale1_disconnected_slot)
            self.scale_manager.release_scale1_signal.emit()
            self.scale_manager.signal_user_scale1_signal.emit(STATE_ACTION.RELEASED)
#            self.scale_manager.tare_scale1_signal.emit()
            self.green_task_stable_weight_before_connection_loss = 0 # reset potential offset from scale disconnect
        elif self.green_task_scale == 2:
            self.scale_manager.scale2_connected_signal.disconnect(self.scale2_connected_slot)
            self.scale_manager.scale2_disconnected_signal.disconnect(self.scale2_disconnected_slot)
            self.scale_manager.release_scale2_signal.emit()
            self.scale_manager.signal_user_scale2_signal.emit(STATE_ACTION.RELEASED)
#            self.scale_manager.tare_scale2_signal.emit()
            self.green_task_stable_weight_before_connection_loss = 0 # reset potential offset from scale disconnect
        self.green_task_scale = 0

    def release_roasted_task_scale(self) -> None:
        self.roasted_task_done_weight = 0
        self.roasted_task_done_step = 0
        self.roasted_task_done_weight = 0
        self.done_roasted_task_timer.stop()
        self.cancel_roasted_task_timer.stop()
        if self.roasted_task_scale == 1:
            try:
                # disconnect can fail if not connected
                self.scale_manager.scale1_connected_signal.disconnect(self.scale1_connected_slot)
            except Exception:   # pylint: disable=broad-except
                pass
            try:
                # disconnect can fail if not connected
                self.scale_manager.scale1_disconnected_signal.disconnect(self.scale1_disconnected_slot)
            except Exception:   # pylint: disable=broad-except
                pass
            self.scale_manager.release_scale1_signal.emit()
            self.scale_manager.signal_user_scale1_signal.emit(STATE_ACTION.RELEASED)
        elif self.roasted_task_scale == 2:
            try:
                # disconnect can fail if not connected
                self.scale_manager.scale2_connected_signal.disconnect(self.scale2_connected_slot)
            except Exception:   # pylint: disable=broad-except
                pass
            try:
                # disconnect can fail if not connected
                self.scale_manager.scale2_disconnected_signal.disconnect(self.scale2_disconnected_slot)
            except Exception:   # pylint: disable=broad-except
                pass
            self.scale_manager.release_scale2_signal.emit()
            self.scale_manager.signal_user_scale2_signal.emit(STATE_ACTION.RELEASED)
        self.roasted_task_scale = 0

    @pyqtSlot()
    def cancel_green_task_slot(self) -> None:
        if self.sm_green.current_state in {GreenWeighingState.cancel_weighing1, GreenWeighingState.cancel_weighing2}:
            self.signal_green_task_scale(STATE_ACTION.CANCEL_EXIT)
            self.sm_green.send('cancel')
            self.task_canceled_step = 0
            if self.sm_green.current_weight_item is not None:
                self.sm_green.current_weight_item.callback('', 0) # trigger an refresh of the next weight_item, a previous fetch_next_green update might have been blocked while processing

    @pyqtSlot()
    def tap_cancel_green_task_slot(self) -> None:
        if (self.green_task_scale != 0 and (self.sm_green.current_state in {
                    GreenWeighingState.empty, GreenWeighingState.done_weighing1, GreenWeighingState.done_weighing2 }
                and self.scale_empty(self.green_task_scale, self.green_task_empty_scale_weight, self.last_nonstable_green_weight))):
            self.signal_green_task_scale(STATE_ACTION.INTERRUPTED)
            self.done_green_task_timer.stop()
            self.green_task_empty_scale_weight = 0
            self.last_nonstable_green_weight = 0
            self.task_done_step = 0
            self.task_done_weight = 0
            self.sm_green.send('reset')
            if self.sm_green.current_weight_item is not None:
                self.sm_green.current_weight_item.callback('', 0) # trigger an refresh of the next weight_item, a previous fetch_next_green update might have been blocked while processing



    @pyqtSlot()
    def cancel_roasted_task_slot(self) -> None:
        if self.sm_roasted.current_state == RoastedWeighingState.cancel_filling:
            self.signal_roasted_task_scale(STATE_ACTION.CANCEL_EXIT)
            self.sm_roasted.send('cancel')
            self.task_canceled_step = 0
            if self.sm_roasted.current_weight_item is not None:
                self.sm_roasted.current_weight_item.callback('', 0) # trigger an refresh of the next weight_item, a previous fetch_next_roasted update might have been blocked while processing


    @pyqtSlot()
    def tap_cancel_roasted_task_slot(self) -> None:
        if (self.roasted_task_scale != 0 and self.sm_roasted.current_state in {RoastedWeighingState.done, RoastedWeighingState.done_filling} and
                self.scale_empty(self.roasted_task_scale, self.roasted_task_empty_scale_weight, self.last_nonstable_roasted_weight)):
            self.signal_roasted_task_scale(STATE_ACTION.INTERRUPTED)
            self.done_roasted_task_timer.stop()
            self.roasted_task_empty_scale_weight = 0
            self.last_nonstable_roasted_weight = 0
            self.roasted_task_done_weight = 0
            self.sm_roasted.send('reset')
            if self.sm_roasted.current_weight_item is not None:
                self.sm_roasted.current_weight_item.callback('', 0) # trigger an refresh of the next weight_item, a previous fetch_next_roasted update might have been blocked while processing, update now to the latest


    @pyqtSlot()
    def done_green_task_slot(self) -> None:
        if self.sm_green.current_state in {GreenWeighingState.done_weighing1, GreenWeighingState.done_weighing2}:
            self.signal_green_task_scale(STATE_ACTION.OK_EXIT)
            self.sm_green.send('end', self.task_done_weight)
            self.task_done_step = 0
            self.task_done_weight = 0

    @pyqtSlot()
    def done_roasted_task_slot(self) -> None:
        if self.sm_roasted.current_state in {RoastedWeighingState.done, RoastedWeighingState.done_filling}:
            self.signal_roasted_task_scale(STATE_ACTION.OK_EXIT)
            self.sm_roasted.send('end', self.roasted_task_done_weight)
            self.roasted_task_done_weight = 0

    def signal_green_task_scale(self, action:STATE_ACTION) -> None:
        if self.green_task_scale == 1:
            self.scale_manager.signal_user_scale1_signal.emit(action)
        elif self.green_task_scale == 2:
            self.scale_manager.signal_user_scale2_signal.emit(action)

    def signal_roasted_task_scale(self, action:STATE_ACTION) -> None:
        if self.roasted_task_scale == 1:
            self.scale_manager.signal_user_scale1_signal.emit(action)
        elif self.roasted_task_scale == 2:
            self.scale_manager.signal_user_scale2_signal.emit(action)

    def signal_scale_stable_weight(self, last_weight:int, new_weight:int, last_component:Optional[int] = None) -> None:
        if  self.sm_green.current_weight_item is not None and last_weight != new_weight:
            batchsize = self.sm_green.current_weight_item.weight * 1000 # batch size in g
            previously_done100percent = round(100 * last_weight / batchsize) == 100
            done100percent = round(100 * new_weight / batchsize) == 100
            if done100percent and not previously_done100percent:
                self.signal_green_task_scale(STATE_ACTION.TARGET_ENTER)
            elif last_component is not None and last_component != self.sm_green.component:
                # blend component changed
                self.signal_green_task_scale(STATE_ACTION.COMPONENT_CHANGED)
            elif self.aw.green_task_precision > 0:
                tolerance = self.aw.green_task_precision/100 * batchsize
                previously_in_zone = abs(last_weight - batchsize) <= tolerance
                now_in_zone = abs(new_weight - batchsize) <= tolerance
                if (previously_done100percent or not previously_in_zone) and now_in_zone and not done100percent:
                    self.signal_green_task_scale(STATE_ACTION.ZONE_ENTER)
                elif previously_in_zone and not previously_done100percent and not now_in_zone and not done100percent:
                    self.signal_green_task_scale(STATE_ACTION.ZONE_EXIT)
                elif previously_done100percent and not done100percent and not now_in_zone:
                    self.signal_green_task_scale(STATE_ACTION.TARGET_EXIT)
            elif previously_done100percent and not done100percent:
                self.signal_green_task_scale(STATE_ACTION.TARGET_EXIT)

    def signal_scale_weight(self, last_component:Optional[int]) -> None:
        if last_component is not None and last_component != self.sm_green.component:
            # blend component changed
            self.signal_green_task_scale(STATE_ACTION.COMPONENT_CHANGED)


    @pyqtSlot()
    def scale1_tare_pressed_slot(self) -> None:
        if self.green_task_scale == 1:
            self.sm_green.send('reset')
        elif self.roasted_task_scale == 1:
            self.sm_roasted.send('reset')


    @pyqtSlot(int)
    def scale1_stable_weight_changed_slot(self, stable_weight:int) -> None:
#        _log.debug('PRINT WM.scale1_stable_weight_changed_slot(%s)',stable_weight)
        last_stable_weight = self.scale1_last_stable_weight
        last_component = self.sm_green.component
        self.scale_stable_weight_changed(1, stable_weight + self.green_task_stable_weight_before_connection_loss)
        if self.green_task_scale == 1 and self.sm_green.current_state in {
                    GreenWeighingState.weighing1, GreenWeighingState.weighing2, GreenWeighingState.empty,
                    GreenWeighingState.done_weighing1, GreenWeighingState.done_weighing2 }:
            new_weight = stable_weight - self.green_task_scale_tare_weight + self.green_task_container1_registered_weight + self.green_task_stable_weight_before_connection_loss
            last_weight = last_stable_weight - self.green_task_scale_tare_weight + self.green_task_container1_registered_weight + self.green_task_stable_weight_before_connection_loss
            self.sm_green.send('fill', max(0, new_weight), True)
            # signal state to the user via a scale signal
            self.signal_scale_stable_weight(last_weight, new_weight, last_component)
        elif self.roasted_task_scale == 1 and self.sm_roasted.current_state in {
                    RoastedWeighingState.filling, RoastedWeighingState.done_filling}:
            new_weight = stable_weight - self.roasted_task_scale_tare_weight +  self.roasted_task_stable_weight_before_connection_loss
            last_weight = last_stable_weight - self.roasted_task_scale_tare_weight + self.roasted_task_stable_weight_before_connection_loss
            self.sm_roasted.send('fill', max(0, new_weight), True)


    @pyqtSlot(int)
    def scale1_weight_changed_slot(self, weight:int) -> None:
#        _log.debug('PRINT WM.scale1_weight_changed_slot(%s)',weight)
        if self.green_task_scale == 1:
            self.last_nonstable_green_weight = weight
            last_component = self.sm_green.component
            new_weight = weight - self.green_task_scale_tare_weight + self.green_task_container1_registered_weight + self.green_task_stable_weight_before_connection_loss
            self.sm_green.send('fill', max(0, new_weight), weight>self.scale1_last_stable_weight) # only update display on increasing weights or if larger than the last stable weight
            self.signal_scale_weight(last_component)
            if (self.sm_green.current_state in { GreenWeighingState.empty, GreenWeighingState.done_weighing1, GreenWeighingState.done_weighing2 } and
                    weight > self.green_task_empty_scale_weight + WeightManager.TAP_CANCEL_THRESHOLD):
                self.tap_cancel_green_task_timer.start(WeightManager.TAP_CANCEL_PERIOD)
        elif self.roasted_task_scale == 1:
            self.last_nonstable_roasted_weight = weight
            if (self.sm_roasted.current_state == RoastedWeighingState.done and
                 weight > self.roasted_task_empty_scale_weight + WeightManager.TAP_CANCEL_THRESHOLD):
                self.tap_cancel_roasted_task_timer.start(WeightManager.TAP_CANCEL_PERIOD)
            elif self.sm_roasted.current_state == RoastedWeighingState.filling:
                new_weight = weight - self.roasted_task_scale_tare_weight + self.roasted_task_stable_weight_before_connection_loss
                self.sm_roasted.send('fill', max(0, new_weight), weight>self.scale1_last_stable_weight) # only update display on increasing weights or if larger than the last stable weight
            elif (self.sm_roasted.current_state == RoastedWeighingState.done_filling and
                        weight > self.roasted_task_empty_scale_weight + WeightManager.TAP_CANCEL_THRESHOLD):
                self.tap_cancel_roasted_task_timer.start(WeightManager.TAP_CANCEL_PERIOD)




    @pyqtSlot()
    def scale2_tare_pressed_slot(self) -> None:
        if self.green_task_scale == 2:
            self.sm_green.send('reset')
        elif self.roasted_task_scale == 2:
            self.sm_roasted.send('reset')


    @pyqtSlot(int)
    def scale2_stable_weight_changed_slot(self, stable_weight:int) -> None:
#        _log.debug('PRINT WM.scale2_stable_weight_changed_slot(%s)',stable_weight)
        last_stable_weight = self.scale1_last_stable_weight
        self.scale_stable_weight_changed(2, stable_weight + self.green_task_stable_weight_before_connection_loss)
        if self.green_task_scale == 2 and self.sm_green.current_state in { GreenWeighingState.done_weighing1, GreenWeighingState.done_weighing2 }:
            new_weight = stable_weight - self.green_task_scale_tare_weight + self.green_task_container1_registered_weight + self.green_task_stable_weight_before_connection_loss
            self.sm_green.send('fill', max(0, new_weight), True)
            # signal state to the user via a scale signal
            last_weight = last_stable_weight - self.green_task_scale_tare_weight + self.green_task_container1_registered_weight + self.green_task_stable_weight_before_connection_loss
            self.signal_scale_stable_weight(last_weight, new_weight)
        elif self.roasted_task_scale == 2 and self.sm_roasted.current_state in {
                    RoastedWeighingState.filling, RoastedWeighingState.done_filling}:
            new_weight = stable_weight - self.roasted_task_scale_tare_weight +  self.roasted_task_stable_weight_before_connection_loss
            last_weight = last_stable_weight - self.roasted_task_scale_tare_weight + self.roasted_task_stable_weight_before_connection_loss
            self.sm_roasted.send('fill', max(0, new_weight), True)

    @pyqtSlot(int)
    def scale2_weight_changed_slot(self, weight:int) -> None:
#        _log.debug('WM.scale2_weight_changed_slot(%s)',weight)
        if self.green_task_scale == 2:
            self.last_nonstable_green_weight = weight
            last_component = self.sm_green.component
            new_weight = weight - self.green_task_scale_tare_weight + self.green_task_container1_registered_weight + self.green_task_stable_weight_before_connection_loss
            self.sm_green.send('fill', max(0, new_weight), weight>self.scale2_last_stable_weight) # only update on increasing weights or if larger than thhe last stable weight
            self.signal_scale_weight(last_component)
            if (self.sm_green.current_state in { GreenWeighingState.empty, GreenWeighingState.done_weighing1, GreenWeighingState.done_weighing2 } and
                 weight > self.green_task_empty_scale_weight + WeightManager.TAP_CANCEL_THRESHOLD):
                self.tap_cancel_green_task_timer.start(WeightManager.TAP_CANCEL_PERIOD)
        elif self.roasted_task_scale == 2:
            self.last_nonstable_roasted_weight = weight
            if (self.sm_roasted.current_state == RoastedWeighingState.done and
                 weight > self.roasted_task_empty_scale_weight + WeightManager.TAP_CANCEL_THRESHOLD):
                self.tap_cancel_roasted_task_timer.start(WeightManager.TAP_CANCEL_PERIOD)
            elif self.sm_roasted.current_state == RoastedWeighingState.filling:
                new_weight = weight - self.roasted_task_scale_tare_weight + self.roasted_task_stable_weight_before_connection_loss
                self.sm_roasted.send('fill', max(0, new_weight), weight>self.scale2_last_stable_weight) # only update display on increasing weights or if larger than the last stable weight
            elif (self.sm_roasted.current_state == RoastedWeighingState.done_filling and
                        weight > self.roasted_task_empty_scale_weight + WeightManager.TAP_CANCEL_THRESHOLD):
                self.tap_cancel_roasted_task_timer.start(WeightManager.TAP_CANCEL_PERIOD)

    def start(self) -> None:
        self.scale_manager.available_signal.connect(self.scales_available)
        self.scale_manager.unavailable_signal.connect(self.scales_unavailable)
        self.scale_manager.scale1_stable_weight_changed_signal.connect(self.scale1_stable_weight_changed_slot)
        self.scale_manager.scale1_weight_changed_signal.connect(self.scale1_weight_changed_slot)
        self.scale_manager.scale1_tare_pressed_signal.connect(self.scale1_tare_pressed_slot)
        self.scale_manager.scale2_stable_weight_changed_signal.connect(self.scale2_stable_weight_changed_slot)
        self.scale_manager.scale2_weight_changed_signal.connect(self.scale2_weight_changed_slot)
        self.scale_manager.scale2_tare_pressed_signal.connect(self.scale2_tare_pressed_slot)
        self.scale_manager.connect_all_signal.emit(self.aw.qmc.device_logging)
        _log.debug('BatchManager started')

    def stop(self) -> None:
        self.reset()
        self.sm_green.send('reset')
        self.sm_roasted.send('reset')
#        self.scale_manager.disconnect_all_signal.emit() # closing via signal does not work on app quite for unknown reasons thus we make a direct call
        self.scale_manager.disconnect_all_slot()
        self.scale_manager.available_signal.disconnect(self.scales_available)
        self.scale_manager.unavailable_signal.disconnect(self.scales_unavailable)
        self.scale_manager.scale1_stable_weight_changed_signal.disconnect(self.scale1_stable_weight_changed_slot)
        self.scale_manager.scale1_weight_changed_signal.disconnect(self.scale1_weight_changed_slot)
        self.scale_manager.scale1_tare_pressed_signal.disconnect(self.scale1_tare_pressed_slot)
        self.scale_manager.scale2_stable_weight_changed_signal.disconnect(self.scale2_stable_weight_changed_slot)
        self.scale_manager.scale2_weight_changed_signal.disconnect(self.scale2_weight_changed_slot)
        self.scale_manager.scale2_tare_pressed_signal.disconnect(self.scale2_tare_pressed_slot)
        _log.debug('BatchManager stopped')
