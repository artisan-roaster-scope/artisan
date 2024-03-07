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

import time
import numpy
import scipy.signal # type:ignore[import-untyped]
import logging
from typing import Final, List, Optional, Callable

from artisanlib.filters import LiveSosFilter

try:
    from PyQt6.QtCore import QSemaphore # @Reimport @UnresolvedImport @UnusedImport
except ImportError:
    from PyQt5.QtCore import QSemaphore # type: ignore # @Reimport @UnresolvedImport @UnusedImport

_log: Final[logging.Logger] = logging.getLogger(__name__)

# expects a function control that takes a value from [<outMin>,<outMax>] to control the heater as called on each update()
class PID:

    __slots__ = [ 'pidSemaphore', 'outMin', 'outMax', 'dutySteps', 'dutyMin', 'dutyMax', 'control', 'Kp',
            'Ki', 'Kd', 'pOnE', 'Pterm', 'errSum', 'Iterm', 'lastError', 'lastInput', 'lastOutput', 'lastTime',
            'lastDerr', 'target', 'active', 'derivative_on_error', 'output_smoothing_factor', 'output_decay_weights',
            'previous_outputs', 'input_smoothing_factor', 'input_decay_weights', 'previous_inputs', 'force_duty', 'iterations_since_duty',
            'derivative_filter_level', 'derivative_filter' ]

    def __init__(self, control:Callable[[float], None]=lambda _: None, p:float=2.0, i:float=0.03, d:float=0.0) -> None:
        self.pidSemaphore:QSemaphore = QSemaphore(1)

        self.outMin:int = 0 # minimum output value
        self.outMax:int = 100 # maximum output value
        self.dutySteps:int = 1 # change [1-10] between previous and new PID duty to trigger call of control function
        self.dutyMin:int = 0
        self.dutyMax:int = 100
        self.control:Callable[[float], None] = control
        self.Kp:float = p
        self.Ki:float = i
        self.Kd:float = d
        # Proposional on Measurement mode see: http://brettbeauregard.com/blog/2017/06/introducing-proportional-on-measurement/
        self.pOnE:bool = True # True for Proposional on Error mode, False for Proposional on Measurement Mode
        self.Pterm:float = 0.0
        self.errSum:float = 0.0
        self.Iterm:float = 0.0
        self.lastError:Optional[float] = None # used for derivative_on_error mode
        self.lastInput:float = 0.0 # used for derivative_on_measurement mode
        self.lastOutput:Optional[float] = None # used to reinitialize the Iterm and to apply simple moving average on the derivative part in derivative_on_measurement mode
        self.lastTime:Optional[float] = None
        self.lastDerr:float = 0.0 # used for simple moving average filtering on the derivative part in derivative_on_error mode
        self.target:float = 0.0
        self.active:bool = False # if active, the control function is called with the PID results
        self.derivative_on_error = False # if False => derivative_on_measurement (avoids the Derivative Kick on changing the target)
        # PID output smoothing
        self.output_smoothing_factor:int = 0 # off if 0
        self.output_decay_weights:Optional[List[float]] = None
        self.previous_outputs:List[float] = []
        # PID input smoothing
        self.input_smoothing_factor:int = 0 # off if 0
        self.input_decay_weights:Optional[List[float]] = None
        self.previous_inputs:List[float] = []
        self.force_duty:int = 3 # at least every n update cycles a new duty value is send, even if its duplicating a previous duty (within the duty step)
        self.iterations_since_duty:int = 0 # reset once a duty is send; incremented on every update cycle
        # PID derivative smoothing
        self.derivative_filter_level: int = 0 # 0: off, 1: on
        self.derivative_filter:LiveSosFilter = self.derivativeFilter()

    def _smooth_output(self,output:float) -> float:
        # create or update smoothing decay weights
        if self.output_smoothing_factor != 0 and (self.output_decay_weights is None or len(self.output_decay_weights) != self.output_smoothing_factor): # recompute only on changes
            self.output_decay_weights = list(numpy.arange(1,self.output_smoothing_factor+1))
        # add new value
        self.previous_outputs.append(output)
        # throw away superfluous values
        self.previous_outputs = self.previous_outputs[-self.output_smoothing_factor:]
        # compute smoothed output
        if self.output_smoothing_factor == 0 or len(self.previous_outputs) < self.output_smoothing_factor:
            return output # no smoothing yet
        return float(numpy.average(self.previous_outputs,weights=self.output_decay_weights))

    def _smooth_input(self,inp:float) -> float:
        # create or update smoothing decay weights
        if self.input_smoothing_factor != 0 and (self.input_decay_weights is None or len(self.input_decay_weights) != self.input_smoothing_factor): # recompute only on changes
            self.input_decay_weights = list(numpy.arange(1,self.input_smoothing_factor+1))
        # add new value
        self.previous_inputs.append(inp)
        # throw away superfluous values
        self.previous_inputs = self.previous_inputs[-self.input_smoothing_factor:]
        # compute smoothed output
        if len(self.previous_inputs) < self.input_smoothing_factor or self.input_smoothing_factor == 0:
            return inp # no smoothing yet
        return float(numpy.average(self.previous_inputs,weights=self.input_decay_weights))

    ### External API guarded by semaphore

    def on(self) -> None:
        try:
            self.pidSemaphore.acquire(1)
