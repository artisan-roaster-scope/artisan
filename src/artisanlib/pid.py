#
# ABOUT
# This program realizes a PID controller as part of the open-source roast logging software Artisan.

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

# Inspired by http://brettbeauregard.com/blog/2011/04/improving-the-beginners-pid-introduction/

import logging
import time
import functools
import numpy
from collections.abc import Callable
from typing import Final, TYPE_CHECKING

if TYPE_CHECKING:
    import numpy.typing as npt # pylint: disable=unused-import


from scipy.signal import iirfilter  # type # ignore[import-untyped]

from artisanlib.filters import LiveSosFilter
from artisanlib.suppress_errors import suppress_stdout_stderr

from PyQt6.QtCore import QSemaphore


_log: Final[logging.Logger] = logging.getLogger(__name__)


@functools.lru_cache(maxsize=4)
def _calculate_integral_limits(outMin:int, outMax:int, integral_limit_factor:float) -> tuple[float, float]:
    """Calculate dynamic integral limits based on output range."""
    output_range = outMax - outMin
    integral_range = output_range * integral_limit_factor

    # Center the integral limits around zero, but adjust if output range is not symmetric
    if outMin >= 0:
        # Positive output range
        integral_min = 0.0
        integral_max = integral_range
    elif outMax <= 0:
        # Negative output range
        integral_min = -integral_range
        integral_max = 0.0
    else:
        # Symmetric around zero
        integral_max = integral_range / 2
        integral_min = -integral_max

    return integral_min, integral_max


@functools.lru_cache(maxsize=3)
def _getParameterLinearFit(x1:float, x2:float, y1:float, y2:float) -> 'npt.NDArray[numpy.floating]':
    return numpy.polyfit([x1,x2], [y1,y2], 1)

@functools.lru_cache(maxsize=3)
def _getParameterQuadraticFit(x1:float, x2:float, x3:float, y1:float, y2:float, y3:float) -> 'npt.NDArray[numpy.floating]':
    return numpy.polyfit([x1,x2,x3], [y1,y2,y3], 2)


