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
# Marko Luther, 2016

# Inspired by http://brettbeauregard.com/blog/2011/04/improving-the-beginners-pid-introduction/

import time
import numpy
import logging
from typing import Final

try:
    #ylint: disable-next = E, W, R, C
    from PyQt6.QtCore import QSemaphore # @Reimport @UnresolvedImport @UnusedImport
except Exception:  # pylint: disable=broad-except
    #ylint: disable = E, W, R, C
    from PyQt5.QtCore import QSemaphore # @Reimport @UnresolvedImport @UnusedImport

_log: Final = logging.getLogger(__name__)

# expects a function control that takes a value from [<outMin>,<outMax>] to control the heater as called on each update()
class PID():

    __slots__ = [ 'pidSemaphore', 'outMin', 'outMax', 'dutySteps', 'dutyMin', 'dutyMax', 'control', 'Kp',
            'Ki', 'Kd', 'pOnE', 'Pterm', 'errSum', 'Iterm', 'lastError', 'lastInput', 'lastOutput', 'lastTime',
            'lastDerr', 'target', 'active', 'derivative_on_error', 'output_smoothing_factor', 'output_decay_weights',
            'previous_outputs', 'input_smoothing_factor', 'input_decay_weights', 'previous_inputs', 'force_duty', 'iterations_since_duty' ]

    def __init__(self, control=lambda _: _, p=2.0, i=0.03, d=0.0):
        self.pidSemaphore = QSemaphore(1)

        self.outMin = 0 # minimum output value
        self.outMax = 100 # maximum output value
        self.dutySteps = 1 # change [1-10] between previous and new PID duty to trigger call of control function
        self.dutyMin = 0
        self.dutyMax = 100
        self.control = control
        self.Kp = p
        self.Ki = i
        self.Kd = d
        # Proposional on Measurement mode see: http://brettbeauregard.com/blog/2017/06/introducing-proportional-on-measurement/
        self.pOnE = True # True for Proposional on Error mode, False for Proposional on Measurement Mode
        self.Pterm = 0.0
        self.errSum = 0.0
        self.Iterm = 0.0
        self.lastError = None # used for derivative_on_error mode
        self.lastInput = 0.0 # used for derivative_on_measurement mode
        self.lastOutput = None # used to reinitialize the Iterm and to apply simple moving average on the derivative part in derivative_on_measurement mode
        self.lastTime = None
        self.lastDerr = 0.0 # used for simple moving average filtering on the derivative part in derivative_on_error mode
        self.target = 0.0
        self.active = False # if active, the control function is called with the PID results
        self.derivative_on_error = False # if False => derivative_on_measurement (avoids the Derivative Kick on changing the target)
        # PID output smoothing
        self.output_smoothing_factor = 0 # off if 0
        self.output_decay_weights = None
        self.previous_outputs = []
        # PID input smoothing
        self.input_smoothing_factor = 0 # off if 0
        self.input_decay_weights = None
        self.previous_inputs = []
        self.force_duty = 3 # at least every n update cycles a new duty value is send, even if its duplicating a previous duty (within the duty step)
        self.iterations_since_duty = 0 # reset once a duty is send; incremented on every update cycle

    def _smooth_output(self,output):
        # create or update smoothing decay weights
        if self.output_smoothing_factor != 0 and (self.output_decay_weights == None or len(self.output_decay_weights) != self.output_smoothing_factor): # recompute only on changes
            self.output_decay_weights = numpy.arange(1,self.output_smoothing_factor+1)
        # add new value
        self.previous_outputs.append(output)
        # throw away superfluous values
        self.previous_outputs = self.previous_outputs[-self.output_smoothing_factor:]
        # compute smoothed output
        if len(self.previous_outputs) < self.output_smoothing_factor or self.output_smoothing_factor == 0:
            res = output # no smoothing yet
        else:
            res = numpy.average(self.previous_outputs,weights=self.output_decay_weights)
        return res

    def _smooth_input(self,inp):
        # create or update smoothing decay weights
        if self.input_smoothing_factor != 0 and (self.input_decay_weights == None or len(self.input_decay_weights) != self.input_smoothing_factor): # recompute only on changes
            self.input_decay_weights = numpy.arange(1,self.input_smoothing_factor+1)
        # add new value
        self.previous_inputs.append(inp)
        # throw away superfluous values
        self.previous_inputs = self.previous_inputs[-self.input_smoothing_factor:]
        # compute smoothed output
        if len(self.previous_inputs) < self.input_smoothing_factor or self.input_smoothing_factor == 0:
            res = inp # no smoothing yet
        else:
            res = numpy.average(self.previous_inputs,weights=self.input_decay_weights)
        return res

    ### External API guarded by semaphore

    def on(self):
        try:
            self.pidSemaphore.acquire(1)