#            self.init() # we keep the PID running always, even if inactive, and do not disturb it with an init on switching it active
            self.lastOutput = None # this ensures that the next update sends a control output
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

    def isActive(self) -> bool:
        try:
            self.pidSemaphore.acquire(1)
            return self.active
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)


    # update control value (the pid loop is running even if PID is inactive, just the control function is only called if active)
    def update(self, i:Optional[float]) -> None:
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
            elif (dt := now - self.lastTime) > 0.2:
                derr = (err - self.lastError) / dt

                # Derivative on Measurement to avoid the derivative kick on SV changes
                # http://brettbeauregard.com/blog/2011/04/improving-the-beginner%e2%80%99s-pid-derivative-kick/
                if self.lastInput:
                    dinput = i - self.lastInput
                    dtinput = dinput / dt
                else:
                    dinput = 0
                    dtinput = 0

#                # apply some simple moving average filter to avoid major spikes (used only for D)
#                if self.lastDerr:
#                    derr = (derr + self.lastDerr) / 2.0
## This smoothing is dangerous if time between readings is not considered!
#                self.lastDerr = derr

                self.lastTime = now
                self.lastError = err
                self.lastInput = i

                # limit the effect of I
                self.Iterm += self.Ki * err * dt

                # clamp Iterm to [outMin,outMax] and avoid integral windup
                self.Iterm = max(self.outMin,min(self.outMax,self.Iterm))

                # compute P-Term
                if self.pOnE:
                    self.Pterm = self.Kp * err
                else:
                    self.Pterm = self.Pterm -self.Kp * dinput

                # compute D-Term
                D:float
                if self.derivative_on_error:
                    D = self.Kd * derr
                else:
                    D = - self.Kd * dtinput

                if self.derivative_filter_level > 0:
                    D = self.derivative_filter(D)
                output:float = self.Pterm + self.Iterm + D

                output = self._smooth_output(output)

                # clamp output to [outMin,outMax] and avoid integral windup
                if output > self.outMax:
                    output = self.outMax
                elif output < self.outMin:
                    output = self.outMin

                int_output = int(round(min(self.dutyMax,max(self.dutyMin,output))))
                if self.lastOutput is None or self.iterations_since_duty >= self.force_duty or int_output >= self.lastOutput + self.dutySteps or int_output <= self.lastOutput - self.dutySteps:
                    if self.active:
                        self.control(int_output)
                        self.iterations_since_duty = 0
                    self.lastOutput = output # kept to initialize Iterm on reactivating the PID
                self.iterations_since_duty += 1
        except Exception as e: # pylint: disable=broad-except
            _log.exception(e)
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    # bring the PID to its initial state (to be called externally)
    def reset(self) -> None:
        try:
            self.pidSemaphore.acquire(1)
            self.init()
            self.Iterm = 0.0
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    # re-initalize the PID on restarting it after a temporary off state
    def init(self) -> None:
        try:
            self.pidSemaphore.acquire(1)
            self.errSum = 0.0
            self.lastError = 0.0
            self.lastInput = 0.0
            self.lastTime = None
            self.lastDerr = 0.0
            self.Pterm = 0.0
            self.input_decay_weights = None
            self.previous_inputs = []

            self.Iterm = 0.0 # for now just reset to 0 in all cases
    #        if self.lastOutput != None:
    #            self.Iterm = self.lastOutput
    #        else:
    #            self.Iterm = 0.0

            self.lastOutput = None
            # initialize the output smoothing
            self.output_decay_weights = None
            self.previous_outputs = []
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def setTarget(self, target:float, init:bool = True) -> None:
        try:
            self.pidSemaphore.acquire(1)
            self.target = target
            if init:
                self.init()
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def getTarget(self) -> float:
        try:
            self.pidSemaphore.acquire(1)
            return self.target
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def setPID(self, p:float, i:float, d:float, pOnE:bool = True) -> None:
        try:
            self.pidSemaphore.acquire(1)
            self.Kp = max(p,0)
            self.Ki = max(i,0)
            self.Kd = max(d,0)
            self.pOnE = pOnE
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def setLimits(self, outMin:int, outMax:int) -> None:
        try:
            self.pidSemaphore.acquire(1)
            self.outMin = outMin
            self.outMax = outMax
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def setDutySteps(self, steps:int) -> None:
        try:
            self.pidSemaphore.acquire(1)
            self.dutySteps = steps
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def setDutyMin(self, m:int) -> None:
        try:
            self.pidSemaphore.acquire(1)
            self.dutyMin = m
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def setDutyMax(self, m:int) -> None:
        try:
            self.pidSemaphore.acquire(1)
            self.dutyMax = m
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def setControl(self, f:Callable[[float], None]) -> None:
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
                return int(round(min(self.dutyMax,max(self.dutyMin,self.lastOutput))))
            return None
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    @staticmethod
    def derivativeFilter() -> LiveSosFilter:
        return LiveSosFilter(
                scipy.signal.iirfilter(1, # order
                Wn=0.2, # 0 < Wn < fs/2 (fs=1 -> fs/2=0.5)
                fs=1, # sampling rate, Hz
                btype='low',
                ftype='butter', output='sos'))

    def setDerivativeFilterLevel(self, v:int) -> None:
        try:
            self.pidSemaphore.acquire(1)
            self.derivative_filter_level = v
            # reset the derivative filter on each filter level change (also on PID ON)
            self.derivative_filter = self.derivativeFilter()
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)
