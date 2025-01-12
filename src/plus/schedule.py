#
# schedule.py
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
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. Seef
# the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import time
import math
import datetime
import json
import html
import textwrap
import platform
import logging
from platform import python_version
from packaging.version import Version
from uuid import UUID
try:
    from PyQt6.QtCore import (QRect, Qt, QMimeData, QSettings, pyqtSlot, pyqtSignal, QPoint, QPointF, QLocale, QDate, QDateTime, QSemaphore, QTimer) # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtGui import (QDrag, QPixmap, QPainter, QTextLayout, QTextLine, QColor, QFontMetrics, QCursor, QAction) # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import (QMessageBox, QStackedWidget, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QTabWidget,  # @UnusedImport @Reimport  @UnresolvedImport
            QCheckBox, QGroupBox, QScrollArea, QLabel, QSizePolicy,  # @UnusedImport @Reimport  @UnresolvedImport
            QGraphicsDropShadowEffect, QPlainTextEdit, QLineEdit, QMenu)  # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import (QRect, Qt, QMimeData, QSettings, pyqtSlot, pyqtSignal, QPoint, QPointF, QLocale, QDate, QDateTime, QSemaphore, QTimer) # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtGui import (QDrag, QPixmap, QPainter, QTextLayout, QTextLine, QColor, QFontMetrics, QCursor) # type: ignore # @UnusedImport @Reimport @UnresolvedImport
    from PyQt5.QtWidgets import (QMessageBox, QStackedWidget, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QTabWidget, # type: ignore # @UnusedImport @Reimport @UnresolvedImport
            QCheckBox, QGroupBox, QScrollArea, QLabel, QSizePolicy, QAction,  # @UnusedImport @Reimport @UnresolvedImport
            QGraphicsDropShadowEffect, QPlainTextEdit, QLineEdit, QMenu)  # @UnusedImport @Reimport  @UnresolvedImport



from babel.dates import format_date
from pydantic import BaseModel, Field, PositiveInt, UUID4, field_validator, model_validator, computed_field, field_serializer
from typing import Final, Tuple, List, Set, Dict, Optional, Any, TypedDict, cast, TextIO, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.atypes import ProfileData # noqa: F401 # pylint: disable=unused-import
    from artisanlib.main import ApplicationWindow # noqa: F401 # pylint: disable=unused-import
    from PyQt6.QtCore import QObject, QEvent, QRect, QMargins # noqa: F401 # pylint: disable=unused-import
    from PyQt6.QtGui import (QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent, QDropEvent, QCloseEvent,  # noqa: F401 # pylint: disable=unused-import
        QResizeEvent, QPaintEvent, QEnterEvent, QMouseEvent, QTextDocument, QKeyEvent) # noqa: F401 # pylint: disable=unused-import
    from PyQt6.QtWidgets import QLayout, QLayoutItem, QBoxLayout # noqa: F401 # pylint: disable=unused-import
    from plus.weight import WeightItem


import plus.register
import plus.controller
import plus.connection
import plus.stock
import plus.config
import plus.sync
import plus.util
from plus.util import datetime2epoch, epoch2datetime, schedulerLink, epoch2ISO8601, ISO86012epoch, plusLink
from plus.weight import Display, WeightManager, GreenWeightItem, RoastedWeightItem
from artisanlib.widgets import ClickableQLabel, ClickableQLineEdit, Splitter
from artisanlib.dialogs import ArtisanResizeablDialog
from artisanlib.util import (float2float, convertWeight, weight_units, render_weight, comma2dot, float2floatWeightVolume, getDirectory)


_log: Final[logging.Logger] = logging.getLogger(__name__)


## Semaphores and persistancy

prepared_items_semaphore = QSemaphore(
    1
)  # protects access to the prepared_items_cache_path file and the prepared_items dict

prepared_items_cache_path = getDirectory(plus.config.prepared_items_cache)

completed_roasts_semaphore = QSemaphore(
    1
)  # protects access to the completed_roasts_cache file and the completed_roasts dict

completed_roasts_cache_path = getDirectory(plus.config.completed_roasts_cache)

hidden_items_semaphore = QSemaphore(
    1
)  # protects access to the hidden_items_cache_path file and the hidden_items list cache

hidden_items_cache_path = getDirectory(plus.config.hidden_items_cache)


## Configuration

# the minimal difference the edited roasted weight in kg of a completed item must have
# to be able to persist the change, compensating back-and-forth unit conversion errors
roasted_weight_editing_minimal_diff: Final[float] = 0.07 # 70g

default_loss:Final[float] = 15.0 # default roast loss in percent
loss_min:Final[float] = 5.0 # minimal loss that makes any sense in percent
loss_max:Final[float] = 25.0 # maximal loss that makes any sense in percent
similar_roasts_max_batch_size_delta:Final[float] = 0.5 # max batch size difference to regard roasts as similar in percent
similar_roasts_max_roast_time_delta:Final[int] = 30 # max roast time difference to regard roasts as similar in seconds
similar_roasts_max_drop_bt_temp_delta_C:Final[float] = 5.0 # max bean temperature difference at DROP to regard roasts as similar in C
similar_roasts_max_drop_bt_temp_delta_F:Final[float] = 4.0 # max bean temperature difference at DROP to regard roasts as similar in F

## Style

border_width: Final[int] = 4
border_radius: Final[int] = 6
tooltip_line_length: Final[int] = 75 # in character
tooltip_max_lines: Final[int] = 3
tooltip_placeholder: Final[str] = '...'

#
plus_red_hover: Final[str] = '#B2153F'
plus_red: Final[str] = '#BC2C52'
plus_blue_hover: Final[str] = '#1985ba'
plus_blue: Final[str] = '#147BB3'
## for selected schedule item:
plus_alt_blue_hover: Final[str] = '#3d81ba'
plus_alt_blue: Final[str] = '#3979ae' # main.py:dark_blue
#
white: Final[str] = 'white'
dull_white: Final[str] = '#FDFDFD'
dim_white: Final[str] = '#EEEEEE'
dark_white: Final[str] = '#505050'
super_light_grey_hover: Final[str] = '#EEEEEE'
super_light_grey: Final[str] = '#E3E3E3'
very_light_grey: Final[str] = '#dddddd'
light_grey_hover: Final[str] = '#D0D0D0'
light_grey: Final[str] = '#BBBBBB'
dark_grey_hover: Final[str] = '#909090'
dark_grey: Final[str] = '#808080'
dull_dark_grey: Final[str] = '#606060'
medium_dark_grey: Final[str] = '#444444'
very_dark_grey: Final[str] = '#222222'
#
drag_indicator_color: Final[str] = very_light_grey
shadow_color: Final[str] = very_dark_grey

tooltip_style: Final[str] = 'QToolTip { padding: 5px; opacity: 240; }'
tooltip_light_background_style: Final[str] = f'QToolTip {{ background: {light_grey}; padding: 5px; opacity: 240; }}'
tooltip_dull_dark_background_style: Final[str] = f'QToolTip {{ background: {dull_dark_grey}; padding: 5px; opacity: 240; }}'



class CompletedItemDict(TypedDict):
    scheduleID:str         # the ID of the ScheduleItem this completed item belongs to
    scheduleDate:str       # the date of the ScheduleItem this completed item belongs to
    roastUUID:str          # the UUID of this roast
    roastdate: float       # as epoch
    roastbatchnr: int      # set to zero if no batch number is assigned
    roastbatchprefix: str  # might be the empty string if no prefix is used
    count: int             # total count >0 of corresponding ScheduleItem
    sequence_id: int       # sequence id of this roast (sequence_id <= count)
    title:str
    coffee_label: Optional[str]
    blend_label: Optional[str]
    store_label: Optional[str]
    batchsize: float # in kg
    weight: float    # in kg (resulting weight as set by the user if measured is True and otherwise equal to weight_estimate)
    weight_estimate: float # in kg (estimated roasted weight based on profile template or previous roasts or similar)
    measured: bool   # True if (out-)weight was measured or manually set, False if estimated from server calculated loss or template
    color: int
    moisture: float  # in %
    density: float   # in g/l
    roastingnotes: str
    cupping_score: float
    cuppingnotes: str


# ordered list of dict with the completed roasts data (latest roast first)
completed_roasts_cache:List[CompletedItemDict] = []

# dict associating ScheduledItem IDs to a list of prepared green weights interpreted in order. Weights beyond item.count will be ignored.
prepared_items_cache:Dict[str, List[float]] = {}

# list containing ScheduledItem IDs that are hidden
hidden_items_cache:List[str] = []


class ScheduledItem(BaseModel):
    id: str = Field(alias='_id')
    date: datetime.date
    count: PositiveInt
    title: str
    coffee: Optional[str] = Field(default=None)
    blend: Optional[str] = Field(default=None)
    store: str = Field(..., alias='location')
    weight: float = Field(..., alias='amount')       # batch size in kg
    loss: float = default_loss                       # default loss based calculated by magic on the server in % (if not given defaults to 15%)
    machine: Optional[str] = Field(default=None)
    user: Optional[str] = Field(default=None)
    nickname: Optional[str] = Field(default=None)
    template: Optional[UUID4] = Field(default=None)  # note that this generates UUID objects. To get a UUID string without dashes use uuid.hex.
    note: Optional[str] = Field(default=None)
    roasts: Set[UUID4] = Field(default=set())        # note that this generates UUID objects. To get a UUID string without dashes use uuid.hex.

    @field_validator('*', mode='before')
    def remove_blank_strings(cls: BaseModel, v: Optional[str]) -> Optional[str]:   # pylint: disable=no-self-argument,no-self-use
        """Removes whitespace characters and return None if empty"""
        if isinstance(v, str):
            v = v.strip()
        if v == '':
            return None
        return v

    @model_validator(mode='after') # pyright:ignore[reportArgumentType]
    def coffee_or_blend(self) -> 'ScheduledItem':
        if self.coffee is None and self.blend is None:
            raise ValueError('Either coffee or blend must be specified')
        if self.coffee is not None and self.blend is not None:
            raise ValueError('Either coffee or blend must be specified, but not both')
        if len(self.title) == 0:
            raise ValueError('Title cannot be empty')
        if (self.date - datetime.datetime.now(datetime.timezone.utc).astimezone().date()).days < 0:
            raise ValueError('Date should not be in the past')
        return self

class CompletedItem(BaseModel):
    count: PositiveInt       # total count >0 of corresponding ScheduleItem
    scheduleID: str
    scheduleDate: str
    sequence_id: PositiveInt # sequence id of this roast (sequence_id <= count)
    roastUUID: UUID4
    roastdate: datetime.datetime
    roastbatchnr: int
    roastbatchprefix: str
    title: str
    coffee_label: Optional[str] = Field(default=None)
    blend_label: Optional[str] = Field(default=None)
    store_label: Optional[str] = Field(default=None)
    batchsize: float # in kg (weight of greens)
    weight: float    # in kg (resulting weight of roasted beans)
    weight_estimate: float # in kg (estimated roasted beans weight based on profile template or previous roasts weight loss)
    measured: bool = Field(default=False)   # True if (out-)weight was measured or manually set, False if estimated from server calculated loss or template
    color: int
    moisture: float # in %
    density: float  # in g/l
    roastingnotes: str = Field(default='')
    cupping_score: float
    cuppingnotes: str = Field(default='')

    @computed_field  # type:ignore[prop-decorator] # Decorators on top of @property are not supported
    @property
    def prefix(self) -> str:
        res = ''
        if self.roastbatchnr > 0:
            res = f'{self.roastbatchprefix}{self.roastbatchnr}'
        return res

    @model_validator(mode='after') # pyright:ignore[reportArgumentType]
    def coffee_or_blend(self) -> 'CompletedItem':
        if len(self.title) == 0:
            raise ValueError('Title cannot be empty')
# as CompletedItems are generated for ScheduledItems where store and one of blend/coffee needs to be set
# the store_label and one of the blend_label/coffee_label should never be empty, but in case they are we
# handle this without further ado
        if self.coffee_label is None and self.blend_label is None:
#            raise ValueError('Either coffee_label or blend_label must be specified')
            _log.info('CompletedItem validation: Either coffee_label (%s) or blend_label (%s) must be specified (%s)', self.coffee_label, self.blend_label, self.scheduleID)
        if self.coffee_label is not None and self.blend_label is not None:
#            raise ValueError('Either coffee_label or blend_label must be specified, but not both')
            _log.info('CompletedItem validation: Either coffee_label (%s) or blend_label (%s) must be specified, but not both (%s)', self.coffee_label, self.blend_label, self.scheduleID)
# you should not be able to complete more roasts than the items coount, but in case it happens we
# handle this without further ado
        if self.sequence_id > self.count:
#            raise ValueError('sequence_id cannot be larger than total count of roasts per ScheduleItem')
            _log.info('CompletedItem validation: sequence_id (%s) cannot be larger than total count (%s) of roasts per ScheduleItem (%s)', self.sequence_id, self.count, self.scheduleID)
        return self

    @field_serializer('roastdate', when_used='json')
    def serialize_roastdate_to_epoch(roastdate: datetime.datetime) -> int: # type:ignore[misc] # pylint: disable=no-self-argument
        return int(roastdate.timestamp())

    @field_serializer('roastUUID', when_used='json')
    def serialize_roastUUID_to_str(roastUUID: UUID4) -> str: # type:ignore[misc] # pylint: disable=no-self-argument
        return roastUUID.hex


    # updates this CompletedItem with the data given in profile_data
    # NOTE: values in profile_data may be None here as those are produced by changes()
    def update_completed_item(self, aw:'ApplicationWindow', profile_data:Dict[str, Any]) -> bool:
        updated:bool = False
        if 'batch_number' in profile_data:
            batch_number = int(profile_data['batch_number'])
            if batch_number != self.roastbatchnr:
                updated = True
                self.roastbatchnr = batch_number
        if 'batch_prefix' in profile_data:
            batch_prefix = str(profile_data['batch_prefix'])
            if batch_prefix != self.roastbatchprefix:
                updated = True
                self.roastbatchprefix = batch_prefix
        if 'label' in profile_data:
            label = str(profile_data['label'])
            if label != self.title:
                updated = True
                self.title = label
        if 'coffee' in profile_data and 'label' in profile_data['coffee']:
            label = profile_data['coffee']['label']
            if label != self.coffee_label:
                updated = True
                self.coffee_label = label
        if 'blend' in profile_data and 'label' in profile_data['blend']:
            label = profile_data['blend']['label']
            if label != self.blend_label:
                updated = True
                self.blend_label = label
        if 'location' in profile_data and 'label' in profile_data['location']:
            label = str(profile_data['location']['label'])
            if label != self.store_label:
                updated = True
                self.store_label = label
        if 'amount' in profile_data:
            amount = float(profile_data['amount'])
            if amount != self.batchsize:
                updated = True
                self.batchsize = amount
        if 'end_weight' in profile_data:
            end_weight = float(profile_data['end_weight'])
            if end_weight != self.weight:
                updated = True
                self.weight = end_weight
        if 'ground_color' in profile_data:
            ground_color = (0 if profile_data['ground_color'] is None else int(float(round(profile_data['ground_color']))))
            if ground_color != self.color:
                updated = True
                self.color = ground_color
        if 'density_roasted' in profile_data:
            density_roasted = (0 if profile_data['density_roasted'] is None else float(profile_data['density_roasted']))
            if density_roasted != self.density:
                updated = True
                self.density = density_roasted
        if 'moisture' in profile_data:
            moisture = (0 if profile_data['moisture'] is None else float(profile_data['moisture']))
            if moisture != self.moisture:
                updated = True
                self.moisture = moisture
        if 'notes' in profile_data:
            notes = ('' if profile_data['notes'] is None else str(profile_data['notes']).strip())
            if notes != self.roastingnotes:
                updated = True
                self.roastingnotes = notes
        if 'cupping_score' in profile_data:
            cupping_score = (50 if profile_data['cupping_score'] is None else float2float(profile_data['cupping_score'], 2))
            if cupping_score != self.cupping_score:
                updated = True
                self.cupping_score = cupping_score
        if 'cupping_notes' in profile_data:
            cupping_notes = ('' if profile_data['cupping_notes'] is None else str(profile_data['cupping_notes']).strip())
            if cupping_notes != self.cuppingnotes:
                updated = True
                self.cuppingnotes = cupping_notes
        if updated:
            # we update the completed_roasts_cache entry
            completed_item_dict = self.model_dump(mode='json')
            if 'prefix' in completed_item_dict:
                del completed_item_dict['prefix']
            add_completed(aw.plus_account_id, cast(CompletedItemDict, completed_item_dict))
        return updated


###################
# completed roasts cache
#
# NOTE: completed roasts data file access is not protected by portalocker for parallel access via a second Artisan instance
#   as the ArtisanViewer disables the scheduler, thus only one Artisan instance is handling this file
#
# NOTE: changes applied to the completed roasts cache via add_completed() are automatically persisted by a call to save_completed()


# save completed roasts data to local file cache
def save_completed(plus_account_id:Optional[str]) -> None:
    _log.debug('save_completed(%s): %s', plus_account_id, len(completed_roasts_cache))
    if plus_account_id is not None:
        try:
            completed_roasts_semaphore.acquire(1)
            f:TextIO
            with open(completed_roasts_cache_path, 'w', encoding='utf-8') as f:
                try:
                    completed_roasts_cache_data = json.load(f)
                except Exception:   # pylint: disable=broad-except
                    completed_roasts_cache_data = {}
                completed_roasts_cache_data[plus_account_id] = completed_roasts_cache
                json.dump(completed_roasts_cache_data, f, indent=None, separators=(',', ':'), ensure_ascii=False)
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)
        finally:
            if completed_roasts_semaphore.available() < 1:
                completed_roasts_semaphore.release(1)


# load completed roasts data from local file cache
def load_completed(plus_account_id:Optional[str]) -> None:
    global completed_roasts_cache  # pylint: disable=global-statement
    _log.debug('load_completed(%s)', plus_account_id)
    try:
        completed_roasts_semaphore.acquire(1)
        completed_roasts_cache = []
        if plus_account_id is not None:
            f:TextIO
            with open(completed_roasts_cache_path, encoding='utf-8') as f:
                completed_roasts_cache_data = json.load(f)
                if plus_account_id in completed_roasts_cache_data:
                    completed_roasts = completed_roasts_cache_data[plus_account_id]
                    today_completed = []
                    previously_completed = []
                    today = datetime.datetime.now(datetime.timezone.utc)
                    for ci in completed_roasts:
                        if 'roastdate' in ci:
                            if epoch2datetime(ci['roastdate']).astimezone().date() == today.astimezone().date():
                                today_completed.append(ci)
                            else:
                                previously_completed.append(ci)
                    if len(previously_completed)>0:
                        previous_session_epoch:float = previously_completed[0].get('roastdate', datetime2epoch(today))
                        previous_session_date = epoch2datetime(previous_session_epoch).astimezone().date()
                        previously_completed = [pc for pc in previously_completed if 'roastdate' in pc and epoch2datetime(pc['roastdate']).astimezone().date() == previous_session_date]
                    # we keep all roasts completed today as well as all from the previous roast session
                    completed_roasts_cache = today_completed + previously_completed
                    completed_roasts_cache.sort(key=lambda cr: cr['roastdate'], reverse=True)
    except FileNotFoundError:
        _log.debug('no completed roast cache file found')
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
    finally:
        if completed_roasts_semaphore.available() < 1:
            completed_roasts_semaphore.release(1)


