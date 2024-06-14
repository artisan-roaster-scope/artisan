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
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
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
import logging
from uuid import UUID

try:
    from PyQt6.QtCore import (Qt, QMimeData, QSettings, pyqtSlot, pyqtSignal, QPoint, QPointF, QLocale, QDate, QDateTime, QSemaphore, QTimer) # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtGui import (QDrag, QPixmap, QPainter, QTextLayout, QTextLine, QColor, QFontMetrics) # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QTabWidget,  # @UnusedImport @Reimport  @UnresolvedImport
            QCheckBox, QGroupBox, QScrollArea, QSplitter, QLabel, QSizePolicy,  # @UnusedImport @Reimport  @UnresolvedImport
            QGraphicsDropShadowEffect, QPlainTextEdit, QLineEdit)  # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import (Qt, QMimeData, QSettings, pyqtSlot, pyqtSignal, QPoint, QPointF, QLocale, QDate, QDateTime, QSemaphore, QTimer) # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtGui import (QDrag, QPixmap, QPainter, QTextLayout, QTextLine, QColor, QFontMetrics) # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QTabWidget, # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
            QCheckBox, QGroupBox, QScrollArea, QSplitter, QLabel, QSizePolicy,  # @UnusedImport @Reimport  @UnresolvedImport
            QGraphicsDropShadowEffect, QPlainTextEdit, QLineEdit)  # @UnusedImport @Reimport  @UnresolvedImport


from babel.dates import format_date
from pydantic import BaseModel, Field, PositiveInt, UUID4, field_validator, model_validator, computed_field, field_serializer
from typing import Final, Tuple, List, Set, Dict, Optional, Any, TypedDict, cast, TextIO, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # noqa: F401 # pylint: disable=unused-import
    from PyQt6.QtCore import QObject, QEvent, QRect, QMargins # noqa: F401 # pylint: disable=unused-import
    from PyQt6.QtGui import (QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent, QDropEvent, QCloseEvent,  # noqa: F401 # pylint: disable=unused-import
        QResizeEvent, QPaintEvent, QEnterEvent, QMouseEvent, QTextDocument, QKeyEvent) # noqa: F401 # pylint: disable=unused-import
    from PyQt6.QtWidgets import QLayout, QLayoutItem, QBoxLayout # noqa: F401 # pylint: disable=unused-import


import plus.register
import plus.controller
import plus.connection
import plus.stock
import plus.config
import plus.sync
import plus.util
from plus.util import datetime2epoch, epoch2datetime
from artisanlib.util import (convertWeight, weight_units, render_weight, comma2dot, float2floatWeightVolume, getDirectory)


_log: Final[logging.Logger] = logging.getLogger(__name__)

completed_roasts_semaphore = QSemaphore(
    1
)  # protects access to the completed_roasts_cache file and the completed_roasts dict

completed_roasts_cache_path = getDirectory(plus.config.completed_roasts_cache)

## Configuration

# the minimal difference the edited roasted weight in kg of a completed item must have
# to be able to persist the change, compensating back-and-forth unit conversion errors
roasted_weight_editing_minimal_diff: Final[float] = 0.07 # 70g

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
dim_white: Final[str] = '#EEEEEE'
dark_white: Final[str] = '#505050'
super_light_grey_hover: Final[str] = '#EEEEEE'
super_light_grey: Final[str] = '#E3E3E3'
very_light_grey: Final[str] = '#dddddd'
light_grey_hover: Final[str] = '#D0D0D0'
light_grey: Final[str] = '#C0C0C0'
dark_grey_hover: Final[str] = '#909090'
dark_grey: Final[str] = '#808080'
very_dark_grey: Final[str] = '#222222'
#
drag_indicator_color: Final[str] = very_light_grey
shadow_color: Final[str] = very_dark_grey


class CompletedItemDict(TypedDict):
    scheduleID:str   # the ID of the ScheduleItem this completed item belongs to
    roastUUID:str
    roastdate: float # as epoch
    roastbatchnr: int
    roastbatchprefix: str
    count: int       # total count >0 of corresponding ScheduleItem
    sequence_id: int # sequence id of this roast (sequence_id <= count)
    title:str
    coffee_label: Optional[str]
    blend_label: Optional[str]
    store_label: Optional[str]
    batchsize: float # in kg
    weight: float    # in kg (resulting weight)
    color: int
    moisture: float  # in %
    density: float   # in g/l
    roastingnotes: str

# ordered list of dict with the completed roasts data (latest roast first)
completed_roasts_cache:List[CompletedItemDict] = []


class ScheduledItem(BaseModel):
    id: str = Field(alias='_id')
    date: datetime.date
    count: PositiveInt
    title: str
    coffee: Optional[str] = Field(default=None)
    blend: Optional[str] = Field(default=None)
    store: str = Field(..., alias='location')
    weight: float = Field(..., alias='amount')       # in kg
    machine: Optional[str] = Field(default=None)
    user: Optional[str] = Field(default=None)
    nickname: Optional[str] = Field(default=None)
    template: Optional[UUID4] = Field(default=None)  # note that this generates UUID objects. To get a UUID string without dashes use uuid.hex.
    note: Optional[str] = Field(default=None)
    roasts: Set[UUID4] = Field(default=set())           # note that this generates UUID objects. To get a UUID string without dashes use uuid.hex.

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
    sequence_id: PositiveInt # sequence id of this roast (sequence_id <= count)
    roastUUID: UUID4
    roastdate: datetime.datetime
    roastbatchnr: int
    roastbatchprefix: str
    title: str
    coffee_label: Optional[str] = Field(default=None)
    blend_label: Optional[str] = Field(default=None)
    store_label: Optional[str] = Field(default=None)
    batchsize: float # in kg
    weight: float    # in kg (resulting weight)
    color: int
    moisture: float # in %
    density: float  # in g/l
    roastingnotes: str = Field(default='')

    @computed_field  # type:ignore[misc] # Decorators on top of @property are not supported
    @property
    def prefix(self) -> str:
        res = ''
        if self.roastbatchnr > 0:
            res = f'{self.roastbatchprefix}{self.roastbatchnr}'
        return res

    @model_validator(mode='after') # pyright:ignore[reportArgumentType]
    def coffee_or_blend(self) -> 'CompletedItem':
