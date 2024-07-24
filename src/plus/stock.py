#
# stock.py
#
# Copyright (c) 2023, Paul Holleis, Marko Luther
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

try:
    #pylint: disable = E, W, R, C
    from PyQt6.QtCore import QSemaphore, QObject, QThread, pyqtSlot, pyqtSignal # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import QApplication # @UnusedImport @Reimport  @UnresolvedImport
except Exception: # pylint: disable=broad-except
    #pylint: disable = E, W, R, C
    from PyQt5.QtCore import QSemaphore, QObject, QThread, pyqtSlot, pyqtSignal # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import QApplication # type: ignore # @UnusedImport @Reimport  @UnresolvedImport

import copy
import json
import time
import datetime
import logging

from artisanlib.util import (decodeLocal, encodeLocal, getDirectory, is_int_list, is_float_list, render_weight,
    weight_units, float2float, convertWeight)
from plus import config, connection, controller, util
from typing import Final, TypedDict, List, Union, Optional, Tuple, Dict, TextIO
from typing_extensions import NotRequired # Python <=3.10


_log: Final[logging.Logger] = logging.getLogger(__name__)


stock_semaphore = QSemaphore(
    1
)  # protects access to the stock_cache file and the stock dict

stock_cache_path = getDirectory(config.stock_cache)


# stock data structures

class CoffeeUnit(TypedDict):
    name: str
    size: int

class ScreenSize(TypedDict, total=False):
    min: int # noqa: A003
    max: int # noqa: A003

class CropDate(TypedDict, total=False):
    picked: List[int]  # max len = 2
    landed: List[int]  # max len = 2

class StockItem(TypedDict):
    location_hr_id: str
    location_label: str
    amount: float

class Coffee(TypedDict, total=False):
    hr_id:str
    label: str
    origin: str
    varietals: List[str]
    grade: str # not transferred from server!
    stock: List[StockItem]
    default_unit: CoffeeUnit
    moisture: float
    density: int
    screen_size: ScreenSize
    processing: str
    crop_date: CropDate

class BlendIngredient(TypedDict):
    coffee: str # coffees hr_id
    ratio: float
    ratio_num: NotRequired[int]
    ratio_denom: NotRequired[int]
    replace_coffee: NotRequired[str]
    replaceLabel: NotRequired[str]
    moisture: NotRequired[float]
    density: NotRequired[int]
    screen_min: NotRequired[int]
    screen_max: NotRequired[int]
    label: NotRequired[str]

class Blend(TypedDict):
    label: str
    ingredients: List[BlendIngredient]
    hr_id: NotRequired[str]
    moisture: NotRequired[float]
    density: NotRequired[int]
    screen_min: NotRequired[int]
    screen_max: NotRequired[int]

class ScheduledItem(TypedDict, total=False):
    _id: str                # ScheduledItem ObjectId
    date: str               # ISO date string 'YYYY-MM-DD'
    count: int              # number of roasts planned for this item
    title: str
    amount: float           # planned batch size in kg
    loss: Optional[float]   # default loss based calculated by magic on the server in % (either not given or guaranteed to be in range 5% < loss < 25%)
    location: str           # location hr_id
    coffee: Optional[str]   # coffee hr_id; only set if no blend is specified
    blend: Optional[str]    # blend hr_id; only set if no coffee is specified
    machine: Optional[str]  # optional target machine name
    user: Optional[str]     # optional target users UUID
    nickname: Optional[str] # optional nickname of target user
    template: Optional[str] # roast_id (UUID) of the selected template profile if any
    note: str
    roasts: List[str]       # roast_id's (UUID) of already completed roasts of this item

class Stock(TypedDict, total=False):
    coffees: List[Coffee]
    blends: List[Blend]
    replBlends: List[Blend]
    schedule: List[ScheduledItem]
    retrieved: float

ReplacementBlend = Tuple[float, Blend]
CoffeeLabelDict = Dict[str, str]
BlendStructure = Tuple[str, Tuple[Blend, StockItem, float, CoffeeLabelDict, float, List[ReplacementBlend]]]
BlendList = List[Union[str, List[List[Union[str,float]]]]]

stock:Optional[Stock] = None  # holds the dict with the current stock data (coffees, blends,..)

# in kg; only stock larger than stock_epsilon (10g)
# will be considered, the rest ignored
stock_epsilon = 0.01
###################
# stock cache update
#

# updates the stock cache


####### Stock Update Thread

worker:Optional['Worker'] = None
worker_thread:Optional[QThread] = None

class Worker(QObject): # pyright: ignore [reportGeneralTypeIssues] # Argument to class must be a base class
    startSignal = pyqtSignal()
    replySignal = pyqtSignal(float, float, str, int, list) # rlimit:float, rused:float, pu:str, notifications:int, machines:List[str]
    updatedSignal = pyqtSignal()  # issued once the stock was updated
    upToDateSignal = pyqtSignal() # issued if the stock was still valid and did NOT get update

    @pyqtSlot()
    def update_blocking(self) -> None:
        _log.debug('update_blocking()')
        if stock is None:
            load()
        fetch_enabled = False
        try:
            stock_semaphore.acquire(1)
            fetch_enabled = config.connected and (
                stock is None
                or (
                    'retrieved' in stock
                    and (time.time() - stock['retrieved'])
                    > config.stock_cache_expiration
                )
            )
        finally:
            if stock_semaphore.available() < 1:
                stock_semaphore.release(1)
        if fetch_enabled:
            res = self.fetch()
            if res:
                save()
                self.updatedSignal.emit()
        else:
            _log.debug('-> stock valid')
            self.upToDateSignal.emit()

    # requests stock data from server and fills the stock cache
    def fetch(self) -> bool:
        global stock  # pylint: disable=global-statement
        _log.debug('fetch()')
        try:
            # fetch from server (send along the current date to have the server filter the schedule correctly for the local timezone)
            d = connection.getData(f'{config.stock_url}?today={datetime.datetime.now().astimezone().date()}')
            _log.debug('-> %s', d.status_code)
            if d.status_code != 204 and d.headers['content-type'].strip().startswith('application/json'):
                j = d.json()
                if j:
                    rlimit,rused,pu,notifications,machines = util.extractAccountState(j)
                    self.replySignal.emit(rlimit,rused,pu,notifications,machines)
                if 'success' in j and j['success'] and 'result' in j and j['result'] is not None:
                    try:
                        stock_semaphore.acquire(1)
                        stock = j['result']
                        if stock is not None:
                            stock['retrieved'] = time.time()
                        _log.debug('-> retrieved')
    #                    _log.debug("stock = %s", stock)
                    finally:
                        if stock_semaphore.available() < 1:
                            stock_semaphore.release(1)
                    controller.reconnected()
                    return True
            _log.error('204: empty response on fetching stock')
            return False
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)
            controller.disconnect(remove_credentials=False, stop_queue=False)
            return False