def get_all_completed() -> List[CompletedItemDict]:
    try:
        completed_roasts_semaphore.acquire(1)
        return completed_roasts_cache
    except Exception as e:  # pylint: disable=broad-except
        _log.error(e)
        return []
    finally:
        if completed_roasts_semaphore.available() < 1:
            completed_roasts_semaphore.release(1)


# add the given CompletedItemDict if it contains a roastUUID which does not occurs yet in the completed_roasts_cache
# if there is already a completed roast with the given UUID, its content is replaced by the given CompletedItemDict
def add_completed(plus_account_id:Optional[str], ci:CompletedItemDict) -> None:
    if 'roastUUID' in ci:
        modified: bool = False
        try:
            completed_roasts_semaphore.acquire(1)
            # test if there is already a completed roasts with that UUID
            idx = next((i for i,d in enumerate(completed_roasts_cache) if 'roastUUID' in d and d['roastUUID'] == ci['roastUUID']), None)
            if idx is None:
                # add ci to front
                completed_roasts_cache.insert(0, ci)
            else:
                completed_roasts_cache[idx] = ci
            modified = True
        except Exception as e:  # pylint: disable=broad-except
            _log.error(e)
        finally:
            if completed_roasts_semaphore.available() < 1:
                completed_roasts_semaphore.release(1)
        if modified:
            save_completed(plus_account_id)



###################
# prepared schedule items cache
#
# NOTE: prepared scheduled items data file access is not protected by portalocker for parallel access via a second Artisan instance
#   as the ArtisanViewer disables the scheduler, thus only one Artisan instance is handling this file
#
# NOTE: changes applied to the prepared schedule item cache via take_prepared(), set_prepared() and set_unprepared()
#   are automatically persisted by a call to save_prepared()


# save prepared schedule items information to local file cache
def save_prepared(plus_account_id:Optional[str]) -> None:
    _log.debug('save_prepared(%s): %s', plus_account_id, len(prepared_items_cache))
    if plus_account_id is not None:
        try:
            prepared_items_semaphore.acquire(1)
            f:TextIO
            with open(prepared_items_cache_path, 'w+', encoding='utf-8') as f:
                try:
                    prepared_items_cache_data = json.load(f)
                except Exception:   # pylint: disable=broad-except
                    prepared_items_cache_data = {}
                prepared_items_cache_data[plus_account_id] = prepared_items_cache
                json.dump(prepared_items_cache_data, f, indent=None, separators=(',', ':'), ensure_ascii=False)
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)
        finally:
            if prepared_items_semaphore.available() < 1:
                prepared_items_semaphore.release(1)

# load prepared schedule items information from local file cache
def load_prepared(plus_account_id:Optional[str], scheduled_items:List[ScheduledItem]) -> None:
    global prepared_items_cache  # pylint: disable=global-statement
    _log.debug('load_prepared(%s)', plus_account_id)
    try:
        prepared_items_semaphore.acquire(1)
        prepared_items_cache = {}
        if plus_account_id is not None:
            f:TextIO
            with open(prepared_items_cache_path, encoding='utf-8') as f:
                prepared_items_cache_data = json.load(f)
                if plus_account_id in prepared_items_cache_data:
                    prepared_items = {}
                    for item_id, prepared_weights in prepared_items_cache_data[plus_account_id].items():
                        si = next((x for x in scheduled_items if x.id == item_id), None)
                        if si is not None and len(prepared_weights)>0:
                            # all batches of this item are prepared
                            prepared_items[item_id] = prepared_weights
                    prepared_items_cache = prepared_items
    except FileNotFoundError:
        _log.debug('no prepared items cache file found')
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
    finally:
        if prepared_items_semaphore.available() < 1:
            prepared_items_semaphore.release(1)

def get_prepared(item:ScheduledItem) -> List[float]:
    try:
        prepared_items_semaphore.acquire(1)
        return prepared_items_cache.get(item.id, [])
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
    finally:
        if prepared_items_semaphore.available() < 1:
            prepared_items_semaphore.release(1)
    return []

# reduce the list of prepared weights by taking the first one (FIFO)
def take_prepared(plus_account_id:Optional[str], item:ScheduledItem) -> Optional[float]:
    _log.debug('take_prepared(%s, %s)', plus_account_id, item)
    modified: bool = False
    try:
        prepared_items_semaphore.acquire(1)
        prepared_items = prepared_items_cache.get(item.id, [])
        if len(prepared_items) > 0:
            first_prepared_item = prepared_items[0]
            remaining_prepared_items = prepared_items[1:]
            if len(remaining_prepared_items) > 0:
                prepared_items_cache[item.id] = remaining_prepared_items
            else:
                del prepared_items_cache[item.id]
            modified = True
            return first_prepared_item
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
    finally:
        if prepared_items_semaphore.available() < 1:
            prepared_items_semaphore.release(1)
    if modified:
        save_prepared(plus_account_id)
    return None

# set all remaining batches as prepared
def add_prepared(plus_account_id:Optional[str], item:ScheduledItem, weight:float) -> None:
    modified: bool = False
    try:
        prepared_items_semaphore.acquire(1)
        if item.id in prepared_items_cache:
            prepared_items_cache[item.id].append(weight)
        else:
            prepared_items_cache[item.id] = [weight]
        modified = True
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
    finally:
        if prepared_items_semaphore.available() < 1:
            prepared_items_semaphore.release(1)
    if modified:
        save_prepared(plus_account_id)

# returns true if all remaining batches are prepared
def fully_prepared(item:ScheduledItem) -> bool:
    try:
        prepared_items_semaphore.acquire(1)
        return item.id in prepared_items_cache and item.count - len(item.roasts) <= len(prepared_items_cache[item.id])
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
    finally:
        if prepared_items_semaphore.available() < 1:
            prepared_items_semaphore.release(1)
    return False

# returns true if no batch is prepared
def fully_unprepared(item:ScheduledItem) -> bool:
    try:
        prepared_items_semaphore.acquire(1)
        return item.id not in prepared_items_cache or len(prepared_items_cache[item.id]) == 0
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
    finally:
        if prepared_items_semaphore.available() < 1:
            prepared_items_semaphore.release(1)
    return False

# set all remaining batches as prepared
def set_prepared(plus_account_id:Optional[str], item:ScheduledItem) -> None:
    modified: bool = False
    try:
        prepared_items_semaphore.acquire(1)
        current_prepared = (prepared_items_cache[item.id][:item.count] if item.id in prepared_items_cache else [])
        prepared_items_cache[item.id] = current_prepared + [item.weight]*(item.count - len(item.roasts) - len(current_prepared))
        modified = True
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
    finally:
        if prepared_items_semaphore.available() < 1:
            prepared_items_semaphore.release(1)
    if modified:
        save_prepared(plus_account_id)

# set all batches as unprepared
def set_unprepared(plus_account_id:Optional[str], item:ScheduledItem) -> None:
    modified: bool = False
    try:
        prepared_items_semaphore.acquire(1)
        del prepared_items_cache[item.id]
        modified = True
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
    finally:
        if prepared_items_semaphore.available() < 1:
            prepared_items_semaphore.release(1)
    if modified:
        save_prepared(plus_account_id)


###################
# hidden schedule items cache
#
# NOTE: hidden scheduled items data file access is not protected by portalocker for parallel access via a second Artisan instance
#   as the ArtisanViewer disables the scheduler, thus only one Artisan instance is handling this file
#
# NOTE: changes applied to the hidden schedule item cache via set_hidden() and set_visible()
#   are automatically persisted by a call to save_hidden()


# save hidden schedule items information to local file cache
def save_hidden(plus_account_id:Optional[str]) -> None:
    _log.debug('save_hidden(%s): %s', plus_account_id, len(hidden_items_cache))
    if plus_account_id is not None:
        try:
            hidden_items_semaphore.acquire(1)
            f:TextIO
            with open(hidden_items_cache_path, 'w+', encoding='utf-8') as f:
                try:
                    hidden_items_cache_data = json.load(f)
                except Exception:   # pylint: disable=broad-except
                    hidden_items_cache_data = {}
                hidden_items_cache_data[plus_account_id] = hidden_items_cache
                json.dump(hidden_items_cache_data, f, indent=None, separators=(',', ':'), ensure_ascii=False)
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)
        finally:
            if hidden_items_semaphore.available() < 1:
                hidden_items_semaphore.release(1)

# load hidden schedule items information from local file cache
def load_hidden(plus_account_id:Optional[str], scheduled_items:List[ScheduledItem]) -> None:
    global hidden_items_cache  # pylint: disable=global-statement
    _log.debug('load_hidden(%s)', plus_account_id)
    try:
        hidden_items_semaphore.acquire(1)
        hidden_items_cache = []
        if plus_account_id is not None:
            f:TextIO
            with open(hidden_items_cache_path, encoding='utf-8') as f:
                hidden_items_cache_data = json.load(f)
                if plus_account_id in hidden_items_cache_data:
                    hidden_items:List[str] = []
                    for item_id in hidden_items_cache_data[plus_account_id]:
                        # remove schedule items from hidden_items_cache that are not in the given list of schedule_items
                        si = next((x for x in scheduled_items if x.id == item_id), None)
                        if si is not None:
                            hidden_items.append(item_id)
                    hidden_items_cache = hidden_items
    except FileNotFoundError:
        _log.debug('no hidden items cache file found')
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
    finally:
        if hidden_items_semaphore.available() < 1:
            hidden_items_semaphore.release(1)

def is_hidden(item:ScheduledItem) -> bool:
    try:
        hidden_items_semaphore.acquire(1)
        return item.id in hidden_items_cache
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
    finally:
        if hidden_items_semaphore.available() < 1:
            hidden_items_semaphore.release(1)
    return False

# set all remaining batches as prepared
def set_hidden(plus_account_id:Optional[str], item:ScheduledItem) -> None:
    modified: bool = False
    try:
        hidden_items_semaphore.acquire(1)
        if item.id not in hidden_items_cache:
            hidden_items_cache.append(item.id)
            modified = True
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
    finally:
        if hidden_items_semaphore.available() < 1:
            hidden_items_semaphore.release(1)
    if modified:
        save_hidden(plus_account_id)


# set all remaining batches as prepared
def set_visible(plus_account_id:Optional[str], item:ScheduledItem) -> None:
    modified: bool = False
    try:
        hidden_items_semaphore.acquire(1)
        if item.id in hidden_items_cache:
            hidden_items_cache.remove(item.id)
            modified = True
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
    finally:
        if hidden_items_semaphore.available() < 1:
            hidden_items_semaphore.release(1)
    if modified:
        save_hidden(plus_account_id)

#--------

def scheduleditem_beans_description(weight_unit_idx:int, item:ScheduledItem) -> str:
    beans_description:str = ''
    if item.coffee is not None:
        coffee = plus.stock.getCoffee(item.coffee)
        if coffee is not None:
            store_label:str = plus.stock.getLocationLabel(coffee, item.store)
            if store_label != '':
                store_label = f'<br>[{html.escape(store_label)}]'
            beans_description = f'<b>{html.escape(plus.stock.coffeeLabel(coffee))}</b>{store_label}'
    else:
        blends = plus.stock.getBlends(weight_unit_idx, item.store)
        blend = next((b for b in blends if plus.stock.getBlendId(b) == item.blend and plus.stock.getBlendStockDict(b)['location_hr_id'] == item.store), None)
        if blend is not None:
            blend_lines = ''.join([f'<tr><td>{html.escape(bl[0])}</td><td>{html.escape(bl[1])}</td></tr>'
                        for bl in plus.stock.blend2weight_beans(blend, weight_unit_idx, item.weight)])
            beans_description = f"<b>{html.escape(plus.stock.getBlendName(blend))}</b> [{html.escape(plus.stock.getBlendStockDict(blend)['location_label'])}]<table>{blend_lines}</table>"
    return beans_description

def completeditem_beans_description(weight_unit_idx:int, item:CompletedItem) -> str:
    if item.coffee_label is None and item.blend_label is None:
        return ''
    coffee_blend_label = (f' {html.escape(item.coffee_label)}' if item.coffee_label is not None else (f' {html.escape(item.blend_label)}' if item.blend_label is not None else ''))
    return f'{render_weight(item.batchsize, 1, weight_unit_idx)}{coffee_blend_label}'



def remove_prefix(s:str, prefix:str) -> str:
    if Version(python_version()) < Version('3.9.0'):
        if s.startswith(prefix):
            return s[len(prefix):]
        return s
    return s.removeprefix(prefix) # type:ignore[attr-defined, no-any-return, reportAttributeAccessIssue, unused-ignore] # not known under Python 3.8 which we use for pyright type checking

def remove_suffix(s:str, suffix:str) -> str:
    if Version(python_version()) < Version('3.9.0'):
        if s.endswith(suffix):
            return s[:-len(suffix)]
        return s
    return s.removesuffix(suffix) # type:ignore[attr-defined, no-any-return, reportAttributeAccessIssue, unused-ignore] # not known under Python 3.8 which we use for pyright type checking

def locale_format_date_no_year(locale:str, date:datetime.date) -> str:
    try:
        # format nicely using babel
        date_without_year = format_date(date, format='long', locale=locale).replace(format_date(date, 'Y', locale=locale),'').strip()
        # strip some more characters for certain locales
        if locale.startswith(('en', 'vi')):
            date_without_year = date_without_year.rstrip(',')
        elif locale.startswith(('es', 'pt')):
            date_without_year = remove_suffix(date_without_year, ' de')
        elif locale.startswith('zh'):
            date_without_year = date_without_year.lstrip('\u5E74')
        elif locale.startswith('ko'):
            date_without_year = date_without_year.lstrip('\uB144')
        elif locale.startswith('th'):
            date_without_year = remove_suffix(date_without_year, '\u0e04.\u0e28.')
        elif locale.startswith('lv'):
            date_without_year = remove_prefix(date_without_year, '. gada')
        elif locale.startswith('hu'):
            date_without_year = remove_prefix(date_without_year, '. ')
        elif locale.startswith('ru'):
            date_without_year = remove_suffix(date_without_year, '\u202f\u0433.')
        elif locale.startswith('uk'):
            date_without_year = remove_suffix(date_without_year, '\u202f\u0440.')
        return date_without_year.strip()
    except Exception as e: # pylint: disable=broad-except
        _log.error(e)
        # format using datetime using system locale
        date_without_year = date.strftime('%x').replace(date.strftime('%Y'),'')
        return date_without_year.strip().strip(',').strip('.').strip('-').strip('/').strip()


#--------

class QLabelRight(QLabel): # pyright: ignore [reportGeneralTypeIssues] # Argument to class must be a base class
    ...


##### https://stackoverflow.com/questions/11446478/pyside-pyqt-truncate-text-in-qlabel-based-on-minimumsize
class QElidedLabel(QLabel): # pyright: ignore[reportGeneralTypeIssues] # Argument to class must be a base class
    """Label with text elision.

    QLabel which will elide text too long to fit the widget.  Based on:
    https://doc-snapshots.qt.io/qtforpython-5.15/overviews/qtwidgets-widgets-elidedlabel-example.html

    Parameters
    ----------
    text : str

        Label text.

    mode : Qt.TextElideMode

       Specify where ellipsis should appear when displaying texts that
       don’t fit.

       Default is QtCore.Qt.TextElideMode.ElideRight.

       Possible modes:
         Qt.TextElideMode.ElideLeft
         Qt.TextElideMode.ElideMiddle
         Qt.TextElideMode.ElideRight

    parent : QWidget

       Parent widget.  Default is None.

    """


    def __init__(self, text:str = '', mode:Qt.TextElideMode = Qt.TextElideMode.ElideMiddle) -> None:
        super().__init__()

        self._mode = mode
        self._contents = ''
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setText(text)


    def setText(self, text:Optional[str]) -> None:
        if text is not None:
            self._contents = text
            self.update()


    def text(self) -> str:
        return self._contents


    def paintEvent(self, event:'Optional[QPaintEvent]') -> None:
        super().paintEvent(event)

        painter = QPainter(self)
        font_metrics = painter.fontMetrics()
        text_width = font_metrics.horizontalAdvance(self.text())

        # layout phase
        text_layout = QTextLayout(self._contents, painter.font())
        text_layout.beginLayout()

        while True:
            line:QTextLine = text_layout.createLine()

            if not line.isValid():
                break

            line.setLineWidth(self.width())

            cr:QRect = self.contentsRect()

            if text_width >= self.width():
                elided_line = font_metrics.elidedText(self._contents, self._mode, self.width())
                painter.drawText(QPoint(cr.left(), font_metrics.ascent()+cr.top()), elided_line)
                break
            line.draw(painter, QPointF(cr.left(), cr.top() + 0.5))

        text_layout.endLayout()



class DragTargetIndicator(QFrame): # pyright: ignore[reportGeneralTypeIssues] # Argument to class must be a base class
    def __init__(self, parent:Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.addWidget(QLabel())
        layout.setSpacing(0)
        layout.setContentsMargins(5,5,5,5)
        self.setLayout(layout)
        self.setStyleSheet(
            f'DragTargetIndicator {{ border:{border_width}px solid {drag_indicator_color}; background: {drag_indicator_color}; border-radius: {border_radius}px; }}')



class StandardItem(QFrame): # pyright: ignore[reportGeneralTypeIssues] # Argument to class must be a base class

    clicked = pyqtSignal()
    selected = pyqtSignal()
    prepared = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        layout = QHBoxLayout()
        left:str = self.getLeft()
        self.first_label = QLabel(left)
        self.first_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        if left != '':
            layout.addWidget(self.first_label)
            layout.addSpacing(2)
        self.second_label = QElidedLabel(self.getMiddle())
        layout.addWidget(self.second_label)
        self.third_label = QLabelRight(self.getRight())
        layout.addWidget(self.third_label)
        layout.setSpacing(5)
        layout.setContentsMargins(5,5,5,5)
        self.setLayout(layout)
        self.setProperty('Hover', False)
        self.setProperty('Selected', False)


    def getFirstLabel(self) -> QLabel:
        return self.first_label

    def getSecondLabel(self) -> QElidedLabel:
        return self.second_label

    def getThirdLabel(self) -> QLabel:
        return self.third_label

    def update_labels(self) -> None:
        self.first_label.setText(self.getLeft())
        self.second_label.setText(self.getMiddle())
        self.third_label.setText(self.getRight())


    def getLeft(self) -> str: # pylint: disable=no-self-argument,no-self-use
        return ''


    def getMiddle(self) -> str: # pylint: disable=no-self-argument,no-self-use
        return ''


    def getRight(self) -> str: # pylint: disable=no-self-argument,no-self-use
        return ''


    def makeShadow(self) -> QGraphicsDropShadowEffect:
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20) # (15)
        shadow.setColor(QColor(shadow_color))
        shadow.setOffset(0,1.5) # (0,0.7)
        return shadow


    def setText(self, txt:str) -> None:
        pass


    def mousePressEvent(self, event:'Optional[QMouseEvent]') -> None:
        if event is not None:
            modifiers = QApplication.keyboardModifiers()
            if modifiers == Qt.KeyboardModifier.AltModifier:  #alt click
                self.clicked.emit()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event:'Optional[QMouseEvent]') -> None:
        if event is not None:
            modifiers = QApplication.keyboardModifiers()
            if modifiers != Qt.KeyboardModifier.AltModifier:  #no alt click
                self.selected.emit()
        super().mouseReleaseEvent(event)


    def enterEvent(self, event:'Optional[QEnterEvent]') -> None:
        if event is not None:
            self.setProperty('Hover', True)
            self.setStyle(self.style())
        super().enterEvent(event)


    def leaveEvent(self, event:'Optional[QEvent]') -> None:
        if event is not None:
            self.setProperty('Hover', False)
            self.setStyle(self.style())
        super().leaveEvent(event)



