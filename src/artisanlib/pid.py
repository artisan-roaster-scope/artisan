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
from typing import Callable, Final, List, Optional, Tuple

import numpy
from scipy.signal import iirfilter  # type # ignore[import-untyped]

from artisanlib.filters import LiveSosFilter

try:
    from PyQt6.QtCore import QSemaphore # @Reimport @UnresolvedImport @UnusedImport
except ImportError:
    from PyQt5.QtCore import QSemaphore # type: ignore # @Reimport @UnresolvedImport @UnusedImport


_log: Final[logging.Logger] = logging.getLogger(__name__)


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
        'Pterm',
        'errSum',
        'Iterm',
        'lastError',
        'lastInput',
        'lastOutput',
        'lastTime',
        'lastDerr',
        'target',
        'active',
        'derivative_on_error',
        'output_smoothing_factor',
        'output_decay_weights',
        'previous_outputs',
        'input_smoothing_factor',
        'input_decay_weights',
        'previous_inputs',
        'force_duty',
        'iterations_since_duty',
        'derivative_filter_level',
        'derivative_filter',
        'lastTarget',
        'derivative_limit',
        'measurement_history',
        'setpoint_changed',
        'integral_windup_prevention',
        'integral_limit_factor',
        'setpoint_change_threshold',
        'integral_reset_on_setpoint_change',
        'back_calculation_factor',
        'integral_just_reset',
    ]

    def __init__(
        self,
        control: Callable[[float], None] = lambda _: None,
        p: float = 2.0,
        i: float = 0.03,
        d: float = 0.0,
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
        self.Kp: float = p
        self.Ki: float = i
        self.Kd: float = d
        # Proposional on Measurement mode see: http://brettbeauregard.com/blog/2017/06/introducing-proportional-on-measurement/
        self.Pterm: float = 0.0
        self.errSum: float = 0.0
        self.Iterm: float = 0.0
        self.lastError: Optional[float] = None  # used for derivative_on_error mode
        self.lastInput: Optional[float] = None  # used for derivative_on_measurement mode
        self.lastOutput: Optional[float] = (
            None  # used to reinitialize the Iterm and to apply simple moving average on the derivative part in derivative_on_measurement mode
        )
        self.lastTime: Optional[float] = None
        self.lastDerr: float = (
            0.0  # used for simple moving average filtering on the derivative part in derivative_on_error mode
        )
        self.target: float = 0.0
        self.active: bool = False  # if active, the control function is called with the PID results
        self.derivative_on_error: bool = False  # if False => derivative_on_measurement (avoids the Derivative Kick on changing the target)
        # PID output smoothing
        self.output_smoothing_factor: int = 0  # off if 0
        self.output_decay_weights: Optional[List[float]] = None
        self.previous_outputs: List[float] = []
        # PID input smoothing
        self.input_smoothing_factor: int = 0  # off if 0
        self.input_decay_weights: Optional[List[float]] = None
        self.previous_inputs: List[float] = []
        self.force_duty: int = (
            3  # at least every n update cycles a new duty value is send, even if its duplicating a previous duty (within the duty step)
        )
        self.iterations_since_duty: int = (
            0  # reset once a duty is send; incremented on every update cycle
        )
        # PID derivative smoothing
        self.derivative_filter_level: int = 0  # 0: off, >0: on
        self.derivative_filter: LiveSosFilter = self.derivativeFilter()

        # Enhanced derivative kick prevention
        self.lastTarget: float = 0.0  # Track target changes
        self.derivative_limit: float = 100.0  # Limit derivative contribution
        self.measurement_history: List[float] = (
            []
        )  # Track recent measurements for discontinuity detection
        self.setpoint_changed: bool = False  # Flag for recent setpoint changes

        # Enhanced integral windup prevention
        self.integral_windup_prevention: bool = True  # Enable advanced windup prevention
        self.integral_limit_factor: float = 1.0  # Limit integral to 100% of output range
        self.setpoint_change_threshold: float = 25.0  # Threshold for significant setpoint changes
        self.integral_reset_on_setpoint_change: bool = (
            True  # Reset integral on large setpoint changes
        )
        self.back_calculation_factor: float = 0.5  # Back-calculation adjustment factor
        self.integral_just_reset: bool = (
            False  # Flag to prevent integration immediately after reset
        )

    def _smooth_output(self, output: float) -> float:
        # create or update smoothing decay weights
        if self.output_smoothing_factor != 0 and (
            self.output_decay_weights is None
            or len(self.output_decay_weights) != self.output_smoothing_factor
        ):  # recompute only on changes
            self.output_decay_weights = list(numpy.arange(1, self.output_smoothing_factor + 1))
        # add new value
        self.previous_outputs.append(output)
        # throw away superfluous values
        self.previous_outputs = self.previous_outputs[-self.output_smoothing_factor :]
        # compute smoothed output
        if (
            self.output_smoothing_factor == 0
            or len(self.previous_outputs) < self.output_smoothing_factor
        ):
            return output  # no smoothing yet
        return float(numpy.average(self.previous_outputs, weights=self.output_decay_weights))

    def _smooth_input(self, inp: float) -> float:
        # create or update smoothing decay weights
        if self.input_smoothing_factor != 0 and (
            self.input_decay_weights is None
            or len(self.input_decay_weights) != self.input_smoothing_factor
        ):  # recompute only on changes
            self.input_decay_weights = list(numpy.arange(1, self.input_smoothing_factor + 1))
        # add new value
        self.previous_inputs.append(inp)
        # throw away superfluous values
        self.previous_inputs = self.previous_inputs[-self.input_smoothing_factor :]
        # compute smoothed output
        if (
            len(self.previous_inputs) < self.input_smoothing_factor
            or self.input_smoothing_factor == 0
        ):
            return inp  # no smoothing yet
        return float(numpy.average(self.previous_inputs, weights=self.input_decay_weights))

    def _detect_measurement_discontinuity(self, current_input: float) -> bool:
        """Detect if there's a sudden discontinuity in the measurement that might cause derivative kick."""
        if len(self.measurement_history) < 2:
            return False

        # Calculate recent rate of change
        recent_changes = []
        for i in range(1, min(len(self.measurement_history), 4)):
            change = abs(self.measurement_history[-i] - self.measurement_history[-i - 1])
            recent_changes.append(change)

        if not recent_changes:
            return False

        avg_recent_change = sum(recent_changes) / len(recent_changes)
        current_change = abs(current_input - self.measurement_history[-1])

        # Detect if current change is significantly larger than recent average
        return current_change > 3.0 * avg_recent_change and current_change > 1.0

    def _calculate_derivative_on_measurement(self, current_input: float, dt: float) -> float:
        """Calculate derivative term using derivative-on-measurement with enhanced kick prevention."""
        if self.lastInput is None:  # First measurement
            return 0.0

        # Basic derivative calculation
        dinput = current_input - self.lastInput
        dtinput = dinput / dt

        # Apply derivative limiting to prevent excessive derivative action
        if abs(dtinput) > self.derivative_limit:
            dtinput = self.derivative_limit if dtinput > 0 else -self.derivative_limit

        # Reduce derivative action immediately after setpoint changes
        if self.setpoint_changed:
            dtinput *= 0.5  # Reduce derivative action by 50%

        # Reduce derivative action if measurement discontinuity is detected
        if self._detect_measurement_discontinuity(current_input):
            dtinput *= 0.3  # Reduce derivative action by 70%

        return -self.Kd * dtinput

    def _update_measurement_history(self, current_input: float) -> None:
        """Update measurement history for discontinuity detection."""
        self.measurement_history.append(current_input)
        # Keep only last 5 measurements
        if len(self.measurement_history) > 5:
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

    def _calculate_integral_limits(self) -> Tuple[float, float]:
        """Calculate dynamic integral limits based on output range."""
        output_range = self.outMax - self.outMin
        integral_range = output_range * self.integral_limit_factor

        # Center the integral limits around zero, but adjust if output range is not symmetric
        if self.outMin >= 0:
            # Positive output range
            integral_min = 0.0
            integral_max = integral_range
        elif self.outMax <= 0:
            # Negative output range
            integral_min = -integral_range
            integral_max = 0.0
        else:
            # Symmetric around zero
            integral_max = integral_range / 2
            integral_min = -integral_max

        return integral_min, integral_max

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
        self, output_before_clamp: float, output_after_clamp: float
    ) -> None:
        """Adjust integral term using back-calculation when output is clamped."""
        if not self.integral_windup_prevention:
            return

        if abs(output_before_clamp - output_after_clamp) > 0.001:  # Output was clamped
            # Calculate the excess that was clamped
            excess = output_before_clamp - output_after_clamp

            # Reduce integral term to compensate for the clamping
            if self.Ki != 0:
                integral_adjustment = excess * self.back_calculation_factor
                self.Iterm -= integral_adjustment

                # Ensure integral term stays within reasonable bounds
                integral_min, integral_max = self._calculate_integral_limits()
                self.Iterm = max(integral_min, min(integral_max, self.Iterm))

    ### External API guarded by semaphore

    def on(self) -> None:
        try:
            self.pidSemaphore.acquire(1)
            #            self.init() # we keep the PID running always, even if inactive, and do not disturb it with an init on switching it active
            self.lastOutput = None  # this ensures that the next update sends a control output
            self.active = True
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def off(self) -> None:
        try:
            self.pidSemaphore.acquire(1)
            self.active = False
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def isActive(self) -> bool:  # pyrefly: ignore[bad-return]
        try:
            self.pidSemaphore.acquire(1)
            return self.active
        except Exception:  # pylint: disable=broad-except
            return False
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    # update control value (the pid loop is running even if PID is inactive, just the control function is only called if active)
    def update(self, i: Optional[float]) -> None:
        #        _log.debug('update(%s)',i)
        try:
            if i == -1 or i is None:
                # reject error values
                return
            self.pidSemaphore.acquire(1)
            i = self._smooth_input(i)
            now = time.time()
            err = self.target - i
            if self.lastError is None or self.lastTime is None:
                self.lastTime = now
                self.lastError = err
                self.lastInput = i
            elif (dt := now - self.lastTime) > 0.1:
                # Update measurement history for discontinuity detection
                self._update_measurement_history(i)

                # Check if setpoint has changed since last update and handle integral
                setpoint_change = self.target - self.lastTarget
                if abs(setpoint_change) > 0.001:
                    self.setpoint_changed = True
                    # Handle integral term for setpoint changes
                    self._handle_setpoint_change_integral(setpoint_change)
                    self.lastTarget = self.target
                else:
                    # Gradually clear the setpoint changed flag
                    self.setpoint_changed = False

                derr = (err - self.lastError) / dt

                # compute P-Term first (needed for saturation check)
                self.Pterm = self.Kp * err

                # Enhanced integral calculation with windup prevention
                # Calculate output before integration to check for saturation
                output_before_integration = self.Pterm + self.Iterm

                # Only integrate if it won't worsen saturation
                if self._should_integrate(err, output_before_integration):
                    self.Iterm += self.Ki * err * dt

                    # Apply dynamic integral limits
                    integral_min, integral_max = self._calculate_integral_limits()
                    self.Iterm = max(integral_min, min(integral_max, self.Iterm))

                # Clear the integral reset flag after processing
                self.integral_just_reset = False

                # compute D-Term with enhanced derivative kick prevention
                D: float
                if self.derivative_on_error:
                    D = self.Kd * derr
                    # Apply derivative limiting for derivative-on-error mode too
                    if abs(D) > self.derivative_limit:
                        D = self.derivative_limit if D > 0 else -self.derivative_limit
                else:
                    # Use enhanced derivative-on-measurement calculation
                    D = self._calculate_derivative_on_measurement(i, dt)

                self.lastTime = now
                self.lastError = err
                self.lastInput = i

                if self.derivative_filter_level > 0:
                    D = self.derivative_filter(D)
                output: float = self.Pterm + self.Iterm + D

                output = self._smooth_output(output)

                # Enhanced output clamping with back-calculation for integral windup prevention
                output_before_clamp = output
                if output > self.outMax:
                    output = self.outMax
                elif output < self.outMin:
                    output = self.outMin

                # Apply back-calculation to adjust integral term if output was clamped
                self._back_calculate_integral(output_before_clamp, output)

                #                _log.debug('P: %s, I: %s, D: %s => output: %s', self.Pterm, self.Iterm, D, output)

                int_output = int(round(min(float(self.dutyMax), max(float(self.dutyMin), output))))
                if (
                    self.lastOutput is None
                    or self.iterations_since_duty >= self.force_duty
                    or int_output >= self.lastOutput + self.dutySteps
                    or int_output <= self.lastOutput - self.dutySteps
                ):
                    if self.active:
                        try:
                            self.control(int_output)
                        except Exception as e:  # pylint: disable=broad-except
                            _log.error(e)
                        self.iterations_since_duty = 0
                    self.lastOutput = output  # kept to initialize Iterm on reactivating the PID
                self.iterations_since_duty += 1
        except Exception as e:  # pylint: disable=broad-except
            _log.exception(e)
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    # bring the PID to its initial state (to be called externally)
    def reset(self) -> None:
        self.init()

    # re-initalize the PID on restarting it after a temporary off state
    def init(self, lock: bool = True) -> None:
        try:
            if lock:
                self.pidSemaphore.acquire(1)
            # reset the derivative filter on each filter level change (also on PID ON)
            self.derivative_filter = self.derivativeFilter()
            self.errSum = 0.0
            self.lastError = 0.0
            self.lastInput = None
            self.lastTime = None
            self.lastDerr = 0.0
            self.Pterm = 0.0
            self.input_decay_weights = None
            self.previous_inputs = []

            self.Iterm = 0.0  # for now just reset to 0 in all cases
            #        if self.lastOutput != None:
            #            self.Iterm = self.lastOutput
            #        else:
            #            self.Iterm = 0.0

            self.lastOutput = None
            # initialize the output smoothing
            self.output_decay_weights = None
            self.previous_outputs = []

            # Reset enhanced derivative kick prevention attributes
            self.lastTarget = self.target
            self.measurement_history = []
            self.setpoint_changed = False

            # Reset integral windup prevention state
            self.integral_just_reset = False

            # Note: Integral windup prevention settings are not reset as they are configuration
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def setTarget(self, target: float, init: bool = True) -> None:
        try:
            self.pidSemaphore.acquire(1)
            self.target = target
            if init:
                self.init(lock=False)
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def getTarget(self) -> float:  # pyrefly: ignore[bad-return]
        try:
            self.pidSemaphore.acquire(1)
            return self.target
        except Exception:  # pylint: disable=broad-except
            return 0.0
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def setPID(self, p: float, i: float, d: float) -> None:
        try:
            self.pidSemaphore.acquire(1)
            self.Kp = max(p, 0)
            self.Ki = max(i, 0)
            self.Kd = max(d, 0)
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def setLimits(self, outMin: int, outMax: int) -> None:
        try:
            self.pidSemaphore.acquire(1)
            self.outMin = outMin
            self.outMax = outMax
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def setDutySteps(self, steps: int) -> None:
        try:
            self.pidSemaphore.acquire(1)
            self.dutySteps = steps
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def setDutyMin(self, m: int) -> None:
        try:
            self.pidSemaphore.acquire(1)
            self.dutyMin = m
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def setDutyMax(self, m: int) -> None:
        try:
            self.pidSemaphore.acquire(1)
            self.dutyMax = m
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def setControl(self, f: Callable[[float], None]) -> None:
        try:
            self.pidSemaphore.acquire(1)
            self.control = f
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def getDuty(self) -> Optional[float]:
        try:
            self.pidSemaphore.acquire(1)
            if self.lastOutput is not None:
                return min(float(self.dutyMax), max(float(self.dutyMin), self.lastOutput))
            return None
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    @staticmethod
    def derivativeFilter() -> LiveSosFilter:
        return LiveSosFilter(
            iirfilter(
                1,  # order
                Wn=0.2,  # 0 < Wn < fs/2 (fs=1 -> fs/2=0.5)
                fs=1,  # sampling rate, Hz
                btype='low',
                ftype='butter',
                output='sos',
            )
        )

    def setDerivativeFilterLevel(self, v: int) -> None:
        try:
            self.pidSemaphore.acquire(1)
            self.derivative_filter_level = v
            # reset the derivative filter on each filter level change (also on PID ON)
            self.derivative_filter = self.derivativeFilter()
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def setDerivativeLimit(self, limit: float) -> None:
        """Set the maximum allowed derivative contribution to prevent excessive derivative action."""
        try:
            self.pidSemaphore.acquire(1)
            self.derivative_limit = max(0.0, limit)  # Ensure non-negative
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def getDerivativeLimit(self) -> float: # pyrefly: ignore[bad-return]
        """Get the current derivative limit."""
        try:
            self.pidSemaphore.acquire(1)
            return self.derivative_limit
        except Exception:  # pylint: disable=broad-except
            return 80.0  # Default value
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def setIntegralWindupPrevention(self, enabled: bool) -> None:
        """Enable or disable advanced integral windup prevention."""
        try:
            self.pidSemaphore.acquire(1)
            self.integral_windup_prevention = enabled
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def getIntegralWindupPrevention(self) -> bool:  # pyrefly: ignore[bad-return]
        """Get the current integral windup prevention setting."""
        try:
            self.pidSemaphore.acquire(1)
            return self.integral_windup_prevention
        except Exception:  # pylint: disable=broad-except
            return True  # Default value
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def setDerivativeOnError(self, enabled: bool) -> None:
        """Enable or disable derivative on error (instead of derivative on measurement)"""
        try:
            self.pidSemaphore.acquire(1)
            self.derivative_on_error = enabled
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def getDerivativeOnError(self) -> bool:  # pyrefly: ignore[bad-return]
        """Get the current derivative on error setting."""
        try:
            self.pidSemaphore.acquire(1)
            return self.derivative_on_error
        except Exception:  # pylint: disable=broad-except
            return True  # Default value
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def setIntegralResetOnSP(self, enabled: bool) -> None:
        """Enable or integral reset on SP"""
        try:
            self.pidSemaphore.acquire(1)
            self.integral_reset_on_setpoint_change = enabled
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def getIntegralResetOnSP(self) -> bool:  # pyrefly: ignore[bad-return]
        """Get the current integral reset on SP setting."""
        try:
            self.pidSemaphore.acquire(1)
            return self.integral_reset_on_setpoint_change
        except Exception:  # pylint: disable=broad-except
            return True  # Default value
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def setIntegralLimitFactor(self, factor: float) -> None:
        """Set the integral limit factor (0.0 to 1.0)."""
        try:
            self.pidSemaphore.acquire(1)
            self.integral_limit_factor = max(0.0, min(1.0, factor))
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def getIntegralLimitFactor(self) -> float:  # pyrefly: ignore[bad-return]
        """Get the current integral limit factor."""
        try:
            self.pidSemaphore.acquire(1)
            return self.integral_limit_factor
        except Exception:  # pylint: disable=broad-except
            return 1.0  # Default value
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def setSetpointChangeThreshold(self, threshold: float) -> None:
        """Set the threshold for significant setpoint changes."""
        try:
            self.pidSemaphore.acquire(1)
            self.setpoint_change_threshold = max(0.0, threshold)
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def getSetpointChangeThreshold(self) -> float: # pyrefly: ignore[bad-return]
        """Get the current setpoint change threshold."""
        try:
            self.pidSemaphore.acquire(1)
            return self.setpoint_change_threshold
        except Exception:  # pylint: disable=broad-except
            return 5.0  # Default value
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)