def getWorker() -> Optional['Worker']:
    global worker, worker_thread  # pylint: disable=global-statement
    try:
        if worker_thread is None:
            worker_thread = QThread()
            worker_thread.start()
            worker = Worker()
            worker.moveToThread(worker_thread)
            worker.startSignal.connect(worker.update_blocking)
            worker.replySignal.connect(util.updateLimits)
            worker.updatedSignal.connect(util.updateSchedule)
            worker.upToDateSignal.connect(util.updateSchedule)
        return worker
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
    return None

@pyqtSlot()
def update() -> None:
    _log.debug('update()')
    try:
        getWorker()
        if worker is not None:
            worker.startSignal.emit()
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)


###################
# stock cache access
#
# NOTE: stock cache data file access is not protected by portalocker for parallel access via a second Artisan instance
#   as the ArtisanViewer handles is separate cache file

# save stock data to local file cache
def save() -> None:
    _log.debug('save()')
    try:
        stock_semaphore.acquire(1)
        if stock is not None:
            f:TextIO
            with open(stock_cache_path, 'w', encoding='utf-8') as f:
                json.dump(stock, f, indent=None, separators=(',', ':'), ensure_ascii=False)
    except Exception as e:  # pylint: disable=broad-except
        _log.error(e)
    finally:
        if stock_semaphore.available() < 1:
            stock_semaphore.release(1)

# try to load stock from cache if empty
def init() -> None:
    _log.debug('init()')
    if stock is None:
        load()

# load stock data from local file cache
def load() -> None:
    global stock  # pylint: disable=global-statement
    _log.debug('load()')
    try:
        stock_semaphore.acquire(1)
        f:TextIO
        with open(stock_cache_path, encoding='utf-8') as f:
            stock = json.load(f)
    except Exception as e:  # pylint: disable=broad-except
        _log.error(e)
    finally:
        if stock_semaphore.available() < 1:
            stock_semaphore.release(1)


###################
# convert between blend dict and list representation


# { "label": "blend", "ingredients": [{ "coffee": "C1", "ratio": 0.5 }, { "coffee": "C2", "ratio": 0.5 }]
#     =>
# [ "blend", [[ "C1", 0.5 ], [ "C2", 0.5 ]]]
def blend2list(blend_dict:Optional[Blend]) -> Optional[BlendList]:
    try:
        if (
            blend_dict is not None
            and 'label' in blend_dict
            and 'ingredients' in blend_dict
            and len(blend_dict['ingredients']) > 0
        ):
            blend_label = encodeLocal(blend_dict['label'])
            if blend_label is not None:
                ingredients:List[List[Union[str, float]]] = []
                for i in blend_dict['ingredients']:
                    coffee:Optional[str] = encodeLocal(i['coffee'])
                    ratio:float = i['ratio']
                    if coffee is None:
                        return None
                    ingredients.append([coffee, ratio])
                return [blend_label, ingredients]
        return None
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
        return None


def list2blend(blend_list: Optional[BlendList]) -> Optional[Blend]:
    try:
        if blend_list is not None and len(blend_list) == 2 and len(blend_list[1]) > 0:
            blend_label:Optional[str] = decodeLocal(blend_list[0])
            if blend_label is not None:
                ingredients: List[BlendIngredient] = []
                for i in blend_list[1]:
                    if len(i) == 2:
                        ic:Union[str,float] = i[0]
                        ir:Union[str,float] = i[1]
                        assert isinstance(ic, str)
                        assert isinstance(ir, (int, float))
                        coffee = decodeLocal(ic)
                        if coffee is None:
                            return None
                        bi:BlendIngredient = {'coffee': coffee, 'ratio': ir}
                        ingredients.append(bi)
                    else:
                        return None
                d:Blend = { 'label': blend_label, 'ingredients': ingredients}
                return d
        return None
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
        return None


###################
# coffee and blend stock access and rendering

unit_translations_singular = {
    'bag': QApplication.translate('Plus', 'bag'),
    'box': QApplication.translate('Plus', 'box'),
    'barrel': QApplication.translate('Plus', 'barrel'),
}
unit_translations_plural = {
    'bag': QApplication.translate('Plus', 'bags'),
    'box': QApplication.translate('Plus', 'boxes'),
    'barrel': QApplication.translate('Plus', 'barrels'),
}


def renderAmount(amount:float, default_unit:Optional[CoffeeUnit]=None, target_unit_idx:int=0) -> str:
    res = ''
    # first try to convert to default_unit (like "bags")
    try:
        if default_unit is not None:
            unit_size = int(default_unit['size'])
            if amount > unit_size:
                a = amount // unit_size
                if a > 1:
                    u = unit_translations_plural[default_unit['name']]
                else:
                    u = unit_translations_singular[default_unit['name']]
                res = f'{int(round(a))}{u}'
    except Exception:  # pylint: disable=broad-except
        pass
    # if we could not convert to default_unit type,
    # we convert to the weightunit
    if not res:
        # we convert the amount from Kg to the target_unit
        res = render_weight(amount, 1, target_unit_idx)
    return res


# ==================
# Schedule

# returns the list of ScheduledItem defined in stock
def getSchedule(acquire_lock:bool=True) -> List[ScheduledItem]:
    _log.debug('getSchedule()')
    try:
        if acquire_lock:
            stock_semaphore.acquire(1)
        if stock is not None and 'schedule' in stock:
            return stock['schedule']
        return []
    finally:
        if acquire_lock and stock_semaphore.available() < 1:
            stock_semaphore.release(1)


# ==================
# Stores
#   store:  <storeLabel,locationID>


def getStoreLabel(store:Tuple[str, str]) -> str:
    return store[0]


def getStoreId(store:Tuple[str, str]) -> str:
    return store[1]


# returns the list of stores defined in stock
def getStores(acquire_lock:bool=True) -> List[Tuple[str, str]]:
    _log.debug('getStores()')
    try:
        if acquire_lock:
            stock_semaphore.acquire(1)
        if stock is not None and 'coffees' in stock:
            res = {}
            for c in stock['coffees']:
                if 'stock' in c:
                    for s in c['stock']:
                        if (
                            'amount' in s
                            and s['amount'] is not None
                            and s['amount'] > stock_epsilon
                        ):
                            res[s['location_label']] = s['location_hr_id']
            return sorted(res.items(), key=getStoreLabel)
        return []
    finally:
        if acquire_lock and stock_semaphore.available() < 1:
            stock_semaphore.release(1)


# given a list of stores, returns a list of labels to populate the stores popup
def getStoreLabels(stores:List[Tuple[str, str]]) -> List[str]:
    return [getStoreLabel(s) for s in stores if getStoreId(s) is not None]


# returns the position of store id in stores or None if store not in the stores
def getStorePosition(storeId:str, stores:List[Tuple[str, str]]) -> Optional[int]:
    try:
        return [
            getStoreId(s) for s in stores if getStoreId(s) is not None
        ].index(storeId)
    except Exception:  # pylint: disable=broad-except
        return None