class NoDragItem(StandardItem):
    # now a datetime in UTC timezone
    def __init__(self, data:CompletedItem, aw:'ApplicationWindow', now:datetime.datetime) -> None:
        # Store data separately from display label, but use label for default.
        self.aw = aw
        self.data:CompletedItem = data
        self.locale_str = self.aw.locale_str
        self.now = now
        self.weight_unit_idx = weight_units.index(self.aw.qmc.weight[2])
        super().__init__()
        layout:Optional[QLayout] = self.layout()
        if layout is not None:
            layout.setContentsMargins(10,5,10,5) # left, top, right, bottom

        item_color = light_grey
        item_color_hover = light_grey_hover
        if self.data.roastdate.astimezone().date() == now.astimezone().date():
            # item roasted today
            item_color = plus_alt_blue
            item_color_hover = plus_alt_blue_hover

        head_line =  ('' if self.data.count == 1 else f'{self.data.sequence_id}/{self.data.count}')
        wrapper =  textwrap.TextWrapper(width=tooltip_line_length, max_lines=tooltip_max_lines, placeholder=tooltip_placeholder)
        title = '<br>'.join(wrapper.wrap(html.escape(self.data.title)))
        accent_color = (white if self.aw.app.darkmode else plus_blue)
        title_line = f"<p style='white-space:pre'><font color=\"{accent_color}\"><b><big>{title}</big></b></font></p>"
        beans_description = completeditem_beans_description(self.weight_unit_idx, self.data)
        store_line = (f'</b><br>[{html.escape(self.data.store_label)}]' if (beans_description != '' and self.data.store_label is not None and self.data.store_label != '') else '')
        detailed_description = f"{head_line}{title_line}<p style='white-space:pre'>{beans_description}{store_line}"
        self.setToolTip(detailed_description)

        self.setStyleSheet(
            f'{tooltip_style} NoDragItem[Selected=false][Hover=false] {{ border:0px solid {item_color}; background: {item_color}; border-radius: {border_radius}px; }}'
            f'NoDragItem[Selected=false][Hover=true] {{ border:0px solid {item_color_hover}; background: {item_color_hover}; border-radius: {border_radius}px; }}'
            f'NoDragItem[Selected=true][Hover=false] {{ border:0px solid {plus_red}; background: {plus_red}; border-radius: {border_radius}px; }}'
            f'NoDragItem[Selected=true][Hover=true] {{ border:0px solid {plus_red_hover}; background: {plus_red_hover}; border-radius: {border_radius}px; }}'
            f'QLabel {{ font-weight: bold; color: {white}; }}'
            f'QLabelRight {{ font-size: 10pt; }}'
            'QElidedLabel { font-weight: normal; }')


    def getLeft(self) -> str:
        return f'{self.data.prefix}'

    def getMiddle(self) -> str:
        return f'{self.data.title}'

    def getRight(self) -> str:
        try:
            # the datetimes now and roastdate are in UTC, we need to compare the dates w.r.t. the local timezone thus we have to convert both via astimezone()
            roastdate = self.data.roastdate
            roastdate_date_local = roastdate.astimezone().date()
            days_diff = (self.now.astimezone().date() - roastdate_date_local).days
            task_date_str = ''
            if days_diff == 0:
                # for time formatting we use the system locale
                locale = QLocale()
                dt = QDateTime.fromSecsSinceEpoch(int(datetime2epoch(roastdate)))
                task_date_str = locale.toString(dt.time(), QLocale.FormatType.ShortFormat)
            elif days_diff == 1:
                task_date_str = QApplication.translate('Plus', 'Yesterday').capitalize()
            elif days_diff < 7:
                # for date formatting we use the artisan-language locale
                locale = QLocale(self.locale_str)
                task_date_str = locale.toString(QDate(roastdate_date_local.year, roastdate_date_local.month, roastdate_date_local.day), 'dddd').capitalize()
            else:
                # date formatted according to the locale without the year
                task_date_str = locale_format_date_no_year(self.locale_str, roastdate_date_local)

            weight = (f'{render_weight(self.data.weight, 1, self.weight_unit_idx)}  ' if self.data.measured else '')

            return f'{weight}{task_date_str}'
        except Exception as e: # pylint: disable=broad-except
            # if anything goes wrong here we log an exception and return the empty string
            _log.exception(e)
            return ''

    def select(self) -> None:
        self.setProperty('Selected', True)
        self.setStyle(self.style())

    def deselect(self) -> None:
        self.setProperty('Selected', False)
        self.setStyle(self.style())



class DragItem(StandardItem):

    registerRoast = pyqtSignal() # register current loaded roast profile in the schedule item with the given scheduleID

    # today a date in local timezone
    def __init__(self, data:ScheduledItem, aw:'ApplicationWindow', today:datetime.date, user_id: Optional[str], machine: str) -> None:
        self.data:ScheduledItem = data
        self.aw = aw
        self.user_id = user_id

        self.today: bool = data.date == today
        self.days_diff = (data.date - today).days
        # my items are all tasks that are explicitly targeting my user and machine
        self.mine: bool = (data.user is not None and user_id is not None and data.user == user_id and
                data.machine is not None and machine != '' and data.machine == machine)
        self.weight_unit_idx = weight_units.index(self.aw.qmc.weight[2])

        self.menu:Optional[QMenu] = None

        super().__init__()
        if not self.is_hidden():
            self.setGraphicsEffect(self.makeShadow())

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.itemMenu)

        self.update_widget()

    def is_hidden(self) -> bool:
        return is_hidden(self.data)

    def set_hidden(self) -> None:
        set_hidden(self.aw.plus_account_id, self.data)

    def visible_filter_on(self) -> bool:
        return self.aw.schedule_visible_filter

    # need to be called if prepared information changes
    def update_widget(self) -> None:
        date_local = self.data.date
        task_date:str = ''
        try:
            if self.days_diff == 0:
                task_date = QApplication.translate('Plus', 'Today')
            elif self.days_diff == 1:
                task_date = QApplication.translate('Plus', 'Tomorrow')
            elif self.days_diff < 7:
                locale = QLocale(self.aw.locale_str)
                task_date = locale.toString(QDate(date_local.year, date_local.month, date_local.day), 'dddd').capitalize()
            else:
                # date formatted according to the locale without the year
                task_date = locale_format_date_no_year(self.aw.locale_str, date_local)
        except Exception as e: # pylint: disable=broad-except
            # if anything goes wrong here we log an exception and use the empty string as task_date
            _log.exception(e)

        user_nickname:Optional[str] = plus.connection.getNickname()
        task_operator = (QApplication.translate('Plus', 'by anybody') if self.data.user is None else
            (f"{QApplication.translate('Plus', 'by')} {(html.escape(user_nickname) if user_nickname is not None else '')}" if self.user_id is not None and self.data.user == self.user_id else
                (f"{QApplication.translate('Plus', 'by')} {html.escape(self.data.nickname)}" if self.data.nickname is not None else
                    (QApplication.translate('Plus', 'by colleague' if self.user_id is not None else '')))))
        task_machine = ('' if self.data.machine is None else f" {QApplication.translate('Plus', 'on')} {html.escape(self.data.machine)}")
        task_operator_and_machine = f'{task_operator}{task_machine}'
        if task_operator_and_machine != '':
            task_operator_and_machine = f', {task_operator_and_machine}'
        nr_roasts_tobedone = self.data.count - len(self.data.roasts)
        prepared = max(0, min(nr_roasts_tobedone, len(get_prepared(self.data))))
        prepared_info = (f", {prepared} { QApplication.translate('Plus', 'prepared')}" if prepared > 0 else '')
        todo = QApplication.translate('Plus', '({} of {} done{})').format(len(self.data.roasts), self.data.count, prepared_info)
        head_line = f'{task_date}{task_operator_and_machine}<br>{todo}'
        wrapper =  textwrap.TextWrapper(width=tooltip_line_length, max_lines=tooltip_max_lines, placeholder=tooltip_placeholder)
        title = '<br>'.join(wrapper.wrap(html.escape(self.data.title)))
        accent_color = (white if self.aw.app.darkmode else plus_blue)
        title_line = f"<p style='white-space:pre'><font color=\"{accent_color}\"><b><big>{title}</big></b></font></p>"
        beans_description = scheduleditem_beans_description(self.weight_unit_idx, self.data)

        detailed_description = f'{head_line}{title_line}{beans_description}'
        # adding a note if any
        if self.data.note is not None:
            detailed_description += f'<hr>{html.escape(self.data.note)}'
        self.setToolTip(detailed_description)

        # colors

        today_text_color = white
        otherday_text_color = dark_white
        open_item_background = super_light_grey
        open_item_background_hover = super_light_grey_hover
        selected_item_color = plus_alt_blue
        selected_item_color_hover = plus_alt_blue_hover
        item_color: str = (dark_grey if self.mine else light_grey)
        item_color_hover: str = (dark_grey_hover if self.mine else light_grey_hover)

        if self.today:
            self.setStyleSheet(
                f'{tooltip_style} DragItem[Selected=true][Hover=false] {{ border:{border_width}px solid {selected_item_color}; background: {selected_item_color}; border-radius: {border_radius}px; }}'
                f'DragItem[Selected=true][Hover=true] {{ border:{border_width}px solid {selected_item_color_hover}; background: {selected_item_color_hover}; border-radius: {border_radius}px; }}'
                f'DragItem[Selected=false][Hover=false] {{ border:{border_width}px solid {item_color}; background: {item_color}; border-radius: {border_radius}px; }}'
                f'DragItem[Selected=false][Hover=true] {{ border:{border_width}px solid {item_color_hover}; background: {item_color_hover}; border-radius: {border_radius}px; }}'
                f'QLabel {{ font-weight: bold; color: {today_text_color}; }}'
                'QElidedLabel { font-weight: normal; }')
        else:
            self.setStyleSheet(
                f'{tooltip_style} DragItem[Selected=true][Hover=false] {{ border:{border_width}px solid {selected_item_color}; background: {open_item_background}; border-radius: {border_radius}px; }}'
                f'DragItem[Selected=true][Hover=true] {{ border:{border_width}px solid {selected_item_color_hover}; background: {open_item_background_hover}; border-radius: {border_radius}px; }}'
                f'DragItem[Selected=false][Hover=false] {{ border:{border_width}px solid {item_color}; background: {open_item_background}; border-radius: {border_radius}px; }}'
                f'DragItem[Selected=false][Hover=true] {{ border:{border_width}px solid {item_color_hover}; background: {open_item_background_hover}; border-radius: {border_radius}px; }}'
                f'QLabel {{ font-weight: bold; color: {otherday_text_color}; }}'
                'QElidedLabel { font-weight: normal; }')

        self.third_label.setText(self.getRight())


    @pyqtSlot()
    def allPrepared(self) -> None:
        set_prepared(self.aw.plus_account_id, self.data)
        self.update_widget()
        self.prepared.emit()

    @pyqtSlot()
    def nonePrepared(self) -> None:
        set_unprepared(self.aw.plus_account_id, self.data)
        self.update_widget()
        self.prepared.emit()

    @pyqtSlot()
    def hideItem(self) -> None:
        set_hidden(self.aw.plus_account_id, self.data)
        self.aw.updateScheduleSignal.emit()

    @pyqtSlot()
    def showItem(self) -> None:
        set_visible(self.aw.plus_account_id, self.data)
        self.aw.updateScheduleSignal.emit()

    def addLoadedProfileToSelectedScheduleItem(self) -> None:
        string = QApplication.translate('Message','Register the currently loaded roast profile<br>in the selected entry.<br>This will overwrite some roast properties.')
        # native dialog
        if platform.system() == 'Darwin':
            mbox = QMessageBox() # only without super this one shows the native dialog on macOS under Qt 6.6.2
            # for native dialogs, text and informativetext need to be plain strings, no RTF incl. HTML instructions like <br>
            mbox.setText(QApplication.translate('Message','Register Roast'))
            mbox.setInformativeText(string.replace('<br>',' '))
            mbox.setWindowModality(Qt.WindowModality.ApplicationModal) # for native dialog it has to be ApplicationModal
            mbox.setStandardButtons(QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Ok)
            mbox.setDefaultButton(QMessageBox.StandardButton.Cancel)
            reply = mbox.exec()
        else:
            # non-native dialog
            reply = QMessageBox.warning(None, #self, # only without super this one shows the native dialog on macOS under Qt 6.6.2 and later
                            QApplication.translate('Message','Register Roast'),string,
                            QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Cancel)

        if reply == QMessageBox.StandardButton.Ok :
            self.registerRoast.emit()


    def itemMenu(self) -> None:
        self.menu = QMenu()
        if not fully_prepared(self.data):
            allPreparedAction:QAction = QAction(QApplication.translate('Contextual Menu', 'All batches prepared'),self)
            allPreparedAction.triggered.connect(self.allPrepared)
            self.menu.addAction(allPreparedAction)
        if not fully_unprepared(self.data):
            nonePreparedAction:QAction = QAction(QApplication.translate('Contextual Menu', 'No batch prepared'),self)
            nonePreparedAction.triggered.connect(self.nonePrepared)
            self.menu.addAction(nonePreparedAction)
        if not self.aw.qmc.flagon and self.aw.curFile is not None and self.aw.qmc.scheduleID is None and self.aw.qmc.roastUUID is not None  and \
                self.aw.schedule_window is not None and \
                not self.aw.schedule_window.in_completed(self.aw.qmc.roastUUID) and \
                self.aw.qmc.roastdate.date().toPyDate() >= self.aw.schedule_window.prev_roast_session_data():
            # if not sampling and a profile without scheduleID loaded which is not yet registered as completed roast,
            # and roast date is not before the last roast session
            # we allow to assign the current profile to the selected schedule item
            # NOTE: that in contrast to the automatic assignment which does not allow incomplete roasts without a DROP to be registered
            #   to prevent recorded snippet to confuse the roast session,
            #   a roast without DROP can still be registered manually
            addToItemAction:QAction = QAction(QApplication.translate('Contextual Menu', 'Register roast'),self)
            addToItemAction.triggered.connect(self.addLoadedProfileToSelectedScheduleItem)
            self.menu.addAction(addToItemAction)
        if is_hidden(self.data):
            showaction:QAction = QAction(QApplication.translate('Contextual Menu', 'Show'),self)
            showaction.triggered.connect(self.showItem)
            self.menu.addAction(showaction)
        else:
            hideAction:QAction = QAction(QApplication.translate('Contextual Menu', 'Hide'),self)
            hideAction.triggered.connect(self.hideItem)
            self.menu.addAction(hideAction)
        self.menu.popup(QCursor.pos())


    def getLeft(self) -> str:
        return f'{max(0,self.data.count - len(self.data.roasts))}x'


    def getMiddle(self) -> str:
        return self.data.title


    def getRight(self) -> str:
        mark = '\u26AB '
        return f"{(mark if fully_prepared(self.data) else '')}{render_weight(self.data.weight, 1, self.weight_unit_idx)}"


    def mouseMoveEvent(self, e:'Optional[QMouseEvent]') -> None:
        super().mouseMoveEvent(e)
        if e is not None and e.buttons() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            drag.setMimeData(mime)

            self.setGraphicsEffect(None)
            # Render at x2 pixel ratio to avoid blur on Retina screens.
            pixmap = QPixmap(self.size().width() * 2, self.size().height() * 2)
            pixmap.setDevicePixelRatio(2)
            self.render(pixmap)
            drag.setPixmap(pixmap)
            if not is_hidden(self.data):
                self.setGraphicsEffect(self.makeShadow())
            drag.exec(Qt.DropAction.MoveAction)


    def select(self, aw:'ApplicationWindow', load_template:bool=True) -> None:
        self.setProperty('Selected', True)
        self.setStyle(self.style())
        if load_template:
            self.load_template(aw)


    def load_template(self, aw:'ApplicationWindow') -> None:
        if self.data.template is not None and aw.curFile is None and aw.qmc.timeindex[6] == 0:
            # if template is set and no profile is loaded and DROP is not set we load the template
            uuid:str = self.data.template.hex
            QTimer.singleShot(500, lambda : aw.loadAndRedrawBackgroundUUID(UUID = uuid, force_reload=False))


    def deselect(self) -> None:
        self.setProperty('Selected', False)
        self.setStyle(self.style())



class BaseWidget(QWidget): # pyright: ignore[reportGeneralTypeIssues] # Argument to class must be a base class
    """Widget list
    """
    def __init__(self, parent:Optional[QWidget] = None, orientation:Qt.Orientation = Qt.Orientation.Vertical) -> None:
        super().__init__(parent)
        # Store the orientation for drag checks later.
        self.orientation = orientation
        self.blayout:QBoxLayout
        if self.orientation == Qt.Orientation.Vertical:
            self.blayout = QVBoxLayout()
        else:
            self.blayout = QHBoxLayout()
        self.blayout.setContentsMargins(7, 7, 7, 7)
        self.blayout.setSpacing(10)
        self.setLayout(self.blayout)


    def clearItems(self) -> None:
        try: # self.blayout.count() fails if self.blayout does not contain any widget
            while self.blayout.count():
                child = self.blayout.takeAt(0)
                if child is not None:
                    widget = child.widget()
                    if widget is not None:
                        widget.setParent(None)
                        widget.deleteLater()
        except Exception: # pylint: disable=broad-except
            pass


    def count(self) -> int:
        return self.blayout.count()


    # returns -1 if not found
    def indexOf(self, widget:'QWidget') -> int:
        return self.blayout.indexOf(widget)


    def itemAt(self, i:int) -> Optional[StandardItem]:
        item:Optional[QLayoutItem] = self.blayout.itemAt(i)
        if item is not None:
            return cast(StandardItem, item.widget())
        return None



class StandardWidget(BaseWidget):
    def __init__(self, parent:Optional[QWidget] = None, orientation:Qt.Orientation = Qt.Orientation.Vertical) -> None:
        super().__init__(parent, orientation)
        self.blayout.setSpacing(5)


    def get_items(self) -> List[NoDragItem]:
        items:List[NoDragItem] = []
        for n in range(self.blayout.count()):
            li:Optional[QLayoutItem] = self.blayout.itemAt(n)
            if li is not None:
                w:Optional[QWidget] = li.widget()
                if w is not None and isinstance(w, NoDragItem):
                    # the target indicator is ignored
                    items.append(w)
        return items


    def add_item(self, item:NoDragItem) -> None:
        self.blayout.addWidget(item)



