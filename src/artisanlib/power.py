#
# ABOUT
# system power management for artisan scope
#
# While Artisan is connected to a roaster the machine expects a continuous
# communication. If the host computer enters standby (idle system sleep) the
# USB/Bluetooth link is torn down and machines with a communication watchdog
# (like Kaleido) fall back into cooling mode. On laptops this typically
# happens towards the end of a roast when the user did not touch the keyboard
# for a while and the display turned off.
#
# This module inhibits the idle system sleep (and on macOS additionally the
# App Nap timer throttling) as long as Artisan is sampling. Display sleep is
# NOT inhibited: the screen may turn off, only the machine has to stay awake.
#
# A system sleep cannot be inhibited in all cases (a laptop closing its lid or
# a user explicitly sending the machine to sleep). Thus this module also offers
# a detector to recognize that the system was suspended such that Artisan can
# re-establish its machine connection right on wake instead of waiting for the
# connection timeouts of the individual device transports.
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

import ctypes
import ctypes.util
import logging
import subprocess
import sys
import time
from collections.abc import Callable
from typing import Any, Final

_log = logging.getLogger(__name__)


# NSActivityOptions (see Foundation/NSProcessInfo.h)
_NSActivityIdleSystemSleepDisabled:Final[int] = 1 << 20
_NSActivityUserInitiated:Final[int] = 0x00FFFFFF | _NSActivityIdleSystemSleepDisabled
_NSActivityLatencyCritical:Final[int] = 0xFF00000000

# IOKit power management (see IOKit/pwr_mgt/IOPMLib.h)
_kIOPMAssertionTypePreventUserIdleSystemSleep:Final[bytes] = b'PreventUserIdleSystemSleep'
_kIOPMAssertionLevelOn:Final[int] = 255
_kCFStringEncodingUTF8:Final[int] = 0x08000100

# Windows execution state flags (see winbase.h)
_ES_CONTINUOUS:Final[int] = 0x80000000
_ES_SYSTEM_REQUIRED:Final[int] = 0x00000001
_ES_AWAYMODE_REQUIRED:Final[int] = 0x00000040


class SleepInhibitor:
    """Prevents the system from entering idle standby while Artisan communicates with a machine.

    The inhibitor is reference counted free, thus repeated calls to inhibit() or release() are
    harmless. All platform interaction is guarded, a platform that is not supported (or an API
    that fails) just results in a logged warning and a non-active inhibitor, never in an
    exception.

    NOTE: on Windows the inhibit()/release() pair has to be called from the same thread as
    SetThreadExecutionState() operates on the calling thread. Artisan calls both from the GUI
    thread.
    """

    __slots__ = ['_reason', '_active', '_activity_token', '_iokit', '_assertion_id', '_inhibit_process']

    def __init__(self, reason:str = 'Artisan is connected to a roasting machine') -> None:
        self._reason:str = reason
        self._active:bool = False
        # macOS: the NSProcessInfo activity token (an opaque NSObject)
        self._activity_token:Any = None
        # macOS: the IOKit lib handle and assertion id of the fallback implementation
        self._iokit:ctypes.CDLL|None = None
        self._assertion_id:ctypes.c_uint32|None = None
        # Linux: the systemd-inhibit process holding the inhibitor lock
        self._inhibit_process:subprocess.Popen[bytes]|None = None

    @property
    def active(self) -> bool:
        return self._active

    def inhibit(self) -> bool:
        """Blocks the idle system sleep. Returns True if the system sleep is blocked now."""
        if self._active:
            return True
        try:
            if sys.platform.startswith('darwin'):
                self._active = self._inhibit_darwin()
            elif sys.platform.startswith('win'):
                self._active = self._inhibit_windows()
            elif sys.platform.startswith('linux'):
                self._active = self._inhibit_linux()
            else:
                _log.info('system sleep inhibition not supported on %s', sys.platform)
                return False
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
            self._active = False
        if self._active:
            _log.info('system sleep inhibited (%s)', self._reason)
        else:
            _log.warning('failed to inhibit the system sleep')
        return self._active

    def release(self) -> None:
        """Releases a previously acquired sleep inhibition. Safe to call if not inhibited."""
        if not self._active:
            return
        try:
            if sys.platform.startswith('darwin'):
                self._release_darwin()
            elif sys.platform.startswith('win'):
                self._release_windows()
            elif sys.platform.startswith('linux'):
                self._release_linux()
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
        finally:
            self._active = False
            _log.info('system sleep released')

    def __enter__(self) -> 'SleepInhibitor':
        self.inhibit()
        return self

    def __exit__(self, *_args:object) -> None:
        self.release()

    def __del__(self) -> None:
        try:
            self.release()
        except Exception: # pylint: disable=broad-except
            pass


