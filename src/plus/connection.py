#
# connection.py
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

from PyQt6.QtCore import QSemaphore

from artisanlib import __version__
from typing import Final, Any

import time
import uuid
import datetime
import gzip
import json
import json.decoder
import logging
import dateutil.parser
import requests
import requests.models
import requests.exceptions

from plus import config, account, util

_log: Final[logging.Logger] = logging.getLogger(__name__)


JSON = Any

token_semaphore = QSemaphore(
    1
)  # protects access to the session token which is manipulated only here

# request timeout

request_read_timeout_step:Final[int] = 2 # step size to decrease request_read_timeout on success in seconds
request_read_timeout:int = config.read_timeout # dynamic read_timeout, updated on successful communication and timeouts

def getReadTimeout() -> int:
    return request_read_timeout
def updateReadTimeoutOnSuccess() -> None:
    global request_read_timeout # pylint:disable=global-statement
    request_read_timeout = max(config.read_timeout, request_read_timeout - request_read_timeout_step)
def updateReadTimeoutOnTimeout() -> None:
    global request_read_timeout # pylint:disable=global-statement
    request_read_timeout = config.read_timeout_max

#

def getToken() -> str|None:
    try:
        token_semaphore.acquire(1)
        return config.token
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
        return None
    finally:
        if token_semaphore.available() < 1:
            token_semaphore.release(1)


def getNickname() -> str|None:
    try:
        token_semaphore.acquire(1)
        return config.nickname
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
        return None
    finally:
        if token_semaphore.available() < 1:
            token_semaphore.release(1)


def setToken(token: str, nickname: str|None = None) -> None:
    try:
        token_semaphore.acquire(1)
        config.token = token
        config.nickname = nickname
        aw = config.app_window
        if (aw is not None
            and aw.qmc.operator == ''
            and nickname is not None
            and nickname != ''
        ):  # @UndefinedVariable
            aw.qmc.operator = nickname
    finally:
        if token_semaphore.available() < 1:
            token_semaphore.release(1)


def clearCredentials(remove_from_keychain: bool = True) -> None:
    _log.debug('clearCredentials()')
    # remove credentials from keychain
    aw = config.app_window
    try:
        if (
            aw is not None
            and aw.plus_account is not None
            and remove_from_keychain
        ):  # @UndefinedVariable
            try:

#                if platform.system().startswith('Windows'):
#                    import keyring.backends.Windows  # @UnusedImport
#                elif platform.system() == 'Darwin':
#                    import keyring.backends.macOS  # @UnusedImport @UnresolvedImport
#                else:
#                    import keyring.backends.SecretService  # @UnusedImport
#                import keyring  # @Reimport # imported last to make py2app work
                import keyring

                keyring.delete_password(
                    config.app_name, aw.plus_account
                )  # @UndefinedVariable
            except Exception as e:  # pylint: disable=broad-except
                _log.error(e)
    except Exception: # pylint: disable=broad-except
        # config.app_window might be still unbound
        pass
    try:
        token_semaphore.acquire(1)
        config.token = None
        if aw is not None:
            aw.plus_account = None
        config.passwd = None
        config.nickname = None
        config.account_nr = None
    finally:
        if token_semaphore.available() < 1:
            token_semaphore.release(1)

