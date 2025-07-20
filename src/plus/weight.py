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
    from PyQt6.QtCore import QObject, QTimer, QSemaphore, pyqtSlot # @Reimport @UnresolvedImport @UnusedImport
except ImportError:
    from PyQt5.QtCore import QObject, QTimer, QSemaphore, pyqtSlot # type: ignore[import-not-found,no-redef]  # @Reimport @UnresolvedImport @UnusedImport

from dataclasses import dataclass
from enum import IntEnum, unique
from statemachine import StateMachine, State
from typing import Optional, List, Tuple, Callable, Final, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # noqa: F401 # pylint: disable=unused-import

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
        'cancel_timer_timeout', 'done_timer_timeout'
        ]

    def __init__(self) -> None:
#        self.active:bool = True
        self.cancel_timer_timeout = 0 # timeout of the cancel state in seconds; if 0, timer is disabled
        self.done_timer_timeout = 0 # timeout of the cancel state in seconds; if 0, timer is disabled

    def clear_green(self) -> None: # pylint: disable=no-self-use
        ...

    def clear_roasted(self) -> None: # pylint: disable=no-self-use
        ...

    def show_item(self, item:WeightItem, state:PROCESS_STATE = PROCESS_STATE.DISCONNECTED, component:int = 0, final_weight:Optional[int] = None) -> None: # pylint: disable=unused-argument,no-self-use
        ...

    # set the displays CANCEL timer timeout in seconds
    def set_cancel_timer_timeout(self, timeout:int) -> None:
        self.cancel_timer_timeout = timeout

    # set the displays DONE timer timeout in seconds
    def set_done_timer_timeout(self, timeout:int) -> None:
        self.done_timer_timeout = timeout

    # show progress of the green weighing process
    def show_progress(self, state:PROCESS_STATE, component:int, bucket:int, current_weight:int) -> None: # pylint: disable=unused-argument,no-self-use
        del state
        del component
        del bucket
        del current_weight

    # show progress of the roasted weighing process
    def show_result(self, state:PROCESS_STATE, current_weight:int) -> None: # pylint: disable=unused-argument,no-self-use
        del state
        del current_weight

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
#    from statemachine import Event
#    @staticmethod
#    def on_transition(event_data, event: Event) -> None: # type:ignore
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
            self.current_weight_item.callback(str(self.current_weight_item.uuid), weight) # register weight in weight_item as prepared


#-
    # render current item and state on all active displays
    # if progress is True, the current weighing progress is displayed
    # final_weight in g if given
    def update_displays(self, progress:bool=False, final_weight:Optional[int] = None) -> None:
        for display in self.displays:
            if self.current_weight_item is not None:
                if progress:
                    display.show_progress(self.process_state, self.component, self.bucket, self.current_weight)
                else:
                    display.show_item(self.current_weight_item, self.process_state, component=self.component, final_weight=final_weight)
            else:
                display.clear_green()



