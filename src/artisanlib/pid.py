#!/usr/bin/env python3

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
import numpy

# expects a function control that takes a value from [<outMin>,<outMax>] to control the heater as called on each update()
class PID(object):
    def __init__(self, control=lambda _: _, p=2.0, i=0.03, d=0.0):
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
        self.active = False
        self.derivative_on_error = False # if False => derivative_on_measurement (avoids the Derivative Kick on changing the target)
        # PID output smoothing    
        self.output_smoothing_factor = 0 # off if 0
        self.output_decay_weights = None
        self.previous_outputs = []
        # PID input smoothing
        self.input_smoothing_factor = 0 # off if 0
        self.input_decay_weights = None
        self.previous_inputs = []
        
    def on(self):
        self.init()
        self.active = True
        
    def off(self):
        self.active = False
        
    def isActive(self):
        return self.active
    
    def smooth_output(self,output):
        # create or update smoothing decay weights
        if self.output_smoothing_factor != 0 and (self.output_decay_weights == None or len(self.output_decay_weights) != self.output_smoothing_factor): # recompute only on changes
            self.output_decay_weights = numpy.arange(1,self.output_smoothing_factor+1)
        # add new value
        self.previous_outputs.append(output)
        # throw away superflous values
        self.previous_outputs = self.previous_outputs[-self.output_smoothing_factor:]
        # compute smoothed output
        if len(self.previous_outputs) < self.output_smoothing_factor or self.output_smoothing_factor == 0:
            res = output # no smoothing yet
        else:
            res = numpy.average(self.previous_outputs,weights=self.output_decay_weights)
        return res
            
    
    def smooth_input(self,inp):
        # create or update smoothing decay weights
        if self.input_smoothing_factor != 0 and (self.input_decay_weights == None or len(self.input_decay_weights) != self.input_smoothing_factor): # recompute only on changes
            self.input_decay_weights = numpy.arange(1,self.input_smoothing_factor+1)
        # add new value
        self.previous_inputs.append(inp)
        # throw away superflous values
        self.previous_inputs = self.previous_inputs[-self.input_smoothing_factor:]
        # compute smoothed output
        if len(self.previous_inputs) < self.input_smoothing_factor or self.input_smoothing_factor == 0:
            res = inp # no smoothing yet
        else:
            res = numpy.average(self.previous_inputs,weights=self.input_decay_weights)
        return res
        

    # update control value
    def update(self, i):
        i = self.smooth_input(i)
        try:
            if self.active:
                now = time.time()
                err = self.target - i
                if self.lastError == None or self.lastTime == None:
                    self.lastTime = now
                    self.lastError = err
                else:
                    dt = now - self.lastTime
                    if dt>0:
                        derr = (err - self.lastError) / dt
                        if self.lastInput:
                            dinput = i - self.lastInput
                            dtinput = dinput / dt
                        else:
                            dinput = 0
                            dtinput = 0
                        
#                        # apply some simple moving average filter to avoid major spikes (used only for D)
#                        if self.lastDerr:
#                            derr = (derr + self.lastDerr) / 2.0
# This smoothing is dangerous if time between readings is not considered!
                        self.lastDerr = derr
                        
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
                        
                        output = self.smooth_output(output)
                        
                        # clamp output to [outMin,outMax] and avoid integral windup
                        if output > self.outMax:
                            output = self.outMax
                        elif output < self.outMin:
                            output = self.outMin
                            
                        int_output = min(self.dutyMax,max(self.dutyMin,int(round(output))))
                        if self.lastOutput == None or int_output >= self.lastOutput + self.dutySteps or int_output <= self.lastOutput - self.dutySteps:
                            self.control(int_output)
                            self.lastOutput = output # kept to initialize Iterm on reactivating the PID   
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
        self.lastInput = 0.0
        self.lastTime = None
        self.lastDerr = 0.0
        self.Pterm = 0.0
        self.input_decay_weights = None
        self.previous_inputs = []
        if False: # self.lastOutput != None:
            self.Iterm = self.lastOutput
        else:
            self.Iterm = 0.0
        self.lastOutput = None
        # initialize the output smoothing
        self.output_decay_weights = None
        self.previous_outputs = []

    def setTarget(self, target, init=True):
        self.target = target
        if init:
            self.init()

    def getTarget(self):
        return self.target

    def setPID(self,p,i,d,pOnE=True):
        self.Kp = max(p,0)
        self.Ki = max(i,0)
        self.Kd = max(d,0)
        self.pOnE = pOnE
        
    def setLimits(self,outMin,outMax):
        self.outMin = outMin
        self.outMax = outMax
        
    def setDutySteps(self,steps):
        self.dutySteps = steps
        
    def setDutyMin(self,m):
        self.dutyMin = m
        
    def setDutyMax(self,m):
        self.dutyMax = m
        
    def setControl(self,f):
        self.control = f
        
    def getDuty(self):
        return self.lastOutput