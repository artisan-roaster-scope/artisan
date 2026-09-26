"""
Unit tests for the artisanlib.power module.

The SleepInhibitor prevents the system from entering idle standby while Artisan is
connected to a roasting machine. These tests verify

- the platform independent state handling (idempotency, release without inhibit,
  never raising on a failing platform API)
- the platform dispatch (only the backend of the current platform is called)
- on macOS the two real backends: the NSProcessInfo activity (if pyobjc is available)
  and the IOKit power assertion fallback
- the WakeDetector recognizing a system suspension by the divergence of the wall clock
  and the monotonic clock
- the Windows backend against a faked ctypes.windll, as its SetThreadExecutionState()
  cannot be exercised on the other platforms
"""

import ctypes
import sys
from typing import Any

import pytest

from artisanlib.power import SleepInhibitor, WakeDetector


def active(si:SleepInhibitor) -> bool:
    """Reads the active state of the given inhibitor.

    The state is read through this function and not directly as the type checker narrows the
    type of a property access and keeps that narrowing across the calls that change the state,
    reporting the assertions of the state after such a call as unreachable.
    """
    return si.active


def assertion_id(si:SleepInhibitor) -> object|None:
    """Reads the IOKit assertion id of the given inhibitor (see active() on why via a function)."""
    return si._assertion_id # pylint: disable=protected-access


def activity_token(si:SleepInhibitor) -> Any:
    """Reads the NSProcessInfo activity token of the given inhibitor (see active())."""
    return si._activity_token # pylint: disable=protected-access


class TestSleepInhibitorState:
    """Platform independent state handling."""

    def test_initially_inactive(self) -> None:
        assert not SleepInhibitor().active

    def test_inhibit_and_release(self, monkeypatch:'pytest.MonkeyPatch') -> None:
        si = SleepInhibitor('test')
        calls:list[str] = []
        _patch_backends(monkeypatch, si, calls, result=True)
        assert si.inhibit()
        assert active(si)
        si.release()
        assert not active(si)
        assert calls == ['inhibit', 'release']

    def test_repeated_inhibit_does_not_acquire_twice(self, monkeypatch:'pytest.MonkeyPatch') -> None:
        si = SleepInhibitor('test')
        calls:list[str] = []
        _patch_backends(monkeypatch, si, calls, result=True)
        assert si.inhibit()
        assert si.inhibit()
        assert calls == ['inhibit']

    def test_release_without_inhibit_is_a_noop(self, monkeypatch:'pytest.MonkeyPatch') -> None:
        si = SleepInhibitor('test')
        calls:list[str] = []
        _patch_backends(monkeypatch, si, calls, result=True)
        si.release()
        assert not si.active
        assert calls == []

    def test_failing_backend_leaves_inhibitor_inactive(self, monkeypatch:'pytest.MonkeyPatch') -> None:
        si = SleepInhibitor('test')
        calls:list[str] = []
        _patch_backends(monkeypatch, si, calls, result=False)
        assert not si.inhibit()
        assert not si.active
        # a release after a failed inhibit must not call the backend
        si.release()
        assert calls == ['inhibit']

    def test_raising_backend_does_not_propagate(self, monkeypatch:'pytest.MonkeyPatch') -> None:
        si = SleepInhibitor('test')

        def boom(_self:SleepInhibitor) -> bool:
            raise OSError('no power management here')

        for platform_method in ('_inhibit_darwin', '_inhibit_windows', '_inhibit_linux'):
            monkeypatch.setattr(SleepInhibitor, platform_method, boom)
        assert not si.inhibit()
        assert not si.active

    def test_unsupported_platform(self, monkeypatch:'pytest.MonkeyPatch') -> None:
        si = SleepInhibitor('test')
        calls:list[str] = []
        _patch_backends(monkeypatch, si, calls, result=True)
        monkeypatch.setattr(sys, 'platform', 'sunos5')
        assert not si.inhibit()
        assert not si.active
        assert calls == []

    def test_context_manager(self, monkeypatch:'pytest.MonkeyPatch') -> None:
        si = SleepInhibitor('test')
        calls:list[str] = []
        _patch_backends(monkeypatch, si, calls, result=True)
        with si as inhibitor:
            assert inhibitor.active
        assert not si.active
        assert calls == ['inhibit', 'release']