def getStoreItem(storeId:str, stores:List[Tuple[str, str]]) -> Optional[Tuple[str, str]]:
    return next((x for x in stores if getStoreId(x) == storeId), None)



# ==================
# Coffees
#   coffee:  <coffeeLabel,<coffeeDict,stockDict>>


def getCoffeeLabel(coffee:Tuple[str, Tuple[Coffee, StockItem]]) -> str:
    return coffee[0]


def getCoffeeCoffeeDict(coffee:Tuple[str, Tuple[Coffee, StockItem]]) -> Coffee:
    return coffee[1][0]


def getCoffeeStockDict(coffee:Tuple[str, Tuple[Coffee, StockItem]]) -> StockItem:
    return coffee[1][1]

# unused
#def getCoffeeId(coffee:Tuple[str, Tuple[Coffee, StockItem]]) -> str:
#    return getCoffeeCoffeeDict(coffee).get('hr_id','')


def getCoffeesLabels(coffees:List[Tuple[str, Tuple[Coffee, StockItem]]]) -> List[str]:
    return [getCoffeeLabel(c) for c in coffees]


def coffee2beans(c:Coffee) -> str:
    origin = ''
    try:
        origin_str = c['origin'].strip() # pyright:ignore[reportTypedDictNotRequiredAccess]
        if len(origin_str) > 0 and origin_str != 'null':
            origin = QApplication.translate('Countries', origin_str)
    except Exception:  # pylint: disable=broad-except
        pass
    if 'label' in c:
        label = c['label']
        if origin:
            label = f' {label}'
    else:
        label = ''
    processing = ''
    try:
        processing_str = c['processing'].strip() # pyright:ignore[reportTypedDictNotRequiredAccess]
        # processing_str can have the form "fully washed" or with
        # newer servers "Wet/fully washed"
        processing_split = processing_str.split('/')
        # we only use the specific term and ignore the category if given
        if len(processing_split) > 1:
            processing_str = processing_split[1].strip()
        else:
            processing_str = processing_split[0]
        if len(processing_str) > 0 and processing_str != 'null':
            processing = f' {processing_str}'
    except Exception:  # pylint: disable=broad-except
        pass
    grade = ''
    try:
        grade = f" {c['grade']}" # pyright:ignore[reportTypedDictNotRequiredAccess]
    except Exception:  # pylint: disable=broad-except
        pass
    varietals = ''
    try:
        if (
            'varietals' in c
            and c['varietals'] is not None
            and len(c['varietals']) > 0
        ):
            vs = [
                v.strip()
                for v in c['varietals']
                if v is not None and v not in {'null', ''}
            ]
            if processing == '':
                varietals = f" {', '.join(vs)}"
            else:
                varietals = f" ({', '.join(vs)})"
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
    bean = f'{processing}{grade}{varietals}'
    if bean:
        bean = f',{bean}'
    year = ''
    try:
        cy = c['crop_date'] # pyright:ignore[reportTypedDictNotRequiredAccess]
        picked = None
        landed = None
        try:
            picked = int(cy['picked'][0]) # pyright:ignore[reportTypedDictNotRequiredAccess]
        except Exception:  # pylint: disable=broad-except
            pass
        try:
            landed = int(cy['landed'][0]) # pyright:ignore[reportTypedDictNotRequiredAccess]
        except Exception:  # pylint: disable=broad-except
            pass
        if picked is not None and not bool(landed):
            year = f', {picked:d}'
        elif landed is not None and not bool(picked):
            year = f', {landed:d}'
        elif picked is not None and landed is not None:
            if picked == landed or landed <= picked:
                year = f', {picked:d}'
            else:
                year = f', {picked:d}/{landed:d}'
    except Exception:  # pylint: disable=broad-except
        pass
    return f'{origin}{label}{bean}{year}'

def coffeeLabel(c:Coffee) -> str:
    origin = ''
    try:
        origin_str = c['origin'].strip() # pyright:ignore[reportTypedDictNotRequiredAccess]
        if len(origin_str) > 0 and origin_str != 'null':
            origin = QApplication.translate(
                'Countries', origin_str
            )
    except Exception:  # pylint: disable=broad-except
        pass
    if origin != '':
        try:
            if 'crop_date' in c:
                cy = c['crop_date']
                if (
                    'picked' in cy
                    and len(cy['picked']) > 0
                    and cy['picked'][0] is not None
                ):
                    origin += f" {cy['picked'][0]:d}"
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)
        origin = f'{origin}, '
    return f"{origin}{c.get('label', '')}"

# returns a dict with all coffees with stock associated as string of the form  "<origin> <picked>, <label>"
# associated to their hr_id
def getCoffeeLabels() -> Dict[str, str]:
    try:
        stock_semaphore.acquire(1)
        if stock is not None and 'coffees' in stock:
            res = {}
            for c in stock['coffees']:
                try:
                    if 'hr_id' in c and 'stock' in c:
                        for s in c['stock']:
                            if 'amount' in s:
                                amount = s['amount']
                                if amount > stock_epsilon:
                                    res[coffeeLabel(c)] = c['hr_id']
                except Exception as e:  # pylint: disable=broad-except
                    _log.exception(e)
            return res
        return {}

    finally:
        if stock_semaphore.available() < 1:
            stock_semaphore.release(1)


def getCoffee(hr_id:str) -> Optional[Coffee]:
    if stock is not None and 'coffees' in stock:
        return next((x for x in stock['coffees'] if 'hr_id' in x and x['hr_id'] == hr_id), None)
    return None

# returns the location label for the given store_id from the given Coffee dict
def getLocationLabel(c:Coffee, location_hr_id:str) -> str:
    if 'stock' in c:
        return next( (si['location_label'] for si in c['stock'] if location_hr_id == si['location_hr_id']), '')
    return ''

# returns coffees with stock
def getCoffees(weight_unit_idx:int, store:Optional[str]=None) -> List[Tuple[str, Tuple[Coffee, StockItem]]]:
    _log.debug('getCoffees(%s,%s)', weight_unit_idx, store)
    try:
        stock_semaphore.acquire(1)
        if stock is not None and 'coffees' in stock:
            res = {}
            for c in stock['coffees']:
                try:
                    origin = ''
                    try:
                        origin_str = c['origin'].strip() # pyright:ignore[reportTypedDictNotRequiredAccess]
                        if len(origin_str) > 0 and origin_str != 'null':
                            origin = QApplication.translate(
                                'Countries', origin_str
                            )
                    except Exception:  # pylint: disable=broad-except
                        pass
                    if origin != '':
                        try:
                            if 'crop_date' in c:
                                cy = c['crop_date']
                                if (
                                    'picked' in cy
                                    and len(cy['picked']) > 0
                                    and cy['picked'][0] is not None
                                ):
                                    origin += f" {cy['picked'][0]:d}"
                        except Exception as e:  # pylint: disable=broad-except
                            _log.exception(e)
                        origin = f'{origin}, '
                    label = c.get('label', '')
                    default_unit = c.get('default_unit', None)
                    if 'stock' in c:
                        for s in c['stock']:
                            if (store is None or (
                                'location_hr_id' in s
                                and s['location_hr_id'] == store
                            )) and 'location_label' in s:
                                location = s['location_label']
                                amount = s['amount']
                                if (
                                    amount > stock_epsilon
                                ):  # TODO: check here the machines # pylint: disable=fixme
                                    # capacity limits
                                    # add location only if this coffee
                                    # is available in several locations
                                    loc = '' if store else f'{location}, '
                                    res[
                                        f'{origin}{label} [{loc}{renderAmount(amount,default_unit,weight_unit_idx)}]'
                                    ] = (c, s)
                except Exception as e:  # pylint: disable=broad-except
                    _log.exception(e)
            return sorted(res.items(), key=lambda x: x[0])
        return []
    finally:
        if stock_semaphore.available() < 1:
            stock_semaphore.release(1)