class DragWidget(BaseWidget):
    """Widget list allowing sorting via drag-and-drop.
    """

    orderChanged = pyqtSignal(list)

    def __init__(self, parent:Optional[QWidget] = None, orientation:Qt.Orientation = Qt.Orientation.Vertical) -> None:
        super().__init__(parent, orientation)
        self.setAcceptDrops(True)

        # Add the drag target indicator. This is invisible by default,
        # we show it and move it around while the drag is active.
        self._drag_target_indicator = DragTargetIndicator()
        self.blayout.addWidget(self._drag_target_indicator)
        self._drag_target_indicator.hide()
        self.drag_source:Optional[QObject] = None


    def dragEnterEvent(self, e:'Optional[QDragEnterEvent]') -> None: # pylint: disable=no-self-argument,no-self-use
        if e is not None:
            self.drag_source = e.source()
            e.accept()


    def dragLeaveEvent(self, e:'Optional[QDragLeaveEvent]') -> None:
        if e is not None:
            try:
                if self.drag_source is not None:
                    widget:Optional[QObject] = self.drag_source
                    if widget is not None and isinstance(widget, DragItem):
                        # Use drop target location for destination, then remove it.
                        self._drag_target_indicator.hide()
                        if not widget.is_hidden():
                            # we mark the underlying ScheduleItem as hidden
                            widget.set_hidden()
                        if not widget.visible_filter_on():
                            # as hidden items are not filtered out we have to put that item back
                            index = self.blayout.indexOf(self._drag_target_indicator)
                            if index is not None:
                                self.blayout.insertWidget(index, widget) # pyright:ignore[reportArgumentType]
                                self.orderChanged.emit(self.get_item_data())
                                widget.show() # pyright:ignore[reportAttributeAccessIssue]
                                self.blayout.activate()

            except Exception:   # pylint: disable=broad-except
                # wrapped C/C++ objects might have been deleted due to a complete redraw of the widget via updateScheduleWindow()
                pass
            e.accept()


    def dragMoveEvent(self, e:'Optional[QDragMoveEvent]') -> None:
        if e is not None:
            try:
                # Find the correct location of the drop target, so we can move it there.
                index = self._find_drop_location(e)
                if index is not None:
                    # Inserting moves the item if its alreaady in the layout.
                    self.blayout.insertWidget(index, self._drag_target_indicator)
                    # Hide the item being dragged.
                    source:Optional[QObject] = e.source()
                    if source is not None and isinstance(source, QWidget):
                        source.hide() # pyright:ignore[reportAttributeAccessIssue]
                    # Show the target.
                    self._drag_target_indicator.show()
            except Exception:   # pylint: disable=broad-except
                # wrapped C/C++ objects might have been deleted due to a complete redraw of the widget via updateScheduleWindow()
                pass
            e.accept()


    def dropEvent(self, e:'Optional[QDropEvent]') -> None:
        if e is not None and e.source() is not None:
            try:
                widget:Optional[QObject] = e.source()
                if widget is not None and isinstance(widget, QWidget):
                    # Use drop target location for destination, then remove it.
                    self._drag_target_indicator.hide()
                    index = self.blayout.indexOf(self._drag_target_indicator)
                    if index is not None:
                        self.blayout.insertWidget(index, widget) # pyright:ignore[reportArgumentType]
                        self.orderChanged.emit(self.get_item_data())
                        widget.show() # pyright:ignore[reportAttributeAccessIssue]
                        self.blayout.activate()
            except Exception:   # pylint: disable=broad-except
                # wrapped C/C++ objects might have been deleted due to a complete redraw of the widget via updateScheduleWindow()
                pass
            e.accept()


    def _find_drop_location(self, e:'QDragMoveEvent') -> int:
        try:
            pos = e.position()
        except Exception:   # pylint: disable=broad-except
            pos = e.posF() # type:ignore[attr-defined]
        spacing = self.blayout.spacing() / 2

        n = 0
        for n in range(self.blayout.count()):
            # Get the widget at each index in turn.
            layoutItem:Optional[QLayoutItem] = self.blayout.itemAt(n)
            if layoutItem is not None:
                w:Optional[QWidget] = layoutItem.widget()
                if w is not None:
                    if self.orientation == Qt.Orientation.Vertical:
                        # Drag drop vertically.
                        drop_here = (
                            pos.y() >= w.y() - spacing
                            and pos.y() <= w.y() + w.size().height() + spacing
                        )
                    else:
                        # Drag drop horizontally.
                        drop_here = (
                            pos.x() >= w.x() - spacing
                            and pos.x() <= w.x() + w.size().width() + spacing
                        )

                    if drop_here:
                        # Drop over this target.
                        break
        return n


    def clearItems(self) -> None:
        while self.blayout.count():
            child = self.blayout.takeAt(0)
            if child is not None:
                widget = child.widget()
                if widget is not None and widget != self._drag_target_indicator:
                    widget.setParent(None)
                    widget.deleteLater()


    def add_item(self, item:DragItem) -> None:
        self.blayout.addWidget(item)


    def itemAt(self, i:int) -> Optional[DragItem]:
        item:Optional[QLayoutItem] = self.blayout.itemAt(i)
        if item is not None:
            return cast(DragItem, item.widget())
        return None


    def get_items(self) -> List[DragItem]:
        items:List[DragItem] = []
        for n in range(self.blayout.count()):
            li:Optional[QLayoutItem] = self.blayout.itemAt(n)
            if li is not None:
                w:Optional[QWidget] = li.widget()
                if w is not None and w != self._drag_target_indicator and isinstance(w, DragItem):
                    # the target indicator is ignored
                    items.append(w)
        return items


    def get_item_data(self) -> List[ScheduledItem]:
        return [item.data for item in self.get_items()]


class ScheduleWindow(ArtisanResizeablDialog): # pyright:ignore[reportGeneralTypeIssues]

    register_completed_roast = pyqtSignal()

    def __init__(self, parent:'QWidget', aw:'ApplicationWindow', activeTab:int = 0) -> None:
        if aw.get_os()[0] == 'RPi':
            super().__init__(None, aw) # set the parent to None to make Schedule windows on RPi Bookworm non-modal (not blocking the main window)
        else:
            super().__init__(parent, aw) # if parent is set to None, Schedule panels hide behind the main window in full screen mode on Windows!

        self.aw = aw # the Artisan application window
        self.activeTab:int = activeTab

        self.scheduled_items:List[ScheduledItem] = []
        self.completed_items:List[CompletedItem] = [] # kept sorted; oldest roasts at begin, youngest appended at the end

        # holds the currently selected remaining DragItem widget if any
        self.selected_remaining_item:Optional[DragItem] = None

        # holds the currently selected completed NoDragItem widget if any
        self.selected_completed_item:Optional[NoDragItem] = None

        # IMPORTANT NOTE: if dialog items have to be access after it has been closed, this Qt.WidgetAttribute.WA_DeleteOnClose attribute
        # has to be set to False explicitly in its initializer (like in comportDlg) to avoid the early GC and one might
        # want to use a dialog.deleteLater() call to explicitly have the dialog and its widgets GCe
        # or rather use sip.delete(dialog) if the GC via .deleteLater() is prevented by a link to a parent object (parent not None)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)

        self.drag_remaining = DragWidget(self, orientation=Qt.Orientation.Vertical)
        self.drag_remaining.setContentsMargins(0, 0, 0, 0)

        self.drag_remaining.orderChanged.connect(self.update_order)

        remaining_widget = QWidget()
        layout_remaining = QVBoxLayout()
        layout_remaining.addWidget(self.drag_remaining)
        layout_remaining.addStretch()
        layout_remaining.setContentsMargins(0, 0, 0, 0)
        remaining_widget.setLayout(layout_remaining)
        remaining_widget.setContentsMargins(0, 0, 0, 0)


        self.visible_filter = QCheckBox(QApplication.translate('Plus','Visible'))
        self.visible_filter.setChecked(self.aw.schedule_visible_filter)
        self.visible_filter.setToolTip(QApplication.translate('Plus','List only visible items'))
        self.visible_filter.stateChanged.connect(self.remainingFilterChanged)
        self.day_filter = QCheckBox(QApplication.translate('Plus','Today'))
        self.day_filter.setChecked(self.aw.schedule_day_filter)
        self.day_filter.stateChanged.connect(self.remainingFilterChanged)
        self.day_filter.setToolTip(QApplication.translate('Plus','List only items scheduled for today'))
        self.user_filter = QCheckBox()
        self.user_filter.setChecked(self.aw.schedule_user_filter)
        self.user_filter.stateChanged.connect(self.remainingFilterChanged)
        self.machine_filter = QCheckBox()
        self.machine_filter.setChecked(self.aw.schedule_machine_filter)
        self.machine_filter.stateChanged.connect(self.remainingFilterChanged)

        remaining_filter_layout = QVBoxLayout()
        remaining_filter_layout.addWidget(self.visible_filter)
        remaining_filter_layout.addWidget(self.day_filter)
        remaining_filter_layout.addWidget(self.user_filter)
        remaining_filter_layout.addWidget(self.machine_filter)
        self.remaining_filter_group = QGroupBox(QApplication.translate('Plus', 'Filters'))
        self.remaining_filter_group.setLayout(remaining_filter_layout)

        self.remaining_scrollarea = QScrollArea()
        self.remaining_scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.remaining_scrollarea.setWidgetResizable(True)
        self.remaining_scrollarea.setWidget(remaining_widget)
        self.remaining_scrollarea.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
#        self.remaining_scrollarea.setMinimumWidth(remaining_widget.minimumSizeHint().width())

        self.remaining_filter_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        self.remaining_message = QLabel()
        self.remaining_message.setTextFormat(Qt.TextFormat.RichText)
        self.remaining_message.setWordWrap(True)
        self.remaining_message.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse)
        self.remaining_message.setOpenExternalLinks(True)

        remaining_message_layout = QVBoxLayout()
        remaining_message_layout.addWidget(self.remaining_message)
        remaining_message_layout.setContentsMargins(15, 15, 15, 15) # left, top, right, bottom

        self.remaining_message_widget = QWidget()
        self.remaining_message_widget.setLayout(remaining_message_layout)

        self.stacked_remaining_widget = QStackedWidget()
        self.stacked_remaining_widget.addWidget(self.remaining_scrollarea)
        self.stacked_remaining_widget.addWidget(self.remaining_message_widget)

        remaining_filter_layout2 =  QVBoxLayout()
        remaining_filter_layout2.addSpacing(1) # ensures a minimum height to keep the handle movable
        remaining_filter_layout2.addWidget(self.remaining_filter_group)
        remaining_filter_layout2.setContentsMargins(2, 10, 2, 2) # left, top, right, bottom # NOTE: if top is reduced to 2, on macOS the spacing of the single filters gets too small
        remaining_filter_group2 = QFrame()
        remaining_filter_group2.setLayout(remaining_filter_layout2)
        self.remaining_filter_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        remaining_filter_group2.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        self.remaining_splitter = Splitter(Qt.Orientation.Vertical)
        self.remaining_splitter.addWidget(self.stacked_remaining_widget)
        self.remaining_splitter.addWidget(remaining_filter_group2)
        self.remaining_splitter.setSizes([100,0]) # the filter section is hidden by default and its position is not remembered


        if not self.aw.scheduler_completed_details_visible:
            self.remaining_filter_group.hide()
        self.filter_frame_hide = False

#####
        self.nodrag_roasted = StandardWidget(self, orientation=Qt.Orientation.Vertical)
        self.nodrag_roasted.setContentsMargins(0, 0, 0, 0)

        roasted_widget = QWidget()
        layout_roasted = QVBoxLayout()
        layout_roasted.addWidget(self.nodrag_roasted)
        layout_roasted.addStretch()
        layout_roasted.setContentsMargins(0, 0, 0, 0)
        roasted_widget.setLayout(layout_roasted)
        roasted_widget.setContentsMargins(0, 0, 0, 0)

        completed_scrollarea = QScrollArea()
        completed_scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        completed_scrollarea.setWidgetResizable(True)
        completed_scrollarea.setWidget(roasted_widget)
        completed_scrollarea.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
#        completed_scrollarea.setFrameShadow(QFrame.Shadow.Sunken)
#        completed_scrollarea.setFrameShape(QFrame.Shape.Panel)
        completed_scrollarea.setMinimumWidth(roasted_widget.minimumSizeHint().width())

        weight_unit_str:str = self.aw.qmc.weight[2].lower()
        density_unit_str:Final[str] = 'g/l'
        moisture_unit_str:Final[str] = '%'
        color_unit_str:Final[str] = '#'

        self.roasted_weight = ClickableQLineEdit()
        self.roasted_weight.setToolTip(QApplication.translate('Label','Weight'))
        self.roasted_weight.setValidator(self.aw.createCLocaleDoubleValidator(0., 9999999., 4, self.roasted_weight, ''))
        self.roasted_weight.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.roasted_weight.editingFinished.connect(self.roasted_weight_changed)
        self.roasted_weight.receivedFocus.connect(self.roasted_weight_selected)
        self.roasted_weight_suffix = ClickableQLabel(weight_unit_str)

        font = self.roasted_weight_suffix.font()
        fontMetrics = QFontMetrics(font)
        weight_density_suffix_width = max(fontMetrics.horizontalAdvance(weight_unit_str), fontMetrics.horizontalAdvance(density_unit_str))
        color_moisture_suffix_width = max(fontMetrics.horizontalAdvance(moisture_unit_str), fontMetrics.horizontalAdvance(color_unit_str))

        self.roasted_weight_suffix.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.roasted_weight_suffix.setFixedWidth(weight_density_suffix_width)
        self.roasted_weight_suffix.setAlignment (Qt.AlignmentFlag.AlignLeft)
        self.roasted_weight_suffix.clicked.connect(self.roasted_measured_toggle)

        self.roasted_density = QLineEdit()
        self.roasted_density.setToolTip(QApplication.translate('Label','Density'))
        self.roasted_density.setValidator(self.aw.createCLocaleDoubleValidator(0., 999., 1, self.roasted_density))
        self.roasted_density.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.roasted_density.editingFinished.connect(self.roasted_density_changed)
        roasted_density_suffix = QLabel(density_unit_str)
        roasted_density_suffix.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        roasted_density_suffix.setFixedWidth(weight_density_suffix_width)
        roasted_density_suffix.setAlignment (Qt.AlignmentFlag.AlignLeft)

        self.roasted_color = QLineEdit()
        self.roasted_color.setToolTip(QApplication.translate('Label','Color'))
        self.roasted_color.setValidator(self.aw.createCLocaleDoubleValidator(0., 255., 2, self.roasted_color))
        self.roasted_color.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.roasted_color.editingFinished.connect(self.roasted_color_changed)
        roasted_color_suffix = QLabel(color_unit_str)
        roasted_color_suffix.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        roasted_color_suffix.setFixedWidth(color_moisture_suffix_width)
        roasted_color_suffix.setAlignment (Qt.AlignmentFlag.AlignLeft)

        self.roasted_moisture = QLineEdit()
        self.roasted_moisture.setToolTip(QApplication.translate('Label','Moisture'))
        self.roasted_moisture.setValidator(self.aw.createCLocaleDoubleValidator(0., 100., 1, self.roasted_moisture))
        self.roasted_moisture.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.roasted_moisture.editingFinished.connect(self.roasted_moisture_changed)

        roasted_moisture_suffix = QLabel(moisture_unit_str)
        roasted_moisture_suffix.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        roasted_moisture_suffix.setFixedWidth(color_moisture_suffix_width)
        roasted_moisture_suffix.setAlignment (Qt.AlignmentFlag.AlignLeft)

        self.roasted_notes = QPlainTextEdit()
        self.roasted_notes.setPlaceholderText(QApplication.translate('Label', 'Roasting Notes'))
        self.roasted_notes.setToolTip(QApplication.translate('Label', 'Roasting Notes'))

        self.cupping_score = QLineEdit()
        self.cupping_score.setFixedWidth(42)
        self.cupping_score.setPlaceholderText(QApplication.translate('Label', 'Score'))
        self.cupping_score.setToolTip(QApplication.translate('Label','Cupping Score'))
        self.cupping_score.setValidator(self.aw.createCLocaleDoubleValidator(0., 100., 2, self.cupping_score))
        self.cupping_score.setAlignment(Qt.AlignmentFlag.AlignCenter) #Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.cupping_score.editingFinished.connect(self.cupping_score_changed)

        self.cupping_notes = QPlainTextEdit()
        self.cupping_notes.setPlaceholderText(QApplication.translate('Label', 'Cupping Notes'))
        self.cupping_notes.setToolTip(QApplication.translate('Label', 'Cupping Notes'))

        roasted_first_line_layout = QHBoxLayout()
        roasted_first_line_layout.setSpacing(0)
        roasted_first_line_layout.addWidget(self.roasted_weight)
        roasted_first_line_layout.addSpacing(2)
        roasted_first_line_layout.addWidget(self.roasted_weight_suffix)
        roasted_first_line_layout.addSpacing(10)
        roasted_first_line_layout.addWidget(self.roasted_color)
        roasted_first_line_layout.addSpacing(2)
        roasted_first_line_layout.addWidget(roasted_color_suffix)
        roasted_first_line_layout.setContentsMargins(0, 0, 0, 0)
        roasted_second_line_layout = QHBoxLayout()
        roasted_second_line_layout.setSpacing(0)
        roasted_second_line_layout.addWidget(self.roasted_density)
        roasted_second_line_layout.addSpacing(2)
        roasted_second_line_layout.addWidget(roasted_density_suffix)
        roasted_second_line_layout.addSpacing(10)
        roasted_second_line_layout.addWidget(self.roasted_moisture)
        roasted_second_line_layout.addSpacing(2)
        roasted_second_line_layout.addWidget(roasted_moisture_suffix)
        roasted_second_line_layout.setContentsMargins(0, 0, 0, 0)
        roasted_details_layout = QVBoxLayout()
        roasted_details_layout.addLayout(roasted_first_line_layout)
        roasted_details_layout.addLayout(roasted_second_line_layout)
        roasted_details_layout.setContentsMargins(0, 0, 0, 0)


        # restrict notes field height to two text lines
        lines:int = 2
        docMargin:float = 0
        lineSpacing:float = 1.5

        roasted_notes_doc:Optional[QTextDocument] = self.roasted_notes.document()
        if roasted_notes_doc is not None:
            docMargin = roasted_notes_doc.documentMargin()
            font = roasted_notes_doc.defaultFont()
            fontMetrics = QFontMetrics(font)
            lineSpacing = fontMetrics.lineSpacing()
        margins:QMargins = self.roasted_notes.contentsMargins()
        notes_hight:int = math.ceil(lineSpacing * lines +
            (docMargin + self.roasted_notes.frameWidth()) * 2 + margins.top() + margins.bottom())
        self.roasted_notes.setFixedHeight(notes_hight)
        self.roasted_notes.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.roasted_notes.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.roasted_notes.setContentsMargins(0, 0, 0, 0)

        cupping_notes_doc:Optional[QTextDocument] = self.cupping_notes.document()
        if cupping_notes_doc is not None:
            docMargin = cupping_notes_doc.documentMargin()
            font = cupping_notes_doc.defaultFont()
            fontMetrics = QFontMetrics(font)
            lineSpacing = fontMetrics.lineSpacing()
        margins = self.cupping_notes.contentsMargins()
        cupping_notes_hight:int = math.ceil(lineSpacing * lines +
            (docMargin + self.cupping_notes.frameWidth()) * 2 + margins.top() + margins.bottom())
        self.cupping_notes.setFixedHeight(cupping_notes_hight)
        self.cupping_notes.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.cupping_notes.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.cupping_notes.setContentsMargins(0, 0, 0, 0)

        cupping_layout = QHBoxLayout()
        cupping_layout.addWidget(self.cupping_score)
        cupping_layout.addWidget(self.cupping_notes)

        completed_details_layout = QVBoxLayout()
        completed_details_layout.addLayout(roasted_details_layout)
        completed_details_layout.addWidget(self.roasted_notes)
        completed_details_layout.addLayout(cupping_layout)
        completed_details_layout.setContentsMargins(0, 0, 0, 0)
        completed_details_layout.setSpacing(3)
        self.completed_details_group = QGroupBox(QApplication.translate('Label','Roasted'))
        self.completed_details_group.setLayout(completed_details_layout)
        self.completed_details_group.setEnabled(False)

        self.completed_details_scrollarea = QScrollArea()
        self.completed_details_scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.completed_details_scrollarea.setWidgetResizable(True)
        self.completed_details_scrollarea.setWidget(self.completed_details_group)
        self.completed_details_scrollarea.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        completed_details_layout2 =  QVBoxLayout()
        completed_details_layout2.addSpacing(1) # ensures a minimum height to keep the handle movable
        completed_details_layout2.addWidget(self.completed_details_scrollarea)
        completed_details_layout2.setSpacing(0)
        completed_details_layout2.setContentsMargins(0, 0, 0, 0) # left, top, right, bottom
        self.completed_frame = QFrame()
        self.completed_frame.setLayout(completed_details_layout2)
        self.completed_frame.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        self.completed_splitter = Splitter(Qt.Orientation.Vertical)
        self.completed_splitter.addWidget(completed_scrollarea)
        self.completed_splitter.addWidget(self.completed_frame)
        self.completed_splitter.setSizes([100,0])
        self.completed_splitter_open_height: int = 0

        if not self.aw.scheduler_filters_visible:
            self.completed_details_scrollarea.hide()
        self.completed_details_scrollarea_hide = False

        completed_message = QLabel(f"{QApplication.translate('Plus', 'No completed roasts')}<br>")
        completed_message.setWordWrap(True)

        completed_message_layout = QVBoxLayout()
        completed_message_layout.addWidget(completed_message)
        completed_message_layout.setContentsMargins(15, 15, 15, 15) # left, top, right, bottom

        self.completed_message_widget = QWidget()
        self.completed_message_widget.setLayout(completed_message_layout)

        self.completed_stacked_widget = QStackedWidget()
        self.completed_stacked_widget.addWidget(self.completed_splitter)
        self.completed_stacked_widget.addWidget(self.completed_message_widget)