@pytest.mark.skipif(not sys.platform.startswith('darwin'), reason='macOS only')
class TestSleepInhibitorDarwin:
    """The real macOS backends."""

    def test_iokit_assertion(self) -> None:
        si = SleepInhibitor('Artisan unit test assertion')
        assert si._create_assertion_darwin() # pylint: disable=protected-access
        assert assertion_id(si) is not None
        si._active = True                    # pylint: disable=protected-access
        si.release()
        assert assertion_id(si) is None
        assert not active(si)

    def test_activity_or_assertion_inhibits(self) -> None:
        # on a macOS build pyobjc is available and the NSProcessInfo activity is used,
        # from a source checkout without pyobjc the IOKit fallback has to kick in
        si = SleepInhibitor('Artisan unit test')
        assert si.inhibit()
        assert active(si)
        assert activity_token(si) is not None or assertion_id(si) is not None
        si.release()
        assert not active(si)
        assert activity_token(si) is None
        assert assertion_id(si) is None


def _patch_backends(monkeypatch:'pytest.MonkeyPatch', si:SleepInhibitor, calls:list[str], result:bool) -> None:
    """Replaces all platform backends by recording stubs.

    Patching happens on the class as SleepInhibitor defines __slots__ and thus does not
    accept per instance attribute overrides. The inhibitor is passed to document which
    instance the stubs are installed for.
    """
    del si

    def inhibit(_self:SleepInhibitor) -> bool:
        calls.append('inhibit')
        return result

    def release(_self:SleepInhibitor) -> None:
        calls.append('release')

    for platform_method in ('_inhibit_darwin', '_inhibit_windows', '_inhibit_linux'):
        monkeypatch.setattr(SleepInhibitor, platform_method, inhibit)
    for platform_method in ('_release_darwin', '_release_windows', '_release_linux'):
        monkeypatch.setattr(SleepInhibitor, platform_method, release)


class FakeClocks:
    """A pair of controllable clocks. advance() ticks both, suspend() only the wall clock."""

    def __init__(self) -> None:
        self.wall:float = 1000.0
        self.mono:float = 500.0

    def advance(self, seconds:float) -> None:
        """Time passes with the system running."""
        self.wall += seconds
        self.mono += seconds

    def suspend(self, seconds:float) -> None:
        """The system is suspended: the wall clock advances, the monotonic clock does not."""
        self.wall += seconds


class TestWakeDetector:

    def test_no_suspension_detected_while_running(self) -> None:
        clocks = FakeClocks()
        wd = WakeDetector(threshold=10, wall_clock=lambda: clocks.wall, mono_clock=lambda: clocks.mono)
        wd.start()
        for _ in range(10):
            clocks.advance(5)
            assert wd.check() == 0

    def test_suspension_detected(self) -> None:
        clocks = FakeClocks()
        wd = WakeDetector(threshold=10, wall_clock=lambda: clocks.wall, mono_clock=lambda: clocks.mono)
        wd.start()
        clocks.advance(5)
        assert wd.check() == 0
        clocks.suspend(600) # the system slept for 10 minutes
        clocks.advance(5)
        assert wd.check() == pytest.approx(600)

    def test_detection_is_rearmed_after_a_suspension(self) -> None:
        clocks = FakeClocks()
        wd = WakeDetector(threshold=10, wall_clock=lambda: clocks.wall, mono_clock=lambda: clocks.mono)
        wd.start()
        clocks.suspend(120)
        assert wd.check() == pytest.approx(120)
        # the very next check must not report the same suspension again
        clocks.advance(5)
        assert wd.check() == 0

    def test_short_suspension_below_threshold_ignored(self) -> None:
        clocks = FakeClocks()
        wd = WakeDetector(threshold=10, wall_clock=lambda: clocks.wall, mono_clock=lambda: clocks.mono)
        wd.start()
        clocks.suspend(3)
        assert wd.check() == 0

    def test_long_check_interval_is_no_suspension(self) -> None:
        # an irregular/long check interval must not be misread as a suspension as both clocks advance
        clocks = FakeClocks()
        wd = WakeDetector(threshold=10, wall_clock=lambda: clocks.wall, mono_clock=lambda: clocks.mono)
        wd.start()
        clocks.advance(3600)
        assert wd.check() == 0

    def test_check_without_start_arms_the_detector(self) -> None:
        clocks = FakeClocks()
        wd = WakeDetector(threshold=10, wall_clock=lambda: clocks.wall, mono_clock=lambda: clocks.mono)
        assert not wd.started
        assert wd.check() == 0 # arms the detector instead of reporting a bogus suspension
        clocks.suspend(60)
        assert wd.check() == pytest.approx(60)

    def test_stop_and_restart_resets_the_reference(self) -> None:
        clocks = FakeClocks()
        wd = WakeDetector(threshold=10, wall_clock=lambda: clocks.wall, mono_clock=lambda: clocks.mono)
        wd.start()
        wd.stop()
        assert not wd.started
        clocks.suspend(300) # a suspension while the detection is off is not reported
        wd.start()
        clocks.advance(5)
        assert wd.check() == 0

    def test_default_clocks_report_no_suspension(self) -> None:
        wd = WakeDetector(threshold=10)
        wd.start()
        assert wd.check() == 0


