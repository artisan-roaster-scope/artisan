#
# ABOUT
# WebLCDs for Artisan

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

# AUTHOR
# Marko Luther, 2023

import time
import asyncio
import logging
import weakref
import jinja2
import aiohttp_jinja2
from contextlib import suppress
from aiohttp import web, WSCloseCode, WSMsgType
from threading import Thread
from typing import Final, Optional, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from aiohttp.web import Request #, Response  # pylint: disable=unused-import

_log: Final[logging.Logger] = logging.getLogger(__name__)

class WebLCDs:

    __slots__ = [ '_loop', '_thread', '_app', '_port', '_last_send', '_min_send_interval', '_resource_path', '_nonesymbol', '_timecolor',
                    '_timebackground', '_btcolor', '_btbackground', '_etcolor', '_etbackground',
                    '_showetflag', '_showbtflag' ]

    def __init__(self, port:int, resource_path:str, nonesymbol:str, timecolor:str, timebackground:str, btcolor:str,
            btbackground:str, etcolor:str, etbackground:str, showetflag:bool, showbtflag:bool) -> None:

        self._loop:        Optional[asyncio.AbstractEventLoop] = None # the asyncio loop
        self._thread:      Optional[Thread]                    = None # the thread running the asyncio loop
        self._app = web.Application(debug=True)
        self._app['websockets'] = weakref.WeakSet()
        self._app.on_shutdown.append(self.on_shutdown)

        self._last_send:float = time.time() # timestamp of the last message send to the clients
        self._min_send_interval:float = 0.03

        aiohttp_jinja2.setup(self._app,
            loader=jinja2.FileSystemLoader(resource_path))

        self._app.add_routes([
            web.get('/artisan', self.index),
            web.get('/websocket', self.websocket_handler),
            web.static('/', resource_path, append_version=True)
        ])

        self._port: int = port
        self._resource_path:str = resource_path
        self._nonesymbol:str = nonesymbol
        self._timecolor:str = timecolor
        self._timebackground:str = timebackground
        self._btcolor:str = btcolor
        self._btbackground:str = btbackground
        self._etcolor:str = etcolor
        self._etbackground:str = etbackground
        self._showetflag:bool = showetflag
        self._showbtflag:bool = showbtflag

    @aiohttp_jinja2.template('artisan.tpl')
    async def index(self, _request: 'Request') -> Dict[str,str]:
        showspace_str = 'inline' if not (self._showbtflag and self._showetflag) else 'none'
        showbt_str = 'inline' if self._showbtflag else 'none'
        showet_str = 'inline' if self._showetflag else 'none'
        return {
            'port': str(self._port),
            'nonesymbol': self._nonesymbol,
            'timecolor': self._timecolor,
            'timebackground': self._timebackground,
            'btcolor': self._btcolor,
            'btbackground': self._btbackground,
            'etcolor': self._etcolor,
            'etbackground': self._etbackground,
            'showbt': showbt_str,
            'showet': showet_str,
            'showspace': showspace_str
        }

    async def send_msg_to_all(self, message:str) -> None:
        if 'websockets' in self._app and self._app['websockets'] is not None:
            ws_set = set(self._app['websockets'])
            for ws in ws_set:
                try:
                    await ws.send_str(message)
                except Exception as e: # pylint: disable=broad-except
                    _log.exception(e)
                    try:
                        self._app['websockets'].discard(ws)
                    except Exception as ex: # pylint: disable=broad-except
                        _log.exception(ex)

    def send_msg(self, message:str, timeout:Optional[float] = 0.2) -> None:
        now: float = time.time()
        if self._loop is not None and (now - self._min_send_interval) > self._last_send:
            self._last_send = now
            future = asyncio.run_coroutine_threadsafe(self.send_msg_to_all(message), self._loop)
            try:
                future.result(timeout)
            except TimeoutError:
                # the coroutine took too long, cancelling the task...
                future.cancel()
            except Exception as ex: # pylint: disable=broad-except
                _log.error(ex)

    # route that establishes the websocket between the Artisan app and the clients
    @staticmethod
    async def websocket_handler(request: 'Request') -> web.WebSocketResponse:
        ws:web.WebSocketResponse = web.WebSocketResponse()
        await ws.prepare(request)
        request.app['websockets'].add(ws)
        try:
            async for msg in ws:
#                _log.info('ws msg: %s', msg)
                if msg.type == WSMsgType.ERROR:
                    _log.error('ws connection closed with exception %s', ws.exception())
        finally:
            request.app['websockets'].discard(ws)
        return ws

    @staticmethod
    async def on_shutdown(app):
        for ws in set(app['websockets']):
            await ws.close(code=WSCloseCode.GOING_AWAY,
                           message='Server shutdown')

    async def startup(self):
        runner = web.AppRunner(self._app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self._port)
        await site.start()

    @staticmethod
    def start_background_loop(loop: asyncio.AbstractEventLoop) -> None:
        asyncio.set_event_loop(loop)
        try:
            # run_forever() returns after calling loop.stop()
            loop.run_forever()
            # clean up tasks
            for task in asyncio.all_tasks(loop):
                task.cancel()
            for t in [t for t in asyncio.all_tasks(loop) if not (t.done() or t.cancelled())]:
                with suppress(asyncio.CancelledError):
                    loop.run_until_complete(t)
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)
        finally:
            loop.close()

    def startWeb(self) -> bool:
        _log.info('start WebLCDs on port %s', self._port)
        try:
            self._loop = asyncio.new_event_loop()
            self._thread = Thread(target=self.start_background_loop, args=(self._loop,), daemon=True)
            self._thread.start()
            # run web task in async loop
            asyncio.run_coroutine_threadsafe(self.startup(), self._loop)
            return True
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)
            return False

    def stopWeb(self) -> None:
        _log.info('stop WebLCDs')
        # _loop.stop() needs to be called as follows as the event loop class is not thread safe
        if self._loop is not None:
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._loop = None
        # wait for the thread to finish
        if self._thread is not None:
            self._thread.join()
            self._thread = None