## returns the position of coffee hr_id in coffees or
## None if coffee not in the coffees
#def getCoffeePosition(coffeeId:str, coffees:Optional[List[Tuple[str, Tuple[Coffee, StockItem]]]]) -> Optional[int]:
#    try:
#        return [getCoffeeId(c) for c in coffees].index(coffeeId)
#    except Exception as e:  # pylint: disable=broad-except
#        _log.exception(e)
#        return None
#        # returns the position of coffee id in coffees or
#        # None if store not in the stores


# returns the position in coffees which matches the given coffeeId and
# stockId and None if no match is found
def getCoffeeStockPosition(coffeeId:str, stockId:str, coffees:Optional[List[Tuple[str, Tuple[Coffee, StockItem]]]]) -> Optional[int]:
    if coffees is None:
        return None
    res = [
        i
        for i, c in enumerate(coffees)
        if getCoffeeCoffeeDict(c).get('hr_id') == coffeeId
            and getCoffeeStockDict(c)['location_hr_id'] == stockId
    ]
    if len(res) > 0:
        return res[0]
    return None


# returns the coffee and stock dicts of the given coffeeId and storeId or None
def getCoffeeStore(coffeeId:str, storeId:str, acquire_lock:bool = True) -> Tuple[Optional[Coffee], Optional[StockItem]]:
    try:
        if acquire_lock:
            stock_semaphore.acquire(1)
        if stock is not None and 'coffees' in stock:
            coffee = [c for c in stock['coffees'] if 'hr_id' in c and c['hr_id'] == coffeeId][0]
            return [
                (coffee, s)
                for s in coffee['stock']  # pyright:ignore[reportTypedDictNotRequiredAccess]
                if s['location_hr_id'] == storeId
            ][0]
        return None, None
    except Exception:  # pylint: disable=broad-except
        # we end up here if there is no stock available
        return None, None
    finally:
        if acquire_lock and stock_semaphore.available() < 1:
            stock_semaphore.release(1)


# ==================
# Blends
#   blend:BlendStructure =  <blendLabel:str, <blendDict:Blend,stockDict:StockItem,maxAmount:float,coffeeLabelDict:Dict[hr_id:str, label:str],
#             replaceMaxAmount:float,replacementBlends:List[Tuple[float, Blend]]>>
#          for blends with replacement coffees defined
#
#   blendDict:Blend = { "label": <blend name>, "hr_id": <BlendID>, "ingredients" :
#           [{"ratio":<r>, "coffee":<CoffeeID>, "replace_coffee":<CoffeeID>}] }
#        Note: "replace_coffee" can be missing in ingredients element
#        Note: ingredients have an additional "label" field with the name of
#              the coffee and can feature density, moisture and screen_min and
#              screen_max fields
#              density, screen_min and screen_max fields are guaranteed to hold
#              valid integer > 0 if available
#              moisture is guaranteed to hold a valid float > 0 if available
#   stockDict:StockItem = { "location_hr_id": <StoreID>, "location_label": <locationName>,
#               "amount": <amount of last ingredient in store }
#   maxAmount:float = maximal amount in kg of coffee available to roast
#        the original blend
#   coffeeLabelDict:Dict[hr_id:str, label:str] = { <CoffeeId>:<CoffeeLabel> } # with <CoffeeLabel>
#        a longer description like "Brazil Santos, 11.5%"
#   replacementBlends:List[Tuple[float, Blend]] = [(maxAmount, replacementBlendDict), ...,
#        (maxAmount, replacementBlendDict)]  # list ordered by maxAmount
#   replacementBlendDict:Dict = same format as blendDict, but without any
#        "replace_coffee" entries in ingredients element


def getBlendLabel(blend:BlendStructure) -> str:
    return blend[0]

def getBlendDict(blend:BlendStructure) -> Blend:
    return blend[1][0]

def getBlendName(blend:BlendStructure) -> str:
    return getBlendDict(blend)['label']