#####

        self.TabWidget = QTabWidget()
        self.TabWidget.addTab(self.remaining_splitter, QApplication.translate('Tab', 'To-Do'))
        self.TabWidget.addTab(self.completed_stacked_widget, QApplication.translate('Tab', 'Completed'))
        self.TabWidget.setStyleSheet(tooltip_style)

        self.task_type = QLabel()
        self.task_position = QLabel('2/5')
        self.task_weight = ClickableQLabel()
        self.task_title = QElidedLabel(mode = Qt.TextElideMode.ElideRight)

        task_type_layout = QHBoxLayout()
        task_type_layout.addWidget(self.task_position)
        task_type_layout.addStretch()
        task_type_layout.addWidget(self.task_type)
        task_type_layout.setSpacing(0)
        task_type_layout.setContentsMargins(0, 0, 0, 0) # left, top, right, bottom

        task_weight_layout = QHBoxLayout()
        task_weight_layout.addStretch()
        task_weight_layout.addWidget(self.task_weight)
        task_weight_layout.addStretch()
        task_weight_layout.setSpacing(0)
        task_weight_layout.setContentsMargins(0, 0, 0, 0) # left, top, right, bottom

        task_title_layout = QHBoxLayout()
        task_title_layout.addWidget(self.task_title)
        task_title_layout.setSpacing(0)
        task_title_layout.setContentsMargins(0, 5, 5, 0) # left, top, right, bottom

        task_layout =  QVBoxLayout()
        task_layout.addLayout(task_type_layout)
        task_layout.addLayout(task_weight_layout)
        task_layout.addLayout(task_title_layout)
        task_layout.setSpacing(0)
        task_layout.setContentsMargins(10, 5, 10, 15) # left, top, right, bottom
        self.task_frame = QFrame()
        self.task_frame.setLayout(task_layout)
        self.task_frame.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)


        task2_layout =  QVBoxLayout()
        task2_layout.addWidget(self.task_frame)
        task2_layout.addSpacing(1) # ensures a minimum height to keep the handle movable
        task2_layout.setSpacing(0)
        task2_layout.setContentsMargins(0, 0, 0, 0) # left, top, right, bottom
        self.task2_frame = QFrame()
        self.task2_frame.setLayout(task2_layout)
        self.task2_frame.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        self.main_splitter = Splitter(Qt.Orientation.Vertical)
        self.main_splitter.addWidget(self.task2_frame)
        self.main_splitter.addWidget(self.TabWidget)
#        self.main_splitter.setSizes([0,100])
        self.main_splitter.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        if not self.aw.scheduler_tasks_visible:
            self.task_frame.hide()
        self.task_frame_hide = False # flag used by mainSplitterMoved()/hide_task_frame() to hide task frame again after closing the drawer


        disconnected_widget = QLabel()
        disconnected_widget.setTextFormat(Qt.TextFormat.RichText)
        disconnected_widget.setText(QApplication.translate('Plus', 'Login to {} to receive your roast schedule').format(f'<a href="{plusLink()}">{plus.config.app_name}</a>'))
        disconnected_widget.setWordWrap(True)
        disconnected_widget.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        disconnected_widget.linkActivated.connect(self.disconnected_link_handler)

        disconnected_layout = QVBoxLayout()
        disconnected_layout.addWidget(disconnected_widget)
        disconnected_layout.setContentsMargins(15, 15, 15, 15) # left, top, right, bottom

        self.message_widget = QWidget()
        self.message_widget.setLayout(disconnected_layout)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self.main_splitter)
        self.stacked_widget.addWidget(self.message_widget)

        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.stacked_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0) # left, top, right, bottom