# expects a function control that takes a value from [<outMin>,<outMax>] to control the heater as called on each update()
class PID:

    __slots__ = [
        'pidSemaphore',
        'outMin',
        'outMax',
        'dutySteps',
        'dutyMin',
        'dutyMax',
        'control',
        'Kp',
        'Ki',
        'Kd',
        'beta',
        'gamma',
        'Pterm',
        'Iterm',
        'Dterm',
        'errSum',
        'lastError',
        'lastInput',
        'lastOutput',
        'lastTime',
        'target',
        'active',
        'output_filter',
        'output_filter_level',
        'force_duty',
        'iterations_since_duty',
        'derivative_filter_level',
        'derivative_filter',
        'lastTarget',
        'derivative_limit',
        'measurement_history',
        'max_len_measurement_history',
        'setpoint_changed_significantly',
        'significant_setup_change_limit',
        'integral_windup_prevention',
        'integral_limit_factor',
        'setpoint_change_threshold',
        'integral_reset_on_setpoint_change',
        'back_calculation_factor',
        'integral_just_reset',
        'sampling_rate',
        'gain_scheduling',
        'gain_scheduling_on_SV',
        'gain_scheduling_quadratic',
        'Kp1',
        'Ki1',
        'Kd1',
        'Kp2',
        'Ki2',
        'Kd2',
        'Schedule0',
        'Schedule1',
        'Schedule2'
    ]

    def __init__(
        self,
        control: Callable[[float], None] = lambda _: None,
        p: float = 2.0,
        i: float = 0.03,
        d: float = 0.0,
        beta: float = 1.,
        gamma: float = 1.,
        sampling_rate: float = 1. # >0 in seconds
    ) -> None:
        self.pidSemaphore: QSemaphore = QSemaphore(1)

        self.outMin: int = 0  # minimum output value
        self.outMax: int = 100  # maximum output value
        self.dutySteps: int = (
            1  # change [1-10] between previous and new PID duty to trigger call of control function
        )
        self.dutyMin: int = 0
        self.dutyMax: int = 100
        self.control: Callable[[float], None] = control
        # first (regular) set of k-p-i parameters corresponding to self.Schedule0
        self.Kp: float = p
        self.Ki: float = i
        self.Kd: float = d
        self.beta: float = beta   # should be larger than 0, defaults to 1 (PoE)
        self.gamma: float = gamma # should be larger than 0, defaults to 1 (DoE)
        self.sampling_rate = sampling_rate
        # Gain Scheduling
        self.gain_scheduling:bool = False # if True, gain scheduling is active, otherwise self.kp, self.ki, and self.kd parameters are used
        self.gain_scheduling_on_SV:bool = True #  by default the observed gain scheduling variable is SV otherwise PV
        self.gain_scheduling_quadratic:bool = False # by default linear approximation between the first and second set of p-i-d parameters is used
        # second set of k-p-i parameters corresponding to self.Schedule1
        self.Kp1: float = p
        self.Ki1: float = i
        self.Kd1: float = d
        # third set of k-p-i parameters corresponding to self.Schedule2
        self.Kp2: float = p
        self.Ki2: float = i
        self.Kd2: float = d
        # schedule values corresponding to the first, second, and if gain_scheduling_quadratic is active, the third gain schedule value (referring to PV or SV, depending on gain_scheduling_on_SV)
        self.Schedule0: float = 0
        self.Schedule1: float = 0
        self.Schedule2: float = 0
        #
        self.Pterm: float = 0.0
        self.Iterm: float = 0.0
        self.Dterm: float = 0.0
        #
        self.errSum: float = 0.0
        self.lastError: float|None = None
        self.lastInput: float|None = None  # used for derivative_on_measurement mode
        self.lastOutput: float|None = (
            None  # used to reinitialize the Iterm and to apply simple moving average on the derivative part in derivative_on_measurement mode
        )
        self.lastTime: float|None = None
        self.target: float = 0.0
        self.active: bool = False  # if active, the control function is called with the PID results
        # PID output smoothing
        self.output_filter_level: int = 0  # off if 0
        self.output_filter: LiveSosFilter = self.outputFilter(self.sampling_rate)
        # PID derivative smoothing
        self.derivative_filter_level: int = 0  # 0: off, >0: on
        self.derivative_filter: LiveSosFilter = self.derivativeFilter(self.sampling_rate)
        #
        self.force_duty: int = (
            3  # at least every n update cycles a new duty value is send, even if its duplicating a previous duty (within the duty step)
        )
        self.iterations_since_duty: int = (
            0  # reset once a duty is send; incremented on every update cycle
        )

        # Enhanced derivative kick prevention
        self.lastTarget: float = 0.0  # Track target changes
        self.derivative_limit: float = 100.0  # Limit derivative contribution
        self.measurement_history: list[float] = (
            []
        )  # Track recent measurements for discontinuity detection
        self.max_len_measurement_history: Final[int] = 5
        self.setpoint_changed_significantly: bool = False # Flag for significant (> significant_setup_change_limit; disabled if significant_setup_change_limit<=0) setpoint changes used to reduce Dterm by 50%
        self.significant_setup_change_limit:float = 15 # used for D; should be smaller than self.setpoint_change_threshold

        # Enhanced integral windup prevention
        self.integral_windup_prevention: bool = True  # Enable advanced windup prevention
        self.integral_limit_factor: float = 1.0  # Limit integral to 100% of output range
        self.setpoint_change_threshold: float = 25.0  # Threshold for significant setpoint changes (used for I)
        self.integral_reset_on_setpoint_change: bool = (
            False  # Reset integral on large setpoint changes
        )
        self.back_calculation_factor: float = 0.5  # Back-calculation adjustment factor
        self.integral_just_reset: bool = (
            True  # Flag to prevent integration immediately after reset
        )

    def _smooth_output(self, output: float) -> float:
        if self.output_filter_level > 0:
            return self.output_filter(output)
        return output

    def _detect_measurement_discontinuity(self, current_input: float) -> bool:
        """Detect if there's a sudden discontinuity in the measurement that might cause derivative kick."""
        if len(self.measurement_history) < 2:
            return False

        # Calculate recent rate of change
        recent_changes:list[float] = []
        for i in range(1, min(len(self.measurement_history), (self.max_len_measurement_history - 1))):
            change = abs(self.measurement_history[-i] - self.measurement_history[-i - 1])
            recent_changes.append(change)

        if not recent_changes:
            return False

        avg_recent_change = sum(recent_changes) / len(recent_changes)
        current_change = abs(current_input - self.measurement_history[-1])

        # Detect if current change is significantly larger than recent average
        return current_change > 2.5 * avg_recent_change and current_change > 1.0

    def _calculate_derivative(self, current_input: float, dt: float) -> float:
        """Calculate derivative term using derivative-on-measurement with enhanced kick prevention."""
        if self.lastInput is None:  # First measurement
            return 0.0

        # Basic derivative calculation
        error = self.gamma*self.target - current_input
        last_error = self.gamma*self.lastTarget - self.lastInput
        derror = (error - last_error) / dt

        # apply derative filter before estimating limits in DoM mode
        if self.derivative_filter_level > 0:
            derror = self.derivative_filter(derror)

        # Apply derivative limiting to prevent excessive derivative action
        if abs(derror) > self.derivative_limit:
            derror = self.derivative_limit if derror > 0 else -self.derivative_limit

        # Reduce derivative action immediately after setpoint changes
        if self.setpoint_changed_significantly:
            derror *= 1 - max(0., min(1., self.gamma))/2  # Reduce derivative action by max. 50% if gamma>=1 and 0% if gamma=0

        # Reduce derivative action if measurement discontinuity is detected
        if self._detect_measurement_discontinuity(current_input):
            derror *= 0.3  # Reduce derivative action by 70%

        return self.getKd(current_input) * derror

    def _update_measurement_history(self, current_input: float) -> None:
        """Update measurement history for discontinuity detection."""
        self.measurement_history.append(current_input)
        # Keep only last 5 measurements
        if len(self.measurement_history) > self.max_len_measurement_history:
            self.measurement_history.pop(0)

    def _should_integrate(self, error: float, output_before_clamp: float) -> bool:
        """Determine if integral term should be updated to prevent windup."""
        if not self.integral_windup_prevention:
            return True

        # Don't integrate immediately after integral was reset due to large setpoint change
        if self.integral_just_reset:
            return False

        # Don't integrate if output is saturated and error would make it worse
        return not (output_before_clamp > self.outMax and error > 0) and not (
            output_before_clamp < self.outMin and error < 0
        )


    def _handle_setpoint_change_integral(self, setpoint_change: float) -> None:
        """Handle integral term when setpoint changes significantly."""
        if not self.integral_reset_on_setpoint_change:
            return

        if abs(setpoint_change) > self.setpoint_change_threshold:
            # Large setpoint change - reset integral term
            self.Iterm = 0.0
            self.integral_just_reset = True  # Prevent integration this cycle
        elif abs(setpoint_change) > self.setpoint_change_threshold * 0.5:
            # Moderate setpoint change - reduce integral term
            self.Iterm *= 0.5

    def _back_calculate_integral(
        self, PV:float, output_before_clamp: float, output_after_clamp: float
    ) -> None:
        """Adjust integral term using back-calculation when output is clamped."""
        if not self.integral_windup_prevention:
            return

        if abs(output_before_clamp - output_after_clamp) > 0.001:  # Output was clamped
            # Calculate the excess that was clamped
            excess = output_before_clamp - output_after_clamp

            # Reduce integral term to compensate for the clamping
            if self.getKi(PV) != 0:
                integral_adjustment = excess * self.back_calculation_factor
                self.Iterm -= integral_adjustment

                # Ensure integral term stays within reasonable bounds
                self.Iterm = self.applyIntegralLimits(PV, self.Iterm)

    ### External API guarded by semaphore

    def on(self) -> None:
        try:
            self.pidSemaphore.acquire(1)
            #            self.init() # we keep the PID running always, even if inactive, and do not disturb it with an init on switching it active
            self.lastOutput = None  # this ensures that the next update sends a control output
            self.active = True
        finally:
            self.pidSemaphore.release(1)

    def off(self) -> None:
        try:
            self.pidSemaphore.acquire(1)
            self.active = False
        finally:
            self.pidSemaphore.release(1)

    def isActive(self) -> bool:
        try:
            self.pidSemaphore.acquire(1)
            return self.active
        except Exception:  # pylint: disable=broad-except
            return False
        finally:
            self.pidSemaphore.release(1)

    def applyIntegralLimits(self, PV:float, iterm:float) -> float:
        integral_min, integral_max = _calculate_integral_limits(self.outMin, self.outMax, self.integral_limit_factor)
        # adjust Iterm max for beta != 0 in which case the Iterm needs to compensate for potentially negative P (beta <0)
        # see https://github.com/CapnBry/HeaterMeter/issues/42#issuecomment-412280142
        integral_max += self.getKp(PV) * (1 - self.beta) * self.target
        return max(integral_min, min(integral_max, iterm))


    # Gain Scheduling

    def getParameter(self, PV:float, y1:float, y2:float, y3:float) -> float:
        if self.gain_scheduling:
            coefficients:npt.NDArray[numpy.floating] | None = None
            try:
                with suppress_stdout_stderr():
                    if self.gain_scheduling_quadratic:
                        coefficients = _getParameterQuadraticFit(self.Schedule0,self.Schedule1,self.Schedule2,y1,y2,y3)
                    else:
                        coefficients = _getParameterLinearFit(self.Schedule0,self.Schedule1,y1,y2)
            except Exception:  # pylint: disable=broad-except
                pass
            if coefficients is not None:
                mapped_parameter:float = float(numpy.poly1d(coefficients)(self.target if self.gain_scheduling_on_SV else PV))
                # parameter is limited to the min/max of the values [y1, y2] on the linear and [y1,y2,y3] on the quadratic scheduling scheme
                max_param = (max(y1,y2,y3) if self.gain_scheduling_quadratic else max(y1,y2))
                min_param = (min(y1,y2,y3) if self.gain_scheduling_quadratic else min(y1,y2))
                return max(min_param, min(max_param, mapped_parameter))
        return y1

    def getKp(self, PV:float) -> float:
        return self.getParameter(PV, self.Kp, self.Kp1, self.Kp2)
    def getKi(self, PV:float) -> float:
        return self.getParameter(PV, self.Ki, self.Ki1, self.Ki2)
    def getKd(self, PV:float) -> float:
        return self.getParameter(PV, self.Kd, self.Kd1, self.Kd2)


    # PID LOOP

    # update control value (the pid loop is running even if PID is inactive, just the control function is only called if active)
    # to enable a bumpless transfer between ON and OFF, the target value (SP) is set to the process value (PV), here i, if OFF (active == False)
    def update(self, i: float|None) -> None:
#        _log.debug('update(%s)',i)
        control_func:Callable[[float], None]|None = None
        output_value:float|None = None
        try:
            if i is not None and not self.isActive():
                # bumpless transfer
                self.target = i
            if i == -1 or i is None:
                # reject error values
                return
            self.pidSemaphore.acquire(1)
            now = time.time()
            err = self.target - i
            if self.lastError is None or self.lastTime is None:
                self.lastTime = now
                self.lastError = err
                self.lastInput = i
            elif (dt := now - self.lastTime) >= 0.05:

                # Check if setpoint has changed since last update and handle integral
                setpoint_change = self.target - self.lastTarget
                if abs(setpoint_change) > 0.001:
                    self.setpoint_changed_significantly = abs(setpoint_change) > self.significant_setup_change_limit > 0
                    self._handle_setpoint_change_integral(setpoint_change)
                    self.lastTarget = self.target
                else:
                    # Gradually clear the setpoint changed flags
                    self.setpoint_changed_significantly = False

                # compute P-Term first (needed for saturation check)
                self.Pterm = self.getKp(i) * (self.beta * self.target - i)

                # Enhanced integral calculation with windup prevention
                # Calculate output before integration to check for saturation
                output_before_integration = self.Pterm + self.Iterm

                # Only integrate if it won't worsen saturation
                if self._should_integrate(err, output_before_integration):
                    self.Iterm += self.getKi(i) * err * dt

                    # Apply dynamic integral limits
                    self.Iterm = self.applyIntegralLimits(i, self.Iterm)

                # Clear the integral reset flag after processing
                self.integral_just_reset = False

                self.Dterm = self._calculate_derivative(i, dt)

                # Update measurement history for discontinuity detection (after calculating D which calls detect discontinuity)
                self._update_measurement_history(i)

                self.lastTime = now
                self.lastError = err
                self.lastInput = i
                output: float = self.Pterm + self.Iterm + self.Dterm

                output = self._smooth_output(output)

                # Enhanced output clamping with back-calculation for integral windup prevention
                output_before_clamp = output
                if output > self.outMax:
                    output = self.outMax
                elif output < self.outMin:
                    output = self.outMin

                # Apply back-calculation to adjust integral term if output was clamped
                self._back_calculate_integral(i, output_before_clamp, output)

                # _log.debug('P: %s, I: %s, D: %s => output: %s', self.Pterm, self.Iterm, D, output)

                final_output = min(float(self.dutyMax), max(float(self.dutyMin), output))
                if (
                    self.lastOutput is None
                    or self.iterations_since_duty >= self.force_duty
                    or final_output >= self.lastOutput + self.dutySteps
                    or final_output <= self.lastOutput - self.dutySteps
                ):
                    if self.active:
                        control_func = self.control
                        output_value = final_output
                    self.lastOutput = output  # kept to initialize Iterm on reactivating the PID
                self.iterations_since_duty += 1
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)
        finally:
            self.pidSemaphore.release(1)
        # send final_output to control function outside of the semaphore to avoid blocking if semaphore is taken within control_function
        if control_func and output_value is not None:
            try:
                control_func(output_value)
                self.iterations_since_duty = 0
            except Exception as e:  # pylint: disable=broad-except
                _log.exception('Control function error: %s', e)

    # bring the PID to its initial state (to be called externally)
    def reset(self) -> None:
        self.init()

    # re-initalize the PID on restarting it after a temporary off state
    def init(self, lock: bool = True, sampling_rate:float = 1.) -> None:
        try:
            if lock:
                self.pidSemaphore.acquire(1)
            # reset the filters on each filter level change (also on PID ON)
            self.derivative_filter = self.derivativeFilter(sampling_rate)
            self.output_filter = self.outputFilter(self.sampling_rate)
            #
            self.errSum = 0.0
            self.lastError = 0.0
            self.lastInput = None
            self.lastTime = None
            self.Pterm = 0.0
            self.Iterm = 0.0  # for now just reset to 0 in all cases
            #        if self.lastOutput != None:
            #            self.Iterm = self.lastOutput
            #        else:
            #            self.Iterm = 0.0

            self.lastOutput = None

            # Reset enhanced derivative kick prevention attributes
            self.lastTarget = self.target
            self.measurement_history = []
            self.setpoint_changed_significantly = False

            # Reset integral windup prevention state
            self.integral_just_reset = False

            # Note: Integral windup prevention settings are not reset as they are configuration
        finally:
            if lock:
                self.pidSemaphore.release(1)

    def setTarget(self, target: float, init: bool = True) -> None:
        try:
            self.pidSemaphore.acquire(1)
            self.target = target
            if init:
                self.init(lock=False)
        finally:
            self.pidSemaphore.release(1)

    def getTarget(self) -> float:
        try:
            self.pidSemaphore.acquire(1)
            return self.target
        finally:
            self.pidSemaphore.release(1)

    def setPID(self, p: float, i: float, d: float) -> None:
        try:
            self.pidSemaphore.acquire(1)
            _getParameterLinearFit.cache_clear()
            _getParameterQuadraticFit.cache_clear()
            self.Kp = max(p, 0)
            self.Ki = max(i, 0)
            self.Kd = max(d, 0)
        finally:
            self.pidSemaphore.release(1)

    def setWeights(self, beta: float|None, gamma: float|None) -> None:
        try:
            self.pidSemaphore.acquire(1)
            if beta is not None:
                self.beta = max(beta, 0)
            if gamma is not None:
                self.gamma = max(gamma, 0)
        finally:
            self.pidSemaphore.release(1)

    def setLimits(self, outMin: int, outMax: int) -> None:
        try:
            self.pidSemaphore.acquire(1)
            self.outMin = outMin
            self.outMax = outMax
            _calculate_integral_limits.cache_clear()
        finally:
            self.pidSemaphore.release(1)

    def setDutySteps(self, steps: int) -> None:
        try:
            self.pidSemaphore.acquire(1)
            self.dutySteps = steps
        finally:
            self.pidSemaphore.release(1)

    def setDutyMin(self, m: int) -> None:
        try:
            self.pidSemaphore.acquire(1)
            self.dutyMin = m
        finally:
            self.pidSemaphore.release(1)

    def setDutyMax(self, m: int) -> None:
        try:
            self.pidSemaphore.acquire(1)
            self.dutyMax = m
        finally:
            self.pidSemaphore.release(1)

    def setControl(self, f: Callable[[float], None]) -> None:
        try:
            self.pidSemaphore.acquire(1)
            self.control = f
        finally:
            self.pidSemaphore.release(1)

    def getDuty(self) -> float|None:
        try:
            self.pidSemaphore.acquire(1)
            if self.lastOutput is not None:
                return min(float(self.dutyMax), max(float(self.dutyMin), self.lastOutput))
            return None
        finally:
            self.pidSemaphore.release(1)

    def getPterm(self) -> float:
        try:
            self.pidSemaphore.acquire(1)
            return self.Pterm
        finally:
            self.pidSemaphore.release(1)

    def getIterm(self) -> float:
        try:
            self.pidSemaphore.acquire(1)
            return self.Iterm
        finally:
            self.pidSemaphore.release(1)

    def getDterm(self) -> float:
        try:
            self.pidSemaphore.acquire(1)
            return self.Dterm
        finally:
            self.pidSemaphore.release(1)

    def getError(self) -> float:
        try:
            self.pidSemaphore.acquire(1)
            return self.lastError or 0
        finally:
            self.pidSemaphore.release(1)

    @staticmethod
    def irrFilter(sampling_rate:float, wn:float) -> LiveSosFilter:
        """infinite impulse response filter"""
        # Note: IIR filter can be computed faster but can suffer from artefacts and FIR filters should be preferred. However, IIR filter specification
        # can be easier adjusted to varying samplings rates
        return LiveSosFilter(
            iirfilter(
                1,         # order (higher-order, sharper cut-off, but incr. delay)
                Wn=max(0., min(wn, sampling_rate/2 - 0.001)),  # 0 < Wn < fs/2 (fs=1 -> fs/2=0.5) # cut-off frequency
                fs=sampling_rate,    # sampling rate, Hz
                btype='low',
                ftype='butter',
                output='sos'))
    @staticmethod
    def derivativeFilter(sampling_rate:float) -> LiveSosFilter:
        return PID.irrFilter(sampling_rate, 0.1)
    @staticmethod
    def outputFilter(sampling_rate:float) -> LiveSosFilter:
        return PID.irrFilter(sampling_rate, 0.35)

    def setOutputFilterLevel(self, v:int, reset:bool = True) -> None:
        try:
            self.pidSemaphore.acquire(1)
            self.output_filter_level = v
            # reset the output filter on each filter level change (also on PID ON), but not if pid is active (reset=False)
            if reset:
                self.output_filter = self.outputFilter(self.sampling_rate)
        finally:
            self.pidSemaphore.release(1)

    def setDerivativeFilterLevel(self, v:int, reset:bool = True) -> None:
        try:
            self.pidSemaphore.acquire(1)
            self.derivative_filter_level = v
            # reset the derivative filter on each filter level change (also on PID ON), but not if pid is active (reset=False)
            if reset:
                self.derivative_filter = self.derivativeFilter(self.sampling_rate)
        finally:
            self.pidSemaphore.release(1)

    def setDerivativeLimit(self, limit:float) -> None:
        """Set the maximum allowed derivative contribution to prevent excessive derivative action."""
        try:
            self.pidSemaphore.acquire(1)
            self.derivative_limit = max(0.0, limit)  # Ensure non-negative
        finally:
            self.pidSemaphore.release(1)

    def getDerivativeLimit(self) -> float:
        """Get the current derivative limit."""
        try:
            self.pidSemaphore.acquire(1)
            return self.derivative_limit
        finally:
            self.pidSemaphore.release(1)

    def setIntegralWindupPrevention(self, enabled: bool) -> None:
        """Enable or disable advanced integral windup prevention."""
        try:
            self.pidSemaphore.acquire(1)
            self.integral_windup_prevention = enabled
        finally:
            self.pidSemaphore.release(1)

    def getIntegralWindupPrevention(self) -> bool:
        """Get the current integral windup prevention setting."""
        try:
            self.pidSemaphore.acquire(1)
            return self.integral_windup_prevention
        finally:
            self.pidSemaphore.release(1)

    def setIntegralResetOnSP(self, enabled: bool) -> None:
        """Enable or integral reset on SP"""
        try:
            self.pidSemaphore.acquire(1)
            self.integral_reset_on_setpoint_change = enabled
        finally:
            self.pidSemaphore.release(1)

    def getIntegralResetOnSP(self) -> bool:
        """Get the current integral reset on SP setting."""
        try:
            self.pidSemaphore.acquire(1)
            return self.integral_reset_on_setpoint_change
        finally:
            self.pidSemaphore.release(1)

    def setIntegralLimitFactor(self, factor: float) -> None:
        """Set the integral limit factor (0.0 to 1.0)."""
        try:
            self.pidSemaphore.acquire(1)
            self.integral_limit_factor = max(0.0, min(1.0, factor))
        finally:
            self.pidSemaphore.release(1)

    def getIntegralLimitFactor(self) -> float:
        """Get the current integral limit factor."""
        try:
            self.pidSemaphore.acquire(1)
            return self.integral_limit_factor
        finally:
            self.pidSemaphore.release(1)

    def setSetpointChangeThreshold(self, threshold: float) -> None:
        """Set the threshold for significant setpoint changes."""
        try:
            self.pidSemaphore.acquire(1)
            self.setpoint_change_threshold = max(0.0, threshold)
        finally:
            self.pidSemaphore.release(1)

    def getSetpointChangeThreshold(self) -> float:
        """Get the current setpoint change threshold."""
        try:
            self.pidSemaphore.acquire(1)
            return self.setpoint_change_threshold
        finally:
            self.pidSemaphore.release(1)

    def setSamplingRate(self, sampling_rate: float) -> None:
        """Set the threshold for significant setpoint changes."""
        try:
            self.pidSemaphore.acquire(1)
            if sampling_rate > 0:
                self.sampling_rate = sampling_rate
        finally:
            self.pidSemaphore.release(1)

    #

    def setGainScheduleState(self, state: bool) -> None:
        """Activates or deactivates Gain Scheduling."""
        try:
            self.pidSemaphore.acquire(1)
            self.gain_scheduling = state
        finally:
            self.pidSemaphore.release(1)

    def setGainScheduleOnSV(self, state: bool) -> None:
        """Activates or deactivates Gain Scheduling."""
        try:
            self.pidSemaphore.acquire(1)
            self.gain_scheduling_on_SV = state
        finally:
            self.pidSemaphore.release(1)

    def setGainSCheduleQuadratic(self, state: bool) -> None:
        """Activates or deactivates Gain Scheduling."""
        try:
            self.pidSemaphore.acquire(1)
            self.gain_scheduling_quadratic = state
        finally:
            self.pidSemaphore.release(1)

    def setGainSchedule(self, kp1:float, ki1:float, kd1:float, kp2:float, ki2:float, kd2:float,
            schedule0:float, schedule1:float, schedule2:float) -> None:
        """Activates or deactivates Gain Scheduling."""
        try:
            self.pidSemaphore.acquire(1)
            _getParameterLinearFit.cache_clear()
            _getParameterQuadraticFit.cache_clear()
            self.Kp1 = kp1
            self.Ki1 = ki1
            self.Kd1 = kd1
            self.Kp2 = kp2
            self.Ki2 = ki2
            self.Kd2 = kd2
            self.Schedule0 = schedule0
            self.Schedule1 = schedule1
            self.Schedule2 = schedule2
        finally:
            self.pidSemaphore.release(1)