# composes a blend for weight in kg taking into account
# the defined replacement coffees per component
def getBlendBlendDict(blend:BlendStructure, weight:Optional[float]=None) -> Blend:
    if (
        weight is None
        or (
            getBlendMaxAmount(blend) != 0
            and weight <= getBlendMaxAmount(blend)
        )
        or not hasBlendReplace(blend)
    ):
        return blend[1][0]
    if getBlendMaxAmount(blend) > 0:
        res = copy.deepcopy(blend[1][0])  # we start with the original blend
        max_amounts_blend_dicts = [(getBlendMaxAmount(blend), blend[1][0])] + [
            (
                getReplacementBlendMaxAmount(rb),
                getReplacementBlendBlendDict(rb),
            )
            for rb in getBlendReplacementBlends(blend)
        ]
    else:
        # we ignore the original blend
        replacement_blends = getBlendReplacementBlends(blend)
        res = getReplacementBlendBlendDict(replacement_blends[0])
        max_amounts_blend_dicts = [
            (
                getReplacementBlendMaxAmount(rb),
                getReplacementBlendBlendDict(rb),
            )
            for rb in replacement_blends
        ]
    if weight > 0:
        components:Dict[str, float] = {}  # associates coffees to the amounts used in the blend
        components_labels = {}  # associates components to their labels
        components_moisture = {}
        # associates components to their moisture,
        # if the moisture is known
        components_density = {}
        # associates components to their density, if the density is known
        components_screen_min = (
            {}
        )  # associates components to their screen_min, if known
        components_screen_max = (
            {}
        )  # associates components to their screen_max, if known
        amount_spent:float = 0
        for (max_amount, blend_dict) in max_amounts_blend_dicts:
            remaining_amount = min(weight - amount_spent, max_amount)
            # we consume the remaining_amount per component
            # according to their blend ratio
            for i in blend_dict['ingredients']:
                c:str = i['coffee']
                c_amount = components.get(c, 0)
                components[c] = i['ratio'] * remaining_amount + c_amount
                if 'label' in i and i['label'] is not None:
                    components_labels[c] = i['label']
                if 'moisture' in i and i['moisture'] is not None:
                    components_moisture[c] = i['moisture']
                if 'density' in i and i['density'] is not None:
                    components_density[c] = i['density']
                if 'screen_min' in i and i['screen_min'] is not None:
                    components_screen_min[c] = i['screen_min']
                if 'screen_max' in i and i['screen_max'] is not None:
                    components_screen_max[c] = i['screen_max']
            if weight - amount_spent <= max_amount:
                amount_spent = amount_spent + remaining_amount
                break
            amount_spent = amount_spent + max_amount
        # in case weight is larger than available amounts considering
        # all replacements, the last replacement blend is "extended"
        missing_amount = weight - amount_spent
        if missing_amount > 0:
            for i in max_amounts_blend_dicts[-1][1][
                'ingredients'
            ]:  # we "fill" according to the last replacement blend
                c = i['coffee']
                c_amount = components.get(c, 0)
                components[c] = i['ratio'] * missing_amount + c_amount
                if 'label' in i and i['label'] is not None:
                    components_labels[c] = i['label']
                if 'moisture' in i and i['moisture'] is not None:
                    components_moisture[c] = i['moisture']
                if 'density' in i and i['density'] is not None:
                    components_density[c] = i['density']
                if 'screen_min' in i and i['screen_min'] is not None:
                    components_screen_min[c] = i['screen_min']
                if 'screen_max' in i and i['screen_max'] is not None:
                    components_screen_max[c] = i['screen_max']

        # we replace the ingredients with a recomputed set based on
        # the usage per blend replacement as accumulated in
        # components and the weight
        ingredients = []
        moistures:List[Optional[float]] = []
        densities:List[Optional[float]] = []
        screen_mins:List[Optional[int]] = []
        screen_maxs:List[Optional[int]] = []
        for c, a in components.items():
            ratio = a / weight
            ingredient:BlendIngredient = {
                'coffee': c,
                'ratio': ratio,
                'label': components_labels[c],
            }
            if c in components_moisture:
                ingredient['moisture'] = components_moisture[c]
            if c in components_density:
                ingredient['density'] = components_density[c]
            if c in components_screen_min:
                ingredient['screen_min'] = components_screen_min[c]
            if c in components_screen_max:
                ingredient['screen_max'] = components_screen_max[c]
            ingredients.append(ingredient)
            moistures.append(
                components_moisture[c] * ratio
                if c in components_moisture
                else None
            )
            densities.append(
                components_density[c] * ratio
                if c in components_density
                else None
            )
            screen_mins.append(
                components_screen_min.get(c)
            )
            screen_maxs.append(
                components_screen_max.get(c)
            )
        res['ingredients'] = ingredients
        try:
            if not is_float_list(moistures):
                del res['moisture']
            elif config.app_window is not None:
                res['moisture'] = float2float(sum(moistures))
        except Exception:  # pylint: disable=broad-except
            pass
        try:
            if is_float_list(densities):
                res['density'] = int(round(sum(densities)))
            else:
                del res['density']
        except Exception:  # pylint: disable=broad-except
            pass
        try:
            del res['screen_min']
        except Exception:  # pylint: disable=broad-except
            pass
        try:
            del res['screen_max']
        except Exception:  # pylint: disable=broad-except
            pass
        try:
            if is_int_list(screen_mins) and is_int_list(screen_maxs):
                sizes:List[int] = screen_mins + screen_maxs
                if len(sizes) > 0:
                    min_size = min(sizes)
                    max_size = max(sizes)
                    res['screen_min'] = min_size
                    if max_size != min_size:
                        res['screen_max'] = max_size
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)
    return res


def getBlendStockDict(blend:BlendStructure) -> StockItem:
    return blend[1][1]


def getBlendMaxAmount(blend:BlendStructure) -> float:
    return blend[1][2]


def getBlendCoffeeLabelDict(blend:BlendStructure) -> CoffeeLabelDict:
    return blend[1][3]


def getBlendReplaceMaxAmount(blend:BlendStructure) -> float:
    if hasBlendReplace(blend):
        return blend[1][4]
    return 0

def getBlendReplacementBlends(blend:BlendStructure) -> List[ReplacementBlend]:
    if hasBlendReplace(blend):
        return blend[1][5]
    return []


def getReplacementBlendMaxAmount(replacementBlend:ReplacementBlend) -> float:
    return replacementBlend[0]


def getReplacementBlendBlendDict(replacementBlend:ReplacementBlend) -> Blend:
    return replacementBlend[1]


def getBlendId(blend:BlendStructure) -> str:
    return getBlendDict(blend).get('hr_id', '')


def hasBlendReplace(blend:BlendStructure) -> bool:
    return len(blend[1]) > 5


def getBlendLabels(blends:List[BlendStructure]) -> List[str]:
    return [getBlendLabel(c) for c in blends]

# weightIn is in kg. Weights are rendered in weight_unit_idx
def blend2weight_beans(blend:BlendStructure, weight_unit_idx:int, weightIn:float=0) -> List[Tuple[str,str]]:
    res:List[Tuple[str,str]] = []
    try:
        blends = getBlendBlendDict(blend, weightIn)
        sorted_ingredients = sorted(
            blends['ingredients'], key=lambda x: x['ratio'], reverse=True
        )
        for i in sorted_ingredients:
            c = getBlendCoffeeLabelDict(blend)[i['coffee']]
            w = ''
            if weightIn:
                w = render_weight(i['ratio'] * weightIn, 1, weight_unit_idx)
            res.append((w,c))
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
    return res

def blend2beans(blend:BlendStructure, weight_unit_idx:int, weightIn:float=0) -> List[str]:
    res = []
    try:
        # convert weightIn to kg
        v = convertWeight(
            weightIn,
            weight_unit_idx,
            weight_units.index('Kg'),
        )  # v is weightIn converted to kg
        blends = getBlendBlendDict(blend, v)
        sorted_ingredients = sorted(
            blends['ingredients'], key=lambda x: x['ratio'], reverse=True
        )
        for i in sorted_ingredients:
            c = getBlendCoffeeLabelDict(blend)[i['coffee']]
            w = ''
            if weightIn:
                w = f"{render_weight(i['ratio'] * weightIn,weight_unit_idx,weight_unit_idx)} " # @UndefinedVariable
            ratio = f"{int(round(i['ratio'] * 100))}% "
            res.append(f'{ratio}{w}{c}')
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
    return res


