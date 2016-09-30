from __future__ import division, print_function
import time
import sys
import platform

# Unresolved bug: rate(X) yields only about 0.8X iterations per second.

MIN_RENDERS = 10
MAX_RENDERS = 30
INTERACT_PERIOD = 1.0/MAX_RENDERS
USER_FRACTION = 0.5

_plat = platform.system()

if _plat == 'Windows':
    # On Windows, the best timer is supposedly time.clock()
    _clock = time.clock
    _tick = 1/60
elif _plat == 'Macintosh':
    # On platforms other than Windows, the best timer is supposedly time.time()
    _clock = time.time
    _tick = 0.01
else: # 'Unix'
    # On platforms other than Windows, the best timer is supposedly time.time()
    _clock = time.time
    _tick = 0.01 # though sleep seems to be accurate at the 1 millisecond level

##Possible way to get one-millisecond accuracy in sleep on Windows:
##http://msdn.microsoft.com/en-us/library/windows/desktop/ms686298(v=vs.85).aspx
##When your program starts, the Windows system's timer resolution has a 
##seemingly random value that depends on which programs are running 
##(and apparently, which programs were run and then exited).  
##Common values for the resolution are 15 ms and 1 ms, but a range 
##of values is possible (use timeGetDevCaps to determine this range).  
##AFAICT, calling timeBeginPeriod() changes the system timer resolution 
##for every call you make to a Win32 function with a timeout 
##(e.g., MsgWaitForMultipleObjects() works exactly the same as Sleep() 
##with respect to the timeout) and every call that every other application 
##in the system makes to a Win32 function with a timeout.

def _sleep(dt):
    # Windows sleep is quantized in multiples of 1/60 second.
    # Moreover, time.sleep can be quite inaccurate on Windows,
    # hence the use of the clock here to check time.sleep.
    if dt >= _tick:
        nticks = int(dt/_tick)
        dtsleep = nticks*_tick
        t = _clock()
        time.sleep(dtsleep)
        t = _clock()-t
        dt -= t
    if dt <= 0.0:
        return
    tend = _clock()+dt
    while _clock() < tend:
        pass
        
class simulateDelay:
    """
    Simulate rendering/compute times.. with an average value of delayAvg with 
    a variance of something like delaySigma**2.
    """

    def __init__(self, delayAvg=0.001, delaySigma=0.0001):
        self.delayAvg=delayAvg
        self.delaySigma=delaySigma
        self.callTimes = []
        
    def __call__(self):
        self.callTimes.append(_clock())