#            self.init() # we keep the PID running always, even if inactive, and do not disturb it with an init on switching it active
            self.lastOutput = None # this ensures that the next update sends a control output
            self.active = True
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def off(self):
        try:
            self.pidSemaphore.acquire(1)
            self.active = False
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def isActive(self):
        try:
            self.pidSemaphore.acquire(1)
            return self.active
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)


    # update control value (the pid loop is running even if PID is inactive, just the control function is only called if active)
    def update(self, i):
        try:
            self.pidSemaphore.acquire(1)
            i = self._smooth_input(i)
            now = time.time()
            err = self.target - i
            if self.lastError == None or self.lastTime == None:
                self.lastTime = now
                self.lastError = err
            else:
                dt = now - self.lastTime
                if dt>0.2:
                    derr = (err - self.lastError) / dt
                    if self.lastInput:
                        dinput = i - self.lastInput
                        dtinput = dinput / dt
                    else:
                        dinput = 0
                        dtinput = 0

#                    # apply some simple moving average filter to avoid major spikes (used only for D)
#                    if self.lastDerr:
#                        derr = (derr + self.lastDerr) / 2.0
## This smoothing is dangerous if time between readings is not considered!
#                    self.lastDerr = derr

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
                    if self.derivative_on_error:
                        D = self.Kd * derr
                    else:
                        D = - self.Kd * dtinput

                    output = self.Pterm + self.Iterm + D

                    output = self._smooth_output(output)

                    # clamp output to [outMin,outMax] and avoid integral windup
                    if output > self.outMax:
                        output = self.outMax
                    elif output < self.outMin:
                        output = self.outMin

                    int_output = min(self.dutyMax,max(self.dutyMin,int(round(output))))
                    if self.lastOutput == None or self.iterations_since_duty >= self.force_duty or int_output >= self.lastOutput + self.dutySteps or int_output <= self.lastOutput - self.dutySteps:
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
    def reset(self):
        try:
            self.pidSemaphore.acquire(1)
            self.init()
            self.Iterm = 0.0
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    # re-initalize the PID on restarting it after a temporary off state
    def init(self):
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

    def setTarget(self, target, init=True):
        try:
            self.pidSemaphore.acquire(1)
            self.target = target
            if init:
                self.init()
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def getTarget(self):
        try:
            self.pidSemaphore.acquire(1)
            return self.target
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def setPID(self,p,i,d,pOnE=True):
        try:
            self.pidSemaphore.acquire(1)
            self.Kp = max(p,0)
            self.Ki = max(i,0)
            self.Kd = max(d,0)
            self.pOnE = pOnE
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def setLimits(self,outMin,outMax):
        try:
            self.pidSemaphore.acquire(1)
            self.outMin = outMin
            self.outMax = outMax
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def setDutySteps(self,steps):
        try:
            self.pidSemaphore.acquire(1)
            self.dutySteps = steps
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def setDutyMin(self,m):
        try:
            self.pidSemaphore.acquire(1)
            self.dutyMin = m
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def setDutyMax(self,m):
        try:
            self.pidSemaphore.acquire(1)
            self.dutyMax = m
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def setControl(self,f):
        try:
            self.pidSemaphore.acquire(1)
            self.control = f
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)

    def getDuty(self):
        try:
            self.pidSemaphore.acquire(1)
            return self.lastOutput
        finally:
            if self.pidSemaphore.available() < 1:
                self.pidSemaphore.release(1)