# returns a list of tuples associating blend labels with blend descriptions,
# having their blend dicts extended by moisture, density and screensize min/max,
# if it can be computed from its components
# returns list of BlendStructures, tuples of the form:
#    <blendLabel,
#         <blendDict: Blend,
#          stockDict: StockItem,
#          maxAmount: float,
#          coffeeLabelDict: CoffeeLabelDict = Dict[hr_id:str, label:str],
#          replaceMaxAmount: float
#          replacementBlends: List[Tuple[float, Blend]]>>
# Blend is an extra locally defined blend that gets added to the result if it has a non-empty ingredients list
#    it is a dict of the form { 'hr_id': '', 'label': <some string>, 'ingredients': [ {'ratio':<num>, 'coffee':<hr_id_str>},...] }
def getBlends(weight_unit_idx:int, store:Optional[str] = None, customBlend:Optional[Blend] = None) -> List[BlendStructure]:
#    _log.debug('getBlends(%s,%s)', weight_unit_idx, store)
    try:
        stock_semaphore.acquire(1)
        if stock is not None and ('blends' in stock or customBlend is not None):
            res = {}
            if store is None:
                stores = [getStoreId(s) for s in getStores(acquire_lock=False)]
            else:
                stores = [store]
            for s in stores:
                location_label = ''
                store_blends = []
                if customBlend is not None:
                    store_blends.append(customBlend)
                if 'blends' in stock and stock['blends'] is not None:
                    store_blends.extend(stock['blends'])
                if 'replBlends' in stock and stock['replBlends'] is not None:
                    store_blends.extend(stock['replBlends'])
                for blend in store_blends:
                    res_sd:Optional[StockItem] = None
                    replacementBlends:List[Tuple[float, Blend]] = []
                    coffeeLabels:CoffeeLabelDict = {}
                    # list of tuples (maxAmount, replacementBlendDict) with
                    # replacementBlendDict the same structure as blend but
                    # without replacement_coffees
                    # replacementBlends are the blends to be roasted in order
                    # with their maximal amount until the blend recipe
                    # needs to be changed
                    # the following entry holds the changed blend recipe again
                    # indicating the reach
                    # note that while coffees of the original blend have to
                    # be distinct, those components can have
                    # replacement coffees that are identical to that of other
                    # blend components
                    # the replacement blends computed join those components
                    # according to their ratio. Thus a replacement blend may
                    # have less ingredients than the original blend
                    # blends without ingredients (like the default Custom Blend) are ignored
                    if 'ingredients' in blend and len(blend['ingredients'])>0:
                        # associates all coffees incl. replacements with
                        # their long labels (coffeeLabels), if known
                        # associates all coffees incl. replacements with
                        # their current amount in store
                        coffee_stock:Dict[str, float] = {}
                        # associates all coffees incl. replacements with
                        # their (cd,sd) tuple from getCoffeeStore();
                        # Note: both cd and sd might be None.
                        coffee_data = {}
                        # associates all coffees incl. replacements with
                        # its moisture, if the moisture is known
                        coffee_moisture = {}
                        # associates all coffees incl. replacements with
                        # its density, if the density is known
                        coffee_density = {}
                        # associates all coffees incl. replacements with
                        # its screen_min, if known
                        coffee_screen_min = {}
                        # its screen_max, if known
                        # first we extract and store the initial amount of
                        # all components and replacements of the original blend
                        coffee_screen_max = (
                            {}
                        )  # associates all coffees incl. replacements with
                        for i in blend['ingredients']:
                            # register data for original coffees per component
                            coffee:str = i['coffee']
                            # if no stock of this coffee is available
                            # this returns None
                            cd, sd = getCoffeeStore(
                                coffee, s, acquire_lock=False
                            )
                            if sd is None or cd is None:
                                coffee_stock[coffee] = 0
                            else:
                                if (
                                    location_label == ''
                                    and 'location_label' in sd
                                    and sd['location_label'] is not None
                                ):
                                    location_label = sd[
                                        'location_label'
                                    ].strip()
                                res_sd = sd
                                coffee_stock[coffee] = sd['amount']
                                coffee_data[coffee] = (cd, sd)
                                coffeeLabels[coffee] = coffee2beans(cd)
                                if cd is not None:
                                    if 'label' in cd:
                                        i['label'] = cd['label']
                                        # add label of coffee to ingredient,
                                        # used in the Roast Properties dialog
                                        # for links to the coffees
                                        try:
                                            if cd['crop_date']['picked'][0] is not None: # pyright:ignore[reportTypedDictNotRequiredAccess]
                                                i['label'] = f"{cd['crop_date']['picked'][0]} {i['label']}" # pyright:ignore[reportTypedDictNotRequiredAccess]
                                            # pylint: disable=broad-except
                                        except Exception:
                                            pass
                                    try:
                                        m = float(cd['moisture']) # pyright:ignore[reportTypedDictNotRequiredAccess]
                                        if m > 0:
                                            coffee_moisture[coffee] = m
                                            i['moisture'] = m
                                        # pylint: disable=broad-except
                                    except Exception:
                                        pass
                                    try:
                                        d = int(cd['density']) # pyright:ignore[reportTypedDictNotRequiredAccess]
                                        if d > 0:
                                            coffee_density[coffee] = d
                                            i['density'] = d
                                        # pylint: disable=broad-except
                                    except Exception:
                                        pass
                                    try:
                                        screen_size_min = int(
                                            cd['screen_size']['min'] # pyright:ignore[reportTypedDictNotRequiredAccess]
                                        )
                                        if screen_size_min > 0:
                                            coffee_screen_min[
                                                coffee
                                            ] = screen_size_min
                                            i['screen_min'] = screen_size_min
                                        # pylint: disable=broad-except
                                    except Exception:
                                        pass
                                    try:
                                        screen_size_max = int(
                                            cd['screen_size']['max'] # pyright:ignore[reportTypedDictNotRequiredAccess]
                                        )
                                        if screen_size_max > 0:
                                            coffee_screen_max[
                                                coffee
                                            ] = screen_size_max
                                            i['screen_max'] = screen_size_max
                                        # pylint: disable=broad-except
                                    except Exception:
                                        pass
                            # add data for replacements if any
                            if 'replace_coffee' in i:
                                replaceCoffee = i['replace_coffee']
                                cd, sd = getCoffeeStore(
                                    replaceCoffee, s, acquire_lock=False
                                )
                                # if no stock of this coffee is available
                                # this returns None
                                if sd is None or cd is None:
                                    coffee_stock[replaceCoffee] = 0
                                else:
                                    res_sd = sd
                                    coffee_stock[replaceCoffee] = sd['amount']
                                    coffee_data[replaceCoffee] = (cd, sd)
                                    coffeeLabels[replaceCoffee] = coffee2beans(cd)
                                    if cd is not None:
                                        if 'label' in cd:
                                            i['replaceLabel'] = cd['label']
                                            # add label of coffee to ingredient
                                            # used in the Roast Properties
                                            # dialog for links to the coffees
                                            try:
                                                if cd['crop_date']['picked'][0] is not None:  # pyright:ignore[reportTypedDictNotRequiredAccess]
                                                    i[
                                                        'replaceLabel'
                                                    ] = f"{cd['crop_date']['picked'][0]} {i['replaceLabel']}"  # pyright:ignore[reportTypedDictNotRequiredAccess]
                                                # pylint: disable=broad-except
                                            except Exception:
                                                pass
                                        try:
                                            m = float(cd['moisture']) # pyright:ignore[reportTypedDictNotRequiredAccess]
                                            if m > 0:
                                                coffee_moisture[
                                                    replaceCoffee
                                                ] = m
                                            # pylint: disable=broad-except
                                        except Exception:
                                            pass
                                        try:
                                            d = int(cd['density']) # pyright:ignore[reportTypedDictNotRequiredAccess]
                                            if d > 0:
                                                coffee_density[
                                                    replaceCoffee
                                                ] = d
                                            # pylint: disable=broad-except
                                        except Exception:
                                            pass
                                        try:
                                            screen_size_min = int(
                                                cd['screen_size']['min'] # pyright:ignore[reportTypedDictNotRequiredAccess]
                                            )
                                            if screen_size_min > 0:
                                                coffee_screen_min[
                                                    replaceCoffee
                                                ] = screen_size_min
                                            # pylint: disable=broad-except
                                        except Exception:
                                            pass
                                        try:
                                            screen_size_max = int(
                                                cd['screen_size']['max'] # pyright:ignore[reportTypedDictNotRequiredAccess]
                                            )
                                            if screen_size_max > 0:
                                                coffee_screen_max[
                                                    replaceCoffee
                                                ] = screen_size_max
                                            # pylint: disable=broad-except
                                        except Exception:
                                            pass
                        # next we iterate again over the ingredients and
                        # replace coffees by their replacements if needed
                        ingredients = copy.deepcopy(blend['ingredients'])
                        while True:
                            # we first compute the minimum reach
                            # over all components
                            reach_per_ingredients = [
                                (0 if i['ratio']<=0 else coffee_stock[i['coffee']] / i['ratio'])
                                for i in ingredients
                            ]
                            # if the minimum reach over all ingredients is
                            # larger than 0 we add an entry to the result list
                            # replacementBlends
                            if reach_per_ingredients is not None and len(reach_per_ingredients) > 0:
                                reach = min(reach_per_ingredients)
                            else:
                                break
                            # we also add the initial blend and blends with
                            # empty reach to replacementBlends and filter
                            # those out later
                            new_blend:Blend = {
                                'label': blend['label'],
                                'hr_id': blend['hr_id'],
                                'ingredients': ingredients,
                            }
                            moistures = [
                                (
                                    coffee_moisture[i['coffee']] * i['ratio']
                                    if i['coffee'] in coffee_moisture
                                    else None
                                )
                                for i in ingredients
                            ]
                            densities = [
                                (
                                    coffee_density[i['coffee']] * i['ratio']
                                    if i['coffee'] in coffee_density
                                    else None
                                )
                                for i in ingredients
                            ]
                            screen_mins = [
                                coffee_screen_min.get(i['coffee'], None)
                                for i in ingredients
                            ]
                            screen_maxs = [
                                coffee_screen_max.get(i['coffee'], None)
                                for i in ingredients
                            ]
                            # only if the moisture of all components is known,
                            # we can estimate the moisture of this blend
                            if is_float_list(moistures) and config.app_window is not None:
                                m = float2float(sum(moistures), 1)
                                new_blend[
                                    'moisture'
                                ] = m  # @UndefinedVariable
                                if not replacementBlends:
                                    # if we are processing the original blend,
                                    # we store the computed moisture/density/
                                    # /screen also in blend
                                    blend['moisture'] = m
                            # only if the density of all components is known,
                            # we can estimate the density of this blend
                            if is_float_list(densities): # component densities are floats as they are ints multiplied by ratio!
                                new_blend['density'] = int(
                                    round(sum(densities))
                                )  # @UndefinedVariable
                                if not replacementBlends:
                                    # if we are processing the original blend,
                                    # we store the computed moisture/density/
                                    # /screen also in blend
                                    blend['density'] = new_blend['density']
                            if (
                                None not in screen_mins
                                and None not in screen_maxs
                            ):
                                sizes:List[Optional[int]] = screen_mins + screen_maxs
                                if len(sizes) > 0 and is_int_list(sizes):
                                    min_size = min(sizes)
                                    max_size = max(sizes)
                                    new_blend['screen_min'] = min_size
                                    if not replacementBlends:
                                        # if we are processing the original
                                        # blend, we store the computed
                                        # moisture/density/screen also in blend
                                        blend['screen_min'] = new_blend[
                                            'screen_min'
                                        ]
                                    if max_size != min_size:
                                        new_blend['screen_max'] = max_size
                                        if not replacementBlends:
                                            # if we are processing the
                                            # original blend, we store the
                                            # computed moisture/density/screen
                                            # also in blend
                                            blend['screen_max'] = new_blend[
                                                'screen_max'
                                            ]
                            replacementBlends.append((reach, new_blend))

                            # now check for (more) replacement blends

                            if reach > 0:
                                # and we deduce the relative amounts per
                                # components on consuming that reach
                                for i in ingredients:
                                    coffee_stock[i['coffee']] = (
                                        coffee_stock[i['coffee']]
                                        - reach * i['ratio']
                                    )

                            # now we see if we can get further on activating
                            # some replacements we compute now a new
                            # replacement blend where components without stock
                            # get replaced by their replacement coffee if any
                            ingredients_with_replacements:List[BlendIngredient] = []
                            out_of_stock = False
                            for i in ingredients:
                                if i['ratio'] > 0:
                                    if coffee_stock[i['coffee']] <= 0.01: # less then 10g is taken as zero to compensate numeric issues
                                        # this one needs a replacement
                                        if 'replace_coffee' in i:
                                            # if that coffee is already used as
                                            # an ingredients we add to
                                            # its ratio
                                            idx = next(
                                                (
                                                    j
                                                    for j, e in enumerate(
                                                        ingredients_with_replacements
                                                    )
                                                    if e['coffee']
                                                    == i['replace_coffee']
                                                ),
                                                None,
                                            )
                                            if idx is None:
                                                # coffee is not yet used, we
                                                # add an ingredients with this
                                                # replacement coffee as coffee
                                                # and its ratio, but without a
                                                # further replacement coffee
                                                rep_ingredients:BlendIngredient = {
                                                    'coffee': i[
                                                        'replace_coffee'
                                                    ],
                                                    'ratio': i['ratio'],
                                                }
                                                # if copy ratio num/denom
                                                # (if given)
                                                if 'ratio_num' in i:
                                                    rep_ingredients[
                                                        'ratio_num'
                                                    ] = i['ratio_num']
                                                if 'ratio_denom' in i:
                                                    rep_ingredients[
                                                        'ratio_denom'
                                                    ] = i['ratio_denom']
                                                if 'replaceLabel' in i:
                                                    rep_ingredients[
                                                        'label'
                                                    ] = i['replaceLabel']
                                                ingredients_with_replacements.append(
                                                    rep_ingredients
                                                )
                                            else:
                                                rep_ingredients = ingredients_with_replacements[
                                                    idx
                                                ]
                                                rep_ingredients['ratio'] = (
                                                    rep_ingredients['ratio']
                                                    + i['ratio']
                                                )
                                                # we remove ratio num/denom if
                                                # given as they do not fit the
                                                # updated ratio anymore
                                                if (
                                                    'ratio_num'
                                                    in rep_ingredients
                                                ):
                                                    del rep_ingredients[
                                                        'ratio_num'
                                                    ]
                                                if (
                                                    'ratio_denom'
                                                    in rep_ingredients
                                                ):
                                                    del rep_ingredients[
                                                        'ratio_denom'
                                                    ]
                                            if (
                                                i['replace_coffee']
                                                in coffee_moisture
                                            ):
                                                rep_ingredients[
                                                    'moisture'
                                                ] = coffee_moisture[
                                                    i['replace_coffee']
                                                ]
                                            if (
                                                i['replace_coffee']
                                                in coffee_density
                                            ):
                                                rep_ingredients[
                                                    'density'
                                                ] = coffee_density[
                                                    i['replace_coffee']
                                                ]
                                            if (
                                                i['replace_coffee']
                                                in coffee_screen_min
                                            ):
                                                rep_ingredients[
                                                    'screen_min'
                                                ] = coffee_screen_min[
                                                    i['replace_coffee']
                                                ]
                                            if (
                                                i['replace_coffee']
                                                in coffee_screen_max
                                            ):
                                                rep_ingredients[
                                                    'screen_max'
                                                ] = coffee_screen_max[
                                                    i['replace_coffee']
                                                ]
                                        else:
                                            # if a blend component is out of
                                            # stock and does not feature a
                                            # replacement component, we stop
                                            out_of_stock = True
                                    else:
                                        idx = next(
                                            (
                                                j
                                                for j, e in enumerate(
                                                    ingredients_with_replacements
                                                )
                                                if e['coffee'] == i['coffee']
                                            ),
                                            None,
                                        )
                                        if idx is None:
                                            ingredients_with_replacements.append(
                                                i
                                            )
                                        else:
                                            ingredients_with_replacements[idx][
                                                'ratio'
                                            ] = (
                                                ingredients_with_replacements[
                                                    idx
                                                ]['ratio']
                                                + i['ratio']
                                            )
                                            # we remove ratio num/denom if
                                            # given as they do not fit the
                                            # updated ratioanymore
                                            if (
                                                'ratio_num'
                                                in ingredients_with_replacements[
                                                    idx
                                                ]
                                            ):
                                                del ingredients_with_replacements[
                                                    idx
                                                ][
                                                    'ratio_num'
                                                ]
                                            if (
                                                'ratio_denom'
                                                in ingredients_with_replacements[
                                                    idx
                                                ]
                                            ):
                                                del ingredients_with_replacements[
                                                    idx
                                                ][
                                                    'ratio_denom'
                                                ]

                                else:
                                    out_of_stock = True
                            if out_of_stock:
                                break
                            ingredients = ingredients_with_replacements
                    if len(replacementBlends) > 0:
                        amount = replacementBlends[0][0]
                        # the first entry of the replacementBlends is the
                        # original blend, even if its amount is zero
                        if (
                            len(replacementBlends) > 1
                        ):  # at least one replacement, we sum up all
                            # those amounts
                            max_replacement_amount = sum(
                                r[0] for r in replacementBlends
                            )  # the total reach using all replacement coffees
                        else:
                            max_replacement_amount = 0
                        if res_sd is not None and (
                            amount > 0 or max_replacement_amount > 0
                        ):  # TODO: check here with machines capacity # pylint: disable=fixme
                            # add location only if this coffee is available
                            # in several locations
                            if store or location_label == '':
                                loc = ''
                            else:
                                loc = f'{location_label}, '
                            if amount == 0:
                                amount_str = '-'
                            else:
                                amount_str = renderAmount(
                                    amount, target_unit_idx=weight_unit_idx
                                )
                            if max_replacement_amount > 0:
                                amount_str = f'{amount_str}/{renderAmount(max_replacement_amount,target_unit_idx=weight_unit_idx)}'
                            loc_amount_str = f'{loc}{amount_str}'
                            if loc_amount_str == '':
                                label = blend['label']
                            else:
                                label = f'{blend["label"]} ({loc_amount_str})'
                            # we filter all items from replacementBlends with
                            # empty amount and the first original blend
                            replacementBlends = [
                                rb for rb in replacementBlends[1:] if rb[0] > 0
                            ]
                            res[label] = (
                                blend,
                                res_sd,
                                amount,
                                coffeeLabels,
                                max_replacement_amount,
                                replacementBlends)
            return sorted(res.items(), key=lambda x: x[0])
        return []
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
        return []
    finally:
        if stock_semaphore.available() < 1:
            stock_semaphore.release(1)