class RateKeeper(object):
    def __init__(self, interactPeriod=INTERACT_PERIOD, interactFunc=simulateDelay):
        self.interactionPeriod = interactPeriod
        self.interactFunc = interactFunc
        self.initialized = False

    def initialize(self):
        self.delay = 0.0
        self.userTime = 0.0
        self.renderTime = 0.0
        self.callTime = 0.0
        self.count = 0
        self.lastCount = 0 # value of self.count at start of a 1-second series
        self.rateCalls = 0 # number of calls to rate function before starting a new 1-sec series
        self.calls = 0 # number of calls to rate since since last render or start of 1-sec series
        self.lastSleep = self.start = _clock()

        # List of which calls to rate in a 1-second cycle should do a render:
        self.whenToRender = []
        for i in range(MAX_RENDERS+2):
            self.whenToRender.append(0)
        self.renderIndex = 0 
        self.rateCount = 0 # counts calls to rate in a 1-second cycle (reset to 0 every second)
        
    def callInteract(self):
        t = _clock()
        self.interactFunc()
        dt = _clock() - t
        if self.count == 1: self.renderTime = 0.005 # first value is abnormal; make small nonzero
        elif self.count == 2: self.renderTime = dt # we now have a measure of actual loop render time
        elif dt < 0.2: # don't count long delays due to menu or similar operations
            self.renderTime = 0.95*self.renderTime + 0.05*dt # time spent in render code

    def distributeRenders(self, M, N):
        self.renderIndex = 0
        self.rateCount = 0
        self.renderWaits = 0
        r = M/N
        x = 0.0
        j = 0
        for i in range(M):
            waits = 0
            while i+1 > x:
                self.whenToRender[j] = i
                waits += 1
                j += 1
                x += r
            if waits > 0:
                self.renderWaits += waits-1
            if i == M-1:
                self.whenToRender[j] = -1

    def buildStrategy(self, rate):
        self.lastCount = self.count
        U = self.userTime
        R = self.renderTime
        M = int(rate) # M is number of user iterations/second
        N = int(1/self.interactionPeriod) # N is number of renders/second
        if M*U + N*R > 1:
            if M*U + MIN_RENDERS*R <= 1:
                N = int((1 - M*U)/R)
            elif MIN_RENDERS*R < 1-USER_FRACTION:
                N = MIN_RENDERS
                M = int((1 - N*R)/U)
            else:
                M = int(USER_FRACTION/U)
                N = int((1-USER_FRACTION)/R)

        if N > MAX_RENDERS: N = MAX_RENDERS
        if M < 1: M = 1
        if N < 1: N = 1
        self.rateCalls = M

        # Prepare the self.renderIndex array of indices for when to do renders:
        self.distributeRenders(M, N)
        
        # M = self.rateCalls = number of calls to rate/second
        # N = number of renders/second
        # callTime = time spent in rate function (very small)
        # waits = number of interact delays/second (due to multiple renders in a long slice)
        # T = self.interactionPeriod
        # M*(U + callTime + delay) + N*R + waits*T = 1 leads to the following delay
        #   to be applied when there is no render when rate() is called:

        self.delay = (1.0 - N*R - self.renderWaits*self.interactionPeriod)/M - self.callTime - U
##        print("%1.4f %i %i %i %1.6f %1.6f %1.6f %1.6f" % (_clock(), M, N, self.renderWaits,
##                                self.userTime, self.callTime, self.delay, self.renderTime))
        
    def __call__(self, maxRate=100):
        #td.add('-------------------------')
        if not self.initialized:
            self.initialize()
            self.initialized = True
        calledTime = _clock()            
        if maxRate < 1: raise ValueError("rate value must be greater than or equal to 1")
        self.count += 1
        if self.count == 1: # first time rate has been called
            self.callInteract()
            self.lastEndRate = _clock()
            return
        
        dt = calledTime - self.lastEndRate # time spent in user code
        nr = self.whenToRender[self.renderIndex]
        if self.count == 2 or (self.count == self.lastCount + self.rateCalls):
            self.userTime = dt # the first time we have a user code time is self.count == 2
            if self.calls > 0: # if there were some calls to rate after the last render
                dt = self.lastSleep + self.calls*(self.userTime + self.callTime + self.delay) - _clock()
                _sleep(dt)
            self.buildStrategy(maxRate)
            nr = self.whenToRender[0]
            self.calls = 0
            self.lastSleep = _clock()
        elif dt < 0.2: # don't count long delays due to menu or similar operations
            self.userTime = 0.95*self.userTime + 0.05*dt
        
        dt = _clock() - calledTime # approximate amount of time spent in this function
        if self.callTime == 0.0: self.callTime = dt
        elif dt < 0.2: # don't count long delays due to menu or similar operations
            self.callTime = 0.95*self.callTime + 0.05*dt

        self.calls += 1
        if nr == self.rateCount: # There is one or more render associated with this call to rate
            renders = sleeps = 0
            while True:
                renders += 1
                self.callInteract()
                self.renderIndex += 1
                if self.whenToRender[self.renderIndex] == self.rateCount:
                    sleeps += 1
                    _sleep(self.interactionPeriod)
                else:
                    break
            # Determine how much time is left before the next predicted call to rate:
            dt = self.lastSleep + self.calls*(self.userTime + self.callTime + self.delay) + \
                 renders*self.renderTime + sleeps*self.interactionPeriod - _clock()
            _sleep(dt)
            self.lastSleep = _clock()
            self.calls = 0
        self.rateCount += 1

        self.lastEndRate = _clock()