#        self.setMinimumWidth(175)

        self.setLayout(self.main_layout)


        # we want minimize and close buttons, but no maximize buttons
        if not platform.system().startswith('Windows'):
            windowFlags = self.windowFlags()
            windowFlags |= Qt.WindowType.Tool
            windowFlags |= Qt.WindowType.CustomizeWindowHint # needed to be able to customize the close/min/max controls (at least on macOS)
            windowFlags |= Qt.WindowType.WindowMinimizeButtonHint
            windowFlags |= Qt.WindowType.WindowCloseButtonHint # not needed on macOS, but maybe on Linux
            #windowFlags |= Qt.WindowType.WindowMinMaxButtonsHint # not needed on macOS
            #windowFlags &= ~Qt.WindowType.WindowMaximizeButtonHint # not needed on macOS as the CustomizeWindowHint is removing min/max controls already
            self.setWindowFlags(windowFlags)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)

        if platform.system() == 'Darwin':
            self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow) # show tool window even if app is in background (see https://bugreports.qt.io/browse/QTBUG-57581)

        self.setWindowTitle(QApplication.translate('Menu', 'Schedule'))

        self.aw.disconnectPlusSignal.connect(self.updateScheduleWindow)

        self.weight_item_display:WeightItemDisplay = WeightItemDisplay(self)
        self.weight_manager:WeightManager = WeightManager([self.weight_item_display])

        plus.stock.update() # explicit update stock on opening the scheduler
        self.updateScheduleWindow()

        # set all child's to NoFocus to receive the up/down arrow key events in keyPressEvent
        self.setChildrenFocusPolicy(self, Qt.FocusPolicy.NoFocus)

        self.register_completed_roast.connect(self.register_completed_roast_slot)


        # a click to the weight in the task display completes it
        self.task_weight.clicked.connect(self.taskCompleted)

        self.TabWidget.currentChanged.connect(self.tabSwitched)

        # we set the active tab with a QTimer after the tabbar has been rendered once, as otherwise
        # some tabs are not rendered at all on Windows using Qt v6.5.1 (https://bugreports.qt.io/projects/QTBUG/issues/QTBUG-114204?filter=allissues)
        QTimer.singleShot(50, self.setActiveTab)

        if self.activeTab == 0:
            # no tabswitch will be triggered, thus we need to "manually" set the next weight item
            self.set_next()

        settings = QSettings()
        if settings.contains('ScheduleGeometry'):
            self.restoreGeometry(settings.value('ScheduleGeometry'))
        else:
            self.resize(250,300)


        settings = QSettings()
        if settings.contains('ScheduleMainSplitter'):
            self.main_splitter.restoreState(settings.value('ScheduleMainSplitter'))
        if settings.contains('ScheduleRemainingSplitter') and settings.contains('ScheduleRemainingSplitterOpen'):
            if settings.value('ScheduleRemainingSplitterOpen'):
                self.remaining_filter_group.show()
            else:
                self.remaining_filter_group.hide()
            self.remaining_splitter.restoreState(settings.value('ScheduleRemainingSplitter'))
        if settings.contains('ScheduleCompletedSplitter') and settings.contains('ScheduleCompletedSplitterOpen'):
            if settings.value('ScheduleCompletedSplitterOpen'):
                self.completed_details_scrollarea.show()
            else:
                self.completed_details_scrollarea.hide()
            self.completed_splitter.restoreState(settings.value('ScheduleCompletedSplitter'))

        self.main_splitter.splitterMoved.connect(self.mainSplitterMoved)
        self.remaining_splitter.splitterMoved.connect(self.remainingSplitterMoved)
        self.completed_splitter.splitterMoved.connect(self.completedSplitterMoved)

        self.aw.sendmessage(QApplication.translate('Message','Scheduler started'))

    def hide_task_frame(self) -> None:
        if self.task_frame_hide:
            splitter_sizes = self.main_splitter.sizes()
            if len(splitter_sizes)>0 and splitter_sizes[0] == 0:
                self.task_frame.hide()
            self.task_frame_hide = False

    @pyqtSlot(int,int)
    def mainSplitterMoved(self, _pos: int, index: int) -> None:
        splitter_sizes = self.main_splitter.sizes()
        if len(splitter_sizes)>1:
            # hide upper splitter content to allow minimizing the window
            if index == 1 and splitter_sizes[0] > 0 and not self.task_frame.isVisible() and not self.task_frame_hide:
                self.setUpdatesEnabled(False)
                self.task_frame.show()
                self.main_splitter.setSizes([0, splitter_sizes[0]+splitter_sizes[1]])
                self.setUpdatesEnabled(True)
            elif index == 1 and splitter_sizes[0] == 0 and self.task_frame.isVisible():
                if not self.task_frame_hide:
                    self.task_frame_hide = True
                    QTimer.singleShot(1000, self.hide_task_frame)

    def hide_filter_frame(self) -> None:
        if self.filter_frame_hide:
            splitter_sizes = self.remaining_splitter.sizes()
            if len(splitter_sizes)>0 and splitter_sizes[1] == 0:
                self.remaining_filter_group.hide()
            self.filter_frame_hide = False

    @pyqtSlot(int,int)
    def remainingSplitterMoved(self, _pos: int, index: int) -> None:
        splitter_sizes = self.remaining_splitter.sizes()
        if len(splitter_sizes)>1:
            # hide lower splitter content to allow minimizing the window
            if index == 1 and splitter_sizes[1] > 0 and not self.remaining_filter_group.isVisible() and not self.filter_frame_hide:
                self.setUpdatesEnabled(False)
                self.remaining_filter_group.show()
                self.remaining_splitter.setSizes([splitter_sizes[0]+splitter_sizes[1], 0])
                self.setUpdatesEnabled(True)
            elif index == 1 and splitter_sizes[1] == 0 and self.remaining_filter_group.isVisible():
                if not self.filter_frame_hide:
                    self.filter_frame_hide = True
                    QTimer.singleShot(1000, self.hide_filter_frame)

    def hide_completed_frame(self) -> None:
        if self.completed_details_scrollarea_hide:
            splitter_sizes = self.completed_splitter.sizes()
            if len(splitter_sizes)>0 and splitter_sizes[1] == 0:
                self.completed_details_scrollarea.hide()
            self.completed_details_scrollarea_hide = False

    @pyqtSlot(int,int)
    def completedSplitterMoved(self, _pos: int, index: int) -> None:
        splitter_sizes = self.completed_splitter.sizes()
        if len(splitter_sizes)>1:
            # hide lower completed splitter content to allow minimizing the window
            if index == 1 and splitter_sizes[1] > 0 and not self.completed_details_scrollarea.isVisible() and not self.completed_details_scrollarea_hide:
                self.setUpdatesEnabled(False)
                self.completed_details_scrollarea.show()
                self.completed_splitter.setSizes([splitter_sizes[0]+splitter_sizes[1], 0])
                self.setUpdatesEnabled(True)
            elif index == 1 and splitter_sizes[1] == 0 and self.completed_details_scrollarea.isVisible():
                if not self.completed_details_scrollarea_hide:
                    self.completed_details_scrollarea_hide = True
                    QTimer.singleShot(1000, self.hide_completed_frame)

    @pyqtSlot(str)
    def disconnected_link_handler(self, _link:str) -> None:
        plus.controller.toggle(self.aw)

    def set_next(self) -> None:
        self.weight_manager.set_next(self.get_next_weight_item())

    @pyqtSlot()
    def taskCompleted(self) -> None:
        self.weight_manager.taskCompleted()

    @pyqtSlot(list)
    def update_order(self, l:List[ScheduledItem]) -> None:
        self.scheduled_items = l
        # update next weight item
        self.set_next()

    @pyqtSlot()
    def tabSwitched(self) -> None:
        self.set_next()

    @pyqtSlot()
    def setActiveTab(self) -> None:
        self.TabWidget.setCurrentIndex(self.activeTab)

    @pyqtSlot()
    def roasted_weight_selected(self) -> None:
        if self.roasted_weight.text() == '':
            self.roasted_weight.setText(self.roasted_weight.placeholderText())
            self.roasted_weight.selectAll()
            if self.selected_completed_item is not None:
                self.selected_completed_item.data.measured = True
            self.roasted_weight_suffix.setEnabled(True)

    @pyqtSlot()
    def roasted_weight_changed(self) -> None:
        text:str = self.roasted_weight.text()
        if self.selected_completed_item is not None:
            if text == '':
                self.selected_completed_item.data.measured = False
                self.roasted_weight_suffix.setEnabled(False)
            else:
                self.roasted_weight.setText(comma2dot(text))
                self.selected_completed_item.data.measured = True
                self.roasted_weight_suffix.setEnabled(True)

    @pyqtSlot()
    def roasted_measured_toggle(self) -> None:
        if self.selected_completed_item is not None:
            self.selected_completed_item.data.measured = False
            self.roasted_weight.setText('')
            self.roasted_weight_suffix.setEnabled(False)

    @pyqtSlot()
    def roasted_color_changed(self) -> None:
        self.roasted_color.setText(str(int(round(float(comma2dot(self.roasted_color.text()))))))


    @pyqtSlot()
    def roasted_moisture_changed(self) -> None:
        self.roasted_moisture.setText(comma2dot(self.roasted_moisture.text()))


    @pyqtSlot()
    def roasted_density_changed(self) -> None:
        self.roasted_density.setText(comma2dot(self.roasted_density.text()))

    @pyqtSlot()
    def cupping_score_changed(self) -> None:
        if self.cupping_score.text() == '0':
            self.cupping_score.setText('')
        else:
            self.cupping_score.setText(str(float2float(float(comma2dot(self.cupping_score.text())), 2)).rstrip('0').rstrip('.'))


    @pyqtSlot(int)
    def remainingFilterChanged(self, _:int = 0) -> None:
        self.aw.schedule_visible_filter = self.visible_filter.isChecked()
        self.aw.schedule_day_filter = self.day_filter.isChecked()
        self.aw.schedule_user_filter = self.user_filter.isChecked()
        self.aw.schedule_machine_filter = self.machine_filter.isChecked()
        self.updateScheduleWindow()


    @staticmethod
    def setChildrenFocusPolicy(parent:'QWidget', policy:Qt.FocusPolicy) -> None:
        def recursiveSetChildFocusPolicy(parentQWidget:'QWidget') -> None:
            for childQWidget in parentQWidget.findChildren(QWidget):
                childQWidget.setFocusPolicy(policy)
                recursiveSetChildFocusPolicy(childQWidget)
        recursiveSetChildFocusPolicy(parent)


    @staticmethod
    def moveSelection(list_widget:BaseWidget, selected_widget:Optional[QWidget], direction_up:bool) -> None:
        list_widget_count:int = list_widget.count()
        if list_widget_count > 0:
            next_selected_item_pos = (list_widget_count - 1 if direction_up else 0)
            if selected_widget is not None:
                selected_item_pos = list_widget.indexOf(selected_widget)
                if selected_item_pos != -1:
                    next_selected_item_pos = (selected_item_pos - 1 if direction_up else selected_item_pos + 1)
            if next_selected_item_pos < list_widget_count:
                next_selected_item:Optional[StandardItem] = list_widget.itemAt(next_selected_item_pos)
                if next_selected_item is not None:
                    next_selected_item.selected.emit()


    @pyqtSlot('QKeyEvent')
    def keyPressEvent(self, event: Optional['QKeyEvent']) -> None:
        if event is not None:
            k = int(event.key())
            if k == 16777235:    # UP
                active_tab = self.TabWidget.currentIndex()
                if active_tab == 0:
                    self.moveSelection(self.drag_remaining, self.selected_remaining_item, True)
                elif active_tab == 1:
                    self.moveSelection(self.nodrag_roasted, self.selected_completed_item, True)
            elif k == 16777237:  # DOWN
                active_tab = self.TabWidget.currentIndex()
                if active_tab == 0:
                    self.moveSelection(self.drag_remaining, self.selected_remaining_item, False)
                elif active_tab == 1:
                    self.moveSelection(self.nodrag_roasted, self.selected_completed_item, False)
            elif k == 16777234:  # LEFT
                active_tab = self.TabWidget.currentIndex()
                if active_tab == 1:
                    self.TabWidget.setCurrentIndex(0)
            elif k == 16777236:  # RIGHT
                active_tab = self.TabWidget.currentIndex()
                if active_tab == 0:
                    self.TabWidget.setCurrentIndex(1)
            elif k == 16777220:  # ENTER
                active_tab = self.TabWidget.currentIndex()
                if active_tab == 1 and self.selected_completed_item:
                    modifiers = QApplication.keyboardModifiers()
                    if modifiers == Qt.KeyboardModifier.AltModifier:  #alt click
                        self.selected_completed_item.clicked.emit()
                    else:
                        self.selected_completed_item.selected.emit()
            elif k == 46 and QApplication.keyboardModifiers() == Qt.KeyboardModifier.ControlModifier: # CMD-.
                self.closeEvent()
            else:
                super().keyPressEvent(event)


    @pyqtSlot('QCloseEvent')
    def closeEvent(self, evnt:Optional['QCloseEvent'] = None) -> None: # type:ignore[reportIncompatibleMethodOverride, unused-ignore]
        if self.aw.scheduler_auto_open and len(self.scheduled_items) > 0 and self.aw.plus_account is not None:
            self.aw.scheduler_auto_open = False
            string = QApplication.translate('Message','Roasts will not adjust the schedule<br>while the schedule window is closed')
            # native dialog
            if platform.system() == 'Darwin':
                mbox = QMessageBox() # only without super this one shows the native dialog on macOS under Qt 6.6.2
                # for native dialogs, text and informativetext need to be plain strings, no RTF incl. HTML instructions like <br>
                mbox.setText(QApplication.translate('Message','Close Scheduler'))
                mbox.setInformativeText(string.replace('<br>',' '))
                mbox.setWindowModality(Qt.WindowModality.ApplicationModal) # for native dialog it has to be ApplicationModal
                mbox.setStandardButtons(QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Close)
                mbox.setDefaultButton(QMessageBox.StandardButton.Cancel)
                reply = mbox.exec()
            else:
                # non-native dialog
                reply = QMessageBox.warning(None, #self, # only without super this one shows the native dialog on macOS under Qt 6.6.2 and later
                                QApplication.translate('Message','Close Scheduler'),string,
                                QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Close, QMessageBox.StandardButton.Cancel)

            if reply == QMessageBox.StandardButton.Close :
                self.closeScheduler()
            elif evnt is not None:
                evnt.ignore()
        else:
            self.closeScheduler()

    @pyqtSlot()
    def close(self) -> bool:
        self.closeEvent(None)
        return True

    def closeScheduler(self) -> None:
        self.aw.scheduled_items_uuids = self.get_scheduled_items_ids()
        # remember Dialog geometry
        settings = QSettings()
        #save window geometry
        settings.setValue('ScheduleGeometry', self.saveGeometry())
        #save splitter states
        QSettings().setValue('ScheduleMainSplitter',self.main_splitter.saveState()) # upper TODO/Completed splitter
        remaining_splitter_sizes = self.remaining_splitter.sizes()
        QSettings().setValue('ScheduleRemainingSplitterOpen', len(remaining_splitter_sizes)>0 and remaining_splitter_sizes[1]>0)
        QSettings().setValue('ScheduleRemainingSplitter',self.remaining_splitter.saveState()) # lower TODO splitter
        completed_splitter_sizes = self.completed_splitter.sizes()
        QSettings().setValue('ScheduleCompletedSplitterOpen', len(completed_splitter_sizes)>0 and completed_splitter_sizes[1]>0)
        QSettings().setValue('ScheduleCompletedSplitter',self.completed_splitter.saveState()) # lower Completed splitter
        self.aw.scheduler_tasks_visible = self.task_frame.isVisible()
        self.aw.scheduler_completed_details_visible = self.completed_details_scrollarea.isVisible()
        self.aw.scheduler_filters_visible = self.completed_details_scrollarea.isVisible()
        #free resources
        self.aw.schedule_window = None
        self.aw.scheduleFlag = False
        self.aw.scheduleAction.setChecked(False)
        self.aw.schedule_activeTab = self.TabWidget.currentIndex()
        if self.aw.qmc.timeindex[6] == 0:
            # if DROP is not set we clear the ScheduleItem UUID/Date
            self.aw.qmc.scheduleID = None
            self.aw.qmc.scheduleDate = None
        self.aw.sendmessage(QApplication.translate('Message','Scheduler stopped'))
        self.accept()

    # updates the current schedule items by joining its roast with those received as part of a stock update from the server
    # adding new items at the end
    def updateScheduledItems(self) -> None:
        today = datetime.datetime.now(datetime.timezone.utc).astimezone().date()
        # remove outdated items which remained in the open app from yesterday
        current_schedule:List[ScheduledItem] = [si for si in self.scheduled_items if (si.date - today).days >= 0]
        plus.stock.init()
        schedule:List[plus.stock.ScheduledItem] = plus.stock.getSchedule()
        _log.debug('schedule: %s',schedule)
        # sort current schedule by order cache (if any)
        if self.aw.scheduled_items_uuids != []:
            new_schedule:List[plus.stock.ScheduledItem] = []
            for uuid in self.aw.scheduled_items_uuids:
                item = next((s for s in schedule if '_id' in s and s['_id'] == uuid), None)
                if item is not None:
                    new_schedule.append(item)
            # append all schedule items with uuid not in the order cache
            schedule = new_schedule + [s for s in schedule if '_id' in s and s['_id'] not in self.aw.scheduled_items_uuids]
            # reset order cache to prevent resorting until next restart as this cached sort order is only used on startup to
            # initially reconstruct the previous order w.r.t. the server ordered schedule loaded from the stock received
            self.aw.scheduled_items_uuids = []
            # schedule now only contains items received from the server (in local order)
        else:
            # remove items from current_schedule that are not in schedule
            current_schedule = [si for si in current_schedule if next((s for s in schedule if '_id' in s and s['_id'] == si.id), None) is not None]
        # iterate over new schedule
        for s in schedule:
            try:
                schedule_item:ScheduledItem = ScheduledItem.model_validate(s)
                idx_existing_item:Optional[int] = next((i for i, si in enumerate(current_schedule) if si.id == schedule_item.id), None)
                # take new item (but merge completed items)
                if idx_existing_item is not None:
                    # remember existing item
                    existing_item = current_schedule[idx_existing_item]
                    # replace the current item with the updated one from the server
                    current_schedule[idx_existing_item] = schedule_item
                    # merge the completed roasts and set them to the newly received item
                    schedule_item.roasts.update(existing_item.roasts)
                    # if all done, remove that item as it is completed
                    if len(schedule_item.roasts) >= schedule_item.count:
                        # remove existing_item from schedule if completed (#roasts >= count)
                        current_schedule.remove(schedule_item)
                elif (len(schedule_item.roasts) < schedule_item.count and
                        (sum(1 for ci in self.completed_items if ci.scheduleID == schedule_item.id) < schedule_item.count)):
                    # only if not yet enough roasts got registered in the local schedule_item.roasts
                    # and there are not enough completed roasts registered locally belonging to this schedule_item by schedule_item.id
                    # we append non-completed new schedule item to schedule
                    # NOTE: this second condition is needed it might happen that the server did not receive (yet) all completed roasts
                    #  for a ScheduleItem which was locally already removed as completed to prevent re-adding that same ScheduleItem
                    #  on re-receiving the current schedule from the server as still received from the server,
                    #  we check if locally we already have registered enough completed roasts in self.completed_items for this ScheduleItem
                    current_schedule.append(schedule_item)
            except Exception:  # pylint: disable=broad-except
                pass # validation fails for outdated items
        # update the list of schedule items to be displayed
        self.scheduled_items = current_schedule

    @staticmethod
    def getCompletedItems() -> List[CompletedItem]:
        res:List[CompletedItem] = []
        completed:List[CompletedItemDict] = get_all_completed()

        for c in completed:
            try:
                res.append(CompletedItem.model_validate(c))
            except Exception as e:  # pylint: disable=broad-except
                _log.error(e)
        return res

    # sets the items values as properties of the current roast and links it back to this schedule item
    def set_roast_properties(self, item:ScheduledItem, overwrite_nondefault_title:bool=True) -> None:
        self.aw.qmc.scheduleID = item.id
        self.aw.qmc.scheduleDate = item.date.isoformat()
        if overwrite_nondefault_title or self.aw.qmc.title == QApplication.translate('Scope Title', 'Roaster Scope'):
            self.aw.qmc.title = item.title
            if not self.aw.qmc.flagstart or self.aw.qmc.title_show_always:
                self.aw.qmc.setProfileTitle(self.aw.qmc.title)
                self.aw.qmc.fig.canvas.draw()
        prepared:List[float] = get_prepared(item)
        # we take the next prepared item weight if any, else the planned batch size from the item
        weight_unit_idx:int = weight_units.index(self.aw.qmc.weight[2])
        schedule_item_weight = (prepared[0] if len(prepared)>0 else item.weight)
        self.aw.qmc.weight = (convertWeight(schedule_item_weight, 1, weight_unit_idx), self.aw.qmc.weight[1], self.aw.qmc.weight[2])
        # initialize all aplus properties
        self.aw.qmc.plus_store = None
        self.aw.qmc.plus_store_label = None
        self.aw.qmc.plus_coffee = None
        self.aw.qmc.plus_coffee_label = None
        self.aw.qmc.plus_blend_label = None
        self.aw.qmc.plus_blend_spec = None
        self.aw.qmc.plus_blend_spec_labels = None
        self.aw.qmc.beans = ''
        # set store/coffee/blend
        store_item:Optional[Tuple[str, str]] = plus.stock.getStoreItem(item.store, plus.stock.getStores())
        if store_item is not None:
            self.aw.qmc.plus_store = item.store
            self.aw.qmc.plus_store_label = plus.stock.getStoreLabel(store_item)
            if item.coffee is not None:
                coffee = plus.stock.getCoffee(item.coffee)
                if coffee is None:
                    # coffee not in stock, we keep at least the coffee hr_id
                    self.aw.qmc.plus_coffee = item.coffee
                    self.aw.qmc.plus_coffee_label = ''
                    self.aw.qmc.beans = ''
                else:
                    self.aw.qmc.plus_coffee = item.coffee
                    self.aw.qmc.plus_coffee_label = plus.stock.coffeeLabel(coffee)
                    self.aw.qmc.beans = plus.stock.coffee2beans(coffee)
                    # set coffee attributes from stock (moisture, density, screen size):
                    try:
                        coffees:Optional[List[Tuple[str, Tuple[plus.stock.Coffee, plus.stock.StockItem]]]] = plus.stock.getCoffees(weight_unit_idx, item.store)
                        idx:Optional[int] = plus.stock.getCoffeeStockPosition(item.coffee, item.store, coffees)
                        if coffees is not None and idx is not None:
                            cd = plus.stock.getCoffeeCoffeeDict(coffees[idx])
                            if 'moisture' in cd and cd['moisture'] is not None:
                                self.aw.qmc.moisture_greens = cd['moisture']
                            else:
                                self.aw.qmc.moisture_greens = 0
                            if 'density' in cd and cd['density'] is not None:
                                self.aw.qmc.density = (cd['density'],'g',1.,'l')
                            else:
                                self.aw.qmc.density = (0,'g',1.,'l')
                            screen_size_min:int = 0
                            screen_size_max:int = 0
                            try:
                                if 'screen_size' in cd and cd['screen_size'] is not None:
                                    screen = cd['screen_size']
                                    if 'min' in screen and screen['min'] is not None:
                                        screen_size_min = int(screen['min'])
                                    if 'max' in screen and screen['max'] is not None:
                                        screen_size_max = int(screen['max'])
                            except Exception:  # pylint: disable=broad-except
                                pass
                            self.aw.qmc.beansize_min = screen_size_min
                            self.aw.qmc.beansize_max = screen_size_max
                    except Exception as e:  # pylint: disable=broad-except
                        _log.error(e)
            elif item.blend is not None:
                blends:List[plus.stock.BlendStructure] = plus.stock.getBlends(weight_unit_idx, item.store)
                # NOTE: a blend might not have an hr_id as is the case for all custom blends
                blend_structure:Optional[plus.stock.BlendStructure] = next((bs for bs in blends if plus.stock.getBlendId(bs) == item.blend), None)
                if blend_structure is not None:
                    blend:plus.stock.Blend = plus.stock.getBlendBlendDict(blend_structure, schedule_item_weight)
                    self.aw.qmc.plus_blend_label = blend['label']
                    self.aw.qmc.plus_blend_spec = cast(plus.stock.Blend, dict(blend)) # make a copy of the blend dict
                    self.aw.qmc.plus_blend_spec_labels = [i.get('label','') for i in self.aw.qmc.plus_blend_spec['ingredients']]
                    # remove labels from ingredients
                    ingredients = []
                    for i in self.aw.qmc.plus_blend_spec['ingredients']:
                        entry:plus.stock.BlendIngredient = {'ratio': i['ratio'], 'coffee': i['coffee']}
                        if 'ratio_num' in i and i['ratio_num'] is not None:
                            entry['ratio_num'] = i['ratio_num']
                        if 'ratio_denom' in i and i['ratio_denom'] is not None:
                            entry['ratio_denom'] = i['ratio_denom']
                        ingredients.append(entry)
                    self.aw.qmc.plus_blend_spec['ingredients'] = ingredients
                    # set beans description
                    blend_lines = plus.stock.blend2beans(blend_structure, weight_unit_idx, self.aw.qmc.weight[0])
                    self.aw.qmc.beans = '\n'.join(blend_lines)
                    # set blend attributes from stock (moisture, density, screen size):
                    if 'moisture' in blend and blend['moisture'] is not None:
                        self.aw.qmc.moisture_greens = blend['moisture']
                    else:
                        self.aw.qmc.moisture_greens = 0
                    if 'density' in blend and blend['density'] is not None:
                        self.aw.qmc.density = (blend['density'],'g',1.,'l')
                    else:
                        self.aw.qmc.density = (0,'g',1.,'l')
                    if 'screen_min' in blend and blend['screen_min'] is not None:
                        self.aw.qmc.beansize_min = blend['screen_min']
                    else:
                        self.aw.qmc.beansize_min = 0
                    if 'screen_max' in blend and blend['screen_max'] is not None:
                        self.aw.qmc.beansize_max = blend['screen_max']
                    else:
                        self.aw.qmc.beansize_max = 0


    def set_selected_remaining_item_roast_properties(self) -> None:
        if self.selected_remaining_item is not None:
            self.set_roast_properties(self.selected_remaining_item.data)


    def load_selected_remaining_item_template(self) -> None:
        if self.selected_remaining_item is not None:
            self.selected_remaining_item.load_template(self.aw)

    def select_item(self, item:DragItem) -> None:
        if self.selected_remaining_item != item:
            previous_selected_item_data:Optional[ScheduledItem] = None
            previous_selected_id:Optional[str] = None
            if self.selected_remaining_item is not None:
                previous_selected_item_data = self.selected_remaining_item.data
                previous_selected_id = previous_selected_item_data.id
                # clear previous selection
                self.selected_remaining_item.deselect()
            # on selecting the item we only load the template if the item.data.id is different to the previous selected one
            item.select(self.aw, load_template = previous_selected_id != item.data.id)
            self.selected_remaining_item = item
            if self.aw.qmc.flagon and self.aw.qmc.timeindex[6] == 0 and (previous_selected_item_data is None or (previous_selected_item_data != item.data)):
                # while sampling and DROP not yet set, we update the roast properties on schedule item changes
                self.set_selected_remaining_item_roast_properties()

    @pyqtSlot()
    def prepared_items_changed(self) -> None:
        sender = self.sender()
        if sender is not None and isinstance(sender, DragItem):
            self.set_next()

    @pyqtSlot()
    def remaining_items_selection_changed(self) -> None:
        sender = self.sender()
        if sender is not None and isinstance(sender, DragItem):
            self.select_item(sender)

    @pyqtSlot()
    def register_roast(self) -> None:
        sender = self.sender()
        if sender is not None and isinstance(sender, DragItem):
            # updates the roast properties from the given ScheduleItem
            self.set_roast_properties(sender.data, overwrite_nondefault_title=False)
            self.aw.qmc.safesaveflag = True

            # send updated roast to server
            plus.controller.updateSyncRecordHashAndSync()

            # register the current loaded roast profile in the
            # schedule item linked to the given DragItem and add a corresponding
            # completed roast item
            self.register_remaining_item(sender)


    def set_green_weight(self, uuid:str, weight:float) -> None:
        item:Optional[ScheduledItem] = next((si for si in self.scheduled_items if si.id == uuid), None)
        if item is not None:
            add_prepared(self.aw.plus_account_id, item, weight)
            self.updateRemainingItems()
            self.set_next()

    def set_roasted_weight(self, uuid:str, _weight:float) -> None:
        item:Optional[CompletedItem] = next((ci for ci in self.completed_items if ci.roastUUID.hex == uuid), None)
        if item is not None:
            item.measured = True
            # we update the completed_roasts_cache entry
            completed_item_dict = item.model_dump(mode='json')
            if 'prefix' in completed_item_dict:
                del completed_item_dict['prefix']
            add_completed(self.aw.plus_account_id, cast(CompletedItemDict, completed_item_dict))
            self.updateRoastedItems()
            self.set_next()

    def get_next_weight_item(self) -> Optional['WeightItem']:
        todo_tab_active:bool = self.TabWidget.currentIndex() == 0
        next_weight_item:Optional[WeightItem] = None
        if todo_tab_active:
            next_weight_item = self.next_not_prepared_item()
        else:
            next_weight_item = self.next_not_completed_item()
        # if there is nothing to do for the active tab, check the inactive tab for tasks
        if next_weight_item is None:
            if todo_tab_active:
                next_weight_item = self.next_not_completed_item()
            else:
                next_weight_item = self.next_not_prepared_item()
        return next_weight_item

    def next_not_prepared_item(self) -> Optional[GreenWeightItem]:
        today:datetime.date = datetime.datetime.now(datetime.timezone.utc).astimezone().date()
        for item in filter(lambda x: self.aw.scheduledItemsfilter(today, x, is_hidden(x)), self.scheduled_items):
            prepared:int = len(get_prepared(item))
            roasted:int = len(item.roasts)
            remaining = item.count - roasted
            if remaining > prepared:
                weight_unit_idx = weight_units.index(self.aw.qmc.weight[2])
                return GreenWeightItem(
                    uuid = item.id,
                    title = item.title,
                    description = scheduleditem_beans_description(weight_unit_idx, item),
                    position = ('' if item.count == 1 else f'{prepared + roasted + 1}/{item.count}'),
                    weight = item.weight,
                    weight_unit_idx = weight_unit_idx,
                    call_back = self.set_green_weight
                )
        return None

    def next_not_completed_item(self) -> Optional[RoastedWeightItem]:
        item:Optional[CompletedItem] = next((ci for ci in self.completed_items if not ci.measured), None)
        if item is not None:
            weight_unit_idx = weight_units.index(self.aw.qmc.weight[2])
            return RoastedWeightItem(
                    uuid = item.roastUUID.hex,
                    title = f"{(item.prefix + ' ' if item.prefix != '' else '')}{item.title}",
                    description = completeditem_beans_description(weight_unit_idx, item),
                    position = ('' if item.count == 1 else f'{item.sequence_id}/{item.count}'),
                    weight = item.weight_estimate,
                    weight_unit_idx = weight_unit_idx,
                    call_back = self.set_roasted_weight
            )
        return None

    # returns number of visible scheduled items
    def updateRemainingItems(self) -> int:
        self.drag_remaining.clearItems()
        today:datetime.date = datetime.datetime.now(datetime.timezone.utc).astimezone().date()
        drag_items_first_label_max_width = 0
        drag_first_labels = []
        selected_item:Optional[DragItem] = None
        for item in filter(lambda x: self.aw.scheduledItemsfilter(today, x, is_hidden(x)), self.scheduled_items):
            drag_item = DragItem(item,
                self.aw,
                today,
                self.aw.plus_user_id,
                self.aw.qmc.roastertype_setup.strip())
            # remember selection
            if self.selected_remaining_item is not None and self.selected_remaining_item.data.id == item.id:
                selected_item = drag_item
            # take the maximum width over all first labels of the DragItems
            drag_first_label = drag_item.getFirstLabel()
            drag_first_labels.append(drag_first_label)
            drag_items_first_label_max_width = max(drag_items_first_label_max_width, drag_first_label.sizeHint().width())
            # connect the selection signal
            drag_item.selected.connect(self.remaining_items_selection_changed)
            drag_item.prepared.connect(self.prepared_items_changed)
            drag_item.registerRoast.connect(self.register_roast)
            # append item to list
            self.drag_remaining.add_item(drag_item)
        if selected_item is not None:
            # reselect the previously selected item
            self.select_item(selected_item)
        else:
            # otherwise select first item if schedule is not empty
            self.selected_remaining_item = None
            if self.drag_remaining.count() > 0:
                first_item:Optional[DragItem] = self.drag_remaining.itemAt(0)
                if first_item is not None:
                    self.select_item(first_item)
        # we set the first label width to the maximum first label width of all items
        for first_label in drag_first_labels:
            first_label.setFixedWidth(drag_items_first_label_max_width)
        # updates the tabs tooltip
        scheduled_items:List[ScheduledItem] = self.drag_remaining.get_item_data()
        if len(scheduled_items) > 0:
            todays_items = []
            later_items = []
            for si in scheduled_items:
                if si.date == today:
                    todays_items.append(si)
                else:
                    later_items.append(si)
            batches_today, batches_later = (sum(max(0, si.count - len(si.roasts)) for si in items) for items in (todays_items, later_items))
            # total weight in kg
            total_weight_today, total_weight_later = (sum(si.weight * max(0, (si.count - len(si.roasts))) for si in items) for items in (todays_items, later_items))
            weight_unit_idx = weight_units.index(self.aw.qmc.weight[2])
            one_batch_label = QApplication.translate('Message', '1 batch')
            if batches_today > 0:
                batches_today_label = (one_batch_label if batches_today == 1 else QApplication.translate('Message', '{} batches').format(batches_today))
                todays_batches = f'{batches_today_label} • {render_weight(total_weight_today, 1, weight_unit_idx)}'
            else:
                todays_batches = ''
            if batches_later > 0:
                batches_later_label = (one_batch_label if batches_later == 1 else QApplication.translate('Message', '{} batches').format(batches_later))
                later_batches = f'{batches_later_label} • {render_weight(total_weight_later, 1, weight_unit_idx)}'
            else:
                later_batches = ''
            self.TabWidget.setTabToolTip(0, f"<p style='white-space:pre'><b>{todays_batches}</b>{('<br>' if (batches_today > 0 and batches_later > 0) else '')}{later_batches}</p>")
            # update app badge number
            self.setAppBadge(batches_today + batches_later)
        else:
            self.TabWidget.setTabToolTip(0,'')
            # update app badge number
            self.setAppBadge(0)
            # clear selection and reset scheduleID
            self.selected_remaining_item = None
            if self.aw.qmc.timeindex[6] == 0:
                # if DROP is not set we clear the ScheduleItem UUID/Date
                self.aw.qmc.scheduleID = None
                self.aw.qmc.scheduleDate = None
        return len(scheduled_items)

    @staticmethod
    def setAppBadge(number:int) -> None:
        try:
            app = QApplication.instance()
            app.setBadgeNumber(max(0, number)) # type: ignore # "QCoreApplication" has no attribute "setBadgeNumber"
        except Exception: # pylint: disable=broad-except
            pass # setBadgeNumber only supported by Qt 6.5 and newer

    # returns number of open items
    @staticmethod
    def openScheduleItemsCount(aw:'ApplicationWindow') -> int:
        try:
            plus.stock.init()
            schedule:List[plus.stock.ScheduledItem] = plus.stock.getSchedule()
            scheduled_items:List[ScheduledItem] = []
            for item in schedule:
                try:
                    schedule_item:ScheduledItem = ScheduledItem.model_validate(item)
                    scheduled_items.append(schedule_item)
                except Exception:  # pylint: disable=broad-except
                    pass # validation fails for outdated items
            today:datetime.date = datetime.datetime.now(datetime.timezone.utc).astimezone().date()
            return sum(max(0, x.count - len(x.roasts)) for x in scheduled_items if aw.scheduledItemsfilter(today, x, is_hidden(x)))
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)
            return 0

    @pyqtSlot()
    def updateFilters(self) -> None:
        nickname:Optional[str] = plus.connection.getNickname()
        if nickname is not None and nickname != '':
            self.user_filter.setText(nickname)
            self.user_filter.setToolTip(QApplication.translate('Plus','List only items scheduled for the current user {}').format(nickname))
            self.user_filter.show()
        else:
            self.user_filter.hide()
        machine_name:str = self.aw.qmc.roastertype_setup.strip()
        if machine_name != '':
            self.machine_filter.setText(machine_name)
            self.machine_filter.show()
            self.user_filter.setToolTip(QApplication.translate('Plus','List only items scheduled for the current machine {}').format(machine_name))
        else:
            self.machine_filter.hide()


    def set_details(self, item:Optional[NoDragItem]) -> None:
        if item is None:
            self.roasted_weight.setText('')
            self.roasted_weight.setPlaceholderText('')
            self.roasted_color.setText('')
            self.roasted_density.setText('')
            self.roasted_moisture.setText('')
            self.roasted_notes.setPlainText('')
            self.cupping_score.setText('')
            self.cupping_notes.setPlainText('')
            self.completed_details_group.setEnabled(False)
        else:
            data = item.data
            converted_estimate = convertWeight(data.weight_estimate, 1, weight_units.index(self.aw.qmc.weight[2]))
            converted_estimate_str = f'{float2floatWeightVolume(converted_estimate):g}'
            self.roasted_weight.setPlaceholderText(converted_estimate_str)
            converted_weight = convertWeight(data.weight, 1, weight_units.index(self.aw.qmc.weight[2]))
            converted_weight_str = f'{float2floatWeightVolume(converted_weight):g}'
            if not data.measured and converted_weight_str != converted_estimate_str:
                # weight might have been set on server by another client
                data.measured = True
                # we update the completed_roasts_cache entry
                completed_item_dict = data.model_dump(mode='json')
                if 'prefix' in completed_item_dict:
                    del completed_item_dict['prefix']
                add_completed(self.aw.plus_account_id, cast(CompletedItemDict, completed_item_dict))
            if data.measured:
                self.roasted_weight.setText(converted_weight_str)
                self.roasted_weight_suffix.setEnabled(True)
            else:
                self.roasted_weight.setText('')
                self.roasted_weight_suffix.setEnabled(False)
            self.roasted_color.setText(str(data.color))
            self.roasted_density.setText(f'{data.density:g}')
            self.roasted_moisture.setText(f'{data.moisture:g}')
            self.roasted_notes.setPlainText(data.roastingnotes)
            if data.cupping_score == 50:
                self.cupping_score.setText('')
            else:
                self.cupping_score.setText(str(float2float(data.cupping_score, 2)).rstrip('0').rstrip('.'))
            self.cupping_notes.setPlainText(data.cuppingnotes)
            self.completed_details_group.setEnabled(True)


    # computes the difference between the UI NoDragItem and the linked CompletedItem
    # and returns only changed attributes as partial sync_record (lacking the roast_id)
    # NOTE: resulting dict values may be None to represent default values (removing corresponding data item on the server)
    def changes(self, item:NoDragItem) -> Dict[str, Any]:
        data = item.data
        changes:Dict[str, Any] = {}
        try:
            converted_data_weight = convertWeight(data.weight, 1, weight_units.index(self.aw.qmc.weight[2]))
            converted_data_weight_str = f'{float2floatWeightVolume(converted_data_weight):g}'
            roasted_weight_text:str = self.roasted_weight.text()
            if roasted_weight_text == '':
                roasted_weight_text = self.roasted_weight.placeholderText()
            if roasted_weight_text != '':
                roasted_weight_value_str = comma2dot(roasted_weight_text)
                if converted_data_weight_str != roasted_weight_value_str:
                    # on textual changes, send updated weight
                    changes['end_weight'] = convertWeight(float(roasted_weight_value_str), weight_units.index(self.aw.qmc.weight[2]), 1)
        except Exception:  # pylint: disable=broad-except
            pass
        current_roasted_color = int(round(float(self.roasted_color.text())))
        if current_roasted_color != data.color:
            if current_roasted_color == 0:
                changes['ground_color'] = None # remove entry on server as this is the default value
            else:
                changes['ground_color'] = current_roasted_color
        current_roasted_density = float(self.roasted_density.text())
        if current_roasted_density != data.density:
            if current_roasted_density == 0:
                changes['density_roasted'] = None # remove entry on server as this is the default value
            else:
                changes['density_roasted'] = current_roasted_density
        current_roasted_moisture = float(self.roasted_moisture.text())
        if current_roasted_moisture != data.moisture:
            if current_roasted_moisture == 0:
                changes['moisture'] = None # remove entry on server as this is the default value
            else:
                changes['moisture'] = current_roasted_moisture
        current_notes = self.roasted_notes.toPlainText().strip()
        if current_notes != data.roastingnotes:
            if current_notes == '':
                changes['notes'] = None # remove entry on server as this is the default value
            else:
                changes['notes'] = current_notes
        current_cupping_score = (50 if self.cupping_score.text() == '' else float2float(float(self.cupping_score.text()), 2))
        if current_cupping_score != data.cupping_score:
            if current_cupping_score == 50:
                changes['cupping_score'] = None # remove entry on server as this is the default value
            else:
                changes['cupping_score'] = current_cupping_score
        current_cupping_notes = self.cupping_notes.toPlainText().strip()
        if current_cupping_notes != data.cuppingnotes:
            if current_cupping_notes == '':
                changes['cupping_notes'] = None # remove entry on server as this is the default value
            else:
                changes['cupping_notes'] = current_cupping_notes
        return changes


    # updates the changeable properties of the currently loaded profiles roast properties from the given CompletedItem
    def updates_roast_properties_from_completed(self, ci:CompletedItem) -> None:
        # roastUUID has to agree and roastdate is fixed
        if ci.roastUUID.hex == self.aw.qmc.roastUUID:
            wunit:str = self.aw.qmc.weight[2]
            wout = convertWeight(
                ci.weight,
                weight_units.index('Kg'),
                weight_units.index(wunit)
            )
            self.aw.qmc.weight = (self.aw.qmc.weight[0], wout, self.aw.qmc.weight[2])
            self.aw.qmc.ground_color = ci.color
            self.aw.qmc.moisture_roasted = ci.moisture
            self.aw.qmc.density_roasted = (ci.density, self.aw.qmc.density_roasted[1], self.aw.qmc.density_roasted[2], self.aw.qmc.density_roasted[3])
            self.aw.qmc.roastingnotes = ci.roastingnotes
            cupping_value = self.aw.qmc.calcFlavorChartScore()
            if ci.cupping_score != cupping_value:
                # as cupping score is only computed from the single values we try to keep things as if the resulting score did not change
                self.aw.qmc.setFlavorChartScore(ci.cupping_score)
            self.aw.qmc.cuppingnotes = ci.cuppingnotes
            # not updated:
            #        roastbatchnr
            #        roastbatchprefix
            #        title
            # don't update the coffee/blend/store labels as we do not maintain the corresponding hr_ids in CompletedItems
            #        coffee_label
            #        blend_label
            #        store_label
            #        batchsize

    # updates all roast properties (the changeable as well as the non-changeable from the loaded profiles roast properties to the give CompletedItem
    # such that changes in the RoastProperties are reflected in the items visualization (even if not yet established to the server)
    def updates_completed_from_roast_properties(self, ci:CompletedItem) -> bool:
        updated:bool = False
        weight_unit_idx = weight_units.index(self.aw.qmc.weight[2])
        weight = convertWeight(self.aw.qmc.weight[0], weight_unit_idx, 1)
        if ci.weight != weight:
            ci.weight = weight
            updated = True
        if ci.color != self.aw.qmc.ground_color:
            ci.color = self.aw.qmc.ground_color
            updated = True
        if ci.moisture != self.aw.qmc.moisture_roasted:
            ci.moisture = self.aw.qmc.moisture_roasted
            updated = True
        if ci.density != self.aw.qmc.density_roasted[0]:
            ci.density = self.aw.qmc.density_roasted[0]
            updated = True
        if ci.roastingnotes != self.aw.qmc.roastingnotes:
            ci.roastingnotes = self.aw.qmc.roastingnotes
            updated = True
        cupping_value = self.aw.qmc.calcFlavorChartScore()
        if ci.cupping_score != cupping_value:
            ci.cupping_score = cupping_value
            updated = True
        if ci.cuppingnotes != self.aw.qmc.cuppingnotes:
            ci.cuppingnotes = self.aw.qmc.cuppingnotes
            updated = True
        # non_changeable attributes:
        if ci.roastbatchnr != self.aw.qmc.roastbatchnr:
            ci.roastbatchnr = self.aw.qmc.roastbatchnr
            updated = True
        if ci.roastbatchprefix != self.aw.qmc.roastbatchprefix:
            ci.roastbatchprefix = self.aw.qmc.roastbatchprefix
            updated = True
        if ci.title != self.aw.qmc.title:
            ci.title = self.aw.qmc.title
            updated = True
        if ci.coffee_label != self.aw.qmc.plus_coffee_label:
            ci.coffee_label = self.aw.qmc.plus_coffee_label
            updated = True
        if ci.blend_label != self.aw.qmc.plus_blend_label:
            ci.blend_label = self.aw.qmc.plus_blend_label
            updated = True
        if ci.store_label != self.aw.qmc.plus_store_label:
            ci.store_label = self.aw.qmc.plus_store_label
            updated = True
        # not editable in RoastProperties (only available from the corresponding creating ScheduledItem) thus not modified
        #batchsize

        if updated:
            # we update the completed_roasts_cache entry
            completed_item_dict = ci.model_dump(mode='json')
            if 'prefix' in completed_item_dict:
                del completed_item_dict['prefix']
            add_completed(self.aw.plus_account_id, cast(CompletedItemDict, completed_item_dict))
        return updated


    @pyqtSlot()
    def completed_item_clicked(self) -> None:
        sender = self.sender()
        if not self.aw.qmc.flagon and sender is not None and isinstance(sender, NoDragItem):
            # Artisan is OFF
            # we try to load the clicked completed items profile if not yet loaded
            sender_roastUUID = sender.data.roastUUID.hex
            if sender_roastUUID != self.aw.qmc.roastUUID:
                item_path = plus.register.getPath(sender_roastUUID)
                if item_path is not None and os.path.isfile(item_path):
                    try:
#                        self.aw.loadFile(item_path)
                        self.aw.loadFileSignal.emit(item_path)
                    except Exception as e: # pylint: disable=broad-except
                        _log.exception(e)


    @pyqtSlot()
    def completed_items_selection_changed(self) -> None:
        sender = self.sender()
        if sender is not None and isinstance(sender, NoDragItem):
            splitter_sizes = self.completed_splitter.sizes()
            if plus.controller.is_on():
                # editing is only possible if artisan.plus is connected or at least ON
                # save previous edits and clear previous selection
                if self.selected_completed_item is not None:
                    # compute the difference between the 5 property edit widget values and the corresponding CompletedItem values linked
                    # to the currently selected NoDragItem as sync_record
                    changes:Dict[str, Any] = self.changes(self.selected_completed_item)
                    if changes:
                        # something got edited, we have to send the changes back to the server
                        # first add essential metadata
                        changes['roast_id'] = self.selected_completed_item.data.roastUUID.hex
                        changes['modified_at'] = epoch2ISO8601(time.time())
                        try:
                            plus.controller.connect(clear_on_failure=False, interactive=False)
                            r = plus.connection.sendData(plus.config.roast_url, changes, 'POST')
                            r.raise_for_status()
                            # update successfully transmitted, we now also add/update the CompletedItem linked to self.selected_completed_item
                            self.selected_completed_item.data.update_completed_item(self.aw, changes)
                            # if previous selected roast is loaded we write the changes to its roast properties
                            if self.selected_completed_item.data.roastUUID.hex == self.aw.qmc.roastUUID:
                                self.updates_roast_properties_from_completed(self.selected_completed_item.data)
                        except Exception as e:  # pylint: disable=broad-except
                            # updating data to server failed, we keep the selection
                            _log.error(e)
                            self.aw.sendmessageSignal.emit(QApplication.translate('Message', 'Updating completed roast properties failed'), True, None)
                            # we keep the selection
                            return
                    # we update the completed_roasts_cache entry
                    completed_item_dict = self.selected_completed_item.data.model_dump(mode='json')
                    add_completed(self.aw.plus_account_id, cast(CompletedItemDict, completed_item_dict))
                    # in case data was not edited or updating the edits to server succeeded we
                    # clear previous selection
                    self.selected_completed_item.deselect()
                    # and update its labels as its measured state might have changed
                    self.selected_completed_item.update_labels()
                    # update next weight item, as the current one might have been completed by closing this edit
                    self.set_next()
                if sender != self.selected_completed_item:
                    if plus.sync.getSync(sender.data.roastUUID.hex) is None:
                        _log.info('completed roast %s could not be edited as corresponding sync record is missing', sender.data.roastUUID.hex)
                    else:
                        # fetch data if roast is participating in the sync record game
                        profile_data: Optional[Dict[str, Any]] = plus.sync.fetchServerUpdate(sender.data.roastUUID.hex, return_data = True)
                        if profile_data is not None:
                            # update completed items data from received profile_data
                            updated:bool = sender.data.update_completed_item(self.aw, profile_data)
                            # on changes, update loaded profile if saved earlier
                            if (updated and self.aw.curFile is not None and sender.data.roastUUID.hex == self.aw.qmc.roastUUID and
                                    self.aw.qmc.plus_file_last_modified is not None and 'modified_at' in profile_data and
                                    ISO86012epoch(profile_data['modified_at']) > self.aw.qmc.plus_file_last_modified):
                                plus.sync.applyServerUpdates(profile_data)
                                # we update the loaded profile timestamp to avoid receiving the same update again
                                self.aw.qmc.plus_file_last_modified = time.time()
                            # start item editing mode
                            sender.select()
                            self.selected_completed_item = sender
                            # update UI item
                            self.set_details(sender)
                            if len(splitter_sizes)>1:
                                # enable focus on input widgets
                                self.roasted_weight.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
                                self.roasted_color.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
                                self.roasted_density.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
                                self.roasted_moisture.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
                                self.roasted_notes.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
                                self.roasted_moisture.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
                                self.cupping_score.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
                                self.cupping_notes.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
                                if not self.completed_details_scrollarea.isVisible():
                                    self.completed_details_scrollarea.show()
                                    self.update()
                                if splitter_sizes[1] == 0:
                                    if self.completed_splitter_open_height != 0:
                                        self.completed_splitter.setSizes([
                                            sum(splitter_sizes) - self.completed_splitter_open_height,
                                            self.completed_splitter_open_height])
                                    else:
                                        second_split_widget = self.completed_splitter.widget(1)
                                        if second_split_widget is not None:
                                            max_details_height = second_split_widget.sizeHint().height()
                                            self.completed_splitter.setSizes([
                                                sum(splitter_sizes) - max_details_height,
                                                max_details_height])
                                else:
                                    self.completed_splitter_open_height = splitter_sizes[1]
                        else:
                            self.aw.sendmessageSignal.emit(QApplication.translate('Message', 'Fetching completed roast properties failed'), True, None)
                else:
                    # edits completed, reset selection
                    self.selected_completed_item = None
                    # clear details split view
                    self.set_details(None)
                    # remember open height (might be user set)
                    if len(splitter_sizes)>1:
                        self.completed_splitter_open_height = splitter_sizes[1]
                    # close details split
                    self.completed_splitter.setSizes([sum(splitter_sizes),0])
                    # disable focus on input widgets to return keyboard focus to parent
                    self.roasted_weight.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                    self.roasted_color.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                    self.roasted_density.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                    self.roasted_moisture.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                    self.roasted_notes.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                    self.cupping_score.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                    self.cupping_notes.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                    if self.completed_details_scrollarea.isVisible():
                        self.completed_details_scrollarea.hide()
            # NOTE: this branch is not reached any longer as if not connected to artisan.plus, the schedule window remains empty with a note
            elif not self.aw.qmc.flagon:
                # plus controller is not on and Artisan is OFF we first close a potentially pending edit section and then try to load that profile
                if self.selected_completed_item is not None:
                    # we terminate editing mode if offline and reset selection
                    self.selected_completed_item = None
                    # clear details split view
                    self.set_details(None)
                    # remember open height (might be user set)
                    if len(splitter_sizes)>1:
                        self.completed_splitter_open_height = splitter_sizes[1]
                    # close details split
                    self.completed_splitter.setSizes([sum(splitter_sizes),0])
                    # disable focus on input widgets to return keyboard focus to parent
                    self.roasted_weight.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                    self.roasted_color.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                    self.roasted_density.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                    self.roasted_moisture.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                    self.roasted_notes.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                    self.cupping_score.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                    self.cupping_notes.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                    if self.completed_details_scrollarea.isVisible():
                        self.completed_details_scrollarea.hide()
                # we try to load the clicked completed items profile if not yet loaded
                sender_roastUUID = sender.data.roastUUID.hex
                if sender_roastUUID != self.aw.qmc.roastUUID:
                    item_path = plus.register.getPath(sender_roastUUID)
                    if item_path is not None and os.path.isfile(item_path):
                        try:
                            self.aw.loadFile(item_path)
                        except Exception as e: # pylint: disable=broad-except
                            _log.exception(e)

    def updateRoastedItems(self) -> None:
        self.nodrag_roasted.clearItems()
        now:datetime.datetime = datetime.datetime.now(datetime.timezone.utc)
        nodrag_items_first_label_max_width = 0
        nodrag_first_labels = []
        new_selected_completed_item:Optional[NoDragItem] = None
        for item in self.completed_items:
            nodrag_item = NoDragItem(item, self.aw, now)
            # take the maximum width over all first labels of the DragItems
            nodrag_first_label = nodrag_item.getFirstLabel()
            nodrag_first_labels.append(nodrag_first_label)
            nodrag_items_first_label_max_width = max(nodrag_items_first_label_max_width, nodrag_first_label.sizeHint().width())
            # connect the selection signal
            nodrag_item.clicked.connect(self.completed_item_clicked)
            nodrag_item.selected.connect(self.completed_items_selection_changed)
            # append item to list
            self.nodrag_roasted.add_item(nodrag_item)
            # check if this is the selected item
            if self.selected_completed_item is not None and self.selected_completed_item.data.roastUUID == item.roastUUID:
                new_selected_completed_item = nodrag_item
        # we set the first label width to the maximum first label width of all items
        for first_label in nodrag_first_labels:
            first_label.setFixedWidth(nodrag_items_first_label_max_width)
        # update selected item if any
        self.selected_completed_item = new_selected_completed_item
        if self.selected_completed_item is not None:
            self.selected_completed_item.select()

        # updates the tabs tooltip
        today:datetime.date = now.astimezone().date() # today in local timezone
        completed_items:List[CompletedItem] = self.completed_items
        if len(completed_items) > 0:
            todays_items = []
            earlier_items = []
            for ci in completed_items:
                if ci.roastdate.astimezone().date() == today:
                    todays_items.append(ci)
                else:
                    earlier_items.append(ci)
            batches_today, batches_earlier = (len(items) for items in (todays_items, earlier_items))
            # total batchsize in kg
            total_batchsize_today, total_batchsize_earlier = (sum(si.batchsize for si in items) for items in (todays_items, earlier_items))
            weight_unit_idx = weight_units.index(self.aw.qmc.weight[2])
            one_batch_label = QApplication.translate('Message', '1 batch')
            if batches_today > 0:
                todays_batches_label = (one_batch_label if batches_today == 1 else QApplication.translate('Message', '{} batches').format(batches_today))
                todays_batches = f'{todays_batches_label} • {render_weight(total_batchsize_today, 1, weight_unit_idx)}'
            else:
                todays_batches = ''
            if batches_earlier > 0:
                earlier_batches_label = (one_batch_label if batches_earlier == 1 else QApplication.translate('Message', '{} batches').format(batches_earlier))
                earlier_batches = f'{earlier_batches_label} • {render_weight(total_batchsize_earlier, 1, weight_unit_idx)}'
            else:
                earlier_batches = ''
            self.TabWidget.setTabToolTip(1, f"<p style='white-space:pre'><b>{todays_batches}</b>{('<br>' if (batches_today > 0 and batches_earlier > 0) else '')}{earlier_batches}</p>")
        else:
            self.TabWidget.setTabToolTip(1, '')

    # returns True if there is a completed item with the given roastID
    def in_completed(self, roastID:str) -> bool:
        return any(ci.roastUUID.hex == roastID for ci in self.completed_items)

    def prev_roast_session_data(self) -> datetime.date:
        if self.completed_items:
            return self.completed_items[-1].roastdate.date()
        return datetime.datetime.now(datetime.timezone.utc).astimezone().date()

    def get_scheduled_items_ids(self) -> List[str]:
        return [si.id for si in self.scheduled_items]

    # returns total roast time in seconds based on given timeindex and timex structures
    @staticmethod
    def roast_time(timeindex:List[int], timex:List[float]) -> float:
        if len(timex) == 0:
            return 0
        starttime = (timex[timeindex[0]] if timeindex[0] != -1 and timeindex[0] < len(timex) else 0)
        endtime = (timex[timeindex[6]] if timeindex[6] > 0  and timeindex[6] < len(timex) else timex[-1])
        return endtime - starttime

    # returns end/drop temperature based on given timeindex and timex structures
    @staticmethod
    def end_temp(timeindex:List[int], temp2:List[float]) -> float:
        if len(temp2) == 0:
            return 0
        if timeindex[6] == 0:
            return temp2[-1]
        return temp2[timeindex[6]]

    # converts given BlendList into a Blend and returns True if equal modulo label to the given Blend
    @staticmethod
    def same_blend(blend_list1:Optional[plus.stock.BlendList], blend2:Optional[plus.stock.Blend]) -> bool:
        if blend_list1 is not None and blend2 is not None:
            blend1 = plus.stock.list2blend(blend_list1)
            if blend1 is not None:
                return plus.stock.matchBlendDict(blend1, blend2, sameLabel=False)
        return False

    # returns the roasted weight estimate in kg calculated from the given ScheduledItem and the current roasts batchsize (in kg)
    def weight_estimate(self, data:ScheduledItem, batchsize:float) -> float:
        _log.debug('weight_estimate(%s)',batchsize)
        background:Optional[ProfileData] = self.aw.qmc.backgroundprofile
        try:
            if (background is not None and 'weight' in background):
                # a background profile is loaded
                same_coffee_or_blend = (('plus_coffee' in background and self.aw.qmc.plus_coffee is not None and background['plus_coffee'] == self.aw.qmc.plus_coffee) or
                    ('plus_blend_spec' in background and self.same_blend(background['plus_blend_spec'], self.aw.qmc.plus_blend_spec)))
                if same_coffee_or_blend:
                    _log.debug('same_coffee_or_blend')
                    # same coffee or blend
                    same_machine = True # item.machine is not None and item.machine == background.machinesetup
                    if same_machine:
                        # roasted on the same machine
                        # criteria not verified as typos, or unset machine name, could hinder correct suggestions
                        background_weight = background['weight']
                        _log.debug('background_weight: %s', background_weight)
                        background_weight_in = float(background_weight[0])
                        background_weight_out = float(background_weight[1])
                        background_loss = self.aw.weight_loss(background_weight_in, background_weight_out)
                        if loss_min < background_loss < loss_max:
                            _log.debug('loss: %s < %s < %s', loss_min, background_loss, loss_max)
                            # with a reasonable loss between 5% and 25%
                            background_weight_unit_idx = weight_units.index(background_weight[2])
                            background_weight_in = convertWeight(background_weight_in, background_weight_unit_idx, 1)  # batchsize converted to kg
                            if abs(background_weight_in - batchsize) < batchsize * similar_roasts_max_batch_size_delta/100:
                                _log.debug('batchsize delta (in kg): %s < %s',abs(background_weight_in - batchsize), batchsize * similar_roasts_max_batch_size_delta/100)
                                # batch size the same (delta < 0.5%)
                                foreground_roast_time = self.roast_time(self.aw.qmc.timeindex, self.aw.qmc.timex)
                                background_roast_time = self.roast_time(self.aw.qmc.timeindexB, self.aw.qmc.timeB)
                                if abs(foreground_roast_time - background_roast_time) < similar_roasts_max_roast_time_delta:
                                    _log.debug('roast time delta: %s < %s', abs(foreground_roast_time - background_roast_time), similar_roasts_max_roast_time_delta)
                                    # roast time is in the range (delta < 30sec)
                                    foreground_end_temp = self.end_temp(self.aw.qmc.timeindex, self.aw.qmc.temp2)
                                    background_end_temp = self.end_temp(self.aw.qmc.timeindexB, self.aw.qmc.temp2B)
                                    if abs(foreground_end_temp - background_end_temp) < (similar_roasts_max_drop_bt_temp_delta_C if self.aw.qmc.mode == 'C' else similar_roasts_max_drop_bt_temp_delta_F):
                                        _log.debug('drop/end temp: %s < %s', abs(foreground_end_temp - background_end_temp), (similar_roasts_max_drop_bt_temp_delta_C if self.aw.qmc.mode == 'C' else similar_roasts_max_drop_bt_temp_delta_F))
                                        # drop/end temp is in the range (delta < 5C/4F)

                                        # the current roast is similar to the one of the loaded background thus we return the
                                        # background profiles roasted weight converted to kg as estimate
                                        _log.debug('roasted weight set from template')
                                        return convertWeight(background_weight_out, background_weight_unit_idx, 1) # roasted weight converted to kg
        except Exception:  # pylint: disable=broad-except
            pass
        # else base roasted weight estimate on server provided loss
        if loss_min < data.loss < loss_max:
            _log.debug('roasted weight set from server provided loss')
            return self.aw.apply_weight_loss(data.loss, batchsize)
        # if we did not get a loss in a sensible range we assume the default loss (15%)
        _log.debug('rosted weight set form default loss (%s%%)', default_loss)
        return self.aw.apply_weight_loss(default_loss, batchsize)


    def register_remaining_item(self, remaining_item:DragItem) -> None:
        if self.aw.qmc.roastUUID is not None:
            _log.info('register completed roast %s', self.aw.qmc.roastUUID)
            try:
                # register roastUUID in (local) currently selected ScheduleItem
                # add roast to list of completed roasts
                remaining_item.data.roasts.add(UUID(self.aw.qmc.roastUUID, version=4))
                # reduce number of prepared batches of the currently selected remaining item
                take_prepared(self.aw.plus_account_id, remaining_item.data)
                # calculate weight estimate
                weight_unit_idx:int = weight_units.index(self.aw.qmc.weight[2])
                batchsize:float = convertWeight(self.aw.qmc.weight[0], weight_unit_idx, 1) # batchsize converted to kg
                weight_estimate = self.weight_estimate(remaining_item.data, batchsize) # in kg

                measured:bool

                if self.aw.qmc.weight[1] == 0:
                    # roasted weight not set
                    measured = False
                    self.aw.qmc.weight = (self.aw.qmc.weight[0], convertWeight(weight_estimate, 1, weight_unit_idx), self.aw.qmc.weight[2])
                    weight = weight_estimate
                else:
                    measured = True
                    weight = convertWeight(self.aw.qmc.weight[1], weight_unit_idx, 1)    # resulting weight converted to kg

                completed_item:CompletedItemDict = {
                    'scheduleID': remaining_item.data.id,
                    'scheduleDate': remaining_item.data.date.isoformat(),
                    'count': remaining_item.data.count,
                    'sequence_id': len(remaining_item.data.roasts),
                    'roastUUID': self.aw.qmc.roastUUID,
                    'roastdate': self.aw.qmc.roastdate.toSecsSinceEpoch(),
                    'title': self.aw.qmc.title,
                    'roastbatchnr' : self.aw.qmc.roastbatchnr,
                    'roastbatchprefix': self.aw.qmc.roastbatchprefix,
                    'coffee_label': self.aw.qmc.plus_coffee_label,
                    'blend_label': self.aw.qmc.plus_blend_label,
                    'store_label': self.aw.qmc.plus_store_label,
                    'batchsize': batchsize,
                    'weight': weight,
                    'weight_estimate': weight_estimate,
                    'measured': measured,
                    'color': self.aw.qmc.ground_color,
                    'moisture': self.aw.qmc.moisture_roasted,
                    'density': self.aw.qmc.density_roasted[0],
                    'roastingnotes': self.aw.qmc.roastingnotes,
                    'cupping_score': self.aw.qmc.calcFlavorChartScore(),
                    'cuppingnotes': self.aw.qmc.cuppingnotes
                }
                add_completed(self.aw.plus_account_id, completed_item)
                # update schedule, removing completed items and selecting the next one

                # we catch potential validation errors for CompletedItemDict here to ensure that the updateScheduleWindow() is always correctly called
            except Exception as e:   # pylint: disable=broad-except
                _log.error(e)
            self.updateScheduleWindow()

    # register the current completed roast
    @pyqtSlot()
    def register_completed_roast_slot(self) -> None:
        # if there is a non-empty schedule with a selected item
        if self.selected_remaining_item is not None:
            self.register_remaining_item(self.selected_remaining_item)

    def update_styles(self) -> None:
        if self.aw.app.darkmode:
            # set dark mode styles
            self.task_type.setStyleSheet(f'QLabel {{ color: {light_grey}; font-weight: 700; }}')
            self.task_position.setStyleSheet(f'QLabel {{ color: {light_grey}; font-weight: 700; }}')
            self.task_weight.setStyleSheet(
                f'{tooltip_dull_dark_background_style} QLabel {{ color: {dim_white}; font-size: 40px; font-weight: 700; }}')
            self.task_frame.setStyleSheet(f'background: {medium_dark_grey};')
        else:
            # set light mode styles
            self.task_type.setStyleSheet(f'QLabel {{ color: {dark_grey}; font-weight: 700; }}')
            self.task_position.setStyleSheet(f'QLabel {{ color: {dark_grey}; font-weight: 700; }}')
            self.task_weight.setStyleSheet(
                f'{tooltip_style} QLabel {{ color: {plus_alt_blue}; font-size: 40px; font-weight: 700; }}')
            self.task_frame.setStyleSheet(f'background: {dull_white};')


    # called from main:updateSchedule() on opening the scheduler dialog, on schedule filter changes, on app raise,
    # on stock updates (eg. after successful login) and on plus disconnect
    # also called on switching between light and dark mode to adjust the colors accordingly
    # Note that on app raise (depending on the interval) also a stock update is triggered fetching the latest schedule from the server along
    @pyqtSlot()
    def updateScheduleWindow(self) -> None:
        _log.debug('updateScheduleWindow()')
        self.update_styles()
        # load completed roasts cache
        load_completed(self.aw.plus_account_id)
        # if the currently loaded profile is among the completed_items, its corresponding entry in that completed list is updated with the information
        # from the current loaded profile as properties might have been changed via the RoastProperties dialog
        if self.aw.qmc.roastUUID is not None:
            completed_item:Optional[CompletedItem] = next((ci for ci in self.completed_items if ci.roastUUID.hex == self.aw.qmc.roastUUID), None)
            if completed_item is not None:
                self.updates_completed_from_roast_properties(completed_item)
        if self.aw.plus_account is None:
            self.stacked_widget.setCurrentWidget(self.message_widget)
        else:
            self.stacked_widget.setCurrentWidget(self.main_splitter)
            # update scheduled and completed items
            self.updateScheduledItems()                                 # updates the current schedule items from received stock data
            load_prepared(self.aw.plus_account_id, self.scheduled_items)# load the prepared items cache and update according to the valid schedule items
            load_hidden(self.aw.plus_account_id, self.scheduled_items)  # load the hidden items cache and update according to the valid schedule items
            self.completed_items = self.getCompletedItems()             # updates completed items from cache
            self.updateFilters()                                        # update filter widget (user and machine)

            # show empty message if there are no scheduled items or the schedule items scrolling widget if there are entries
            if self.scheduled_items == []:
                # clear selection and reset scheduleID
                self.selected_remaining_item = None
                if self.aw.qmc.timeindex[6] == 0:
                    # if DROP is not set we clear the ScheduleItem UUID/Date
                    self.aw.qmc.scheduleID = None
                    self.aw.qmc.scheduleDate = None
                # show empty schedule message
                self.remaining_message.setText(QApplication.translate('Plus', 'Schedule empty!{}Plan your schedule on {}').format('<BR><BR>', f'<a href="{schedulerLink()}">{plus.config.app_name}</a><br>'))
                self.stacked_remaining_widget.setCurrentWidget(self.remaining_message_widget)
                self.setAppBadge(0)
            else:
                displayed_scheduled_items = self.updateRemainingItems() # redraw To-Do's widget
                if displayed_scheduled_items > 0:
                    self.stacked_remaining_widget.setCurrentWidget(self.remaining_scrollarea)
                else:
                    self.remaining_message.setText(f"{QApplication.translate('Plus', 'Nothing scheduled for you today!{}Deactivate filters to see all items.').format('<BR><BR>')}<br>")
                    self.stacked_remaining_widget.setCurrentWidget(self.remaining_message_widget)


            # show empty message if there are no completed items or the completed splitter widget if there are entries
            if not self.completed_items:
                self.completed_stacked_widget.setCurrentWidget(self.completed_message_widget)
            else:
                self.updateRoastedItems()                               # redraw Completed widget
                self.completed_stacked_widget.setCurrentWidget(self.completed_splitter)

            # the weight unit might have changed, we update its label
            self.roasted_weight_suffix.setText(self.aw.qmc.weight[2].lower())
            # update next weight item
            self.set_next()



class WeightItemDisplay(Display):
    def __init__(self, schedule_window:'ScheduleWindow') -> None:
        self.schedule_window:ScheduleWindow = schedule_window
        super().__init__()

    def clear(self) -> None: # pylint: disable=no-self-use
        self.schedule_window.task_type.setText('')
        self.schedule_window.task_title.setText('')
        self.schedule_window.task_position.setText('')
        self.schedule_window.task_weight.setText('--')
        self.schedule_window.task_weight.setToolTip(QApplication.translate('Plus', 'nothing to weight'))

    def show_item(self, item:'WeightItem') -> None: # pylint: disable=unused-argument,no-self-use
        if isinstance(item, GreenWeightItem):
            self.schedule_window.task_type.setText(' '.join(QApplication.translate('Label', 'Green').lower()))
        else:
            self.schedule_window.task_type.setText(' '.join(QApplication.translate('Label', 'Roasted').lower()))
        self.schedule_window.task_title.setText(item.title)
        self.schedule_window.task_position.setText(item.position)
        self.schedule_window.task_weight.setText(render_weight(item.weight, 1, item.weight_unit_idx))
        self.schedule_window.task_weight.setToolTip(item.description)