# returns True on successful authentication
# NOTE: authentify might be called from outside the GUI thread
def authentify() -> bool:
    _log.debug('authentify()')
    try:
        aw = config.app_window
        if (
            aw is not None
            and aw.plus_account is not None
        ):  # @UndefinedVariable
            # fetch passwd
            if config.passwd is None:
                try:
                    import keyring  # @Reimport # imported last to make py2app work

                    config.passwd = keyring.get_password(
                        config.app_name, aw.plus_account
                    )  # @UndefinedVariable
                except Exception as e:  # pylint: disable=broad-except
                    _log.exception(e)
            if config.passwd is None:
                _log.debug('-> password not found')
                clearCredentials()
                return False
            _log.debug(
                '-> authentifying %s',
                aw.plus_account,
            )  # @UndefinedVariable
            data = {
                'email': aw.plus_account,
                'password': config.passwd,
            }  # @UndefinedVariable
            r = sendData(config.auth_url, data, 'POST', False)
            _log.debug(
                '-> authentifying reply status code: %s',
                r.status_code,
            )  # @UndefinedVariable
            # returns 404: login wrong and 401: passwd wrong
            if r.status_code != 204 and r.headers['content-type'].strip().startswith('application/json'):
                res = r.json()
                if (
                    'success' in res
                    and res['success']
                    and 'result' in res
                    and 'user' in res['result']
                    and 'token' in res['result']['user']
                ):
                    _log.debug(
                        '-> authentified, token received'
                    )
                    # extract in user/account data
                    nickname = util.extractInfo(
                        res['result']['user'], 'nickname', None
                    )
                    aw.plus_language = util.extractInfo(
                        res['result']['user'], 'language', 'en'
                    )
                    aw.plus_user_id = util.extractInfo(
                        res['result']['user'], 'user_id', None
                    )
                    aw.plus_paidUntil = None
                    aw.plus_subscription = None
                    aw.plus_rlimit = 0
                    aw.plus_used = 0
                    if 'account' in res['result']['user']:
                        res_account = res['result']['user']['account']
                        if '_id' in res_account:
                            aw.plus_account_id = res_account['_id']
                        subscription = util.extractInfo(
                            res_account, 'subscription', ''
                        )
                        aw.updateSubscriptionSignal.emit(subscription)
                        paidUntil = util.extractInfo(
                            res_account, 'paidUntil', ''
                        )
                        rlimit = -1
                        rused = -1
                        notifications = 0 # unqualified notifications
                        machines = [] # list of machine names with matching notifications
                        try:
                            if 'limit' in res['result']['user']['account']:
                                ol = res_account['limit']
                                if 'rlimit' in ol:
                                    rlimit = ol['rlimit']
                                if 'rused' in ol:
                                    rused = ol['rused']
                        except Exception as e:  # pylint: disable=broad-except
                            _log.exception(e)

                        if 'notifications' in res:
                            notificationDict = res['notifications']
                            if notificationDict:
                                notifications = util.extractInfo(notificationDict, 'unqualified', 0)
                                machines = util.extractInfo(notificationDict, 'machines', [])
                            try:
                                aw.updateLimitsSignal.emit(rlimit,rused,paidUntil,notifications,machines)
                            except Exception as e:  # pylint: disable=broad-except
                                _log.exception(e)


                        # note, here we have to convert the dateUtil string locally , instead of accessing aw.plus_paidUntil which might not yet have been set via the signal processing above
                        try:
                            if paidUntil != '' and (
                                dateutil.parser.parse(paidUntil).date()
    #                            - datetime.datetime.now().date()  # DTZ005 The use of `datetime.datetime.now()` without `tz` argument is not allowed
                                - datetime.datetime.now(datetime.UTC).date()
                            ).days < (-config.expired_subscription_max_days):
                                _log.debug(
                                        '-> authentication failed due to'
                                        ' long expired subscription'
                                )
                                if 'error' in res:
                                    aw.sendmessage(
                                        res['error']
                                    )  # @UndefinedVariable
                                clearCredentials()
                                return False
                        except Exception as e:  # pylint: disable=broad-except
                            _log.exception(e)

                    if 'readonly' in res['result']['user'] and isinstance(
                        res['result']['user']['readonly'], bool
                    ):
                        aw.plus_readonly = res['result']['user'][
                            'readonly'
                        ]
                    else:
                        aw.plus_readonly = False
                    #
                    setToken(res['result']['user']['token'], nickname)
                    if (
                        'account' in res['result']['user']
                        and '_id' in res['result']['user']['account']
                    ):
                        account_nr = account.setAccount(
                            res['result']['user']['account']['_id']
                        )
                        config.account_nr = account_nr
                        _log.debug(
                            '-> account: %s', account_nr
                        )
                    return True
                _log.debug('-> authentication failed')
                if 'error' in res:
                    aw.sendmessage(
                        res['error']
                    )  # @UndefinedVariable
                clearCredentials()
                return False
            _log.error('204: empty response')
            clearCredentials()
        return False
    except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout) as e:
        _log.info(e)
        raise e
    except requests.exceptions.SSLError as e:
        _log.info(e)
        clearCredentials()
        aw = config.app_window
        if aw is not None:
            aw.sendmessage('SSLError')
        raise e
    except requests.exceptions.RequestException as e:
        # most likely some protocol issue
        _log.info(e)
        raise e
    except json.decoder.JSONDecodeError as e:
        if not e.doc:
            raise ValueError('Empty response.') from e
        raise ValueError(f"Decoding error at char {e.pos} (line {e.lineno}, col {e.colno}): '{e.doc}'") from e
    except Exception as e:  # pylint: disable=broad-except
        _log.exception(e)
        clearCredentials()
        raise e


def getHeaders(
    authorized: bool = True, decompress: bool = True) -> dict[str, str]:
    aw = config.app_window
    if aw is not None:
        os, os_version, os_arch = aw.get_os()  # @UndefinedVariable
        headers = {
            'user-agent': f'Artisan/{__version__} ({os}; {os_version}; {os_arch})',
            'Accept-Charset': 'utf-8'
        }
        try:
            locale = aw.locale_str
            if locale != '':
                assert isinstance(locale, str)
                locale = locale.lower().replace('_', '-')
                headers['Accept-Language'] = locale
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)
        if authorized:
            token = getToken()
            if token is not None:
                headers['Authorization'] = f'Bearer {token}'
        if decompress:
            headers[
                'Accept-Encoding'
            ] = 'deflate, compress, gzip'  # identity should not be in here!
        return headers
    return {}

