#
# ABOUT
# Profile upload to platform
#
# COPYRIGHT (C) 2010-2026 The artisan team represented by
#   Marko Luther <marko.luther@gmx.net> (maintainer) and all contributors
#
# LICENSE
# This program or module is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# MAINTAINER
# Marko Luther, 2026
#
# AUTHOR
# Marko Luther, 2026

import logging
import asyncio
import aiohttp
import uuid
import concurrent.futures
from aiohttp_retry import RetryClient, ExponentialRetry
from collections.abc import Callable
from typing import Final, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # noqa: F401 # pylint: disable=unused-import
    from artisanlib.atypes import ProfileData # pylint: disable=unused-import
    from proto import artisan_roast_pb2 # pylint: disable=unused-import

from artisanlib.util import roast_message
from plus.connection import getHeaders
from plus.config import upload_url, verify_ssl

_log: Final[logging.Logger] = logging.getLogger(__name__)

POST_RETRIES:Final[int] = 4
RETRY_STATUSES:Final[set[int]] = {x for x in range(100, 600) if x not in {200,201,400,401,403}}
START_TIMEOUT:Final[float] = 0.5   # Base timeout time, then it exponentially grow (default: 0.1s)
#don't retry:
#  200: OK
#  201: Created
#  400: Bad Request
#  401: Unauthorized (wrong token)
#  403: Forbidden
#  500: Internal Server Error

async def send_roast(roast_id:str, roast:'artisan_roast_pb2.Roast',
        on_success:Callable[[], None] | None = None,
        on_failure:Callable[[], None] | None = None) -> None:
    try:
        async with aiohttp.ClientSession() as session:
            headers = getHeaders()
            headers['Content-Type'] = 'application/protobuf'
            headers['Idempotency-Key'] = uuid.uuid4().hex

            url=f'{upload_url}/{roast_id}'
            payload = roast.SerializeToString()
            retry_options = ExponentialRetry(
                attempts=POST_RETRIES,
                statuses=RETRY_STATUSES, # will be retried
                start_timeout=START_TIMEOUT,
                retry_all_server_errors=True) # retry on return code higher than 500 (internal server errors, gateway timeouts,..)
            retry_client = RetryClient(
                client_session=session,
                raise_for_status=False, # don't raise an exception for return codes higher than 400 (client request errors)
                retry_options=retry_options)
            try:
                async with retry_client.post(url, data=payload,
                        ssl=verify_ssl, headers=headers, compress=True, timeout=1) as response:
                    if response.status in {200, 201}:
                        _log.debug('profile uploaded successful to artisan platform')
                        if on_success is not None:
                            on_success()
                    else:
                        _log.debug('profile upload to artisan platform failed with status: %s', response.status)
                        if on_failure is not None:
                            on_failure()
            except TimeoutError as e:
                _log.debug('TimeoutError: %s',e)
    except Exception as e:  # pylint: disable=broad-except
        _log.error('exception in send_roast: %s', e)


def send_profile(
        profile:'ProfileData',
        # filter conf
        interpolate_drops:bool = True,
        curvefilter:int = 3,
        medfilt_factor:int = 3,
        limit_ror:bool = True,
        ror_limit_min:int = 0,
        ror_limit_max:int = 170,
        delta_span_ET:int = 20,
        delta_span_BT:int = 20,
        medfilt_factor_RoR:int = 3,
        delta_ET_filter:int = 7,
        delta_BT_filter:int = 7,
        # handlers
        on_success:Callable[[], None] | None = None,
        on_failure:Callable[[], None] | None = None) -> None:

    roast_id:str|None = profile.get('roastUUID', None)
    if roast_id is not None:
        roast:artisan_roast_pb2.Roast|None = roast_message( # pylint: disable=no-member
                profile,
                # filter conf
                interpolate_drops=interpolate_drops,
                smooth_curves=True,
                curvefilter=curvefilter,
                medfilt_factor=medfilt_factor,
                decay_smoothing_p=False, # optimal smoothing # qmc.optimalSmoothing
                limit_ror=limit_ror,
                ror_limit_min=ror_limit_min,
                ror_limit_max=ror_limit_max,
                delta_span_ET=delta_span_ET,
                delta_span_BT=delta_span_BT,
                medfilt_factor_RoR=medfilt_factor_RoR,
                delta_ET_filter=delta_ET_filter,
                delta_BT_filter=delta_BT_filter
            ) # pylint: disable=no-member
        if roast is not None:
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                executor.submit(asyncio.run, send_roast(roast_id, roast, on_success, on_failure))
        else:
            _log.error('generating profile payload failed')
    else:
        _log.error('profile without roast id')