# returns True if blendSpec of the form
#   {"label": <blend-name>, "ingredients": [{"coffee": <hr_id>, "ratio": <n>},
#         .. ,{"coffee":<hr_id>, "ratio": <n>}]}
# matches the blendDict in the coffee hr_ids and ratios and the blend label
# note that the ratio_num and ratio_denom attributes of ingredents are ignored
# in these matches
def matchBlendDict(blendSpec:Blend, blendDict:Blend, sameLabel:bool=True) -> bool:
    if not sameLabel or blendSpec['label'] == blendDict['label']:
        if (
            'hr_id' in blendSpec
            and 'hr_id' in blendDict
            and blendSpec['hr_id'] == blendDict['hr_id']
        ):
            return True
        if (
            len(blendSpec['ingredients']) == len(blendDict['ingredients'])
            and len(blendSpec['ingredients']) > 0
        ):
            return all(
                    i1['coffee'] == i2['coffee'] and i1['ratio'] == i2['ratio']
                    for (i1, i2) in (
                        zip(
                            blendSpec['ingredients'],
                            blendDict['ingredients'],
                        )
                    )
            )
        return False
    return False


# returns the position in blends which matches the given blendId and stockId
# and None if no match is found
def getBlendSpecStockPosition(blendSpec:Blend, stockId:str, blends:List[BlendStructure]) -> Optional[int]:
    res = [
        i
        for i, b in enumerate(blends)
        if getBlendStockDict(b)['location_hr_id'] == stockId
        and matchBlendDict(blendSpec, getBlendBlendDict(b))
    ]
    if len(res) > 0:
        return res[0]
    # check again, but now ignore label
    # (thus allow renaming of blend names)
    res = [
        i
        for i, b in enumerate(blends)
        if getBlendStockDict(b)['location_hr_id'] == stockId
        and matchBlendDict(blendSpec, getBlendBlendDict(b), sameLabel=False)
    ]
    if len(res) > 0:
        return res[0]
    return None