# Win32 execution state flags as documented for SetThreadExecutionState(), spelled out here
# instead of importing them from the module under test so that a typo in the module is caught
_ES_CONTINUOUS = 0x80000000
_ES_SYSTEM_REQUIRED = 0x00000001
_ES_AWAYMODE_REQUIRED = 0x00000040


class FakeExecutionStateFunc:
    """Stands in for kernel32.SetThreadExecutionState.

    A plain method would not do: the implementation assigns argtypes/restype on the function
    object, which is only possible on an object of its own (as with a real ctypes function).
    """

    def __init__(self, results:list[int]) -> None:
        self.results:list[int] = list(results) # the value returned per call
        self.calls:list[int] = []              # the flags of each call
        self.argtypes:Any = None
        self.restype:Any = None

    def __call__(self, flags:int) -> int:
        self.calls.append(flags)
        return self.results.pop(0) if self.results else 0


def fake_windll(results:list[int]) -> tuple[Any, FakeExecutionStateFunc]:
    """Returns a stand-in for ctypes.windll and the SetThreadExecutionState stub it holds."""
    func = FakeExecutionStateFunc(results)
    kernel32 = type('FakeKernel32', (), {'SetThreadExecutionState': func})()
    windll = type('FakeWinDLL', (), {'kernel32': kernel32})()
    return windll, func


class TestSleepInhibitorWindows:
    """The Windows backend, faked as it cannot be executed on macOS/Linux."""

    def test_inhibit_requests_system_required_with_away_mode(self, monkeypatch:'pytest.MonkeyPatch') -> None:
        windll, func = fake_windll([_ES_CONTINUOUS]) # a non-zero result signals success
        monkeypatch.setattr(ctypes, 'windll', windll, raising=False)
        si = SleepInhibitor('test')
        assert si._inhibit_windows() # pylint: disable=protected-access
        assert func.calls == [_ES_CONTINUOUS | _ES_SYSTEM_REQUIRED | _ES_AWAYMODE_REQUIRED]

    def test_inhibit_retries_without_away_mode(self, monkeypatch:'pytest.MonkeyPatch') -> None:
        # away mode is not supported on all systems: the first call fails, the retry succeeds
        windll, func = fake_windll([0, _ES_CONTINUOUS])
        monkeypatch.setattr(ctypes, 'windll', windll, raising=False)
        si = SleepInhibitor('test')
        assert si._inhibit_windows() # pylint: disable=protected-access
        assert func.calls == [
            _ES_CONTINUOUS | _ES_SYSTEM_REQUIRED | _ES_AWAYMODE_REQUIRED,
            _ES_CONTINUOUS | _ES_SYSTEM_REQUIRED]

    def test_inhibit_reports_failure(self, monkeypatch:'pytest.MonkeyPatch') -> None:
        windll, func = fake_windll([0, 0]) # both attempts fail
        monkeypatch.setattr(ctypes, 'windll', windll, raising=False)
        si = SleepInhibitor('test')
        assert not si._inhibit_windows() # pylint: disable=protected-access
        assert len(func.calls) == 2

    def test_release_clears_the_requested_state(self, monkeypatch:'pytest.MonkeyPatch') -> None:
        windll, func = fake_windll([_ES_CONTINUOUS])
        monkeypatch.setattr(ctypes, 'windll', windll, raising=False)
        si = SleepInhibitor('test')
        si._release_windows() # pylint: disable=protected-access
        # ES_CONTINUOUS alone resets the state without requesting anything
        assert func.calls == [_ES_CONTINUOUS]

    def test_platform_dispatch_on_windows(self, monkeypatch:'pytest.MonkeyPatch') -> None:
        """inhibit()/release() reach the Windows backend and keep the state consistent."""
        windll, func = fake_windll([_ES_CONTINUOUS, _ES_CONTINUOUS])
        monkeypatch.setattr(ctypes, 'windll', windll, raising=False)
        monkeypatch.setattr(sys, 'platform', 'win32')
        si = SleepInhibitor('test')
        assert si.inhibit()
        assert active(si)
        si.release()
        assert not active(si)
        assert func.calls == [
            _ES_CONTINUOUS | _ES_SYSTEM_REQUIRED | _ES_AWAYMODE_REQUIRED,
            _ES_CONTINUOUS]