# as CompletedItems are generated for ScheduledItems where store and one of blend/coffee needs to be set
# the store_label and one of the blend_label/coffee_label should never be empty, but in case they are we
# handle this without further ado
#        if self.coffee_label is None and self.blend_label is None:
#            raise ValueError('Either coffee_label or blend_label must be specified')
#        if self.coffee_label is not None and self.blend_label is not None:
#            raise ValueError('Either coffee_label or blend_label must be specified, but not both')
        if len(self.title) == 0:
            raise ValueError('Title cannot be empty')
        if self.sequence_id > self.count:
            raise ValueError('sequence_id cannot be larger than total count of roasts per ScheduleItem')
        return self

    @field_serializer('roastdate', when_used='json')
    def serialize_roastdate_to_epoch(roastdate: datetime.datetime) -> int: # type:ignore[misc] # pylint: disable=no-self-argument
        return int(roastdate.timestamp())

    @field_serializer('roastUUID', when_used='json')
    def serialize_roastUUID_to_str(roastUUID: UUID4) -> str: # type:ignore[misc] # pylint: disable=no-self-argument
        return roastUUID.hex


    # updates this CompletedItem with the data given in profile_data
    def update_completed_item(self, profile_data:Dict[str, Any]) -> bool:
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
            ground_color = int(float(round(profile_data['ground_color'])))
            if ground_color != self.color:
                updated = True
                self.color = ground_color
        if 'density_roasted' in profile_data:
            density_roasted = float(profile_data['density_roasted'])
            if density_roasted != self.density:
                updated = True
                self.density = density_roasted
        if 'moisture' in profile_data:
            moisture = float(profile_data['moisture'])
            if moisture != self.moisture:
                updated = True
                self.moisture = moisture
        if 'notes' in profile_data:
            notes = str(profile_data['notes'])
            if notes != self.roastingnotes:
                updated = True
                self.roastingnotes = notes
        if updated:
            # we update the completed_roasts_cache entry
            completed_item_dict = self.model_dump(mode='json')
            if 'prefix' in completed_item_dict:
                del completed_item_dict['prefix']
            add_completed(cast(CompletedItemDict, completed_item_dict))
        return updated


###################
# completed roasts cache access
#
# NOTE: completed roasts data file access is not protected by portalocker for parallel access via a second Artisan instance
#   as the ArtisanViewer disables the scheduler, thus only one Artisan instance is handling this file


# save completed roasts data to local file cache
def save_completed() -> None:
    _log.debug('save_completed(): %s', len(completed_roasts_cache))
    try:
        completed_roasts_semaphore.acquire(1)
        f:TextIO
        with open(completed_roasts_cache_path, 'w', encoding='utf-8') as f:
            json.dump(completed_roasts_cache, f)
    except Exception as e:  # pylint: disable=broad-except
        _log.error(e)
    finally:
        if completed_roasts_semaphore.available() < 1:
            completed_roasts_semaphore.release(1)


