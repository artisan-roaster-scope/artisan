#!/usr/bin/python
# -*- coding: utf-8 -*-

# ABOUT
# This program realizes a PID controler as part of the open-source roast logging software Artisan.

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later versison. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

# AUTHOR
# Marko Luther, 2016

# Inspiered by http://brettbeauregard.com/blog/2011/04/improving-the-beginners-pid-introduction/

import time

# expects a function control that takes a value from [<outMin>,<outMax>] to control the heater as called on each update()
class PID(object):
    def __init__(self, control=lambda _: _, p=2.0, i=0.03, d=0.0):
        self.outMin = 0 # minimum output value
        self.outMax = 100 # maximum output value
        self.control = control
        self.Kp = p
        self.Ki = i
        self.Kd = d
        self.errSum = 0.0
        self.Iterm = 0.0
        self.lastError = 0.0 # used for derivative_on_error mode
        self.lastInput = 0.0 # used for derivative_on_measurement mode
        self.lastOutput = 0.0 # used to reinitialize the Iterm and to apply simple moving average on the derivative part in derivative_on_measurement mode
        self.lastTime = 0.0
        self.lastDerr = 0.0 # used for simple moving average filtering on the derivative part in derivative_on_error mode
        self.filterInput = False
        self.filterTarger = False
        self.filterDerivative = False
        self.target = 0.0
        self.active = False
        self.derivative_on_error = False # if False => derivative_on_measurement (avoids the Derivative Kick on changing the target)
        
    def on(self):
        self.init()
        self.active = True
        
    def off(self):
        self.active = False
        
    def isActive(self):
        return self.active

    # update control value
    def update(self, i):
        try:
            if self.active:
                now = time.time()
                err = self.target - i
                
                if not self.lastError or not self.lastTime:
                    self.lastTime = now
                    self.lastError = err
                else:
                    dt = now - self.lastTime
                    if dt>0:
                        derr = (err - self.lastError) / dt
                        if self.lastInput:
                            dinput = (i - self.lastInput) / dt
                        else:
                            dinput = 0
                        
                        # apply some simple moving average filter to avoid major spikes (used only for D)
                        if self.lastDerr:
                            derr = (derr + self.lastDerr) / 2.0
                        self.lastDerr = derr
                        
                        self.lastTime = now
                        self.lastError = err
                        self.lastInput = i
                        
                        # limit the effect of I
                        self.Iterm += self.Ki * err * dt
                            
                        P = self.Kp * err
                        if self.derivative_on_error:
                            D = self.Kd * derr
                        else:
                            D = - self.Kd * dinput
                        
                        output = P + self.Iterm + D
                        
                        # clamp output to [outMin,outMax] and avoid integral windup
                        if output > self.outMax:
                            if self.Ki > 0.0:
                                self.Iterm -= output - self.outMax
                            output = self.outMax
                        elif output < self.outMin:
                            if self.Ki > 0.0:
                                self.Iterm += self.outMin - output
                            output = self.outMin
                            
                        self.lastOutput = output # kept to initialize Iterm on reactivating the PID
                        
                        output = int(round(output))
                        self.control(output)
        except Exception:
#            import sys
#            import traceback
#            traceback.print_exc(file=sys.stdout)
            pass
            
    # bring the PID to its initial state (to be called externally)
    def reset(self):
        self.initialize()
        self.Iterm = 0.0
        
    # re-initalize the PID on restarting it after a temporary off state
    def init(self):
        self.errSum = 0.0
        self.lastError = 0.0
        self.lastTime = 0.0
        self.lastDerr = 0.0
        self.Iterm = self.lastOutput

    def setTarget(self, target,init=True):
        self.target = target
        if init:
            self.init()

    def getTarget(self):
        return self.target

    def setPID(self,p,i,d):
        self.Kp = max(p,0)
        self.Ki = max(i,0)
        self.Kd = max(d,0)
        
    def setLimits(self,outMin,outMax):
        self.outMin = outMin
        self.outMax = outMax
        
    def setControl(self,f):
        self.control = f