# --- macOS

    # the preferred macOS implementation: an NSProcessInfo activity which
    #  - prevents the idle system sleep (NSActivityIdleSystemSleepDisabled)
    #  - prevents App Nap and the timer coalescing which otherwise delays the sampling
    #    of an app whose window is fully occluded or whose display is asleep
    #    (NSActivityLatencyCritical)
    # while it still allows the display to go to sleep
    def _inhibit_darwin(self) -> bool:
        if self._begin_activity_darwin():
            return True
        # if pyobjc is not available we fall back to a plain IOKit power assertion
        return self._create_assertion_darwin()

    def _begin_activity_darwin(self) -> bool:
        try:
            from Foundation import NSProcessInfo # type:ignore[import-not-found,attr-defined,unused-ignore,import-untyped] # @UnresolvedImport # pylint: disable=import-error,no-name-in-module
            options:int = _NSActivityUserInitiated | _NSActivityLatencyCritical
            self._activity_token = NSProcessInfo.processInfo().beginActivityWithOptions_reason_(options, self._reason)
            return self._activity_token is not None
        except Exception as e: # pylint: disable=broad-except
            _log.error(e)
            self._activity_token = None
            return False

    def _create_assertion_darwin(self) -> bool:
        try:
            iokit_path:str|None = ctypes.util.find_library('IOKit')
            cf_path:str|None = ctypes.util.find_library('CoreFoundation')
            if iokit_path is None or cf_path is None:
                return False
            iokit = ctypes.cdll.LoadLibrary(iokit_path)
            cf = ctypes.cdll.LoadLibrary(cf_path)
            cf.CFStringCreateWithCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint32]
            cf.CFStringCreateWithCString.restype = ctypes.c_void_p
            cf.CFRelease.argtypes = [ctypes.c_void_p]
            cf.CFRelease.restype = None
            iokit.IOPMAssertionCreateWithName.argtypes = [ctypes.c_void_p, ctypes.c_uint32,
                    ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
            iokit.IOPMAssertionCreateWithName.restype = ctypes.c_int
            assertion_type = cf.CFStringCreateWithCString(None,
                    _kIOPMAssertionTypePreventUserIdleSystemSleep, _kCFStringEncodingUTF8)
            assertion_name = cf.CFStringCreateWithCString(None,
                    self._reason.encode('utf-8'), _kCFStringEncodingUTF8)
            assertion_id = ctypes.c_uint32(0)
            try:
                res:int = iokit.IOPMAssertionCreateWithName(assertion_type, _kIOPMAssertionLevelOn,
                        assertion_name, ctypes.byref(assertion_id))
            finally:
                if assertion_type is not None:
                    cf.CFRelease(assertion_type)
                if assertion_name is not None:
                    cf.CFRelease(assertion_name)
            if res == 0: # kIOReturnSuccess
                self._iokit = iokit
                self._assertion_id = assertion_id
                return True
            _log.error('IOPMAssertionCreateWithName failed: %s', res)
            return False
        except Exception as e: # pylint: disable=broad-except
            _log.error(e)
            return False

    def _release_darwin(self) -> None:
        if self._activity_token is not None:
            try:
                from Foundation import NSProcessInfo # type:ignore[import-not-found,attr-defined,unused-ignore,import-untyped] # @UnresolvedImport # pylint: disable=import-error,no-name-in-module
                NSProcessInfo.processInfo().endActivity_(self._activity_token)
            except Exception as e: # pylint: disable=broad-except
                _log.error(e)
            finally:
                self._activity_token = None
        if self._iokit is not None and self._assertion_id is not None:
            try:
                self._iokit.IOPMAssertionRelease.argtypes = [ctypes.c_uint32]
                self._iokit.IOPMAssertionRelease.restype = ctypes.c_int
                self._iokit.IOPMAssertionRelease(self._assertion_id)
            except Exception as e: # pylint: disable=broad-except
                _log.error(e)
            finally:
                self._iokit = None
                self._assertion_id = None


# --- Windows

    # sets the execution state of the calling thread and returns the previous state
    # (0 if the call failed)
    @staticmethod
    def _set_thread_execution_state(flags:int) -> int:
        kernel32 = ctypes.windll.kernel32 # type:ignore[attr-defined,unused-ignore] # pylint: disable=no-member
        kernel32.SetThreadExecutionState.argtypes = [ctypes.c_uint32]
        kernel32.SetThreadExecutionState.restype = ctypes.c_uint32
        res:int = kernel32.SetThreadExecutionState(flags)
        return res

    def _inhibit_windows(self) -> bool:
        # away mode keeps the system running with the display off on systems supporting it
        res:int = self._set_thread_execution_state(_ES_CONTINUOUS | _ES_SYSTEM_REQUIRED | _ES_AWAYMODE_REQUIRED)
        if res == 0:
            # away mode is not supported on all systems, retry without it
            res = self._set_thread_execution_state(_ES_CONTINUOUS | _ES_SYSTEM_REQUIRED)
        return res != 0

    def _release_windows(self) -> None:
        self._set_thread_execution_state(_ES_CONTINUOUS)


# --- Linux

    # best effort: hold a systemd inhibitor lock blocking idle and sleep as long as the
    # spawned helper process is alive
    def _inhibit_linux(self) -> bool:
        try:
            self._inhibit_process = subprocess.Popen( # pylint: disable=consider-using-with
                    ['systemd-inhibit', '--what=idle:sleep', '--who=Artisan',
                     f'--why={self._reason}', '--mode=block',
                     'sleep', 'infinity'],
                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return self._inhibit_process.poll() is None
        except Exception as e: # pylint: disable=broad-except
            _log.error(e)
            self._inhibit_process = None
            return False

    def _release_linux(self) -> None:
        if self._inhibit_process is not None:
            try:
                self._inhibit_process.terminate()
                self._inhibit_process.wait(timeout=2)
            except Exception as e: # pylint: disable=broad-except
                _log.error(e)
                try:
                    self._inhibit_process.kill()
                except Exception: # pylint: disable=broad-except
                    pass
            finally:
                self._inhibit_process = None


class WakeDetector:
    """Detects that the system was suspended (or the app was frozen) since the last check.

    The detection is based on the divergence of the wall clock and the monotonic clock: the
    monotonic clock does not advance while the system is suspended (on all supported platforms)
    while the wall clock does. The difference of both deltas is the time the system was away.

    check() has to be called regularly (eg. by a QTimer). It is robust against irregular call
    intervals as only the difference of the two clocks is evaluated and not the call interval.

    NOTE: a wall clock adjustment (NTP step, timezone independent) larger than the threshold is
    reported as a suspension too. As the only consequence is a reconnect of the machine
    connection this is acceptable.
    """

    __slots__ = ['_threshold', '_wall_clock', '_mono_clock', '_wall', '_mono', '_started']

    def __init__(self, threshold:float = 10,
                wall_clock:Callable[[], float] = time.time,
                mono_clock:Callable[[], float] = time.monotonic) -> None:
        # a suspension is reported only if the system was away for at least threshold seconds
        self._threshold:float = threshold
        self._wall_clock:Callable[[], float] = wall_clock
        self._mono_clock:Callable[[], float] = mono_clock
        self._wall:float = 0
        self._mono:float = 0
        self._started:bool = False

    # (re-)starts the detection taking the current clocks as reference
    def start(self) -> None:
        self._wall = self._wall_clock()
        self._mono = self._mono_clock()
        self._started = True

    def stop(self) -> None:
        self._started = False

    @property
    def started(self) -> bool:
        return self._started

    # returns the number of seconds the system was suspended since the last check or 0 if the
    # system was not suspended (or the suspension was shorter than the configured threshold).
    # The detection is re-armed by every call.
    def check(self) -> float:
        if not self._started:
            self.start()
            return 0
        wall:float = self._wall_clock()
        mono:float = self._mono_clock()
        gap:float = (wall - self._wall) - (mono - self._mono)
        self._wall = wall
        self._mono = mono
        return gap if gap >= self._threshold else 0