# load completed roasts data from local file cache
def load_completed() -> None:
    global completed_roasts_cache  # pylint: disable=global-statement
    _log.debug('load_completed()')
    try:
        completed_roasts_semaphore.acquire(1)
        f:TextIO
        with open(completed_roasts_cache_path, encoding='utf-8') as f:
            completed_roasts = json.load(f)
            today_completed = []
            previously_completed = []
            today = datetime.datetime.now(tz=datetime.timezone.utc)
            for ci in completed_roasts:
                if 'roastdate' in ci:
                    if epoch2datetime(ci['roastdate']).date() == today.date():
                        today_completed.append(ci)
                    else:
                        previously_completed.append(ci)
            if len(previously_completed)>0:
                previous_session_epoch:float = previously_completed[0].get('roastdate', datetime2epoch(today))
                previous_session_date = epoch2datetime(previous_session_epoch).date()
                previously_completed = [pc for pc in previously_completed if 'roastdate' in pc and epoch2datetime(pc['roastdate']).date() == previous_session_date]
            # we keep all roasts completed today as well as all from the previous roast session
            completed_roasts_cache = today_completed + previously_completed
    except Exception as e:  # pylint: disable=broad-except
        _log.error(e)
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
def add_completed(ci:CompletedItemDict) -> None:
    if 'roastUUID' in ci:
        # test if there is already a completed roasts with that UUID
        idx = next((i for i,d in enumerate(completed_roasts_cache) if 'roastUUID' in d and d['roastUUID'] == ci['roastUUID']), None)
        try:
            completed_roasts_semaphore.acquire(1)
            if idx is None:
                # add ci to front
                completed_roasts_cache.insert(0, ci)
            else:
                # we replace the existing entry by ci
                completed_roasts_cache[idx] = ci
        except Exception as e:  # pylint: disable=broad-except
            _log.error(e)
        finally:
            if completed_roasts_semaphore.available() < 1:
                completed_roasts_semaphore.release(1)


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


    def __init__(self, text:str = '', mode:Qt.TextElideMode = Qt.TextElideMode.ElideMiddle):
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

    selected = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        layout = QHBoxLayout()
        left:str = self.getLeft()
        self.first_label = QLabel(left)
        if left != '':
            self.first_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            layout.addWidget(self.first_label)
        layout.addWidget(QElidedLabel(self.getMiddle()))
        layout.addWidget(QLabelRight(self.getRight()))
        layout.setSpacing(5)
        layout.setContentsMargins(5,5,5,5)
        self.setLayout(layout)
        self.setProperty('Hover', False)
        self.setProperty('Selected', False)


    def getFirstLabel(self) -> QLabel:
        return self.first_label


    def getLeft(self) -> str: # pylint: disable=no-self-argument,no-self-use
        return ''


    def getMiddle(self) -> str: # pylint: disable=no-self-argument,no-self-use
        return ''


    def getRight(self) -> str: # pylint: disable=no-self-argument,no-self-use
        return ''


    def makeShadow(self) -> QGraphicsDropShadowEffect:
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(shadow_color))
        shadow.setOffset(0,0.7)
        return shadow


    def setText(self, txt:str) -> None:
        pass


    def mouseReleaseEvent(self, event:'Optional[QMouseEvent]') -> None:
        if event is not None:
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
        if self.data.roastdate.date() == now.date():
            # item roasted today
            item_color = plus_alt_blue
            item_color_hover = plus_alt_blue_hover

        head_line =  ('' if self.data.count == 1 else f'{self.data.sequence_id}/{self.data.count}')
        wrapper =  textwrap.TextWrapper(width=tooltip_line_length, max_lines=tooltip_max_lines, placeholder=tooltip_placeholder)
        title = '<br>'.join(wrapper.wrap(html.escape(self.data.title)))
        accent_color = (white if self.aw.app.darkmode else plus_blue)
        title_line = f"<p style='white-space:pre'><font color=\"{accent_color}\"><b><big>{title}</big></b></font></p>"
        coffee_blend_label = (f' {html.escape(self.data.coffee_label)}' if self.data.coffee_label is not None else (f' {html.escape(self.data.blend_label)}' if self.data.blend_label is not None else ''))
        beans_description = f'{render_weight(self.data.batchsize, 1, self.weight_unit_idx)}{coffee_blend_label}'
        store_line = (f'</b><br>{html.escape(self.data.store_label)}]' if (self.data.store_label is not None and self.data.store_label != '') else '')
        detailed_description = f"{head_line}{title_line}<p style='white-space:pre'>{beans_description}{store_line}"
        self.setToolTip(detailed_description)

        self.setStyleSheet(
            'QToolTip { padding: 5px; opacity: 240; }'
            f'NoDragItem[Selected=false][Hover=false] {{ border:0px solid {item_color}; background: {item_color}; border-radius: {border_radius}px; }}'
            f'NoDragItem[Selected=false][Hover=true] {{ border:0px solid {item_color_hover}; background: {item_color_hover}; border-radius: {border_radius}px; }}'
            f'NoDragItem[Selected=true][Hover=false] {{ border:0px solid {plus_red}; background: {plus_red}; border-radius: {border_radius}px; }}'
            f'NoDragItem[Selected=true][Hover=true] {{ border:0px solid {plus_red_hover}; background: {plus_red_hover}; border-radius: {border_radius}px; }}'
            f'QLabel {{ font-weight: bold; color: {dim_white}; }}'
            f'QLabelRight {{ font-size: 10pt; }}'
            'QElidedLabel { font-weight: normal; }')


    def getLeft(self) -> str:
        return f'{self.data.prefix}'


    def getMiddle(self) -> str:
        return f'{self.data.title}'


    def getRight(self) -> str:
        days_diff = (self.now.date() - self.data.roastdate.date()).days
        task_date_str = ''
        if days_diff == 0:
            # for time formatting we use the system locale
            locale = QLocale()
            dt = QDateTime.fromSecsSinceEpoch(int(datetime2epoch(self.data.roastdate)))
            task_date_str = locale.toString(dt.time(), QLocale.FormatType.ShortFormat)
        elif days_diff == 1:
            task_date_str = QApplication.translate('Plus', 'Yesterday').capitalize()
        elif days_diff < 7:
            # for date formatting we use the artisan-language locale
            locale = QLocale(self.locale_str)
            task_date_str = locale.toString(QDate(self.data.roastdate.date().year, self.data.roastdate.date().month, self.data.roastdate.date().day), 'dddd').capitalize()
        else:
            # date formatted according to the locale without the year
            task_date_str = format_date(self.data.roastdate.date(), format='long', locale=self.locale_str).replace(format_date(self.data.roastdate.date(), 'Y', locale=self.locale_str),'').strip().rstrip(',')
        return task_date_str

    def select(self) -> None:
        self.setProperty('Selected', True)
        self.setStyle(self.style())

    def deselect(self) -> None:
        self.setProperty('Selected', False)
        self.setStyle(self.style())