class RoastedWeighingState(StateMachine):

    idle = State(initial=True)  # display_state = 0
    scale = State()             # scale available, display_state = 1
    item = State()              # current_item available, display_state = 0
    ready = State()             # display_state = 1
    weighing = State()          # weighing
    done = State()              # weighing done

    reset = (
        idle.to(idle)
        | scale.to(scale)
        | item.to(item)
        | ready.to(ready)
        | weighing.to(ready)
        | done.to(ready)
    )

    current_item = (
        idle.to(item)
        | item.to(item)    # needed for updating displays to new current_item!
        | ready.to(ready, internal=True)  # needed for updating displays to new current_item, no entry/exist actions triggered!
        | scale.to(ready)
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

    update = (
        weighing.to(weighing)
    )

    task_completed = (
        weighing.to(done)
    )

    end = (
        done.to(ready)
    )

    def __init__(self, displays:List[Display], release_scale:Callable[[],None]) -> None:

        # list of displays control, incl. the display of the selected scale if any
        self.displays: List[Display] = displays
        # release scale after weighing is done
        self.release_scale = release_scale

        # holds the WeightItem currently processed, if any
        self.current_weight_item:Optional[RoastedWeightItem] = None
        self.process_state:PROCESS_STATE = PROCESS_STATE.DISCONNECTED
        self.current_weight:int = 0 # in g # the current total weight of the roasted coffee (without the weight of the bucket)

        super().__init__(allow_event_without_transition=True) # no errors for events which do not lead to transitions

    def on_enter_ready(self) -> None:
        self.release_scale()

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

    def after_reset(self) -> None:
        self.release_scale()
        if self.process_state != PROCESS_STATE.DISCONNECTED:
            self.process_state = PROCESS_STATE.CONNECTED
        self.update_displays()


    # weight is yield in g
    def after_bucket_placed(self, weight:int) -> None:
        self.current_weight = weight
        self.process_state = PROCESS_STATE.WEIGHING
        self.update_displays(result=True)

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


# TESTING
#    @staticmethod
#    from statemachine import Event
#    def on_transition(event_data, event: Event) -> None: # type:ignore
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
            self.current_weight_item.callback(str(self.current_weight_item.uuid), weight) # register weight in weight_item as prepared



    # render current item and state on all active displays
    # if result is True, the current weighing result is displayed
    # final_weight in g if given
    def update_displays(self, result:bool=False, final_weight:Optional[int] = None) -> None:
        for display in self.displays:
            if self.current_weight_item is not None:
                if result:
                    display.show_result(self.process_state, self.current_weight)
                else:
                    display.show_item(self.current_weight_item, self.process_state, final_weight=final_weight)
            else:
                display.clear_roasted()



class WeightManager(QObject): # pyright:ignore[reportGeneralTypeIssues] # pyrefly: ignore [invalid-inheritance] # error: Argument to class must be a base class

    __slots__ = [ 'displays', 'scale_manager', 'next_green_item',  'next_roasted_item',
                    'greenItemSemaphore', 'roastedItemSemaphore', 'green_sm' ]

    MIN_STABLE_WIGHT_CHANGE:Final[int] = 2                  # minimum stable weight changes being recognized in g
    MIN_CUSTOM_EMPTY_BUCKET_WEIGHT:Final[int] = 15          # minimum custom empty bucket weight recognized in g
    MIN_EMPTY_BUCKET_WEIGHT:Final[int] = 300                # minimum empty bucket weight recognized in g
    MAX_EMPTY_BUCKET_WEIGHT:Final[int] = 4000               # maximum empty bucket weight recognized in g
    MIN_EMPTY_BUCKET_WEIGHT_BATCH_PERECENT:Final[int] = 5   # minimum empty bucket weight percentage of batch size in %
    MAX_EMPTY_BUCKET_WEIGHT_BATCH_PERECENT:Final[int] = 25  # maximum empty bucket weight percentage of batch size in %
    MIN_EMPTY_BUCKET_RECOGNITION_TOLERANCE:Final[int] = 10  # +- minimal tolerance to recognize empty green bucket in g
    EMPTY_BUCKET_RECOGNITION_TOLERANCE_PERCENT:Final[float] = 1     # +- tolerance to recognize empty green bucket in % of bucket weight
    #-
    EMPTY_SCALE_RECOGNITION_TOLERANCE_TIGHT:Final[int] = 25 # +- tight tolerance to recognize empty scale in g for scale.readability() < 1g
    EMPTY_SCALE_RECOGNITION_TOLERANCE_LOOSE:Final[int] = 40 # +- loose tolerance to recognize empty scale in g for scale.readability() >= 1g
    CANCELED_STEP_RECOGNITION_TOLERANCE:Final[int] = 15     # +- tolerance to recognize a previous 'task_cancel' step to restart via 'bucket_put_back' in g
    DONE_STEP_RECOGNITION_TOLERANCE:Final[int] = 15         # +- tolerance to recognize a previous 'task_completed' step to restart via 'bucket_put_back_done' in g
    SWAP_STEP_RECOGNITION_TOLERANCE:Final[int] = 15         # +- tolerance to recognize a previous 'bucket_swapped' step to restart via 'bucket_put_back_swapped' in g
    ROASTED_BUCKET_TOLERANCE:Final[int] = 15                # +- tolerance to recognize filled roasted container in % w.r.t. the estimated weight
                                                            # (weight loss defaults to 15% if no template is given)
    ROASTED_BUCKET_REMOVALE_TOLERANCE:Final[int] = 10       # +- tolerance to recognize roasted bucket removal
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
        self.green_task_scale_tare_weight:int = 0             # last stable weight after placing the current empty bucket
        self.green_task_container1_registered_weight:int = 0  # holds the green fill weight of the first container after container swap
        self.green_task_stable_weight_before_connection_loss = 0 # holds the green weight before the connection to the assigned scale got lost
        self.task_canceled_step:int = 0                       # remember step (in g) that did lead to "task_cancel" allowing for a restart via "bucket_put_back" on recognizing the inverse step
        self.task_done_step:int = 0                           # remember step (in g) that did lead to "task_completed" allowing for a restart via "bucket_put_back_done" on recognizing the
        self.task_swapped_step:int = 0                        # remember step (in g) that did lead to "task_swapped" allowing for a restart via "bucket_put_back_swapped" on recognizing the
        self.task_done_weight:int = 0                         # remember weight (in g) that did lead to "task_completed" allowing to complete this task
        #-
        self.roasted_task_empty_scale_weight:int = 0          # weight of the empty scale (tare weight)
        self.roasted_task_scale_total_weight:int = 0
        self.roasted_task_done_weight:int =0                  # remember weight (in g) that did lead to roasted task_completed allowing to complete this task

        # Timers
        self.cancel_green_task_timer = QTimer()
        self.cancel_green_task_timer.setSingleShot(True)
        self.cancel_green_task_timer.timeout.connect(self.cancel_green_task_slot)

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
    @pyqtSlot()
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
        self.sm_green.send('available')
        if self.roasted_container_weight() is not None:
            # if no roasting container is set, the roasting weihing process is disabled
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
        estimated_roasted_weight_g = estimated_roasted_weight*1000
        return abs(estimated_roasted_weight_g - (filled_container_weight - roasted_bucket_weight)) < (estimated_roasted_weight_g * WeightManager.ROASTED_BUCKET_TOLERANCE/100)

    # step in g
    # batchsize in kg
    #--
    # empty bucket weight needs in any case to be larger than WeightManager.MIN_CUSTOM_EMPTY_BUCKET_WEIGHT and smaller than roasted total weight of filled roasted bucket
    # recognition tolerance is at least +-MIN_EMPTY_BUCKET_RECOGNITION_TOLERANCE and otherwise +-EMPTY_BUCKET_RECOGNITION_TOLERANCE percent of the
    #   selected bucket or (-EMPTY_BUCKET_RECOGNITION_TOLERANCE percent of the min_bucket_weight and EMPTY_BUCKET_RECOGNITION_TOLERANCE of the max_bucket weight)
    # the bucket weight has to be
    #   +-WeightManager.MIN_EMPTY_BUCKET_RECOGNITION_TOLERANCE of the set green bucket weight if available
    #   +-WeightManager.MIN_EMPTY_BUCKET_RECOGNITION_TOLERANCE of the defined bucket weights if available (an no green bucket is set)
    #   between WeightManager.MIN_EMPTY_BUCKET_WEIGHT_BATCH_PERECENT and WeightManager.MAX_EMPTY_BUCKET_WEIGHT_BATCH_PERECENT of the batchsize
    #     but not smaller than WeightManager.MIN_EMPTY_BUCKET_WEIGHT and WeightManager.MAX_EMPTY_BUCKET_WEIGHT
    def empty_bucket_placed(self, step:int, batchsize:float) -> bool:
        # the empty bucket weight must be lighter than the total weight of a filled roasted bucket
        # to avoid overlapping recognition
        # NOTE: a very light roasting task can block the recognition of the placement of empty green buckets
        #       Thus, this is rather unlikely as the roasted task contains already the weight of a bucket
        if (self.sm_roasted.current_weight_item is not None and                        # there is a current roasting task
                self.roasted_task_scale == 0 and                                       # there is no scale yet assigned to the roasted task
                0 <= self.aw.container2_idx <= len(self.aw.qmc.container_weights) and  # there is a roasted container weight specified
                step >= self.filled_roasted_bucket_estimated_minimal_weight(self.sm_roasted.current_weight_item.weight, self.aw.qmc.container_weights[self.aw.container2_idx])):
            return False

        # bucket smaller than the total weight of the filled roasted bucket

        if step > WeightManager.MIN_CUSTOM_EMPTY_BUCKET_WEIGHT:
            # larger than absolute minimum bucket weight

            if 0 <= self.aw.container1_idx < len(self.aw.qmc.container_weights):
                # if green bucket is set, step should be about the weight of the user defined green bucket
                selected_container_weight = self.aw.qmc.container_weights[self.aw.container1_idx]
                return abs(selected_container_weight - step) <= max(float(WeightManager.MIN_EMPTY_BUCKET_RECOGNITION_TOLERANCE),
                    selected_container_weight*WeightManager.EMPTY_BUCKET_RECOGNITION_TOLERANCE_PERCENT/100)

            # default min/max limits between 5% and 25% of batchsize in g, with absolute min. of 300g and max. of 4000g
            min_bucket_weight:float = max(float(WeightManager.MIN_EMPTY_BUCKET_WEIGHT), batchsize*1000*WeightManager.MIN_EMPTY_BUCKET_WEIGHT_BATCH_PERECENT/100)
            max_bucket_weight:float = min(float(WeightManager.MAX_EMPTY_BUCKET_WEIGHT), batchsize*1000*WeightManager.MAX_EMPTY_BUCKET_WEIGHT_BATCH_PERECENT/100)

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
                self.cancel_green_task_timer.stop()
                self.task_canceled_step = 0
                self.sm_green.send('bucket_put_back')

            # 2. Cancel Green Done
            elif (self.green_task_scale == scale_nr and
                    self.sm_green.current_state in {GreenWeighingState.done_weighing1, GreenWeighingState.done_weighing2} and
                    self.task_done_step < 0 and abs(step + self.task_done_step) < self.DONE_STEP_RECOGNITION_TOLERANCE):
                # Cancel of the done operation; we restart at the done state
                self.done_green_task_timer.stop()
                self.task_done_step = 0
                self.task_done_weight = 0
                self.sm_green.send('bucket_put_back_done')

            # 3. Cancel Container Swap (from EMPTY TO WEIHING1; bucket_put_back_swapped
            elif (self.green_task_scale == scale_nr and
                    self.sm_green.current_state == GreenWeighingState.empty and
                    self.task_swapped_step < 0 and abs(step + self.task_swapped_step) < self.SWAP_STEP_RECOGNITION_TOLERANCE):
                # Cancel of the done operation; we restart at the done state
                self.task_swapped_step = 0
                self.green_task_container1_registered_weight = 0
                self.sm_green.send('bucket_put_back_swapped')

            # 4. Place Empty Green Bucket
            elif (self.sm_green.current_weight_item is not None and                            # current green weight item is established
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

                if self.sm_green.current_state in {GreenWeighingState.cancel_weighing1,GreenWeighingState.cancel_weighing2}:
                    # if task got canceled and cancel timer is still running we stop it here
                    self.cancel_green_task_timer.stop()
                    self.task_canceled_step = 0
                    self.sm_green.send('cancel', block_scale_release=True)
                elif self.sm_green.current_state in {GreenWeighingState.done_weighing1,GreenWeighingState.done_weighing2}:
                    # if task got completed and done timer is still running we stop it here
                    self.done_green_task_timer.stop()
                    self.sm_green.send('end', self.task_done_weight, block_scale_release=True)
                    self.task_done_step = 0
                    self.task_done_weight = 0

                # reserve scale for the green task
                if scale_nr == 1:
                    self.green_task_scale = scale_nr
                    self.green_task_scale_tare_weight = stable_weight # the reading of the scale with the empty bucket placed
                    self.green_task_empty_scale_weight = self.scale1_last_stable_weight
                    self.scale_manager.scale1_connected_signal.connect(self.scale1_connected_slot)
                    self.scale_manager.scale1_disconnected_signal.connect(self.scale1_disconnected_slot)
                    self.scale_manager.reserve_scale1_signal.emit()
                    # make state transition (which then triggers the display update)
                    self.sm_green.send('bucket_placed')
                elif scale_nr == 2:
                    self.green_task_scale = scale_nr
                    self.green_task_scale_tare_weight = stable_weight # the reading of the scale with the empty bucket placed
                    self.green_task_empty_scale_weight = self.scale2_last_stable_weight
                    self.scale_manager.scale2_connected_signal.connect(self.scale2_connected_slot)
                    self.scale_manager.scale2_disconnected_signal.connect(self.scale2_disconnected_slot)
                    self.scale_manager.reserve_scale2_signal.emit()
                    # make state transition (which then triggers the display update)
                    self.sm_green.send('bucket_placed')

            # 5. Place Full Roasted Bucket
            elif (self.sm_roasted.current_weight_item is not None and                      # current roasted weight item is established
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
                    self.roasted_task_scale_total_weight = stable_weight - self.roasted_task_empty_scale_weight # the reading of the scale with the full roasted bucket placed minus the tare
                    self.scale_manager.scale1_connected_signal.connect(self.scale1_connected_slot)
                    self.scale_manager.scale1_disconnected_signal.connect(self.scale1_disconnected_slot)
                    self.scale_manager.reserve_scale1_signal.emit()
                elif scale_nr == 2:
                    self.roasted_task_scale = scale_nr
                    self.roasted_task_empty_scale_weight = self.scale2_last_stable_weight
                    self.roasted_task_scale_total_weight = stable_weight - self.roasted_task_empty_scale_weight # the reading of the scale with the full roasted bucket placed minus the tare
                    self.scale_manager.scale2_connected_signal.connect(self.scale2_connected_slot)
                    self.scale_manager.scale2_disconnected_signal.connect(self.scale2_disconnected_slot)
                    self.scale_manager.reserve_scale2_signal.emit()
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
                self.sm_green.send('bucket_removed')

            elif self.green_task_container1_registered_weight == 0 and self.aw.two_bucket_mode and batchsize * 1/3 <= weight < batchsize * 2/3:
                # case 2: bucket filled between 1/3 and 2/3 (only in two-bucket-mode)
                # buckets not yet swapped
                # we register the already weighted greens
                self.green_task_container1_registered_weight = weight
                self.task_swapped_step = step
                self.sm_green.send('fill', weight, True) # update widget after registered weight of container 1 has been set
                self.sm_green.send('bucket_swapped')

            elif self.green_task_container1_registered_weight != 0 and abs(weight - self.green_task_container1_registered_weight) < self.empty_scale_tolerance(scale_nr):
                self.sm_green.send('bucket_removed')

            elif self.aw.green_task_precision == 0: # precision is deactivated; all weights are accepted (overloading/underloading outside of target range); canceling deactivated
                # case 3: bucket completely filled (precision deactivated) => done
                self.task_done_step = step
                self.task_done_weight = weight
                self.done_green_task_timer.start(self.WAIT_BEFORE_DONE)
                self.sm_green.send('task_completed', self.task_done_weight)

            elif (self.aw.green_task_precision > 0 and
                    (batchsize - (self.aw.green_task_precision/100 * batchsize)) <= weight <= (batchsize + (self.aw.green_task_precision/100 * batchsize))):
                # if weight is in target zone (batchsize - green_task_precision% <= weight <= batchsize + green_task_precision%) the task is completed
                # case 4: bucket completely filled (precision activated) => done
                self.task_done_step = step
                self.task_done_weight = weight
                self.done_green_task_timer.start(self.WAIT_BEFORE_DONE)
                self.sm_green.send('task_completed', self.task_done_weight)

            else:
                # task canceled
                self.task_canceled_step = step
                self.cancel_green_task_timer.start(self.WAIT_BEFORE_CANCEL)
                self.sm_green.send('task_canceled')


        ## roasted task
        elif (self.sm_roasted.current_weight_item is not None and self.scale_empty(scale_nr, self.roasted_task_empty_scale_weight, stable_weight) and
                self.roasted_task_scale == scale_nr):
            # weight removed completely, scale empty now

            if abs(self.roasted_task_scale_total_weight + step) < self.ROASTED_BUCKET_REMOVALE_TOLERANCE:
                weight = int(round(self.roasted_task_scale_total_weight - self.aw.qmc.container_weights[self.aw.container2_idx]
                            - self.roasted_task_empty_scale_weight))             # remove tare weight
                self.roasted_task_done_weight = weight
                self.sm_roasted.send('task_completed', self.roasted_task_done_weight)
                self.done_roasted_task_timer.start(self.WAIT_BEFORE_DONE)
            else:
                # this does nothing!
                # cancel on tap while DONE
                self.sm_roasted.send('cancel')

        # independent on the step direction do always update the roasting weight while weighing the roasted container
        if self.roasted_task_scale == scale_nr and self.sm_roasted.current_state == RoastedWeighingState.weighing:
            # while roasting scale is in weighing state, we updated the
            self.roasted_task_scale_total_weight = stable_weight - self.roasted_task_empty_scale_weight
            self.sm_roasted.send('update',int(round(self.roasted_task_scale_total_weight - self.aw.qmc.container_weights[self.aw.container2_idx])))


        # if stable_weight gets negative, limit tare to zero?

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

    @pyqtSlot()
    def scale1_connected_slot(self) -> None:
        if self.green_task_scale == 1:
            self.green_task_scale_reconnect()

    @pyqtSlot()
    def scale1_disconnected_slot(self) -> None:
        if self.green_task_scale == 1:
            self.green_task_scale_discconnect(self.scale1_last_stable_weight)

    @pyqtSlot()
    def scale2_connected_slot(self) -> None:
        if self.green_task_scale == 2:
            self.green_task_scale_reconnect()

    @pyqtSlot()
    def scale2_disconnected_slot(self) -> None:
        if self.green_task_scale == 2:
            self.green_task_scale_discconnect(self.scale2_last_stable_weight)

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
#            self.scale_manager.tare_scale1_signal.emit()
            self.green_task_stable_weight_before_connection_loss = 0 # reset potential offset from scale disconnect
        elif self.green_task_scale == 2:
            self.scale_manager.scale2_connected_signal.disconnect(self.scale2_connected_slot)
            self.scale_manager.scale2_disconnected_signal.disconnect(self.scale2_disconnected_slot)
            self.scale_manager.release_scale2_signal.emit()
#            self.scale_manager.tare_scale2_signal.emit()
            self.green_task_stable_weight_before_connection_loss = 0 # reset potential offset from scale disconnect
        self.green_task_scale = 0

    def release_roasted_task_scale(self) -> None:
        self.roasted_task_done_weight = 0
        if self.roasted_task_scale == 1:
            self.scale_manager.scale1_connected_signal.disconnect(self.scale1_connected_slot)
            self.scale_manager.scale1_disconnected_signal.disconnect(self.scale1_disconnected_slot)
            self.scale_manager.release_scale1_signal.emit()
#            self.scale_manager.tare_scale1_signal.emit()
        elif self.roasted_task_scale == 2:
            self.scale_manager.scale2_connected_signal.disconnect(self.scale2_connected_slot)
            self.scale_manager.scale2_disconnected_signal.disconnect(self.scale2_disconnected_slot)
            self.scale_manager.release_scale2_signal.emit()
#            self.scale_manager.tare_scale2_signal.emit()
        self.roasted_task_scale = 0

    @pyqtSlot()
    def cancel_green_task_slot(self) -> None:
        if self.sm_green.current_state in {GreenWeighingState.cancel_weighing1, GreenWeighingState.cancel_weighing2}:
            self.sm_green.send('cancel')
            self.task_canceled_step = 0

    @pyqtSlot()
    def tap_cancel_green_task_slot(self) -> None:
        if (self.green_task_scale != 0 and (self.sm_green.current_state in {
                    GreenWeighingState.empty, GreenWeighingState.done_weighing1, GreenWeighingState.done_weighing2 }
                and self.scale_empty(self.green_task_scale, self.green_task_empty_scale_weight, self.last_nonstable_green_weight))):
            self.done_green_task_timer.stop()
            self.green_task_empty_scale_weight = 0
            self.last_nonstable_green_weight = 0
            self.task_done_step = 0
            self.task_done_weight = 0
            self.sm_green.send('reset')

    @pyqtSlot()
    def tap_cancel_roasted_task_slot(self) -> None:
        if (self.roasted_task_scale != 0 and self.sm_roasted.current_state == RoastedWeighingState.done and
                self.scale_empty(self.roasted_task_scale, self.roasted_task_empty_scale_weight, self.last_nonstable_roasted_weight)):
            self.done_roasted_task_timer.stop()
            self.roasted_task_empty_scale_weight = 0
            self.last_nonstable_roasted_weight = 0
            self.roasted_task_done_weight = 0
            self.sm_roasted.send('reset')

    @pyqtSlot()
    def done_green_task_slot(self) -> None:
        if self.sm_green.current_state in {GreenWeighingState.done_weighing1, GreenWeighingState.done_weighing2}:
            self.sm_green.send('end', self.task_done_weight)
            self.task_done_step = 0
            self.task_done_weight = 0

    @pyqtSlot()
    def done_roasted_task_slot(self) -> None:
        if self.sm_roasted.current_state == RoastedWeighingState.done:
            self.sm_roasted.send('end', self.roasted_task_done_weight)
            self.roasted_task_done_weight = 0

    @pyqtSlot(int)
    def scale1_stable_weight_changed_slot(self, stable_weight:int) -> None:
#        _log.debug('PRINT WM.scale1_stable_weight_changed_slot(%s)',stable_weight)
        self.scale_stable_weight_changed(1, stable_weight + self.green_task_stable_weight_before_connection_loss)
        if self.green_task_scale == 1:
            new_weight = stable_weight - self.green_task_scale_tare_weight + self.green_task_container1_registered_weight + self.green_task_stable_weight_before_connection_loss
            self.sm_green.send('fill', max(0, new_weight), True)

    @pyqtSlot(int)
    def scale1_weight_changed_slot(self, weight:int) -> None:
#        _log.debug('PRINT WM.scale1_weight_changed_slot(%s)',weight)
        if self.green_task_scale == 1:
            self.last_nonstable_green_weight = weight
            new_weight = weight - self.green_task_scale_tare_weight + self.green_task_container1_registered_weight + self.green_task_stable_weight_before_connection_loss
            self.sm_green.send('fill', max(0, new_weight), weight>self.scale1_last_stable_weight) # only update on increasing weights or if larger than thhe last stable weight
            if (self.sm_green.current_state in { GreenWeighingState.empty, GreenWeighingState.done_weighing1, GreenWeighingState.done_weighing2 } and
                 weight > self.green_task_empty_scale_weight + WeightManager.TAP_CANCEL_THRESHOLD):
                self.tap_cancel_green_task_timer.start(WeightManager.TAP_CANCEL_PERIOD)
        elif self.roasted_task_scale == 1:
            self.last_nonstable_roasted_weight = weight
            if (self.sm_roasted.current_state == RoastedWeighingState.done and
                 weight > self.roasted_task_empty_scale_weight + WeightManager.TAP_CANCEL_THRESHOLD):
                self.tap_cancel_roasted_task_timer.start(WeightManager.TAP_CANCEL_PERIOD)


    @pyqtSlot(int)
    def scale2_stable_weight_changed_slot(self, stable_weight:int) -> None:
#        _log.debug('PRINT WM.scale2_stable_weight_changed_slot(%s)',stable_weight)
        self.scale_stable_weight_changed(2, stable_weight + self.green_task_stable_weight_before_connection_loss)
        if self.green_task_scale == 2:
            new_weight = stable_weight - self.green_task_scale_tare_weight + self.green_task_container1_registered_weight + self.green_task_stable_weight_before_connection_loss
            self.sm_green.send('fill', max(0, new_weight), True)

    @pyqtSlot(int)
    def scale2_weight_changed_slot(self, weight:int) -> None:
#        _log.debug('WM.scale2_weight_changed_slot(%s)',weight)
        if self.green_task_scale == 2:
            self.last_nonstable_green_weight = weight
            new_weight = weight - self.green_task_scale_tare_weight + self.green_task_container1_registered_weight + self.green_task_stable_weight_before_connection_loss
            self.sm_green.send('fill', max(0, new_weight), weight>self.scale2_last_stable_weight) # only update on increasing weights or if larger than thhe last stable weight
            if (self.sm_green.current_state in { GreenWeighingState.empty, GreenWeighingState.done_weighing1, GreenWeighingState.done_weighing2 } and
                 weight > self.green_task_empty_scale_weight + WeightManager.TAP_CANCEL_THRESHOLD):
                self.tap_cancel_green_task_timer.start(WeightManager.TAP_CANCEL_PERIOD)
        elif self.roasted_task_scale == 2:
            self.last_nonstable_roasted_weight = weight
            if (self.sm_roasted.current_state == RoastedWeighingState.done and
                 weight > self.roasted_task_empty_scale_weight + WeightManager.TAP_CANCEL_THRESHOLD):
                self.tap_cancel_roasted_task_timer.start(WeightManager.TAP_CANCEL_PERIOD)

    def start(self) -> None:
        self.scale_manager.available_signal.connect(self.scales_available)
        self.scale_manager.unavailable_signal.connect(self.scales_unavailable)
        self.scale_manager.scale1_stable_weight_changed_signal.connect(self.scale1_stable_weight_changed_slot)
        self.scale_manager.scale1_weight_changed_signal.connect(self.scale1_weight_changed_slot)
        self.scale_manager.scale2_stable_weight_changed_signal.connect(self.scale2_stable_weight_changed_slot)
        self.scale_manager.scale2_weight_changed_signal.connect(self.scale2_weight_changed_slot)
        self.scale_manager.connect_all()

    def stop(self) -> None:
        self.reset()
        self.sm_green.send('reset')
        self.sm_roasted.send('reset')
        self.scale_manager.disconnect_all()
        self.scale_manager.available_signal.disconnect(self.scales_available)
        self.scale_manager.unavailable_signal.disconnect(self.scales_unavailable)
        self.scale_manager.scale1_stable_weight_changed_signal.disconnect(self.scale1_stable_weight_changed_slot)
        self.scale_manager.scale1_weight_changed_signal.disconnect(self.scale1_weight_changed_slot)
        self.scale_manager.scale2_stable_weight_changed_signal.disconnect(self.scale2_stable_weight_changed_slot)
        self.scale_manager.scale2_weight_changed_signal.disconnect(self.scale2_weight_changed_slot)