def getHeadersAndData(authorized: bool, compress: bool, jsondata: JSON, verb: str) -> tuple[dict[str, str],bytes]:
    headers = getHeaders(authorized, decompress=compress)
    headers['Content-Type'] = 'application/json; charset=utf-8'
    if verb == 'POST':
        headers['Idempotency-Key'] = uuid.uuid4().hex
    if compress and len(jsondata) > config.post_compression_threshold:
        postdata = gzip.compress(jsondata)
        _log.debug('-> compressed size %s', len(postdata))
        headers['Content-Encoding'] = 'gzip'
    else:
        postdata = jsondata
    return headers, postdata


def sendData(
    url: str,
    data: dict[Any, Any],
    verb: str, # POST or PUT
    authorized: bool = True,
    compress: bool = config.compress_posts,
) -> requests.models.Response:
    # don't log POST data as it might contain credentials!
    _log.debug('sendData(%s,_data_,%s,%s)', url, verb, authorized)
    jsondata = json.dumps(data, indent=None, separators=(',', ':'), ensure_ascii=False).encode('utf8')
    _log.debug('-> size %s', len(jsondata))
#    _log.debug("PRINT jsondata: %s",jsondata)
    headers, postdata = getHeadersAndData(authorized, compress, jsondata, verb)

    try:
        if verb == 'POST':
            r = requests.post(
                url,
                headers=headers,
                data=postdata,
                verify=config.verify_ssl,
                timeout=(config.connect_timeout, getReadTimeout()),
            )
        else:
            r = requests.put(
                url,
                headers=headers,
                data=postdata,
                verify=config.verify_ssl,
                timeout=(config.connect_timeout, getReadTimeout()),
            )
        updateReadTimeoutOnSuccess()
        _log.debug('-> status %s, time %s', r.status_code, r.elapsed.total_seconds())
        if authorized and r.status_code == 401:  # authorisation failed
            _log.debug('-> session token outdated (401)')
            # we re-authentify by renewing the session token and try again
            if authentify():
                time.sleep(0.3) # a little delay not to stress out the server too much
                headers, postdata = getHeadersAndData(
                    authorized, compress, jsondata, verb
                )  # recreate header with new token
                if verb == 'POST':
                    r = requests.post(
                        url,
                        headers=headers,
                        data=postdata,
                        verify=config.verify_ssl,
                        timeout=(config.connect_timeout, getReadTimeout()),
                    )
                else:
                    r = requests.put(
                        url,
                        headers=headers,
                        data=postdata,
                        verify=config.verify_ssl,
                        timeout=(config.connect_timeout, getReadTimeout()),
                    )
                updateReadTimeoutOnSuccess()
                _log.debug('on retry: -> status %s, time %s', r.status_code, r.elapsed.total_seconds())
        return r
    except requests.exceptions.Timeout as e:
        _log.error(e)
        updateReadTimeoutOnTimeout()
        raise e


def getData(url: str, authorized: bool = True, params:dict[str,str]|None = None) -> requests.models.Response|None:
    _log.debug('getData(%s,%s,%s)', url, authorized, params)
    headers = getHeaders(authorized)
    params = params or {}
    #    _log.debug("-> request headers %s",headers)
    try:
        r:requests.models.Response = requests.get(
            url,
            headers=headers,
            verify=config.verify_ssl,
            params=params,
            timeout=(config.connect_timeout, getReadTimeout()),
        )
        updateReadTimeoutOnSuccess()
        _log.debug('-> status %s', r.status_code)
        # _log.debug("-> headers %s",r.headers)
        _log.debug('-> time %s', r.elapsed.total_seconds())
        if authorized and r.status_code == 401:  # authorisation failed
            _log.debug(
                '-> session token outdated (404) - re-authentify'
            )
            # we re-authentify by renewing the session token and try again
            if authentify():
                time.sleep(0.3) # a little delay not to stress out the server too much
                headers = getHeaders(authorized)  # recreate header with new token
                r = requests.get(
                    url,
                    headers=headers,
                    verify=config.verify_ssl,
                    params=params,
                    timeout=(config.connect_timeout, getReadTimeout()),
                )
                updateReadTimeoutOnSuccess()
                _log.debug('-> status %s', r.status_code)
                #        _log.debug("-> headers %s",r.headers)
                _log.debug(
                    'on retry: -> time %s', r.elapsed.total_seconds()
                )
        try:
            _log.debug('-> size %s', len(r.content))
    #        _log.debug("-> data %s",r.json())
        except Exception:  # pylint: disable=broad-except
            pass
        return r
    except requests.exceptions.Timeout as e:
        _log.error(e)
        updateReadTimeoutOnTimeout()
        return None