class DragItem(StandardItem):
    def __init__(self, data:ScheduledItem, aw:'ApplicationWindow', today:datetime.date, user_id: Optional[str], machine: str) -> None:
        self.aw = aw
        self.data:ScheduledItem = data
        self.weight_unit_idx = weight_units.index(self.aw.qmc.weight[2])

        super().__init__()
        self.setGraphicsEffect(self.makeShadow())


        # my items are all tasks that are explicitly targeting my user and machine
        self.mine: bool = (data.user is not None and user_id is not None and data.user == user_id and
                data.machine is not None and machine != '' and data.machine == machine)
        self.today: bool = data.date == today

        days_diff = (data.date - today).days
        task_date:str
        if days_diff == 0:
            task_date = QApplication.translate('Plus', 'Today')
        elif days_diff == 1:
            task_date = QApplication.translate('Plus', 'Tomorrow')
        elif days_diff < 7:
            locale = QLocale(self.aw.locale_str)
            task_date = locale.toString(QDate(data.date.year, data.date.month, data.date.day), 'dddd').capitalize()
        else:
            # date formatted according to the locale without the year
            task_date = format_date(data.date, format='long', locale=self.aw.locale_str).replace(format_date(data.date, 'Y', locale=self.aw.locale_str),'').strip().rstrip(',')

        user_nickname:Optional[str] = plus.connection.getNickname()
        task_operator = (QApplication.translate('Plus', 'by anybody') if data.user is None else
            (f"{QApplication.translate('Plus', 'by')} {(html.escape(user_nickname) if user_nickname is not None else '')}" if user_id is not None and data.user == user_id else
                (f"{QApplication.translate('Plus', 'by')} {html.escape(data.nickname)}" if data.nickname is not None else
                    (QApplication.translate('Plus', 'by colleague' if user_id is not None else '')))))
        task_machine = ('' if data.machine is None else f" {QApplication.translate('Plus', 'on')} {html.escape(data.machine)}")
        task_operator_and_machine = f'{task_operator}{task_machine}'
        if task_operator_and_machine != '':
            task_operator_and_machine = f', {task_operator_and_machine}'
        todo = QApplication.translate('Plus', '({} of {} done)').format(len(self.data.roasts), self.data.count)
        head_line = f'{task_date}{task_operator_and_machine}<br>{todo}'
        wrapper =  textwrap.TextWrapper(width=tooltip_line_length, max_lines=tooltip_max_lines, placeholder=tooltip_placeholder)
        title = '<br>'.join(wrapper.wrap(html.escape(self.data.title)))
        accent_color = (white if self.aw.app.darkmode else plus_blue)
        title_line = f"<p style='white-space:pre'><font color=\"{accent_color}\"><b><big>{title}</big></b></font></p>"

        beans_description = ''
        if data.coffee is not None:
            coffee = plus.stock.getCoffee(data.coffee)
            if coffee is not None:
                store_label:str = plus.stock.getLocationLabel(coffee, data.store)
                if store_label != '':
                    store_label = f'<br>[{html.escape(store_label)}]'
                beans_description = f'<b>{html.escape(plus.stock.coffeeLabel(coffee))}</b>{store_label}'
        else:
            blends = plus.stock.getBlends(self.weight_unit_idx, data.store)
            blend = next((b for b in blends if plus.stock.getBlendId(b) == data.blend and plus.stock.getBlendStockDict(b)['location_hr_id'] == data.store), None)
            if blend is not None:
                blend_lines = ''.join([f'<tr><td>{html.escape(bl[0])}</td><td>{html.escape(bl[1])}</td></tr>'
                            for bl in plus.stock.blend2weight_beans(blend,self.weight_unit_idx, data.weight)])
                beans_description = f"<b>{html.escape(plus.stock.getBlendName(blend))}</b> [{html.escape(plus.stock.getBlendStockDict(blend)['location_label'])}]<table>{blend_lines}</table>"
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
                'QToolTip { padding: 5px; opacity: 240;  }'
                f'DragItem[Selected=true][Hover=false] {{ border:{border_width}px solid {selected_item_color}; background: {selected_item_color}; border-radius: {border_radius}px; }}'
                f'DragItem[Selected=true][Hover=true] {{ border:{border_width}px solid {selected_item_color_hover}; background: {selected_item_color_hover}; border-radius: {border_radius}px; }}'
                f'DragItem[Selected=false][Hover=false] {{ border:{border_width}px solid {item_color}; background: {item_color}; border-radius: {border_radius}px; }}'
                f'DragItem[Selected=false][Hover=true] {{ border:{border_width}px solid {item_color_hover}; background: {item_color_hover}; border-radius: {border_radius}px; }}'
                f'QLabel {{ font-weight: bold; color: {today_text_color}; }}'
                'QElidedLabel { font-weight: normal; }')
        else:
            self.setStyleSheet(
                'QToolTip { padding: 5px; opacity: 240; }'
                f'DragItem[Selected=true][Hover=false] {{ border:{border_width}px solid {selected_item_color}; background: {open_item_background}; border-radius: {border_radius}px; }}'
                f'DragItem[Selected=true][Hover=true] {{ border:{border_width}px solid {selected_item_color_hover}; background: {open_item_background_hover}; border-radius: {border_radius}px; }}'
                f'DragItem[Selected=false][Hover=false] {{ border:{border_width}px solid {item_color}; background: {open_item_background}; border-radius: {border_radius}px; }}'
                f'DragItem[Selected=false][Hover=true] {{ border:{border_width}px solid {item_color_hover}; background: {open_item_background_hover}; border-radius: {border_radius}px; }}'
                f'QLabel {{ font-weight: bold; color: {otherday_text_color}; }}'
                'QElidedLabel { font-weight: normal; }')


    def getLeft(self) -> str:
        return f'{max(0,self.data.count - len(self.data.roasts))}x'


    def getMiddle(self) -> str:
        return self.data.title


    def getRight(self) -> str:
        return f'{render_weight(self.data.weight, 1, self.weight_unit_idx)}'


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
            self.setGraphicsEffect(self.makeShadow())
            drag.exec(Qt.DropAction.MoveAction)


    def select(self, aw:'ApplicationWindow') -> None:
        self.setProperty('Selected', True)
        self.setStyle(self.style())
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
            self._drag_target_indicator.hide()

            if self.drag_source is not None:
                widget:Optional[QObject] = self.drag_source
                if widget is not None and isinstance(widget, QWidget):
                    # Use drop target location for destination, then remove it.
                    self._drag_target_indicator.hide()
                    index = self.blayout.indexOf(self._drag_target_indicator)
                    if index is not None:
                        self.blayout.insertWidget(index, widget) # pyright:ignore[reportArgumentType]
                        self.orderChanged.emit(self.get_item_data())
                        widget.show() # pyright:ignore[reportAttributeAccessIssue]
                        self.blayout.activate()

            e.accept()


    def dragMoveEvent(self, e:'Optional[QDragMoveEvent]') -> None:
        if e is not None:
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
            e.accept()


    def dropEvent(self, e:'Optional[QDropEvent]') -> None:
        if e is not None and e.source() is not None:
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
            e.accept()


    def _find_drop_location(self, e:'QDragMoveEvent') -> int:
        pos = e.position()
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




class ScheduleWindow(QWidget): # pyright:ignore[reportGeneralTypeIssues]

    register_completed_roast = pyqtSignal()

    def __init__(self, parent:'QWidget', aw:'ApplicationWindow', activeTab:int = 0) -> None:
        if aw.get_os()[0] == 'RPi':
            super().__init__(None) # set the parent to None to make Schedule windows on RPi Bookworm non-modal (not blocking the main window)
        else:
            super().__init__(parent) # if parent is set to None, Schedule panels hide behind the main window in full screen mode on Windows!

        self.aw = aw # the Artisan application window
        self.activeTab:int = activeTab

        self.scheduled_items:List[ScheduledItem] = []
        self.completed_items:List[CompletedItem] = []

        # holds the currently selected remaining DragItem widget if any
        self.selected_remaining_item:Optional[DragItem] = None

        # holds the currently selected completed NoDragItem widget if any
        self.selected_completed_item:Optional[NoDragItem] = None

        settings = QSettings()
        if settings.contains('ScheduleGeometry'):
            self.restoreGeometry(settings.value('ScheduleGeometry'))
        else:
            self.resize(250,300)

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

        self.day_filter = QCheckBox(QApplication.translate('Plus','Today'))
        self.day_filter.setChecked(self.aw.schedule_day_filter)
        self.day_filter.stateChanged.connect(self.remainingFilterChanged)
        self.user_filter = QCheckBox()
        self.user_filter.setChecked(self.aw.schedule_user_filter)
        self.user_filter.stateChanged.connect(self.remainingFilterChanged)
        self.machine_filter = QCheckBox()
        self.machine_filter.setChecked(self.aw.schedule_machine_filter)
        self.machine_filter.stateChanged.connect(self.remainingFilterChanged)

        remaining_filter_layout = QVBoxLayout()
        remaining_filter_layout.addWidget(self.day_filter)
        remaining_filter_layout.addWidget(self.user_filter)
        remaining_filter_layout.addWidget(self.machine_filter)
        remaining_filter_group = QGroupBox('Filters')
        remaining_filter_group.setLayout(remaining_filter_layout)

        remaining_scrollarea = QScrollArea()
        remaining_scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        remaining_scrollarea.setWidgetResizable(True)
        remaining_scrollarea.setWidget(remaining_widget)
        remaining_scrollarea.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
#        remaining_scrollarea.setFrameShadow(QFrame.Shadow.Sunken)
#        remaining_scrollarea.setFrameShape(QFrame.Shape.Panel)
        remaining_scrollarea.setMinimumWidth(remaining_widget.minimumSizeHint().width())

        remaining_filter_scrollarea = QScrollArea()
        remaining_filter_scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        remaining_filter_scrollarea.setWidgetResizable(True)
        remaining_filter_scrollarea.setWidget(remaining_filter_group)
        remaining_filter_scrollarea.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        self.remaining_splitter = QSplitter(Qt.Orientation.Vertical)
        self.remaining_splitter.addWidget(remaining_scrollarea)
        self.remaining_splitter.addWidget(remaining_filter_scrollarea)
        self.remaining_splitter.setSizes([100,0])

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
        completed_scrollarea.setMinimumWidth(remaining_widget.minimumSizeHint().width())

        self.roasted_weight = QLineEdit()
        self.roasted_weight.setToolTip(QApplication.translate('Label','Weight'))
        self.roasted_weight.setValidator(self.aw.createCLocaleDoubleValidator(0., 9999999., 4, self.roasted_weight))
        self.roasted_weight.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.roasted_weight.editingFinished.connect(self.roasted_weight_changed)
        self.roasted_weight_suffix = QLabel(self.aw.qmc.weight[2].lower())
        self.roasted_weight_suffix.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.roasted_color = QLineEdit()
        self.roasted_color.setToolTip(QApplication.translate('Label','Color'))
        self.roasted_color.setValidator(self.aw.createCLocaleDoubleValidator(0., 999., 2, self.roasted_color))
        self.roasted_color.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.roasted_color.editingFinished.connect(self.roasted_color_changed)
        roasted_color_suffix = QLabel('#')
        roasted_color_suffix.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.roasted_density = QLineEdit()
        self.roasted_density.setToolTip(QApplication.translate('Label','Density'))
        self.roasted_density.setValidator(self.aw.createCLocaleDoubleValidator(0., 999., 1, self.roasted_density))
        self.roasted_density.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.roasted_density.editingFinished.connect(self.roasted_density_changed)
        roasted_density_suffix = QLabel('g/l')
        roasted_density_suffix.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.roasted_moisture = QLineEdit()
        self.roasted_moisture.setToolTip(QApplication.translate('Label','Moisture'))
        self.roasted_moisture.setValidator(self.aw.createCLocaleDoubleValidator(0., 99., 1, self.roasted_moisture))
        self.roasted_moisture.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.roasted_moisture.editingFinished.connect(self.roasted_moisture_changed)

        roasted_moisture_suffix = QLabel('%')
        roasted_moisture_suffix.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.roasted_notes = QPlainTextEdit()
        self.roasted_notes.setPlaceholderText(QApplication.translate('Label', 'Roasting Notes'))

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
        roasted_first_line_layout.addSpacing(2)
        roasted_second_line_layout.addWidget(roasted_density_suffix)
        roasted_second_line_layout.addSpacing(10)
        roasted_second_line_layout.addWidget(self.roasted_moisture)
        roasted_first_line_layout.addSpacing(2)
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


        completed_details_layout = QVBoxLayout()
        completed_details_layout.addLayout(roasted_details_layout)
        completed_details_layout.addWidget(self.roasted_notes)
        completed_details_layout.setContentsMargins(0, 0, 0, 0)
        self.completed_details_group = QGroupBox(QApplication.translate('Label','Roasted'))
        self.completed_details_group.setLayout(completed_details_layout)
        self.completed_details_group.setEnabled(False)


        completed_details_scrollarea = QScrollArea()
        completed_details_scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        completed_details_scrollarea.setWidgetResizable(True)
        completed_details_scrollarea.setWidget(self.completed_details_group)
        completed_details_scrollarea.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        self.completed_splitter = QSplitter(Qt.Orientation.Vertical)
        self.completed_splitter.addWidget(completed_scrollarea)
        self.completed_splitter.addWidget(completed_details_scrollarea)
        self.completed_splitter.setSizes([100,0])
        self.completed_splitter_open_height: int = 0

#####

        self.TabWidget = QTabWidget()
        self.TabWidget.addTab(self.remaining_splitter, QApplication.translate('Tab', 'To-Do'))
        self.TabWidget.addTab(self.completed_splitter, QApplication.translate('Tab', 'Done'))
        self.TabWidget.setStyleSheet('QToolTip { padding: 5px; opacity: 240; }')

        layout = QVBoxLayout()
        layout.addWidget(self.TabWidget)
        layout.setContentsMargins(0, 10, 0, 0)

        settings = QSettings()
        if settings.contains('ScheduleRemainingSplitter'):
            self.remaining_splitter.restoreState(settings.value('ScheduleRemainingSplitter'))

        self.setLayout(layout)

        windowFlags = self.windowFlags()
        windowFlags |= Qt.WindowType.Tool
        self.setWindowFlags(windowFlags)

        self.setWindowTitle(QApplication.translate('Menu', 'Schedule'))

        self.aw.disconnectPlusSignal.connect(self.updateScheduleWindow)

        plus.stock.update() # explicit update stock on opening the scheduler!?
        self.updateScheduleWindow()

        # we set the active tab with a QTimer after the tabbar has been rendered once, as otherwise
        # some tabs are not rendered at all on Windows using Qt v6.5.1 (https://bugreports.qt.io/projects/QTBUG/issues/QTBUG-114204?filter=allissues)
        QTimer.singleShot(50, self.setActiveTab)

        # set all child's to NoFocus to receive the up/down arrow key events in keyPressEvent
        self.setChildrenFocusPolicy(self, Qt.FocusPolicy.NoFocus)

        self.register_completed_roast.connect(self.register_completed_roast_slot)

        _log.info('Scheduler started')

# WEIGHT:
#        from plus.weight import DialogDisplay, WeightManager
#        dd:DialogDisplay = DialogDisplay()
#        wm:WeightManager = WeightManager([dd])


    @pyqtSlot(list)
    def update_order(self, l:List[ScheduledItem]) -> None:
        self.scheduled_items = l


    @pyqtSlot()
    def setActiveTab(self) -> None:
        self.TabWidget.setCurrentIndex(self.activeTab)


    @pyqtSlot()
    def roasted_weight_changed(self) -> None:
        self.roasted_weight.setText(comma2dot(self.roasted_weight.text()))


    @pyqtSlot()
    def roasted_color_changed(self) -> None:
        self.roasted_color.setText(str(int(round(float(comma2dot(self.roasted_color.text()))))))


    @pyqtSlot()
    def roasted_moisture_changed(self) -> None:
        self.roasted_moisture.setText(comma2dot(self.roasted_moisture.text()))


    @pyqtSlot()
    def roasted_density_changed(self) -> None:
        self.roasted_density.setText(comma2dot(self.roasted_density.text()))


    @pyqtSlot(int)
    def remainingFilterChanged(self, _:int = 0) -> None:
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
                    self.selected_completed_item.selected.emit()
            else:
                super().keyPressEvent(event)


    @pyqtSlot('QCloseEvent')
    def closeEvent(self, _:Optional['QCloseEvent'] = None) -> None:
        # save completed roasts cache
        save_completed()
        # remember custom schedule item order
        self.aw.scheduled_items_uuids = self.get_scheduled_items_ids()
        # remember Dialog geometry
        settings = QSettings()
        #save window geometry
        settings.setValue('ScheduleGeometry', self.saveGeometry())
        #save splitter state
        QSettings().setValue('ScheduleRemainingSplitter',self.remaining_splitter.saveState())
        #free resources
        self.aw.schedule_window = None
        self.aw.scheduleFlag = False
        self.aw.scheduleAction.setChecked(False)
        self.aw.schedule_activeTab = self.TabWidget.currentIndex()
        if self.aw.qmc.timeindex[6] == 0:
            # if DROP is not set we clear the ScheduleItem UUID
            self.aw.qmc.scheduleID = None
        _log.info('Scheduler stopped')


    # updates the current schedule items by joining its roast with those received as part of a stock update from the server
    # adding new items at the end
    def updateScheduledItems(self) -> None:
        today = datetime.datetime.now(datetime.timezone.utc).astimezone().date()
        # remove outdated items which remained in the open app from yesterday
        current_schedule:List[ScheduledItem] = [si for si in self.scheduled_items if (si.date - today).days >= 0]
        plus.stock.init()
        schedule:List[plus.stock.ScheduledItem] = plus.stock.getSchedule()
#        _log.debug('schedule: %s',schedule)
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
        # iterate over new schedule
        for s in schedule:
            try:
                schedule_item:ScheduledItem = ScheduledItem.model_validate(s)
#                existing_item:Optional[ScheduledItem] = next((si for si in current_schedule if si.id == schedule_item.id), None)
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

#                # keep old item (only update completed items)
#                if existing_item is not None:
#                    existing_item.roasts.update(schedule_item.roasts)
#                    if len(existing_item.roasts) >= existing_item.count:
#                        # remove existing_item from schedule if completed (#roasts >= count)
#                        current_schedule.remove(existing_item)

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

#    def scheduledItemsfilter(self, today:datetime.date, item:ScheduledItem) -> bool:
#        # if user filter is active only items not for a specific user or for the current user (if available) are listed
#        # if machine filter is active only items not for a specific machine or for the current machine setup are listed in case a current machine is set
#        return ((not self.aw.schedule_day_filter or item.date == today) and
#                (not self.aw.schedule_user_filter or not bool(plus.connection.getNickname()) or item.user is None or item.user == self.aw.plus_user_id) and
#                (self.aw.qmc.roastertype_setup.strip() == '' or not self.aw.schedule_machine_filter or item.machine is None or
#                    (self.aw.qmc.roastertype_setup.strip() != '' and item.machine is not None and
#                        item.machine.strip() == self.aw.qmc.roastertype_setup.strip())))

    # sets the items values as properties of the current roast and links it back to this item
    def set_roast_properties(self, item:ScheduledItem) -> None:
        self.aw.qmc.scheduleID = item.id
        self.aw.qmc.title = item.title
        if not self.aw.qmc.flagstart or self.aw.qmc.title_show_always:
            self.aw.qmc.setProfileTitle(self.aw.qmc.title)
            self.aw.qmc.fig.canvas.draw()
        weight_unit_idx:int = weight_units.index(self.aw.qmc.weight[2])
        self.aw.qmc.weight = (convertWeight(item.weight, 1, weight_unit_idx), self.aw.qmc.weight[1], self.aw.qmc.weight[2])
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
                if coffee is not None:
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
                    blend:plus.stock.Blend = plus.stock.getBlendBlendDict(blend_structure, item.weight)
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
        if self.selected_remaining_item is not None:
            # clear previous selection
            self.selected_remaining_item.deselect()
        item.select(self.aw)
        self.selected_remaining_item = item
        if self.aw.qmc.flagon and self.aw.qmc.timeindex[6] == 0:
            # while sampling and DROP not yet set, we update the roast properties on schedule item changes
            self.set_selected_remaining_item_roast_properties()


    @pyqtSlot()
    def remaining_items_selection_changed(self) -> None:
        sender = self.sender()
        if sender is not None and isinstance(sender, DragItem):
            self.select_item(sender)


    def updateRemainingItems(self) -> None:
        self.drag_remaining.clearItems()
        today:datetime.date = datetime.datetime.now(datetime.timezone.utc).astimezone().date()
        drag_items_first_label_max_width = 0
        drag_first_labels = []
        selected_item:Optional[DragItem] = None
        for item in filter(lambda x: self.aw.scheduledItemsfilter(today, x), self.scheduled_items):
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
            # append item to list
            self.drag_remaining.add_item(drag_item)
        if selected_item is not None:
            # reselect the previously selected item
            self.select_item(selected_item)
        else:
            # otherwise select first item schedule is not empty
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
            batches_today, batches_later = (sum(max(0, (si.count - len(si.roasts))) for si in items) for items in (todays_items, later_items))
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
        else:
            self.TabWidget.setTabToolTip(0,'')
        # update app badge number:
        self.setAppBadge(len(scheduled_items))

    @staticmethod
    def setAppBadge(number:int) -> None:
        try:
            app = QApplication.instance()
            app.setBadgeNumber(max(0, number)) # type: ignore # "QCoreApplication" has no attribute "setBadgeNumber"
        except Exception: # pylint: disable=broad-except
            pass # setBadgeNumber only supported by Qt 6.5 and newer

    # update app badge to be called from outside of the ScheduleWindow if ScheduleWindow is not open, recomputing all data
    @staticmethod
    def updateAppBadge(aw:'ApplicationWindow') -> None:
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
            ScheduleWindow.setAppBadge(len([x for x in scheduled_items if aw.scheduledItemsfilter(today, x)]))
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)


    @pyqtSlot()
    def updateFilters(self) -> None:
        nickname:Optional[str] = plus.connection.getNickname()
        if nickname is not None and nickname != '':
            self.user_filter.setText(nickname)
            self.user_filter.show()
        else:
            self.user_filter.hide()
        machine_name:str = self.aw.qmc.roastertype_setup.strip()
        if machine_name != '':
            self.machine_filter.setText(machine_name)
            self.machine_filter.show()
        else:
            self.machine_filter.hide()


    def set_details(self, item:Optional[NoDragItem]) -> None:
        if item is None:
            self.roasted_weight.setText('')
            self.roasted_color.setText('')
            self.roasted_density.setText('')
            self.roasted_moisture.setText('')
            self.roasted_notes.setPlainText('')
            self.completed_details_group.setEnabled(False)
        else:
            data = item.data
            converted_weight = convertWeight(data.weight, 1, weight_units.index(self.aw.qmc.weight[2]))
            self.roasted_weight.setText(f'{float2floatWeightVolume(converted_weight):g}')
            self.roasted_color.setText(str(data.color))
            self.roasted_density.setText(f'{data.density:g}')
            self.roasted_moisture.setText(f'{data.moisture:g}')
            self.roasted_notes.setPlainText(data.roastingnotes)
            self.completed_details_group.setEnabled(True)


    # computes the difference between the UI NoDragItem and the linked CompletedItem
    # and returns only changed attributes as partial sync_record (lacking the roast_id)
    def changes(self, item:NoDragItem) -> Dict[str, Any]:
        data = item.data
        changes:Dict[str, Any] = {}
        try:
            converted_data_weight = convertWeight(data.weight, 1, weight_units.index(self.aw.qmc.weight[2]))
            converted_data_weight_str = f'{float2floatWeightVolume(converted_data_weight):g}'
            roasted_weight_value_str = comma2dot(self.roasted_weight.text())
            if converted_data_weight_str != roasted_weight_value_str:
                # on textual changes, send updated weight
                changes['end_weight'] = convertWeight(float(roasted_weight_value_str), weight_units.index(self.aw.qmc.weight[2]), 1)
        except Exception:  # pylint: disable=broad-except
            pass
        current_roasted_color = int(round(float(self.roasted_color.text())))
        if current_roasted_color != data.color:
            changes['ground_color'] = current_roasted_color
        current_roasted_density = float(self.roasted_density.text())
        if current_roasted_density != data.density:
            changes['density_roasted'] = current_roasted_density
        current_roasted_moisture = float(self.roasted_moisture.text())
        if current_roasted_moisture != data.moisture:
            changes['moisture'] = current_roasted_moisture
        current_notes = self.roasted_notes.toPlainText()
        if current_notes != data.roastingnotes:
            changes['notes'] = current_notes
        return changes


    # updates the changeable properties of the current loaded profiles roast properties from the given CompletedItem
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
            # not updated:
            #        roastbatchnr
            #        roastbatchprefix
            #        title
            # don't update the coffee/blend/store labels as we do not maintaine the corresponding hr_ids in CompletedItems
            #        coffee_label
            #        blend_label
            #        store_label
            #        batchsize


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
                        changes['modified_at'] = plus.util.epoch2ISO8601(time.time())
                        try:
                            plus.controller.connect(clear_on_failure=False, interactive=False)
                            r = plus.connection.sendData(plus.config.roast_url, changes, 'POST')
                            r.raise_for_status()
                            # update successfully transmitted, we now also add/update the CompletedItem linked to self.selected_completed_item
                            updated_completed_item:bool = self.selected_completed_item.data.update_completed_item(changes)
                            if updated_completed_item:
                                save_completed()
                            # if previous selected roast is loaded we write the changes to its roast properties
                            if self.selected_completed_item.data.roastUUID.hex == self.aw.qmc.roastUUID:
                                self.updates_roast_properties_from_completed(self.selected_completed_item.data)
                        except Exception as e:  # pylint: disable=broad-except
                            # updating data to server failed, we keep the selection
                            _log.error(e)
                            self.aw.sendmessageSignal.emit(QApplication.translate('Message', 'Updating completed roast properties failed'), True, None)
                            # we keep the selection
                            return
                    # in case data was not edited or updating the edits to server succeeded we
                    # clear previous selection
                    self.selected_completed_item.deselect()
                if sender != self.selected_completed_item:
                    if plus.sync.getSync(sender.data.roastUUID.hex) is None:
                        _log.info('completed roast %s could not be edited as corresponding sync record is missing', sender.data.roastUUID.hex)
                    else:
                        # fetch data if roast is participating in the sync record game
                        profile_data: Optional[Dict[str, Any]] = plus.sync.fetchServerUpdate(sender.data.roastUUID.hex, return_data = True)
                        if profile_data is not None:
                            # update completed items data from received profile_data
                            updated:bool = sender.data.update_completed_item(profile_data)
                            # on changes, update loaded profile if saved earlier
                            if (updated and self.aw.curFile is not None and sender.data.roastUUID.hex == self.aw.qmc.roastUUID and
                                    self.aw.qmc.plus_file_last_modified is not None and 'modified_at' in profile_data and
                                    plus.util.ISO86012epoch(profile_data['modified_at']) > self.aw.qmc.plus_file_last_modified):
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
        now:datetime.datetime = datetime.datetime.now(datetime.timezone.utc).astimezone()
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
        today:datetime.date = datetime.datetime.now(datetime.timezone.utc).astimezone().date()
        completed_items:List[CompletedItem] = self.completed_items
        if len(completed_items) > 0:
            todays_items = []
            earlier_items = []
            for ci in completed_items:
                if ci.roastdate == today:
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
            self.TabWidget.setTabToolTip(1, f"<p style='white-space:pre'><b>{todays_batches}</b>{('<br>' if (batches_today > 0 and batches_earlier > 1) else '')}{earlier_batches}</p>")
        else:
            self.TabWidget.setTabToolTip(1, '')


    def get_scheduled_items_ids(self) -> List[str]:
        return [si.id for si in self.scheduled_items]


    # register the current completed roast
    @pyqtSlot()
    def register_completed_roast_slot(self) -> None:
        # if there is a non-empty schedule with a selected item
        if self.selected_remaining_item is not None and self.aw.qmc.roastUUID is not None:
            _log.info('register completed roast %s', self.aw.qmc.roastUUID)
            # register roastUUID in (local) currently selected ScheduleItem
            self.selected_remaining_item.data.roasts.add(UUID(self.aw.qmc.roastUUID, version=4))
            # add roast to list of completed roasts
            weight_unit_idx:int = weight_units.index(self.aw.qmc.weight[2])
            batchsize = convertWeight(self.aw.qmc.weight[0], weight_unit_idx, 1) # batchsize converted to kg
            weight = convertWeight(self.aw.qmc.weight[1], weight_unit_idx, 1)    # resulting weight converted to kg
            completed_item:CompletedItemDict = {
                'scheduleID': self.selected_remaining_item.data.id,
                'count': self.selected_remaining_item.data.count,
                'sequence_id': len(self.selected_remaining_item.data.roasts),
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
                'color': self.aw.qmc.ground_color,
                'moisture': self.aw.qmc.moisture_roasted,
                'density': self.aw.qmc.density_roasted[0],
                'roastingnotes': self.aw.qmc.roastingnotes
            }
            add_completed(completed_item)
            save_completed()
            # update schedule, removing completed items and selecting the next one
            self.updateScheduleWindow()


    # called from main:updateSchedule() on opening the scheduler dialog, on schedule filter changes, on app raise,
    # on stock updates (eg. after successful login) and on plus disconnect
    # Note that on app raise (depending on the interval) also a stock update is triggered fetching the latest schedule from the server along
    @pyqtSlot()
    def updateScheduleWindow(self) -> None:
        # load completed roasts cache
        load_completed()
        # update scheduled and completed items
        self.updateScheduledItems()                     # updates the current schedule items from received stock data
        self.completed_items = self.getCompletedItems() # updates completed items from cache
        self.updateFilters()                            # update filter widget (user and machine)
        self.updateRemainingItems()                     # redraw To-Do's widget
        self.updateRoastedItems()                       # redraw Completed widget
        # the weight unit might have changed, we update its label
        self.roasted_weight_suffix = QLabel(self.aw.qmc.weight[2].lower())
