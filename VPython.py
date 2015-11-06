from __future__ import print_function, division, absolute_import
from . import crayola as color
from . import materials
import numpy as np
#from array import array
from .rate_control import *
import IPython
if IPython.__version__ >= '4.0.0' :
    import ipykernel
    from ipykernel.comm import Comm
    import notebook
else:
    from IPython.kernel.comm import Comm
    import IPython.html.nbextensions
from IPython.display import HTML
from IPython.display import display, display_html, display_javascript
from IPython.display import Javascript
from IPython.core.getipython import get_ipython

import time
import math
import uuid
import inspect
from time import clock
import os
import datetime, threading
import collections
import copy
import sys
import weakref

from numpy import zeros, random
#import wx
import platform

glowlock = threading.Lock()

class RateKeeper2(RateKeeper):
    
    def __init__(self, interactPeriod=INTERACT_PERIOD, interactFunc=simulateDelay):
        self.active = False
        self.send = False
        self.sz = 0
        self.sendcnt = 0
        self.rval = 1
        super(RateKeeper2, self).__init__(interactPeriod=interactPeriod, interactFunc=interactFunc)

    def sendtofrontend(self):
        self.active = True
        if self.send:
            with glowlock:                    
                try:
                    if (len(baseObj.cmds) > 0):
                        a = copy.copy(baseObj.cmds)
                        l = len(a)
                        baseObj.glow.comm.send(list(a))
                        a.clear()
                        while l > 0:
                            del baseObj.cmds[0]
                            l -= 1                

                    l = self.sz
                    req = commcmds[:l]
                    baseObj.glow.comm.send(req)
                finally:
                    self.send = False
                    self.sendcnt = 0
                    self.sz = 0

        # Check if events to process from front end
        if IPython.__version__ >= '3.0.0' :
            kernel = get_ipython().kernel
            parent = kernel._parent_header
            ident = kernel._parent_ident
            kernel.do_one_iteration()
            kernel.set_parent(ident, parent)
            
    def __call__(self, maxRate = 100):
        if (self.rval != maxRate) and (maxRate >= 1.0):
            with glowlock:
                self.rval = maxRate 
        super(RateKeeper2, self).__call__(maxRate)

if sys.version > '3':
    long = int

ifunc = simulateDelay(delayAvg = 0.001)
rate = RateKeeper2(interactFunc = ifunc)

display(HTML("""<div id="scene0"><div id="glowscript" class="glowscript"></div></div>"""))

package_dir = os.path.dirname(__file__)
if IPython.__version__ >= '4.0.0' :
    notebook.nbextensions.install_nbextension(path = package_dir+"/data/jquery-ui.custom.min.js",overwrite = True,user = True,verbose = 0)
    notebook.nbextensions.install_nbextension(path = package_dir+"/data/glow.1.1.min.js",overwrite = True,user = True,verbose = 0)
    notebook.nbextensions.install_nbextension(path = package_dir+"/data/glowcomm.js",overwrite = True,user = True,verbose = 0)
elif IPython.__version__ >= '3.0.0' :
    IPython.html.nbextensions.install_nbextension(path = package_dir+"/data/jquery-ui.custom.min.js",overwrite = True,user = True,verbose = 0)
    IPython.html.nbextensions.install_nbextension(path = package_dir+"/data/glow.1.1.min.js",overwrite = True,user = True,verbose = 0)
    IPython.html.nbextensions.install_nbextension(path = package_dir+"/data/glowcomm.js",overwrite = True,user = True,verbose = 0)
else:
    IPython.html.nbextensions.install_nbextension(files = [package_dir+"/data/jquery-ui.custom.min.js",package_dir+"/data/glow.1.1.min.js",package_dir+"/data/glowcomm.js"],overwrite=True,verbose=0)


object_registry = {} # GUID -> Instance
callback_registry = {}  # GUID -> Callback

_id2obj_dict = weakref.WeakValueDictionary()

def remember(obj):
    oid = id(obj)
    _id2obj_dict[oid] = obj
    return oid

def id2obj(oid):
    return _id2obj_dict[oid]


class baseObj(object):
    txtime = 0.0
    idx = 0
    qSize = 500            # default to 500
    qTime = 0.034          # default to 0.05
    glow = None
    cmds = collections.deque()
    updtobjs = set()
    objCnt = 0
    
    def __init__(self, **kwargs):
        guid = str(uuid.uuid4())
        object_registry[guid] = self
        object.__setattr__(self, 'guid', guid)
        object.__setattr__(self, 'idx', baseObj.objCnt)
        object.__setattr__(self, 'attrsupdt', set())
        object.__setattr__(self, 'oid', remember(self))
        if kwargs is not None:
            for key, value in kwargs.items():
                object.__setattr__(self, key, value)
        baseObj.incrObjCnt()
        if(canvas.get_selected() != None):
            canvas.get_selected().objects.append(self)
        
    def delete(self):
        baseObj.decrObjCnt()
        cmd = {"cmd": "delete", "idx": self.idx}
        if (baseObj.glow != None):
            baseObj.glow.comm.send([cmd])
        else:
            self.appendcmd(cmd)
        #baseObj.cmds.append(cmd)

    def appendcmd(self,cmd):
        if (baseObj.glow != None):
            #if rate.active and rate.sendcnt < 5:
            #    baseObj.cmds.append(cmd)
            #else:
            #    baseObj.glow.comm.send([cmd])
            baseObj.glow.comm.send([cmd])
        else:
            baseObj.cmds.append(cmd)


    def addattr(self, name):
        # New-way to use a lock
        with glowlock:
            self.attrsupdt.add(name)
            baseObj.updtobjs.add(self.oid)
    
    @classmethod
    def incrObjCnt(cls):
        cls.objCnt += 1

    @classmethod
    def decrObjCnt(cls):
        cls.objCnt -= 1

    def __del__(self):
        cmd = {"cmd": "delete", "idx": self.idx}
        if (baseObj.glow != None):
            baseObj.glow.comm.send([cmd])
        else:
            self.appendcmd(cmd)
        #baseObj.cmds.append(cmd)

commcmds = []
for i in range(baseObj.qSize):
    commcmds.append({"idx": -1, "attr": 'dummy', "val": 0})
updtobjs2 = set()
next_call = time.time()

def commsend():
    global next_call, commcmds, updtobjs2, glowlock, rate
    #glowlock.acquire()
    with glowlock:
        try:
            if (baseObj.glow != None):

                if (len(baseObj.cmds) > 0) and (not rate.active):
                    #print("commsend len(baseObj.cmds) > 0")
                    a = copy.copy(baseObj.cmds)
                    l = len(a)
                    baseObj.glow.comm.send(list(a))
                    a.clear()
                    while l > 0:
                        del baseObj.cmds[0]
                        l -= 1 

                l = rate.sz if (rate.send == True) else 0
                if (l > 0):
                    rate.sendcnt += 1
                    thresh = math.ceil(30.0/rate.rval) * 2 + 1
                    if (rate.sendcnt > thresh ):
                        rate.send = False
                        rate.sz = 0
                        rate.active = False       # rate fnc no longer appears to be being called
                else:
                    rate.sendcnt = 0
                if(len(updtobjs2) == 0):
                    updtobjs2 = baseObj.updtobjs.copy()
                    baseObj.updtobjs.clear()
                if l < baseObj.qSize:
                    while updtobjs2:
                        oid = updtobjs2.pop()
                        ob = id2obj(oid)
                        if  (ob is not None) and (hasattr(ob,'attrsupdt')) and (len(ob.attrsupdt) > 0 ):
                            while ob.attrsupdt:
                                attr = ob.attrsupdt.pop()
                                if attr is not None:
                                    attrval = getattr(ob,attr)
                                    if attrval is not None:
                                        if attr in ['axis','pos','up','axis_and_length','center','forward','origin']:
                                            attrvalues = attrval.values()
                                            if attrvalues is not None:
                                                commcmds[l]['idx'] = ob.idx
                                                commcmds[l]['attr'] = attr
                                                commcmds[l]['val'] = attrvalues
                                        elif attr == 'size':
                                            if hasattr(ob,'size_units'):
                                                commcmds[l]['idx'] = ob.idx
                                                commcmds[l]['attr'] = attr
                                                commcmds[l]['val'] = attrval
                                            else:
                                                attrvalues = attrval.values()
                                                if attrvalues is not None:
                                                    commcmds[l]['idx'] = ob.idx
                                                    commcmds[l]['attr'] = attr
                                                    commcmds[l]['val'] = attrvalues
                                        elif attr in ['range','scale']:
                                            attrvalues = attrval[0]
                                            if attrvalues is not None:
                                                commcmds[l]['idx'] = ob.idx
                                                commcmds[l]['attr'] = attr
                                                commcmds[l]['val'] = attrvalues
                                        else:
                                            commcmds[l]['idx'] = ob.idx
                                            commcmds[l]['attr'] = attr
                                            commcmds[l]['val'] = attrval
                                        l += 1
                                        if l >= baseObj.qSize:
                                            if (len(ob.attrsupdt) > 0):
                                                updtobjs2.add(ob.oid)
                                            #ob.attrsupdt.add(attr)
                                            #baseObj.updtobjs.add(ob.oid)
                                            #baseObj.updtobjs.append(ob.oid)

                                            """
                                            if not rate.active:
                                                req = commcmds[:l]
                                                baseObj.glow.comm.send(req)
                                            else:
                                                rate.sz = l
                                                rate.send = True
                                            """
                                            break
                        if l >= baseObj.qSize:
                            #l = 0
                            break
                if l > 0:
                    if not rate.active:
                        l = l if (l <= baseObj.qSize) else baseObj.qSize
                        baseObj.glow.comm.send(commcmds[:l])
                    else:
                        rate.sz = l if (l <= baseObj.qSize) else baseObj.qSize
                        rate.send = True

        finally:
            next_call = next_call+0.03333
            tmr = next_call - time.time()
            if tmr < 0.0:
                tmr = 0.03333
                next_call = time.time()+tmr
            threading.Timer(tmr, commsend ).start()
    
commsend()

class AllMyFields(object):
    def __init__(self, dictionary):
        for k, v in dictionary.items():
            setattr(self, k, v)
            
class GlowWidget(object):
    
    def __init__(self, comm, msg):
        self.comm = comm
        self.comm.on_msg(self.handle_msg)
        self.comm.on_close(self.handle_close)
        baseObj.glow = self

    
    #def handle_msg(self, data):
    def handle_msg(self, msg):
        data = msg['content']['data']
        if 'callback' in data:
            guid = data['callback']
            callback = callback_registry[guid]
            args = data['arguments']
            #args = json.loads(data['arguments'])
            #args = [self.parse_object(a) for a in args]
            #self.comm.send([{'cmd': 'debug', 'data': data}])
            #cmd = {'cmd': 'debug', 'data': data}
            #baseObj.cmds.append(cmd)
            evt = {}
            evt['pos'] = tuple(args[0]['pos'])
            evt['type'] = args[0]['type']
            evt['which'] = args[0]['which']
            evt['event'] = args[0]['type']
            evt['button'] = 'left' if evt['which'] == 1 else 'right' if evt['which'] == 2 else 'middle'
            evt['pickpos'] = args[0]['mouse']['pickpos']
            if 'pickguid' in args[0]['mouse']:
                pickguid = args[0]['mouse']['pickguid']
                evt['pick'] = object_registry[pickguid]
            else:
                evt['pick'] = None
            """
            mouse = {}
            if 'pickguid' in args[0]['mouse']:
                pickguid = args[0]['mouse']['pickguid']
                mouse['pick'] = object_registry[pickguid]
            else:
                mouse['pick'] = None
            #mouse['pickpos'] = args[0]['mouse']['pickpos']
            #mouse['ray'] = args[0]['mouse']['ray']
            #mouse['alt'] = args[0]['mouse']['alt']
            mouse['ctrl'] = args[0]['mouse']['ctrl']
            mouse['shift'] = args[0]['mouse']['shift']
            evt['mouse'] = AllMyFields(mouse)
            """
            mouse = Mouse(pos = vector(evt['pos']), pick = evt['pick'], pickpos = vector(args[0]['mouse']['pickpos']), alt = args[0]['mouse']['alt'], ctrl = args[0]['mouse']['ctrl'],
                          shift = args[0]['mouse']['shift'])
            evt['mouse'] = mouse
            if 'scene' in data:
                sguid = data['scene']
                object_registry[sguid].mouse = mouse

            tp = inspect.getargspec(callback)   # named tuple of callback args  (args, varargs, keywords, defaults)
            if (len(tp.args) == 0) and (tp.varargs == None) and (tp.keywords == None) and (tp.defaults == None):
                callback()
            elif (len(tp.args) == 1) and (tp.varargs == None) and (tp.keywords == None) and (tp.defaults == None):
                callback(AllMyFields(evt))
            elif (len(tp.args) >= 2) and (tp.varargs == None) and (tp.keywords == None) and (tp.defaults == None):
                addArgs = self.parse_object(args[1])
                if type(addArgs) is list:
                    callback(AllMyFields(evt),*addArgs)
                else:
                    callback(AllMyFields(evt), addArgs)
            elif (len(tp.args) == 1) and (tp.varargs != None) and (tp.keywords == None) and (tp.defaults == None):
                if len(data['arguments']) > 1:
                    addArgs = self.parse_object(args[1])
                    if type(addArgs) is list:
                        callback(AllMyFields(evt),*addArgs)
                    else:
                        ta = [addArgs]
                        callback(AllMyFields(evt),*ta)
                else:
                    callback(AllMyFields(evt))
            elif (len(tp.args) == 0) and (tp.varargs != None) and (tp.keywords == None) and (tp.defaults == None):
                if len(data['arguments']) > 1:
                    addArgs = self.parse_object(args[1])
                    ta = [AllMyFields(evt),addArgs]
                    callback(*ta)
                else:
                    ta = [AllMyFields(evt)]
                    callback(*ta)
            else:
                #cmd = {'cmd': 'debug', 'data': {'cb_called': False}}
                #baseObj.cmds.append(cmd)
                pass
            

    def handle_close(self, data):
        print ("Comm closed")

    def get_execution_count(self):
        return get_ipython().execution_count

    def parse_object(self, obj):
        if type(obj) in [str, int, long, bool, float, tuple, complex]:
            return obj
        elif isinstance(obj, collections.Sequence):
            if type(obj) is list:
                lst = []
                for itm in obj:
                    if isinstance(itm, collections.Sequence) and  ('guido' in itm):
                        lst.append(object_registry[itm['guido']])
                    else:
                        lst.append(itm)
                if (len(lst) == 3) and (type(lst[0]) in [int, long, float]) and (type(lst[1]) in [int, long, float]) and (type(lst[2]) in [int, long, float]):
                    return tuple(lst)
                return lst
        elif 'guido' in obj:
            return object_registry[obj['guido']]
        
        return obj

if IPython.__version__ >= '3.0.0' :
    get_ipython().kernel.comm_manager.register_target('glow', GlowWidget)
else:
    get_ipython().comm_manager.register_target('glow', GlowWidget)   
display(Javascript("""require.undef("nbextensions/glow.1.0.min");"""))
display(Javascript("""require.undef("nbextensions/jquery-ui.custom.min");"""))
display(Javascript("""require.undef("nbextensions/glow.1.1.min");"""))
display(Javascript("""require.undef("nbextensions/glowcomm");"""))
display(Javascript("""require(["nbextensions/glowcomm"], function(){console.log("glowcomm loaded");})"""))
            
get_ipython().kernel.do_one_iteration()

class vector(object):
    'vector class'
    __change_notifications = None
    def __init__(self, x=(0.,0.,0.), y=0., z=0.):
        if isinstance(x, (int, long, float)) and isinstance(y, (int, long, float)) and isinstance(z, (int, long, float)):
            self.__dict__['x'] = x
            self.__dict__['y'] = y
            self.__dict__['z'] = z
        elif isinstance(x, (complex)) or isinstance(y, (complex)) or isinstance(z, (complex)):
            raise Exception("ArgumentError: complex argument not supported for vector(arg0,arg1,arg2)")
        else:
            self.__dict__['x'] = x[0]
            self.__dict__['y'] = x[1]
            self.__dict__['z'] = x[2]
        #self.__dict__['shape'] = (3L,)          # python 2
        self.__dict__['shape'] = (3,)           # python 3K
        self.__change_notifications = set()
        
    def __str__(self):
        return '<%f, %f, %f>' % (self.x, self.y, self.z)
   
    def __repr__(self):
        return '<%f, %f, %f>' % (self.x, self.y, self.z)
   
    def __array__(self, dtypes = [None]):
        return np.array((self.x, self.y, self.z), dtype = dtypes[0])

    def __add__(self,other):
        if type(other) in [np.ndarray, tuple, list]:
            return vector(self.x + other[0], self.y + other[1], self.z + other[2])
        else:
            return vector(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self,other):
        if type(other) in [np.ndarray, tuple, list]:
            return vector(self.x - other[0], self.y - other[1], self.z - other[2])
        else:
            return vector(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __mul__(self, other):
        if isinstance(other, (int, long, float)):
            return vector(self.x * other, self.y * other, self.z * other)
        elif isinstance(other, (complex)):
            raise Exception("TypeError: unsupported operand type(s) for *: 'complex' and 'vector'")
        return self
    
    def __rmul__(self, other):
        if isinstance(other, (int, long, float)):
            return vector(self.x * other, self.y * other, self.z * other)
        elif isinstance(other, (complex)):
            raise Exception("TypeError: unsupported operand type(s) for *: 'complex' and 'vector'")
        return self

    def __div__(self, other):
        if isinstance(other, (int, long, float)):
            return vector(self.x / other, self.y / other, self.z / other)
        elif isinstance(other, (complex)):
            raise Exception("TypeError: unsupported operand type(s) for /: 'complex' and 'vector'")
        return self
    
    def __truediv__(self, other):
        if isinstance(other, (int, long, float)):
            return vector(self.x / other, self.y / other, self.z / other)
        elif isinstance(other, (complex)):
            raise Exception("TypeError: unsupported operand type(s) for /: 'complex' and 'vector'")
        return self

    def __neg__(self):
        return vector(-1.*self.x, -1.*self.y, -1.*self.z)

    def __getitem__(self,key):
        if key == 0:
            return self.x
        elif key == 1:
            return self.y
        elif key == 2:
            return self.z
        else:
            return

    def __setitem__(self,key,value):
        if key == 0:
            self.x = value
        elif key == 1:
            self.y = value
        elif key == 2:
            self.z = value

    def __del__(self):
        self.__change_notifications.clear()
        
    def mag(self):
        return np.linalg.norm(np.array([self.x,self.y,self.z]))

    def mag2(self):
        return self.mag()*self.mag()

    def norm(self):
        smag = self.mag()
        if (smag > 0.):
            return self / self.mag()
        else:
            return vector(0.,0.,0.)

    def dot(self,other):
        if type(other) is np.ndarray:
            return np.dot(np.array([self.x,self.y,self.z]),other)
        else:
            return np.dot(np.array([self.x,self.y,self.z]),np.array([other.x,other.y,other.z]))

    def cross(self,other):
        if type(other) is np.ndarray:
            return vector(np.cross(np.array([self.x,self.y,self.z]),other))
        elif (type(other) is tuple) or (type(other) is list):
            return vector(np.cross(np.array([self.x,self.y,self.z]),np.array(other)))
        else:
            return vector(np.cross(np.array([self.x,self.y,self.z]),np.array([other.x,other.y,other.z])))

    def proj(self,other):
        normB = other.norm()
        return self.dot(normB) * normB

    def comp(self,other):
        normB = other.norm()
        return self.dot(normB) * normB

    def diff_angle(self, other):
        return np.arccos(np.clip(self.norm().dot(other.norm()),-1.,1.))

    def rotate(self,angle = 0.,axis = (0,0,1)):
        if type(axis) is np.ndarray:
            axis = axis/math.sqrt(np.dot(axis,axis))
        elif (type(axis) is tuple) or (type(axis) is list):
            axis = np.array(axis)
            axis = axis/math.sqrt(np.dot(axis,axis))
        else:
            axis = axis/math.sqrt(axis.dot(axis))
            axis = np.array([axis.x,axis.y,axis.z])
        c = math.cos(angle)
        s = math.sin(angle)
        t = 1-c
        u = norm(axis)
        x = u.x
        y = u.y
        z = u.z
        mat = np.array([ [t*x*x+c, t*x*y-z*s, t*x*z+y*s],
                         [t*x*y+z*s, t*y*y+c, t*y*z-x*s],
                         [t*x*z-y*s, t*y*z+x*s, t*z*z+c] ])
        v = np.array([self.x,self.y,self.z])
        res = np.dot(mat,v)
        return vector(res)
    
    def astuple(self):
        return (self.x,self.y,self.z)
  
    def keys(self):
        return [0,1,2]
    
    def values(self):
        return [self.x,self.y,self.z]

    def __setattr__(self, name, value):
        if name in ['mag','mag2']:
            normA = self.norm()
            if name == 'mag':
                self.__dict__['x'] = value * normA.x
                self.__dict__['y'] = value * normA.y
                self.__dict__['z'] = value * normA.z
                self.on_change()
            elif name == 'mag2':
                self.__dict__['x'] = math.sqrt(value) * normA.x
                self.__dict__['y'] = math.sqrt(value) * normA.y
                self.__dict__['z'] = math.sqrt(value) * normA.z
                self.on_change()
        elif name in ['x','y','z']:
            if getattr(self, name) != value:
                self.on_change()
            self.__dict__[name] = value
        else:
            super(vector, self).__setattr__(name, value)

    def add_notification(self, tup):
        self.__change_notifications.add(tup)

    def remove_notification(self, tup):
        self.__change_notifications.remove(tup)

    def on_change(self):
        for tup in self.__change_notifications:
            tup[0](tup[1])

def mag(A):
    if (type(A) is np.ndarray) or (type(A) is tuple) or (type(A) is list):
        return vector(A).mag()
    else:
        return A.mag()
    
def mag2(A):
    if (type(A) is np.ndarray) or (type(A) is tuple) or (type(A) is list):
        return vector(A).mag2()
    else:
        return A.mag2()

def norm(A):
    if (type(A) is np.ndarray) or (type(A) is tuple) or (type(A) is list):
        return vector(A).norm()
    else:
        return A.norm()

def dot(A,B):
    if (type(A) is np.ndarray) or (type(A) is tuple) or (type(A) is list):
        return vector(A).dot(B)
    else:
        return A.dot(B)

def cross(A,B):
    if (type(A) is np.ndarray) or (type(A) is tuple) or (type(A) is list):
        return vector(A).cross(B)
    else:
        return A.cross(B)

def proj(A,B):
    if (type(A) is np.ndarray) or (type(A) is tuple) or (type(A) is list):
        return vector(A).proj(B)
    else:
        return A.proj(B)

def comp(A,B):
    if (type(A) is np.ndarray) or (type(A) is tuple) or (type(A) is list):
        return vector(A).comp(B)
    else:
        return A.comp(B)

def diff_angle(A,B):
    if (type(A) is np.ndarray) or (type(A) is tuple) or (type(A) is list):
        return vector(A).diff_angle(B)
    else:
        return A.diff_angle(B)

def rotate(A,angle = 0.,axis = (0,0,1)):
    if (type(A) is np.ndarray) or (type(A) is tuple) or (type(A) is list):
        return vector(A).rotate(angle,axis)
    else:
        return A.rotate(angle,axis)

def astuple(A):
    if (type(A) is np.ndarray) or (type(A) is tuple) or (type(A) is list):
        return vector(A).astuple()
    else:
        return A.astuple()


class baseAttrs(baseObj):
    pos = vector(0.,0.,0.)
    x = 0.
    y = 0.
    z = 0.
    size = vector(1.,1.,1.)
    axis = vector(1.,0.,0.)
    up = vector(0.,1.,0.)
    red = 1.
    green = 1.
    blue = 1.
    visible = False
    
    def __init__(self, pos=(0.,0.,0.), x=0., y=0., z=0., axis=(1.,0.,0.), size=(1.,1.,1.), visible=True,
                 up=(0.,1.,0.), color=(1.,1.,1.), red=1., green=1., blue=1., frame=None, display=None, **kwargs):
        super(baseAttrs, self).__init__(**kwargs)
        if (x != 0.) or (y != 0.) or (z != 0.):
            pos = vector(x,y,z) if type(pos) is tuple else pos
        else:
            x = pos[0]
            y = pos[1]
            z = pos[2]
        if (red != 1.) or (green != 1.) or (blue != 1.):
            color = (red,green,blue)
        else:
            red = color[0]
            green = color[1]
            blue = color[2]
        
        object.__setattr__(self, 'pos', vector(pos) if type(pos) in [tuple, list, np.ndarray] else pos )
        object.__setattr__(self, 'x', x)
        object.__setattr__(self, 'y', y)
        object.__setattr__(self, 'z', z)        
        object.__setattr__(self, 'axis', vector(axis) if type(axis) in [tuple, list, np.ndarray] else axis)
        object.__setattr__(self, 'size', vector(size) if type(size) in [tuple, list, np.ndarray] else size)
        object.__setattr__(self, 'up', vector(up) if type(up) in [tuple, list, np.ndarray] else up)
        object.__setattr__(self, 'color', color)
        object.__setattr__(self, 'red', red)
        object.__setattr__(self, 'green', green)
        object.__setattr__(self, 'blue', blue)        
        object.__setattr__(self, 'visible', visible)
        object.__setattr__(self, 'display', display)
        object.__setattr__(self, 'frame', frame)
        object.__getattribute__(self, 'pos').add_notification((self.addattr,'pos'))
        object.__getattribute__(self, 'axis').add_notification((self.addattr,'axis'))
        object.__getattribute__(self, 'size').add_notification((self.addattr,'size'))
        object.__getattribute__(self, 'up').add_notification((self.addattr,'up'))

    def __setattr__(self, name, value):
        if name in ['pos','size','axis','up','visible','x','y','z','red','green','blue']:
            if name in ['pos','axis','size','up']:
                self.__dict__[name].remove_notification((self.addattr,name))

            self.__dict__[name] = value if type(value) is vector else vector(value) if type(value) in [tuple, list, np.ndarray] else value

            if name == 'x':
                self.__dict__['pos'][0] = value
                self.addattr('pos')
            elif name == 'y':
                self.__dict__['pos'][1] = value
                self.addattr('pos')
            elif name == 'z':
                self.__dict__['pos'][2] = value
                self.addattr('pos')
            elif name == 'pos':
                self.__dict__[name].add_notification((self.addattr,name))
                self.addattr(name)
            elif name == 'axis':
                self.__dict__[name].add_notification((self.addattr,name))
                self.addattr(name)
            elif name == 'size':
                self.__dict__[name].add_notification((self.addattr,name))
                self.addattr(name)
            elif name == 'up':
                self.__dict__[name].add_notification((self.addattr,name))
                self.addattr(name)
            elif name == 'visible':
                self.addattr(name)
            elif name == 'red':
                self.__dict__['color'] = (value,self.green,self.blue)
                self.addattr('color')
            elif name == 'green':
                self.__dict__['color'] = (self.red,value,self.blue)
                self.addattr('color')
            elif name == 'blue':
                self.__dict__['color'] = (self.red,self.green,value)
                self.addattr('color')
        elif name == 'color':
            self.__dict__[name] = value
            self.addattr(name)                
        else:
            super(baseAttrs, self).__setattr__(name, value)

    def __getattribute__(self, name):
        if name in ['x','y','z','red','green','blue']:
            if name == 'x':
                return object.__getattribute__(self, 'pos')[0]
            elif name == 'y':
                return object.__getattribute__(self, 'pos')[1]
            elif name == 'z':
                return object.__getattribute__(self, 'pos')[2]
            if name == 'red':
                return object.__getattribute__(self, 'color')[0]
            elif name == 'green':
                return object.__getattribute__(self, 'color')[1]
            elif name == 'blue':
                return object.__getattribute__(self, 'color')[2]
        else:
            return super(baseAttrs, self).__getattribute__(name)
            
    def rotate(self, angle=math.pi/4, axis=None, origin=None):
        if axis == None:
            rotaxis = self.__getattribute__('axis')
        else:
            rotaxis = norm(vector(axis)) if type(axis) in [tuple, list, np.ndarray] else axis
        if origin == None:
            origin = self.__getattribute__('pos')
        else:
            origin = vector(origin) if type(origin) in [tuple, list, np.ndarray] else origin
        self.__setattr__('pos', origin+(self.pos-origin).rotate(angle, rotaxis))
        axis = self.__getattribute__('axis')
        X = norm(axis)
        Y = self.__getattribute__('up')
        Z = X.cross(Y)
        if Z.dot(Z) < 1e-10:
            Y = vector(1,0,0)
            Z = X.cross(Y)
            if Z.dot(Z) < 1e-10:
                Y = vector(0,1,0)            
        self.__setattr__('axis', axis.rotate(angle, rotaxis))          
        self.__setattr__('up', Y.rotate(angle, rotaxis))

    def __del__(self):
        for attr in ['pos','axis','size','up']:
            object.__getattribute__(self, attr).remove_notification((self.addattr,attr))
        super(baseAttrs, self).__del__()

        
class baseAttrs2(baseAttrs):
    texture = None
    opacity = 1.0
    shininess = 0.6
    emissive = False
    
    def __init__(self, pos=(0.,0.,0.), x=0., y=0., z=0., axis=(1.,0.,0.), size=(1.,1.,1.), visible=True,
                 up=(0.,1.,0.), color=(1.,1.,1.), red=1., green=1., blue=1., frame=None, display=None, material=None,
                 opacity=1.0, **kwargs):
        super(baseAttrs2, self).__init__(pos=pos, axis=axis, size=size, up=up, color=color, red=red, green=green, blue=blue,
                                         x=x, y=y, z=z, frame=frame, display=display, visible=visible, **kwargs)
        object.__setattr__(self, 'texture', None )
        object.__setattr__(self, 'opacity', opacity )
        object.__setattr__(self, 'shininess', 0.6)
        object.__setattr__(self, 'emissive', False)
        object.__setattr__(self, 'material', material)
        if (material != None):
            if (material == materials.emissive):
                object.__setattr__(self, 'emissive', True)
            elif (material == materials.plastic):
                object.__setattr__(self, 'emissive', False)
            else:
                pass
        
    def __setattr__(self, name, value):
        if name in ['material','opacity']:
            if name == 'material':
                self.__dict__[name] = value
                if (value == materials.emissive):
                    object.__setattr__(self, 'emissive', True)
                    self.addattr('emissive')
                elif (value == materials.plastic):
                    object.__setattr__(self, 'emissive', False)
                    self.addattr('emissive')
                else:
                    object.__setattr__(self, 'emissive', False)
                    self.addattr('emissive')
            elif name == 'opacity':
                self.__dict__[name] = value
                self.addattr(name)            
        else:
            super(baseAttrs2, self).__setattr__(name, value)

    def __del__(self):
        super(baseAttrs2, self).__del__()

class trailAttrs(baseAttrs2):
    make_trail = False
    trail_type = "curve"
    interval = 1
    retain = -1
    trail_object = None
    
    def __init__(self, pos=(0.,0.,0.), x=0., y=0., z=0., axis=(1.,0.,0.), size=(1.,1.,1.), visible=True,
                 up=(0.,1.,0.), color=(1.,1.,1.), red=1., green=1., blue=1., frame=None, display=None, material=None,
                 opacity=1.0, make_trail=False, trail_type="curve", interval=1, retain=-1, **kwargs):
        super(trailAttrs, self).__init__(pos=pos, axis=axis, size=size, up=up, color=color, red=red, green=green, 
                                         blue=blue, x=x, y=y, z=z, frame=frame, display=display, visible=visible, 
                                         material=material, opacity=opacity, **kwargs)
        object.__setattr__(self, 'make_trail', make_trail )
        if (trail_type not in ['curve', 'points']):
            raise Exception("ArgumentError: trail_type must be 'curve' or 'points'")
        object.__setattr__(self, 'trail_type', trail_type )
        object.__setattr__(self, 'interval', interval)
        object.__setattr__(self, 'retain', retain)
        #object.__setattr__(self, 'trail_object', curve() if self.trail_type == "curve" else pnts())

    def __setattr__(self, name, value):
        if name in ['make_trail','trail_type','interval','retain']:
            if (name == 'trail_type') and (value not in ['curve', 'points']):
                raise Exception("ArgumentError: trail_type must be 'curve' or 'points'")
            self.__dict__[name] = value
            self.addattr(name)
        else:
            super(trailAttrs, self).__setattr__(name, value)

    def __del__(self):
        super(trailAttrs, self).__del__()


class box(trailAttrs):
    """see box documentation at http://vpython.org/contents/docs/box.html"""
    def __init__(self, pos=(0.,0.,0.), x=0., y=0., z=0., axis=(1.,0.,0.), size=None,
                 length=None, width=1., height=1., up=(0.,1.,0.), color=(1.,1.,1.), red=1., green=1., blue=1.,
                 frame=None, material=None, opacity=1.0, display=None, visible=True,
                 make_trail=False, trail_type="curve", interval=1, retain=-1, **kwargs):
        axis = vector(axis) if type(axis) in [tuple, list, np.ndarray] else axis
        if (length == None) and (size == None):
            length = axis.mag()
            size = vector(length, height, width)
        elif (length == None):
            length = size[0]
            height = size[1]
            width = size[2]
        else:
            size = vector(length, height, width)
        size = vector(size) if type(size) in [tuple, list, np.ndarray] else size
        axis = axis.norm() * length
        super(box, self).__init__(pos=pos, x=x, y=y, z=z, axis=axis, size=size, up=up, color=color, red=red, green=green, blue=blue,
                                  material=material, opacity=opacity, frame=frame, display=display, visible=visible,
                                  make_trail=make_trail, trail_type=trail_type, interval=interval, retain=retain, **kwargs)
        object.__setattr__(self, 'length', length)
        object.__setattr__(self, 'width', width)
        object.__setattr__(self, 'height', height)
        cmd = {"cmd": "box", "idx": self.idx, "guid": self.guid, 
               "attrs": [{"attr": "pos", "value": self.pos.values()},
                         {"attr": "axis", "value": self.axis.values()},
                         {"attr": "size", "value": self.size.values()},
                         {"attr": "up", "value": self.up.values()},
                         {"attr": "color", "value": self.color},
                         {"attr": "opacity", "value": self.opacity},
                         {"attr": "shininess", "value": self.shininess},
                         {"attr": "emissive", "value": self.emissive},
                         {"attr": "canvas", "value": self.display.idx if self.display != None else canvas.get_selected().idx if canvas.get_selected() != None else -1},
                         {"attr": "make_trail", "value": self.make_trail},
                         {"attr": "type", "value": 'curve' if self.trail_type == 'curve' else 'spheres'},
                         {"attr": "interval", "value": self.interval},
                         {"attr": "visible", "value": self.visible},
                         {"attr": "retain", "value": self.retain}]}
        self.appendcmd(cmd)
        if (frame != None):
            frame.objects.append(self)
            frame.update_obj_list()
        
    def __setattr__(self, name, value):
        if name in ['size','length','width','height']:
            if name in ['size']:
                self.__dict__[name].remove_notification((self.addattr,name))
            val = value if type(value) is vector else vector(value) if type(value) in [tuple, list, np.ndarray] else value
            self.__dict__[name] = val
        
            if name == 'size':
                self.__dict__['axis'] = self.axis.norm() * value[0]
                self.__dict__['height'] = value[1]
                self.__dict__['width'] = value[2]
                self.__dict__[name].add_notification((self.addattr,name))
                self.addattr(name)
            elif name == 'length':
                self.__dict__['axis'] = self.axis.norm() * value
                self.addattr('axis')
            elif name == 'height':
                self.addattr('size')
            elif name == 'width':
                self.addattr('size')
        else:
            super(box, self).__setattr__(name, value)


    def __getattribute__(self, name):
        if name in ['size','length']:
            if name == 'length':
                return object.__getattribute__(self, 'axis').mag()
            elif name == 'size':
                return vector(object.__getattribute__(self, 'axis').mag(), object.__getattribute__(self, 'height'), object.__getattribute__(self, 'width'))
        else:
            return super(box, self).__getattribute__(name)
        
    def __del__(self):
        cmd = {"cmd": "delete", "idx": self.idx}
        self.appendcmd(cmd)
        #baseObj.cmds.append(cmd)
        super(box, self).__del__()

    
class cone(trailAttrs):
    """see cone documentation at http://vpython.org/contents/docs/cone.html"""    
    def __init__(self, pos=(0.,0.,0.), x=0., y=0., z=0., axis=(1.,0.,0.), length=-1., radius=1.,
                 frame=None, up=(0.,1.,0.), color=(1.,1.,1.), red=1., green=1., blue=1., material=None, opacity=1.0,
                 display=None, visible=True, make_trail=False, trail_type="curve", interval=1, retain=-1, **kwargs):
        axis = vector(axis) if type(axis) in [tuple, list, np.ndarray] else axis
        if (length == -1.):
            length = axis.mag()
        else:
            axis = axis.norm() * length
        size = vector(length,radius*2,radius*2)
        super(cone, self).__init__(pos=pos, x=x, y=y, z=z, axis=axis, size=size, up=up, color=color, red=red, green=green, blue=blue,
                                   material=material, opacity=opacity, frame=frame, display=display, visible=visible,
                                   make_trail=make_trail, trail_type=trail_type, interval=interval, retain=retain, **kwargs)
        object.__setattr__(self, 'length', length)
        object.__setattr__(self, 'radius', radius)
        cmd = {"cmd": "cone", "idx": self.idx, "guid": self.guid, 
               "attrs": [{"attr": "pos", "value": self.pos.values()},
                         {"attr": "axis", "value": self.axis.values()},
                         {"attr": "size", "value": self.size.values()},
                         {"attr": "up", "value": self.up.values()},
                         {"attr": "color", "value": self.color},
                         {"attr": "opacity", "value": self.opacity},
                         {"attr": "shininess", "value": self.shininess},
                         {"attr": "emissive", "value": self.emissive},
                         {"attr": "canvas", "value": self.display.idx if self.display != None else canvas.get_selected().idx if canvas.get_selected() != None else -1},
                         {"attr": "make_trail", "value": self.make_trail},
                         {"attr": "type", "value": 'curve' if self.trail_type == 'curve' else 'spheres'},
                         {"attr": "interval", "value": self.interval},
                         {"attr": "visible", "value": self.visible},
                         {"attr": "retain", "value": self.retain}]}

        self.appendcmd(cmd)
        if (frame != None):
            frame.objects.append(self)
            frame.update_obj_list()
        
    def __setattr__(self, name, value):
        if name in ['length','radius']:
            val = value if type(value) is vector else vector(value) if type(value) in [tuple, list, np.ndarray] else value
            self.__dict__[name] = val
       
            if name == 'length':
                self.__dict__['axis'] = self.axis.norm() * value
                self.addattr('axis')
            elif name == 'radius':
                self.addattr('size')
        else:
            super(cone, self).__setattr__(name, value)

    def __getattribute__(self, name):
        if name in ['size','length']:
            if name == 'length':
                return object.__getattribute__(self, 'axis').mag()
            elif name == 'size':
                return vector(object.__getattribute__(self, 'axis').mag(), object.__getattribute__(self, 'radius')*2.0, object.__getattribute__(self, 'radius')*2.0)
        else:
            return super(cone, self).__getattribute__(name)
        
    def __del__(self):
        cmd = {"cmd": "delete", "idx": self.idx}
        self.appendcmd(cmd)
        super(cone, self).__del__()

class curve(baseAttrs2):
    """see curve documentation at http://vpython.org/contents/docs/curve.html"""        
    xs = np.array([],float)
    ys = np.array([],float)
    zs = np.array([],float)
    def __init__(self, pos=[], x=[], y=[], z=[], axis=(1.,0.,0.), radius=0., display=None, visible=True,
                 up=(0.,1.,0.), color=[], red=[], green=[], blue=[], frame=None, material=None, **kwargs):
        if type(pos) is list:
            for idx, val in enumerate(pos):
                if type(val) is not tuple:
                    pos[idx] = astuple(val)
        posns = np.array(pos, dtype=('f4,f4,f4')) if type(pos) is list and (len(pos) == 0 or len(pos[0]) == 3) else np.array(pos, dtype=('f4,f4')) if type(pos) is list and len(pos[0]) == 2 else pos
        if len(posns) > 0:
            xs = posns['f0']
            ys = posns['f1']
            if(len(posns[0]) == 3):
                zs = posns['f2']
            else:
                zs = np.zeros(len(posns))
        elif (len(x) > 0) or (len(y) > 0) or (len(z) > 0):
            lsz = max(len(x),len(y),len(z))
            if len(x) < lsz:
                if len(x) > 0:
                    a = np.array(x, float) if type(x) is list or tuple else np.array([x], float) if type(x) is float or int else x
                    b = np.zeros(lsz-len(a))
                    x = np.concatenate(a,b)
                else:
                    x = np.zeros(lsz)
            if len(y) < lsz:
                if len(y) > 0:
                    a = np.array(y, float) if type(y) is list or tuple else np.array([y], float) if type(y) is float or int else y
                    b = np.zeros(lsz-len(a))
                    y = np.concatenate(a,b)
                else:
                    y = np.zeros(lsz)
            if len(z) < lsz:
                if len(z) > 0:
                    a = np.array(z, float) if type(z) is list or tuple else np.array([z], float) if type(z) is float or int else z
                    b = np.zeros(lsz-len(a))
                    z = np.concatenate(a,b)
                else:
                    z = np.zeros(lsz)
            posns = np.zeros(lsz, dtype=('f4,f4,f4'))
            posns['f0'] = x
            posns['f1'] = y
            posns['f2'] = z
        xs = np.array(x, float) if type(x) is list or tuple else np.array([x], float) if type(x) is float or int else x
        ys = np.array(y, float) if type(y) is list or tuple else np.array([y], float) if type(y) is float or int else y
        zs = np.array(z, float) if type(z) is list or tuple else np.array([z], float) if type(z) is float or int else z

        colors = np.array(color, dtype=('f4,f4,f4')) if type(color) is list else np.array([color], dtype=('f4,f4,f4')) if type(color) is tuple else color
        if len(colors) > 0:
            reds = colors['f0']
            greens = colors['f1']
            blues = colors['f2']
        elif (len(red) > 0) or (len(green) > 0) or (len(blue) > 0):
            lsz = max(len(red),len(green),len(blue))
            if len(red) < lsz:
                if len(red) > 0:
                    a = np.array(red, float) if type(red) is list or tuple else np.array([red], float) if type(red) is float or int else red
                    b = np.zeros(lsz-len(a))
                    red = np.concatenate(a,b)
                else:
                    red = np.zeros(lsz)
            if len(green) < lsz:
                if len(green) > 0:
                    a = np.array(green, float) if type(green) is list or tuple else np.array([green], float) if type(green) is float or int else green
                    b = np.zeros(lsz-len(a))
                    green = np.concatenate(a,b)
                else:
                    green = np.zeros(lsz)
            if len(blue) < lsz:
                if len(blue) > 0:
                    a = np.array(blue, float) if type(blue) is list or tuple else np.array([blue], float) if type(blue) is float or int else blue
                    b = np.zeros(lsz-len(a))
                    blue = np.concatenate(a,b)
                else:
                    blue = np.zeros(lsz)
            colors = np.zeros(lsz, dtype = ('f4,f4,f4'))
            colors['f0'] = red
            colors['f1'] = green
            colors['f2'] = blue
        else:
            colors = np.ones(1, dtype = ('f4,f4,f4'))
            reds = colors['f0']
            greens = colors['f1']
            blues = colors['f2']

        reds = np.array(red, float) if type(red) is list or tuple else np.array([red], float) if type(red) is float or int else red
        greens = np.array(green, float) if type(green) is list or tuple else np.array([green], float) if type(green) is float or int else green
        blues = np.array(blue, float) if type(blue) is list or tuple else np.array([blue], float) if type(blue) is float or int else blue
        
        pnts = []
        cols = []
        if len(posns) > 0:
            i = 0
            col = colors[-1]
            for posn in posns:
                col = colors[i] if len(colors) > i else colors[-1]
                if i >= len(colors):
                    cols.append(col)
                if (len(posn) == 3):
                    pnts.append({"pos": posn.tolist(), "color": col.tolist()})
                elif(len(posn) == 2):
                    p3 = list(posn)
                    p3.append(0.0)
                    p3a = np.array([tuple(p3)], dtype=('f4,f4,f4'))
                    pnts.append({"pos": p3a[0].tolist(), "color": col.tolist()})
                    
                i += 1
            if len(cols) > 0:
                colors = np.append(colors, np.array(cols, dtype=colors.dtype))

        super(curve, self).__init__(axis=axis, up=up, material=material, frame=frame, display=display, visible=visible, **kwargs)
        object.__getattribute__(self, 'pos').remove_notification((self.addattr,'pos'))
        object.__setattr__(self, 'radius', radius)
        object.__setattr__(self, 'color', colors)
        object.__setattr__(self, 'pos', posns)
        object.__setattr__(self, 'x', xs)
        object.__setattr__(self, 'y', ys)
        object.__setattr__(self, 'z', zs)
        object.__setattr__(self, 'red', reds)
        object.__setattr__(self, 'green', greens)
        object.__setattr__(self, 'blue', blues)
        cmd = {"cmd": "curve", "idx": self.idx, "guid": self.guid, 
               "attrs": [#{"attr": "pos", "value": self.pos.values()},
                         #{"attr": "axis", "value": self.axis.values()},
                         #{"attr": "size", "value": self.size.values()},
                         #{"attr": "up", "value": self.up.values()},
                         #{"attr": "color", "value": self.color},
                         #{"attr": "shininess", "value": self.shininess},
                         #{"attr": "emissive", "value": self.emissive},
                         #{"attr": "pnts", "value": [{"pos": [0, 0, 0]}, {"pos": [1, 0, 0]}]},
                         #{"attr": "pnts", "value": pntsa.tolist()},
                         {"attr": "pnts", "value": pnts},
                         {"attr": "radius", "value": self.radius},
                         {"attr": "visible", "value": self.visible},
                         {"attr": "canvas", "value": self.display.idx if self.display != None else canvas.get_selected().idx if canvas.get_selected() != None else -1}]}

        self.appendcmd(cmd)
        
    def __setattr__(self, name, value):
        if name in ['pos','color','x','y','z','red','green','blue','radius']:
        
            if name == 'radius':
                self.__dict__[name] = vector(value) if type(value) is tuple else value
                self.addattr(name)
            elif name == 'pos':
                if type(value) is list:
                    for idx, val in enumerate(value):
                        if type(val) is not tuple:
                            value[idx] = astuple(val)
                self.__dict__[name] = np.array(value, dtype = ('f4,f4,f4')) if type(value) is list and (len(value) == 0 or len(value[0]) == 3) else np.array(value, dtype=('f4,f4')) if type(value) is list and len(value[0]) == 2 else value
                self.__dict__['x'] = self.pos['f0']
                self.__dict__['y'] = self.pos['f1']
                if len(value[0]) == 3:
                    self.__dict__['z'] = self.pos['f2']
                    cmd = {"cmd": "modify", "idx": self.idx, 
                        "attrs":[{"attr": 'posns', "value": self.pos.tolist()}]}
                    baseObj.cmds.append(cmd)
                else:
                    posns = []
                    if len(self.pos) > 0:
                        for posn in self.pos:
                            p3 = list(posn)
                            p3.append(0.0)
                            posns.append(tuple(p3))
                        posns2 = np.array(posns, dtype = ('f4,f4,f4'))
                        cmd = {"cmd": "modify", "idx": self.idx, 
                            "attrs":[{"attr": 'posns', "value": posns2.tolist()}]}
                        baseObj.cmds.append(cmd)
                    
            elif name == 'x':
                self.__dict__[name] = np.array(value, float) if type(value) is list or tuple else np.array([value], float) if type(value) is float or int else value
                self.__dict__['pos']['f0'] = self.x
                cmd = {"cmd": "modify", "idx": self.idx, 
                    "attrs":[{"attr": name, "value": self.x.tolist()}]}
                baseObj.cmds.append(cmd)
            elif name == 'y':
                self.__dict__[name] = np.array(value, float) if type(value) is list or tuple else np.array([value], float) if type(value) is float or int else value
                self.__dict__['pos']['f1'] = self.y
                cmd = {"cmd": "modify", "idx": self.idx, 
                    "attrs":[{"attr": name, "value": self.y.tolist()}]}
                baseObj.cmds.append(cmd)
            elif name == 'z':
                self.__dict__[name] = np.array(value, float) if type(value) is list or tuple else np.array([value], float) if type(value) is float or int else value
                self.__dict__['pos']['f2'] = self.z
                cmd = {"cmd": "modify", "idx": self.idx, 
                    "attrs":[{"attr": name, "value": self.z.tolist()}]}
                baseObj.cmds.append(cmd)
            elif name == 'red':
                self.__dict__[name] = np.array(value, float) if type(value) is list or tuple else np.array([value], float) if type(value) is float or int else value
                self.__dict__['color']['f0'] = self.red
                cmd = {"cmd": "modify", "idx": self.idx, 
                    "attrs":[{"attr": name, "value": self.red.tolist()}]}
                baseObj.cmds.append(cmd)
            elif name == 'green':
                self.__dict__[name] = np.array(value, float) if type(value) is list or tuple else np.array([value], float) if type(value) is float or int else value
                self.__dict__['color']['f1'] = self.green
                cmd = {"cmd": "modify", "idx": self.idx, 
                    "attrs":[{"attr": name, "value": self.green.tolist()}]}
                baseObj.cmds.append(cmd)
            elif name == 'blue':
                self.__dict__[name] = np.array(value, float) if type(value) is list or tuple else np.array([value], float) if type(value) is float or int else value
                self.__dict__['color']['f2'] = self.blue
                cmd = {"cmd": "modify", "idx": self.idx, 
                    "attrs":[{"attr": name, "value": self.blue.tolist()}]}
                baseObj.cmds.append(cmd)
            elif name == 'color':
                self.__dict__[name] = np.array(value, dtype=('f4,f4,f4')) if type(value) is list and (len(value) == 0 or len(value[0]) == 3) else np.array(value, dtype=('f4,f4')) if type(value) is list and len(value[0]) == 2 else value
                self.__dict__['red'] = self.color['f0']
                self.__dict__['green'] = self.color['f1']
                self.__dict__['blue'] = self.color['f2']
                cmd = {"cmd": "modify", "idx": self.idx, 
                    "attrs":[{"attr": 'colors', "value": self.color.tolist()}]}
                baseObj.cmds.append(cmd)
        else:
            super(curve, self).__setattr__(name, value)

    def append(self, pos = None, color = None, red = None, green = None, blue = None):

        if (red is not None) and (green is not None) and (blue is not None):
            color = (red,green,blue)

        if (pos is not None) and (color is not None):
            if type(pos) is not tuple:
                pos = astuple(pos)
            self.__dict__['pos'] = np.append(self.pos, np.array([pos], dtype=self.pos.dtype))
            self.__dict__['color'] = np.append(self.color, np.array([color], dtype=self.color.dtype))
            pos = list(pos)
            if len(pos) == 2:
                pos.append(0.0)
            cmd = {"cmd": "push", "idx": self.idx, 
                    "attrs":[{"attr": "pos", "value": pos},{"attr": "color", "value": list(color)}]}
            baseObj.cmds.append(cmd)
        elif (pos is not None):
            if type(pos) is not tuple:
                pos = astuple(pos)
            self.__dict__['pos'] = np.append(self.pos, np.array([pos], dtype=self.pos.dtype))
            color = self.color[-1]
            self.__dict__['color'] = np.append(self.color, np.array([color], dtype=self.color.dtype))
            pos = list(pos)
            if len(pos) == 2:
                pos.append(0.0)
            cmd = {"cmd": "push", "idx": self.idx, 
                    "attrs":[{"attr": "pos", "value": pos},{"attr": "color", "value": self.color[-1].tolist()}]}
            baseObj.cmds.append(cmd)

    def __del__(self):
        pass
    
class points(baseAttrs2):
    """see points documentation at http://vpython.org/contents/docs/points.html"""    
    xs = np.array([],float)
    ys = np.array([],float)
    zs = np.array([],float)
    def __init__(self, pos=[], x=[], y=[], z=[], size=5, size_units="pixels", shape="round", 
                 display=None, visible=True, color=[], red=[], green=[], blue=[], frame=None, **kwargs):
        if type(pos) is list:
            for idx, val in enumerate(pos):
                if type(val) is not tuple:
                    pos[idx] = astuple(val)
        posns = np.array(pos, dtype=('f4,f4,f4')) if type(pos) is list and (len(pos) == 0 or len(pos[0]) == 3) else np.array(pos, dtype=('f4,f4')) if type(pos) is list and len(pos[0]) == 2 else pos
        if len(posns) > 0:
            xs = posns['f0']
            ys = posns['f1']
            if(len(posns[0]) == 3):
                zs = posns['f2']
            else:
                zs = np.zeros(len(posns))
        elif (len(x) > 0) or (len(y) > 0) or (len(z) > 0):
            lsz = max(len(x),len(y),len(z))
            if len(x) < lsz:
                if len(x) > 0:
                    a = np.array(x, float) if type(x) is list or tuple else np.array([x], float) if type(x) is float or int else x
                    b = np.zeros(lsz-len(a))
                    x = np.concatenate(a,b)
                else:
                    x = np.zeros(lsz)
            if len(y) < lsz:
                if len(y) > 0:
                    a = np.array(y, float) if type(y) is list or tuple else np.array([y], float) if type(y) is float or int else y
                    b = np.zeros(lsz-len(a))
                    y = np.concatenate(a,b)
                else:
                    y = np.zeros(lsz)
            if len(z) < lsz:
                if len(z) > 0:
                    a = np.array(z, float) if type(z) is list or tuple else np.array([z], float) if type(z) is float or int else z
                    b = np.zeros(lsz-len(a))
                    z = np.concatenate(a,b)
                else:
                    z = np.zeros(lsz)
            posns = np.zeros(lsz, dtype=('f4,f4,f4'))
            posns['f0'] = x
            posns['f1'] = y
            posns['f2'] = z
        xs = np.array(x, float) if type(x) is list or tuple else np.array([x], float) if type(x) is float or int else x
        ys = np.array(y, float) if type(y) is list or tuple else np.array([y], float) if type(y) is float or int else y
        zs = np.array(z, float) if type(z) is list or tuple else np.array([z], float) if type(z) is float or int else z

        colors = np.array(color, dtype=('f4,f4,f4')) if type(color) is list else np.array([color], dtype=('f4,f4,f4')) if type(color) is tuple else color
        if len(colors) > 0:
            reds = colors['f0']
            greens = colors['f1']
            blues = colors['f2']
        elif (len(red) > 0) or (len(green) > 0) or (len(blue) > 0):
            lsz = max(len(red),len(green),len(blue))
            if len(red) < lsz:
                if len(red) > 0:
                    a = np.array(red, float) if type(red) is list or tuple else np.array([red], float) if type(red) is float or int else red
                    b = np.zeros(lsz-len(a))
                    red = np.concatenate(a,b)
                else:
                    red = np.zeros(lsz)
            if len(green) < lsz:
                if len(green) > 0:
                    a = np.array(green, float) if type(green) is list or tuple else np.array([green], float) if type(green) is float or int else green
                    b = np.zeros(lsz-len(a))
                    green = np.concatenate(a,b)
                else:
                    green = np.zeros(lsz)
            if len(blue) < lsz:
                if len(blue) > 0:
                    a = np.array(blue, float) if type(blue) is list or tuple else np.array([blue], float) if type(blue) is float or int else blue
                    b = np.zeros(lsz-len(a))
                    blue = np.concatenate(a,b)
                else:
                    blue = np.zeros(lsz)
            colors = np.zeros(lsz, dtype=('f4,f4,f4'))
            colors['f0'] = red
            colors['f1'] = green
            colors['f2'] = blue
        else:
            colors = np.ones(1, dtype=('f4,f4,f4'))
            reds = colors['f0']
            greens = colors['f1']
            blues = colors['f2']

        reds = np.array(red, float) if type(red) is list or tuple else np.array([red], float) if type(red) is float or int else red
        greens = np.array(green, float) if type(green) is list or tuple else np.array([green], float) if type(green) is float or int else green
        blues = np.array(blue, float) if type(blue) is list or tuple else np.array([blue], float) if type(blue) is float or int else blue
        
        pnts = []
        cols = []
        if len(posns) > 0:
            i = 0
            col = colors[-1]
            for posn in posns:
                col = colors[i] if len(colors) > i else colors[-1]
                if i >= len(colors):
                    cols.append(col)
                if (len(posn) == 3):
                    pnts.append({"pos": posn.tolist(), "color": col.tolist()})
                elif(len(posn) == 2):
                    p3 = list(posn)
                    p3.append(0.0)
                    p3a = np.array([tuple(p3)], dtype=('f4,f4,f4'))
                    pnts.append({"pos": p3a[0].tolist(), "color": col.tolist()})
                    
                i += 1
            if len(cols) > 0:
                colors = np.append(colors, np.array(cols, dtype=colors.dtype))

        super(points, self).__init__(frame=frame, display=display, visible=visible, **kwargs)
        object.__getattribute__(self, 'pos').remove_notification((self.addattr,'pos'))
        object.__getattribute__(self, 'size').remove_notification((self.addattr,'size'))
        object.__setattr__(self, 'size', size)
        object.__setattr__(self, 'size_units', size_units)
        object.__setattr__(self, 'shape', shape)
        object.__setattr__(self, 'color', colors)
        object.__setattr__(self, 'pos', posns)
        object.__setattr__(self, 'x', xs)
        object.__setattr__(self, 'y', ys)
        object.__setattr__(self, 'z', zs)
        object.__setattr__(self, 'red', reds)
        object.__setattr__(self, 'green', greens)
        object.__setattr__(self, 'blue', blues)
        cmd = {"cmd": "points", "idx": self.idx, "guid": self.guid, 
               "attrs": [#{"attr": "pos", "value": self.pos.values()},
                         #{"attr": "axis", "value": self.axis.values()},
                         #{"attr": "size", "value": self.size.values()},
                         #{"attr": "up", "value": self.up.values()},
                         #{"attr": "color", "value": self.color},
                         #{"attr": "shininess", "value": self.shininess},
                         #{"attr": "emissive", "value": self.emissive},
                         #{"attr": "pnts", "value": [{"pos": [0, 0, 0]}, {"pos": [1, 0, 0]}]},
                         #{"attr": "pnts", "value": pntsa.tolist()},
                         {"attr": "visible", "value": self.visible},
                         {"attr": "pnts", "value": pnts},
                         {"attr": "size", "value": self.size},
                         {"attr": "size_units", "value": self.size_units},
                         {"attr": "canvas", "value": self.display.idx if self.display != None else canvas.get_selected().idx if canvas.get_selected() != None else -1}]}

        self.appendcmd(cmd)
        
    def __setattr__(self, name, value):
        if name in ['pos','color','x','y','z','red','green','blue','size','size_units','shape']:
        
            if name == 'size':
                self.__dict__[name] = value
                self.addattr(name)
            elif name == 'size_units':
                if value in ['pixels','world']:
                    self.__dict__[name] = value
                    self.addattr(name)
            elif name == 'shape':
                if value in ['round','square']:
                    self.__dict__[name] = value
                    self.addattr(name)
            elif name == 'pos':
                if type(value) is list:
                    for idx, val in enumerate(value):
                        if type(val) is not tuple:
                            value[idx] = astuple(val)
                self.__dict__[name] = np.array(value, dtype=('f4,f4,f4')) if type(value) is list and (len(value) == 0 or len(value[0]) == 3) else np.array(value, dtype=('f4,f4')) if type(value) is list and len(value[0]) == 2 else value
                self.__dict__['x'] = self.pos['f0']
                self.__dict__['y'] = self.pos['f1']
                if len(value[0]) == 3:
                    self.__dict__['z'] = self.pos['f2']
                    cmd = {"cmd": "modify", "idx": self.idx, 
                        "attrs":[{"attr": 'posns', "value": self.pos.tolist()}]}
                    baseObj.cmds.append(cmd)
                else:
                    posns = []
                    if len(self.pos) > 0:
                        for posn in self.pos:
                            p3 = list(posn)
                            p3.append(0.0)
                            posns.append(tuple(p3))
                        posns2 = np.array(posns, dtype=('f4,f4,f4'))
                        cmd = {"cmd": "modify", "idx": self.idx, 
                            "attrs":[{"attr": 'posns', "value": posns2.tolist()}]}
                        baseObj.cmds.append(cmd)
                    
            elif name == 'x':
                self.__dict__[name] = np.array(value, float) if type(value) is list or tuple else np.array([value], float) if type(value) is float or int else value
                self.__dict__['pos']['f0'] = self.x
                cmd = {"cmd": "modify", "idx": self.idx, 
                    "attrs":[{"attr": name, "value": self.x.tolist()}]}
                baseObj.cmds.append(cmd)
            elif name == 'y':
                self.__dict__[name] = np.array(value, float) if type(value) is list or tuple else np.array([value], float) if type(value) is float or int else value
                self.__dict__['pos']['f1'] = self.y
                cmd = {"cmd": "modify", "idx": self.idx, 
                    "attrs":[{"attr": name, "value": self.y.tolist()}]}
                baseObj.cmds.append(cmd)
            elif name == 'z':
                self.__dict__[name] = np.array(value, float) if type(value) is list or tuple else np.array([value], float) if type(value) is float or int else value
                self.__dict__['pos']['f2'] = self.z
                cmd = {"cmd": "modify", "idx": self.idx, 
                    "attrs":[{"attr": name, "value": self.z.tolist()}]}
                baseObj.cmds.append(cmd)
            elif name == 'red':
                self.__dict__[name] = np.array(value, float) if type(value) is list or tuple else np.array([value], float) if type(value) is float or int else value
                self.__dict__['color']['f0'] = self.red
                cmd = {"cmd": "modify", "idx": self.idx, 
                    "attrs":[{"attr": name, "value": self.red.tolist()}]}
                baseObj.cmds.append(cmd)
            elif name == 'green':
                self.__dict__[name] = np.array(value, float) if type(value) is list or tuple else np.array([value], float) if type(value) is float or int else value
                self.__dict__['color']['f1'] = self.green
                cmd = {"cmd": "modify", "idx": self.idx, 
                    "attrs":[{"attr": name, "value": self.green.tolist()}]}
                baseObj.cmds.append(cmd)
            elif name == 'blue':
                self.__dict__[name] = np.array(value, float) if type(value) is list or tuple else np.array([value], float) if type(value) is float or int else value
                self.__dict__['color']['f2'] = self.blue
                cmd = {"cmd": "modify", "idx": self.idx, 
                    "attrs":[{"attr": name, "value": self.blue.tolist()}]}
                baseObj.cmds.append(cmd)
            elif name == 'color':
                self.__dict__[name] = np.array(value, dtype=('f4,f4,f4')) if type(value) is list and (len(value) == 0 or len(value[0]) == 3) else np.array(value, dtype=('f4,f4')) if type(value) is list and len(value[0]) == 2 else value
                self.__dict__['red'] = self.color['f0']
                self.__dict__['green'] = self.color['f1']
                self.__dict__['blue'] = self.color['f2']
                cmd = {"cmd": "modify", "idx": self.idx, 
                    "attrs":[{"attr": 'colors', "value": self.color.tolist()}]}
                baseObj.cmds.append(cmd)
        else:
            super(points, self).__setattr__(name, value)

    def __del__(self):
        pass

    def append(self, pos = None, color = None, red = None, green = None, blue = None):

        if (red is not None) and (green is not None) and (blue is not None):
            color = (red,green,blue)

        if (pos is not None) and (color is not None):
            if type(pos) is not tuple:
                pos = astuple(pos)
            self.__dict__['pos'] = np.append(self.pos, np.array([pos], dtype=self.pos.dtype))
            self.__dict__['color'] = np.append(self.color, np.array([color], dtype=self.color.dtype))
            pos = list(pos)
            if len(pos) == 2:
                pos.append(0.0)
            cmd = {"cmd": "push", "idx": self.idx, 
                    "attrs":[{"attr": "pos", "value": pos},{"attr": "color", "value": list(color)}]}
            baseObj.cmds.append(cmd)
        elif (pos is not None):
            if type(pos) is not tuple:
                pos = astuple(pos)
            self.__dict__['pos'] = np.append(self.pos, np.array([pos], dtype=self.pos.dtype))
            color = self.color[-1]
            self.__dict__['color'] = np.append(self.color, np.array([color], dtype=self.color.dtype))
            pos = list(pos)
            if len(pos) == 2:
                pos.append(0.0)
            cmd = {"cmd": "push", "idx": self.idx, 
                    "attrs":[{"attr": "pos", "value": pos},{"attr": "color", "value": self.color[-1].tolist()}]}
            baseObj.cmds.append(cmd)


class faces(baseAttrs2):
    """see faces documentation at http://vpython.org/contents/docs/faces.html"""    
    xs = np.array([],float)
    ys = np.array([],float)
    zs = np.array([],float)
    def __init__(self, pos=[], x=[], y=[], z=[], axis=(1.,0.,0.), radius=0., display=None, visible=True,
                 up=(0.,1.,0.), color=[], red=[], green=[], blue=[], normal=[], frame=None, material=None, **kwargs):
        if type(pos) is list:
            for idx, val in enumerate(pos):
                if type(val) is not tuple:
                    pos[idx] = tuple(val)
        posns = np.array(pos, dtype=('f4,f4,f4')) if type(pos) is list and (len(pos) == 0 or len(pos[0]) == 3) else np.array(pos, dtype=('f4,f4')) if type(pos) is list and len(pos[0]) == 2 else pos
        if len(posns) > 0:
            xs = posns['f0']
            ys = posns['f1']
            if(len(posns[0]) == 3):
                zs = posns['f2']
            else:
                zs = np.zeros(len(posns))
        elif (len(x) > 0) or (len(y) > 0) or (len(z) > 0):
            lsz = max(len(x),len(y),len(z))
            if len(x) < lsz:
                if len(x) > 0:
                    a = np.array(x, float) if type(x) is list or tuple else np.array([x], float) if type(x) is float or int else x
                    b = np.zeros(lsz-len(a))
                    x = np.concatenate(a,b)
                else:
                    x = np.zeros(lsz)
            if len(y) < lsz:
                if len(y) > 0:
                    a = np.array(y, float) if type(y) is list or tuple else np.array([y], float) if type(y) is float or int else y
                    b = np.zeros(lsz-len(a))
                    y = np.concatenate(a,b)
                else:
                    y = np.zeros(lsz)
            if len(z) < lsz:
                if len(z) > 0:
                    a = np.array(z, float) if type(z) is list or tuple else np.array([z], float) if type(z) is float or int else z
                    b = np.zeros(lsz-len(a))
                    z = np.concatenate(a,b)
                else:
                    z = np.zeros(lsz)
            posns = np.zeros(lsz, dtype=('f4,f4,f4'))
            posns['f0'] = x
            posns['f1'] = y
            posns['f2'] = z
        xs = np.array(x, float) if type(x) is list or tuple else np.array([x], float) if type(x) is float or int else x
        ys = np.array(y, float) if type(y) is list or tuple else np.array([y], float) if type(y) is float or int else y
        zs = np.array(z, float) if type(z) is list or tuple else np.array([z], float) if type(z) is float or int else z

        colors = np.array(color, dtype=('f4,f4,f4')) if type(color) is list else np.array([color], dtype=('f4,f4,f4')) if type(color) is tuple else color
        if len(colors) > 0:
            reds = colors['f0']
            greens = colors['f1']
            blues = colors['f2']
        elif (len(red) > 0) or (len(green) > 0) or (len(blue) > 0):
            lsz = max(len(red),len(green),len(blue))
            if len(red) < lsz:
                if len(red) > 0:
                    a = np.array(red, float) if type(red) is list or tuple else np.array([red], float) if type(red) is float or int else red
                    b = np.zeros(lsz-len(a))
                    red = np.concatenate(a,b)
                else:
                    red = np.zeros(lsz)
            if len(green) < lsz:
                if len(green) > 0:
                    a = np.array(green, float) if type(green) is list or tuple else np.array([green], float) if type(green) is float or int else green
                    b = np.zeros(lsz-len(a))
                    green = np.concatenate(a,b)
                else:
                    green = np.zeros(lsz)
            if len(blue) < lsz:
                if len(blue) > 0:
                    a = np.array(blue, float) if type(blue) is list or tuple else np.array([blue], float) if type(blue) is float or int else blue
                    b = np.zeros(lsz-len(a))
                    blue = np.concatenate(a,b)
                else:
                    blue = np.zeros(lsz)
            colors = np.zeros(lsz, dtype=('f4,f4,f4'))
            colors['f0'] = red
            colors['f1'] = green
            colors['f2'] = blue
        else:
            colors = np.ones(1, dtype=('f4,f4,f4'))
            reds = colors['f0']
            greens = colors['f1']
            blues = colors['f2']

        reds = np.array(red, float) if type(red) is list or tuple else np.array([red], float) if type(red) is float or int else red
        greens = np.array(green, float) if type(green) is list or tuple else np.array([green], float) if type(green) is float or int else green
        blues = np.array(blue, float) if type(blue) is list or tuple else np.array([blue], float) if type(blue) is float or int else blue

        normals = np.array(normal, dtype=('f4,f4,f4')) if type(normal) is list and (len(normal) == 0 or len(normal[0]) == 3) else np.array(normal, dtype=('f4,f4')) if type(normal) is list and len(normal[0]) == 2 else normal
        
        pnts = []
        cols = []
        if len(posns) > 0:
            i = 0
            col = colors[-1]
            for posn in posns:
                col = colors[i] if len(colors) > i else colors[-1]
                if i >= len(colors):
                    cols.append(col)
                if (len(posn) == 3):
                    pnts.append({"pos": posn.tolist(), "color": col.tolist()})
                elif(len(posn) == 2):
                    p3 = list(posn)
                    p3.append(0.0)
                    p3a = np.array([tuple(p3)], dtype=('f4,f4,f4'))
                    pnts.append({"pos": p3a[0].tolist(), "color": col.tolist()})
                    
                i += 1
            if len(cols) > 0:
                colors = np.append(colors, np.array(cols, dtype=colors.dtype))

        super(faces, self).__init__(axis=axis, up=up, material=material, display=display, visible=visible, **kwargs)
        object.__getattribute__(self, 'pos').remove_notification((self.addattr,'pos'))
        object.__setattr__(self, 'radius', radius)
        object.__setattr__(self, 'color', colors)
        object.__setattr__(self, 'pos', posns)
        object.__setattr__(self, 'normal', posns)
        object.__setattr__(self, 'x', xs)
        object.__setattr__(self, 'y', ys)
        object.__setattr__(self, 'z', zs)
        object.__setattr__(self, 'red', reds)
        object.__setattr__(self, 'green', greens)
        object.__setattr__(self, 'blue', blues)
        object.__setattr__(self, 'frame', frame)
        cmd = {"cmd": "faces", "idx": self.idx, "guid": self.guid, 
               "attrs": [#{"attr": "pos", "value": self.pos.values()},
                         #{"attr": "axis", "value": self.axis.values()},
                         #{"attr": "size", "value": self.size.values()},
                         #{"attr": "up", "value": self.up.values()},
                         #{"attr": "color", "value": self.color},
                         #{"attr": "shininess", "value": self.shininess},
                         #{"attr": "emissive", "value": self.emissive},
                         #{"attr": "pnts", "value": [{"pos": [0, 0, 0]}, {"pos": [1, 0, 0]}]},
                         #{"attr": "pnts", "value": pntsa.tolist()},
                         {"attr": "pnts", "value": pnts},
                         {"attr": "radius", "value": self.radius},
                         {"attr": "canvas", "value": self.display.idx if self.display != None else canvas.get_selected().idx if canvas.get_selected() != None else -1}]}
        """
        if (baseObj.glow != None):
            baseObj.glow.comm.send([cmd])
        else:
            self.appendcmd(cmd)
        #self.appendcmd(cmd)
        """
        
    def __setattr__(self, name, value):
        if name in ['pos','color','x','y','z','red','green','blue','radius']:
        
            if name == 'radius':
                self.__dict__[name] = vector(value) if type(value) is tuple else value
                cmd = {"idx": self.idx, "attr": "radius", "val": self.radius}            
                baseObj.cmds.append(cmd)
            elif name == 'pos':
                self.__dict__[name] = np.array(value, dtype=('f4,f4,f4')) if type(value) is list and (len(value) == 0 or len(value[0]) == 3) else np.array(value, dtype=('f4,f4')) if type(value) is list and len(value[0]) == 2 else value
                self.__dict__['x'] = self.pos['f0']
                self.__dict__['y'] = self.pos['f1']
                if len(value[0]) == 3:
                    self.__dict__['z'] = self.pos['f2']
                    cmd = {"cmd": "modify", "idx": self.idx, 
                        "attrs":[{"attr": 'posns', "value": self.pos.tolist()}]}
                    baseObj.cmds.append(cmd)
                else:
                    posns = []
                    if len(self.pos) > 0:
                        for posn in self.pos:
                            p3 = list(posn)
                            p3.append(0.0)
                            posns.append(tuple(p3))
                        posns2 = np.array(posns, dtype=('f4,f4,f4'))
                        cmd = {"cmd": "modify", "idx": self.idx, 
                            "attrs":[{"attr": 'posns', "value": posns2.tolist()}]}
                        baseObj.cmds.append(cmd)
                    
            elif name == 'x':
                self.__dict__[name] = np.array(value, float) if type(value) is list or tuple else np.array([value], float) if type(value) is float or int else value
                self.__dict__['pos']['f0'] = self.x
                cmd = {"cmd": "modify", "idx": self.idx, 
                    "attrs":[{"attr": name, "value": self.x.tolist()}]}
                baseObj.cmds.append(cmd)
            elif name == 'y':
                self.__dict__[name] = np.array(value, float) if type(value) is list or tuple else np.array([value], float) if type(value) is float or int else value
                self.__dict__['pos']['f1'] = self.y
                cmd = {"cmd": "modify", "idx": self.idx, 
                    "attrs":[{"attr": name, "value": self.y.tolist()}]}
                baseObj.cmds.append(cmd)
            elif name == 'z':
                self.__dict__[name] = np.array(value, float) if type(value) is list or tuple else np.array([value], float) if type(value) is float or int else value
                self.__dict__['pos']['f2'] = self.z
                cmd = {"cmd": "modify", "idx": self.idx, 
                    "attrs":[{"attr": name, "value": self.z.tolist()}]}
                baseObj.cmds.append(cmd)
            elif name == 'red':
                self.__dict__[name] = np.array(value, float) if type(value) is list or tuple else np.array([value], float) if type(value) is float or int else value
                self.__dict__['color']['f0'] = self.red
                cmd = {"cmd": "modify", "idx": self.idx, 
                    "attrs":[{"attr": name, "value": self.red.tolist()}]}
                baseObj.cmds.append(cmd)
            elif name == 'green':
                self.__dict__[name] = np.array(value, float) if type(value) is list or tuple else np.array([value], float) if type(value) is float or int else value
                self.__dict__['color']['f1'] = self.green
                cmd = {"cmd": "modify", "idx": self.idx, 
                    "attrs":[{"attr": name, "value": self.green.tolist()}]}
                baseObj.cmds.append(cmd)
            elif name == 'blue':
                self.__dict__[name] = np.array(value, float) if type(value) is list or tuple else np.array([value], float) if type(value) is float or int else value
                self.__dict__['color']['f2'] = self.blue
                cmd = {"cmd": "modify", "idx": self.idx, 
                    "attrs":[{"attr": name, "value": self.blue.tolist()}]}
                baseObj.cmds.append(cmd)
            elif name == 'color':
                self.__dict__[name] = np.array(value, dtype=('f4,f4,f4')) if type(value) is list and (len(value) == 0 or len(value[0]) == 3) else np.array(value, dtype=('f4,f4')) if type(value) is list and len(value[0]) == 2 else value
                self.__dict__['red'] = self.color['f0']
                self.__dict__['green'] = self.color['f1']
                self.__dict__['blue'] = self.color['f2']
                cmd = {"cmd": "modify", "idx": self.idx, 
                    "attrs":[{"attr": 'colors', "value": self.color.tolist()}]}
                baseObj.cmds.append(cmd)
        else:
            super(faces, self).__setattr__(name, value)

    def append(self, pos = None, normal = None, color = None, red = None, green = None, blue = None):
        """
        Usage:
        f.append(pos=(x,y,z))
        f.append(pos=(x,y,z), normal=(nx,ny,nz))
        f.append(pos=(x,y,z), normal=(nx,ny,nz), color=(r,g,b))
        f.append(pos=(x,y,z), normal=(nx,ny,nz), red=r, green=g, blue=b)                    
        """
        
        if (red is not None) and (green is not None) and (blue is not None):
            color = (red,green,blue)

        if (pos is not None) and (normal is not None) and (color is not None):
            self.__dict__['pos'] = np.append(self.pos, np.array([pos], dtype=self.pos.dtype))
            self.__dict__['normal'] = np.append(self.normal, np.array([normal], dtype=self.normal.dtype))
            self.__dict__['color'] = np.append(self.color, np.array([color], dtype=self.color.dtype))
            #cmd = {"cmd": "push", "idx": self.idx, 
            #        "attrs":[{"attr": "pos", "value": list(pos)},{"attr": "normal", "value": list(normal)},{"attr": "color", "value": list(color)}]}
            #baseObj.cmds.append(cmd)
        elif (pos is not None) and (normal is not None):
            self.__dict__['pos'] = np.append(self.pos, np.array([pos], dtype=self.pos.dtype))
            self.__dict__['normal'] = np.append(self.normal, np.array([normal], dtype=self.normal.dtype))
            #color = self.color[-1]
            #self.__dict__['color'] = np.append(self.color, np.array([color], dtype=self.color.dtype))
            #cmd = {"cmd": "push", "idx": self.idx, 
            #        "attrs":[{"attr": "pos", "value": list(pos)},{"attr": "normal", "value": list(normal)},{"attr": "color", "value": self.color[-1].tolist()}]}
            #baseObj.cmds.append(cmd)
        elif (pos is not None):
            self.__dict__['pos'] = np.append(self.pos, np.array([pos], dtype=self.pos.dtype))

    def make_normals(self):
        # for triangle with vertices abc, (b-a).cross(c-b).norm() will be perpendicular to triangle
        pass

    def make_twosided(self):
        pass

    def smooth(self, angle = 0.95):
        pass
    
    def __del__(self):
        pass

class faces2(baseAttrs2):

    def __init__(self, pos=[], color=[], normal=[], red=[1.], green=[1.], blue=[1.], material=None, frame=None, visible=True, display=None, **kwargs):
        posns = np.array(pos, dtype=('f4,f4,f4')) if type(pos) is list else pos
        normals = np.array(normal, dtype=('f4,f4,f4')) if type(pos) is list else normal
        colors = np.array(color, dtype=('f4,f4,f4')) if type(color) is list else np.array([color], dtype=('f4,f4,f4')) if type(color) is tuple else color
        reds = np.array(red, float) if type(red) is list else np.array([red], float) if type(red) is float or int else red
        greens = np.array(green, float) if type(green) is list else np.array([green], float) if type(green) is float or int else green
        blues = np.array(blue, float) if type(blue) is list else np.array([blue], float) if type(blue) is float or int else blue
        
        super(faces, self).__init__(**kwargs)
        object.__setattr__(self, 'frame', frame)
        object.__setattr__(self, 'display', display)
        
        pnts = []
        if len(posns) > 0:
            i = 0
            #col = np.array([(1.,1.,1.)], dtype=('f4,f4,f4'))[-1]
            col = colors[-1]
            for posn in posns:
                col = colors[i] if len(colors) > i else col
                """
                if len(colors) > i:
                    pnts.append({"pos": posn.tolist(), "color": col.tolist()})
                else:
                    pnts.append({"pos": posn.tolist()})
                """
                pnts.append({"pos": posn.tolist(), "color": col.tolist()})
                i += 1
        
        cmd = {"cmd": "faces", "idx": self.idx, 
               "attrs": [#{"attr": "pos", "value": self.pos.values()},
                         #{"attr": "axis", "value": self.axis.values()},
                         #{"attr": "size", "value": self.size.values()},
                         #{"attr": "up", "value": self.up.values()},
                         #{"attr": "color", "value": self.color},
                         #{"attr": "shininess", "value": self.shininess},
                         #{"attr": "emissive", "value": self.emissive},
                         #{"attr": "pnts", "value": [{"pos": [0, 0, 0]}, {"pos": [1, 0, 0]}]},
                         #{"attr": "pnts", "value": pntsa.tolist()},
                         {"attr": "pnts", "value": pnts},
                         {"attr": "radius", "value": self.radius},
                         {"attr": "canvas", "value": self.display.idx if self.display != None else canvas.get_selected().idx if canvas.get_selected() != None else -1}]}

        if (baseObj.glow != None):
            baseObj.glow.comm.send([cmd])
        else:
            self.appendcmd(cmd)
        #self.appendcmd(cmd)
        """
        if len(posns) > 0:
            i = 0
            col = (1.,1.,1.)
            for posn in posns:
                col = colors[i] if len(colors) > i else col
                cmd2 = {"cmd": "push", "idx": self.idx, 
                       "attrs":[{"attr": "pos", "value": list(posn)},
                                {"attr": "color", "value": list(col)}]}
                i += 1
                self.appendcmd(cmd2)
                #baseObj.cmds.append(cmd)
        """
        
    def __setattr__(self, name, value):
        if name in ['frame','display']:
            self.__dict__[name] = vector(value) if type(value) is tuple else value
        
            if name == 'radius':
                cmd = {"idx": self.idx, "attr": "radius", "val": self.radius}            
                baseObj.cmds.append(cmd)
            elif name == 'axis':
                cmd = {"idx": self.idx, "attr": name, "val": self.axis.values()}            
                baseObj.cmds.append(cmd)
        else:
            super(faces, self).__setattr__(name, value)

    def append(self, pos = None, color = None, normal = None, red = None, green = None, blue = None):
        # need to implement this

        if (red is not None) and (green is not None) and (blue is not None):
            color = (red,green,blue)

        if (pos is not None) and (color is not None):
            # self.__dict__['colors'] = np.append(self.colors,np.array([color], dtype=('f4,f4,f4'))[0],axis=0)
            #y = np.append(self.colors, np.array([color], dtype=self.colors.dtype))
            #self.colors = y
            self.colors = np.append(self.colors, np.array([color], dtype=self.colors.dtype))
            cmd = {"cmd": "push", "idx": self.idx, 
                    "attrs":[{"attr": "pos", "value": list(pos)},{"attr": "color", "value": list(color)}]}
            baseObj.cmds.append(cmd)
        elif (pos is not None):
            cmd = {"cmd": "push", "idx": self.idx, 
                    "attrs":[{"attr": "pos", "value": list(pos)},{"attr": "color", "value": self.colors[-1].tolist()}]}
            #"attrs":[{"attr": "pos", "value": list(pos)}]}
            baseObj.cmds.append(cmd)


class helix(baseAttrs2):
    """see helix documentation at http://vpython.org/contents/docs/helix.html"""    
    
    def __init__(self, pos=(0.,0.,0.), x=0., y=0., z=0., axis=(1.,0.,0.), length=-1., radius=1., thickness=0., coils=5,
                 up=(0.,1.,0.), color=(1.,1.,1.), red=1., green=1., blue=1., frame=None, visible=True, display=None, material=None, **kwargs):
        axis = vector(axis) if type(axis) in [tuple, list, np.ndarray] else axis
        if (length == -1.):
            length = axis.mag()
        else:
            axis = axis.norm() * length
        if (thickness == 0.):
            thickness = radius/20.
        size = vector(length,radius*2,radius*2)
        super(helix, self).__init__(pos=pos, x=x, y=y, z=z, axis=axis, size=size, up=up, color=color, red=red, green=green, 
                                    blue=blue, material=material, frame=frame, display=display, visible=visible, **kwargs)
        object.__getattribute__(self, 'size').remove_notification((self.addattr,'size'))
        object.__setattr__(self, 'length', length)
        object.__setattr__(self, 'radius', radius)
        object.__setattr__(self, 'thickness', thickness)
        object.__setattr__(self, 'coils', coils)
        cmd = {"cmd": "helix", "idx": self.idx, "guid": self.guid, 
               "attrs": [{"attr": "pos", "value": self.pos.values()},
                         {"attr": "axis", "value": self.axis.values()},
                         {"attr": "size", "value": self.size.values()},
                         {"attr": "up", "value": self.up.values()},
                         {"attr": "color", "value": self.color},
                         {"attr": "thickness", "value": self.thickness},
                         {"attr": "coils", "value": self.coils},
                         {"attr": "visible", "value": self.visible},
                         {"attr": "canvas", "value": self.display.idx if self.display != None else canvas.get_selected().idx if canvas.get_selected() != None else -1}]}

        self.appendcmd(cmd)
        
    def __setattr__(self, name, value):
        if name in ['length','radius','thickness','coils','size']:
            val = value if type(value) is vector else vector(value) if type(value) in [tuple, list, np.ndarray] else value
            self.__dict__[name] = val
        
            if name == 'length':
                self.__dict__['axis'] = self.axis.norm() * value
                self.addattr('axis')
            elif name == 'radius':
                self.addattr('size')
            elif name == 'thickness':
                self.addattr(name)
            elif name == 'coils':
                self.addattr(name)
            elif name == 'size':
                """VPython helix does not hava a size attribute but Glowscript helix does"""
                pass
        else:
            super(helix, self).__setattr__(name, value)

    def __getattribute__(self, name):
        if name in ['size','length']:
            if name == 'length':
                return object.__getattribute__(self, 'axis').mag()
            elif name == 'size':
                return vector(object.__getattribute__(self, 'axis').mag(), object.__getattribute__(self, 'radius')*2.0, object.__getattribute__(self, 'radius')*2.0)
        else:
            return super(helix, self).__getattribute__(name)
        
    def __del__(self):
        cmd = {"cmd": "delete", "idx": self.idx}
        self.appendcmd(cmd)
        #baseObj.cmds.append(cmd)
        super(helix, self).__del__()

class arrow(trailAttrs):
    """see arrow documentation at http://vpython.org/contents/docs/arrow.html"""    
    
    def __init__(self, pos=(0.,0.,0.), x=0., y=0., z=0., axis=(1.,0.,0.), length=-1., shaftwidth=0., headwidth=0., headlength=0., fixedwidth=False,
                 frame=None, up=(0.,1.,0.), color=(1.,1.,1.), red=1., green=1., blue=1., material=None, opacity=1.0,
                 display=None, visible=True, make_trail=False, trail_type="curve", interval=1, retain=-1, **kwargs):
        axis = vector(axis) if type(axis) in [tuple, list, np.ndarray] else axis
        shaftwidth_provided = headwidth_provided = headlength_provided = True
        if (length == -1.):
            length = axis.mag()
        else:
            axis = axis.norm() * length
        if (shaftwidth == 0.):
            shaftwidth_provided = False
            shaftwidth = 0.1*length
        if (headwidth == 0.):
            headwidth_provided = False
            headwidth = 2.*shaftwidth
        if (headlength == 0.):
            headlength_provided = False
            headlength = 3.*shaftwidth
        super(arrow, self).__init__(pos=pos, x=x, y=y, z=z, axis=axis, up=up, color=color, red=red, green=green, blue=blue, 
                                    material=material, opacity=opacity, frame=frame, display=display, visible=visible, 
                                    make_trail=make_trail, trail_type=trail_type, interval=interval, retain=retain, **kwargs)
        object.__setattr__(self, 'length', length)
        object.__setattr__(self, 'shaftwidth', shaftwidth)
        object.__setattr__(self, 'headwidth', headwidth)
        object.__setattr__(self, 'headlength', headlength)
        if ((shaftwidth_provided == True) or (headwidth_provided == True) or (headlength_provided == True)):
            cmd = {"cmd": "arrow", "idx": self.idx, "guid": self.guid, 
                   "attrs": [{"attr": "pos", "value": self.pos.values()},
                             {"attr": "axis_and_length", "value": self.axis.values()},
                             {"attr": "up", "value": self.up.values()},
                             {"attr": "color", "value": self.color},
                             {"attr": "opacity", "value": self.opacity},
                             {"attr": "canvas", "value": self.display.idx if self.display != None else canvas.get_selected().idx if canvas.get_selected() != None else -1},
                             {"attr": "visible", "value": self.visible},
                             {"attr": "make_trail", "value": self.make_trail},
                             {"attr": "type", "value": 'curve' if self.trail_type == 'curve' else 'spheres'},
                             {"attr": "interval", "value": self.interval},
                             {"attr": "shaftwidth", "value": self.shaftwidth},
                             {"attr": "headwidth", "value": self.headwidth},
                             {"attr": "headlength", "value": self.headlength},
                             {"attr": "retain", "value": self.retain}]}

            self.appendcmd(cmd)
        else:
            cmd = {"cmd": "arrow", "idx": self.idx, "guid": self.guid, 
                   "attrs": [{"attr": "pos", "value": self.pos.values()},
                             {"attr": "axis_and_length", "value": self.axis.values()},
                             {"attr": "up", "value": self.up.values()},
                             {"attr": "color", "value": self.color},
                             {"attr": "opacity", "value": self.opacity},
                             {"attr": "canvas", "value": self.display.idx if self.display != None else canvas.get_selected().idx if canvas.get_selected() != None else -1},
                             {"attr": "visible", "value": self.visible},
                             {"attr": "make_trail", "value": self.make_trail},
                             {"attr": "type", "value": 'curve' if self.trail_type == 'curve' else 'spheres'},
                             {"attr": "interval", "value": self.interval},
                             {"attr": "retain", "value": self.retain}]}

            self.appendcmd(cmd)

        """
        if (shaftwidth_provided == True):
            self.shaftwidth = shaftwidth
        if (headwidth_provided == True):
            self.headwidth = headwidth
        if (headlength_provided == True):
            self.headlength = headlength
        """
                
        object.__getattribute__(self, 'axis').remove_notification((self.addattr,'axis'))
        object.__getattribute__(self, 'axis').add_notification((self.addattr,'axis_and_length'))
        
        if (frame != None):
            frame.objects.append(self)
            frame.update_obj_list()
        
    def __setattr__(self, name, value):
        if name in ['length','axis','shaftwidth','headwidth','headlength','fixedwidth']:
            if name == 'axis':
                self.__dict__['axis'].remove_notification((self.addattr,'axis_and_length'))
                
            val = value if type(value) is vector else vector(value) if type(value) in [tuple, list, np.ndarray] else value
            self.__dict__[name] = val
        
            if name == 'length':
                self.__dict__['axis'] = self.axis.norm() * value
                self.addattr('axis_and_length')
            elif name == 'axis':
                self.__dict__['axis'].add_notification((self.addattr,'axis_and_length'))
                self.addattr('axis_and_length')
            elif name == 'shaftwidth':
                self.addattr(name)
            elif name == 'headwidth':
                self.addattr(name)
            elif name == 'headlength':
                self.addattr(name)
                
        else:
            super(arrow, self).__setattr__(name, value)

    def __getattribute__(self, name):
        if name in ['length', 'axis_and_length']:
            if name == 'length':
                return object.__getattribute__(self, 'axis').mag()
            elif name == 'axis_and_length':
                return object.__getattribute__(self, 'axis')
        else:
            return super(arrow, self).__getattribute__(name)
        
    def __del__(self):
        cmd = {"cmd": "delete", "idx": self.idx}
        self.appendcmd(cmd)
        object.__getattribute__(self, 'axis').remove_notification((self.addattr,'axis_and_length'))
        super(arrow, self).__del__()


class cylinder(trailAttrs):
    """see cylinder documentation at http://vpython.org/contents/docs/cylinder.html"""    
    
    def __init__(self, pos=(0.,0.,0.), x=0., y=0., z=0., axis=(1.,0.,0.), 
                 length=None, radius=1., frame=None, up=(0.,1.,0.), 
                 color=(1.,1.,1.), red=1., green=1., blue=1., material=None, 
                 opacity=1.0, display=None, visible=True, make_trail=False, 
                 trail_type="curve", interval=1, retain=-1, **kwargs):
        axis = vector(axis) if type(axis) in [tuple, list, np.ndarray] else axis
        if (length == None):
            length = axis.mag()
        else:
            axis = axis.norm() * length
        size = vector(length,radius*2,radius*2)
        super(cylinder, self).__init__(pos=pos, x=x, y=y, z=z, axis=axis, size=size, up=up, color=color, red=red, green=green, blue=blue,
                                       material=material, opacity=opacity, frame=frame, display=display, visible=visible,
                                       make_trail=make_trail, trail_type=trail_type, interval=interval, retain=retain, **kwargs)
        object.__setattr__(self, 'length', length)
        object.__setattr__(self, 'radius', radius)
        cmd = {"cmd": "cylinder", "idx": self.idx, "guid": self.guid, 
               "attrs": [{"attr": "pos", "value": self.pos.values()},
                         {"attr": "axis", "value": self.axis.values()},
                         {"attr": "size", "value": self.size.values()},
                         {"attr": "up", "value": self.up.values()},
                         {"attr": "color", "value": self.color},
                         {"attr": "opacity", "value": self.opacity},
                         {"attr": "shininess", "value": self.shininess},
                         {"attr": "emissive", "value": self.emissive},
                         {"attr": "canvas", "value": self.display.idx if self.display != None else canvas.get_selected().idx if canvas.get_selected() != None else -1},
                         {"attr": "make_trail", "value": self.make_trail},
                         {"attr": "type", "value": 'curve' if self.trail_type == 'curve' else 'spheres'},
                         {"attr": "interval", "value": self.interval},
                         {"attr": "visible", "value": self.visible},
                         {"attr": "retain", "value": self.retain}]}

        self.appendcmd(cmd)
        if (frame != None):
            frame.objects.append(self)
            frame.update_obj_list()
        
    def __setattr__(self, name, value):
        if name in ['length','radius']:
            val = value if type(value) is vector else vector(value) if type(value) in [tuple, list, np.ndarray] else value
            self.__dict__[name] = val
        
            if name == 'length':
                self.__dict__['axis'] = self.axis.norm() * value
                self.addattr('axis')
            elif name == 'radius':
                self.addattr('size')
        else:
            super(cylinder, self).__setattr__(name, value)
 
    def __getattribute__(self, name):
        if name in ['size','length']:
            if name == 'length':
                return object.__getattribute__(self, 'axis').mag()
            elif name == 'size':
                return vector(object.__getattribute__(self, 'axis').mag(), object.__getattribute__(self, 'radius')*2.0, object.__getattribute__(self, 'radius')*2.0)
        else:
            return super(cylinder, self).__getattribute__(name)
        
    def __del__(self):
        cmd = {"cmd": "delete", "idx": self.idx}
        self.appendcmd(cmd)
        super(cylinder, self).__del__()


class pyramid(trailAttrs):
    """see pyramid documentation at http://vpython.org/contents/docs/pyramid.html"""    
    
    def __init__(self, pos=(0.,0.,0.), x=0., y=0., z=0., axis=(1.,0.,0.), size=(1.,1.,1.),
                 length=-1., width=1., height=1., up=(0.,1.,0.), color=(1.,1.,1.), red=1., green=1., blue=1.,
                 frame=None, material=None, opacity=1.0, display=None, visible=True,
                 make_trail=False, trail_type="curve", interval=1, retain=-1, **kwargs):
        axis = vector(axis) if type(axis) in [tuple, list, np.ndarray] else axis
        size = vector(size) if type(size) in [tuple, list, np.ndarray] else size
        if (length == -1.):
            if size[0] == 1. and size[1] == 1. and size[2] == 1.:
                length = axis.mag()
                size[0] = length
            else:
                length = size[0]
                height = size[1]
                width = size[2]
        if (length != 1.0) or (width != 1.0) or (height != 1.0):
            size = vector(length,height,width)
        else:
            length = size[0]
            height = size[1]
            width = size[2]
        axis = axis.norm() * length
        super(pyramid, self).__init__(pos=pos, x=x, y=y, z=z, axis=axis, size=size, up=up, color=color, red=red, green=green, blue=blue,
                                      material=material, opacity=opacity, frame=frame, display=display, visible=visible,
                                      make_trail=make_trail, trail_type=trail_type, interval=interval, retain=retain, **kwargs)
        object.__setattr__(self, 'length', length)
        object.__setattr__(self, 'width', width)
        object.__setattr__(self, 'height', height)
        cmd = {"cmd": "pyramid", "idx": self.idx, "guid": self.guid, 
               "attrs": [{"attr": "pos", "value": self.pos.values()},
                         {"attr": "axis", "value": self.axis.values()},
                         {"attr": "size", "value": self.size.values()},
                         {"attr": "up", "value": self.up.values()},
                         {"attr": "color", "value": self.color},
                         {"attr": "opacity", "value": self.opacity},
                         {"attr": "shininess", "value": self.shininess},
                         {"attr": "emissive", "value": self.emissive},
                         {"attr": "canvas", "value": self.display.idx if self.display != None else canvas.get_selected().idx if canvas.get_selected() != None else -1},
                         {"attr": "make_trail", "value": self.make_trail},
                         {"attr": "type", "value": 'curve' if self.trail_type == 'curve' else 'spheres'},
                         {"attr": "interval", "value": self.interval},
                         {"attr": "visible", "value": self.visible},
                         {"attr": "retain", "value": self.retain}]}

        self.appendcmd(cmd)
        if (frame != None):
            frame.objects.append(self)
            frame.update_obj_list()
        
    def __setattr__(self, name, value):
        if name in ['length','width','height','size']:
            val = value if type(value) is vector else vector(value) if type(value) in [tuple, list, np.ndarray] else value
            self.__dict__[name] = val
        
            if name == 'length':
                self.__dict__['axis'] = self.axis.norm() * val
                self.addattr('axis')
            elif name == 'height':
                self.addattr('size')
            elif name == 'width':
                self.addattr('size')
            elif name == 'size':
                self.__dict__['axis'] = self.axis.norm() * val[0]
                self.__dict__['height'] = val[1]
                self.__dict__['width'] = val[2]
                self.addattr(name)
        else:
            super(pyramid, self).__setattr__(name, value)

    def __getattribute__(self, name):
        if name in ['size','length']:
            if name == 'length':
                return object.__getattribute__(self, 'axis').mag()
            elif name == 'size':
                return vector(object.__getattribute__(self, 'axis').mag(), object.__getattribute__(self, 'height'), object.__getattribute__(self, 'width'))
        else:
            return super(pyramid, self).__getattribute__(name)
        
    def __del__(self):
        cmd = {"cmd": "delete", "idx": self.idx}
        self.appendcmd(cmd)
        super(pyramid, self).__del__()


class sphere(trailAttrs):
    """see sphere documentation at http://vpython.org/contents/docs/sphere.html"""    
    
    def __init__(self, pos=(0.,0.,0.), x=0., y=0., z=0., axis=(1.,0.,0.), radius=1.0,
                 frame=None, up=(0.,1.,0.), color=(1.,1.,1.), red=1., green=1., blue=1., material=None, opacity=1.0,
                 display=None, visible=True, make_trail=False, trail_type="curve", interval=1, retain=-1, **kwargs):
        size = vector(radius*2,radius*2,radius*2)
        super(sphere, self).__init__(pos=pos, x=x, y=y, z=z, axis=axis, size=size, up=up, color=color, red=red, green=green, blue=blue,
                                     material=material, opacity=opacity, frame=frame, display=display, visible=visible,
                                     make_trail=make_trail, trail_type=trail_type, interval=interval, retain=retain, **kwargs)
        object.__setattr__(self, 'radius', radius )
        object.__setattr__(self, 'display', display )

        cmd = {"cmd": "sphere", "idx": self.idx, "guid": self.guid, 
               "attrs": [{"attr": "pos", "value": self.pos.values()},
                         {"attr": "axis", "value": self.axis.values()},
                         {"attr": "size", "value": self.size.values()},
                         {"attr": "up", "value": self.up.values()},
                         {"attr": "color", "value": self.color},
                         {"attr": "opacity", "value": self.opacity},
                         {"attr": "shininess", "value": self.shininess},
                         {"attr": "emissive", "value": self.emissive},
                         {"attr": "canvas", "value": self.display.idx if self.display != None else canvas.get_selected().idx if canvas.get_selected() != None else -1},
                         {"attr": "make_trail", "value": self.make_trail},
                         {"attr": "type", "value": 'curve' if self.trail_type == 'curve' else 'spheres'},
                         {"attr": "interval", "value": self.interval},
                         {"attr": "visible", "value": self.visible},
                         {"attr": "retain", "value": self.retain}]}
        self.appendcmd(cmd)
        if (frame != None):
            frame.objects.append(self)
            frame.update_obj_list()
        
    def __setattr__(self, name, value):        
        if name == 'radius':
            self.__dict__[name] = value
            self.__dict__['size'][0] = value*2
            self.__dict__['size'][1] = value*2
            self.__dict__['size'][2] = value*2
            self.addattr('size')
        else:
            super(sphere, self).__setattr__(name, value)

    def __del__(self):
        cmd = {"cmd": "delete", "idx": self.idx}
        self.appendcmd(cmd)
        super(sphere, self).__del__()


class ellipsoid(trailAttrs):
    """see ellipsoid documentation at http://vpython.org/contents/docs/ellipsoid.html"""    
    def __init__(self, pos=(0.,0.,0.), x=0., y=0., z=0., axis=(1.,0.,0.), 
                 size=None, length=None, width=1., height=1., up=(0.,1.,0.), 
                 color=(1.,1.,1.), red=1., green=1., blue=1.,
                 frame=None, material=None, opacity=1.0, display=None, visible=True,
                 make_trail=False, trail_type="curve", interval=1, retain=-1, **kwargs):
        axis = vector(axis) if type(axis) in [tuple, list, np.ndarray] else axis
        if (length == None) and (size == None):
            length = axis.mag()
            size = vector(length, height, width)
        elif (length == None):
            length = size[0]
            height = size[1]
            width = size[2]
        else:
            size = vector(length, height, width)
        size = vector(size) if type(size) in [tuple, list, np.ndarray] else size
        axis = axis.norm() * length

        super(ellipsoid, self).__init__(pos=pos, x=x, y=y, z=z, axis=axis, size=size, up=up, color=color, red=red, green=green, blue=blue,
                                  material=material, opacity=opacity, frame=frame, display=display, visible=visible,
                                  make_trail=make_trail, trail_type=trail_type, interval=interval, retain=retain, **kwargs)
        object.__setattr__(self, 'length', length)
        object.__setattr__(self, 'width', width)
        object.__setattr__(self, 'height', height)
        cmd = {"cmd": "ellipsoid", "idx": self.idx, "guid": self.guid, 
               "attrs": [{"attr": "pos", "value": self.pos.values()},
                         {"attr": "axis", "value": self.axis.values()},
                         {"attr": "size", "value": self.size.values()},
                         {"attr": "up", "value": self.up.values()},
                         {"attr": "color", "value": self.color},
                         {"attr": "opacity", "value": self.opacity},
                         {"attr": "shininess", "value": self.shininess},
                         {"attr": "emissive", "value": self.emissive},
                         {"attr": "canvas", "value": self.display.idx if self.display != None else canvas.get_selected().idx if canvas.get_selected() != None else -1},
                         {"attr": "make_trail", "value": self.make_trail},
                         {"attr": "type", "value": 'curve' if self.trail_type == 'curve' else 'spheres'},
                         {"attr": "interval", "value": self.interval},
                         {"attr": "visible", "value": self.visible},
                         {"attr": "retain", "value": self.retain}]}

        self.appendcmd(cmd)
        if (frame != None):
            frame.objects.append(self)
            frame.update_obj_list()
        
    def __setattr__(self, name, value):
        if name in ['length','width','height','size']:
            val = value if type(value) is vector else vector(value) if type(value) in [tuple, list, np.ndarray] else value
            self.__dict__[name] = val
        
            if name == 'length':
                self.__dict__['axis'] = self.axis.norm() * value
                self.addattr('axis')
            elif name == 'height':
                self.addattr('size')
            elif name == 'width':
                self.addattr('size')
            elif name == 'size':
                self.__dict__['axis'] = self.axis.norm() * value[0]
                self.__dict__['height'] = value[1]
                self.__dict__['width'] = value[2]
                self.addattr(name)
        else:
            super(ellipsoid, self).__setattr__(name, value)

    def __getattribute__(self, name):
        if name in ['size','length']:
            if name == 'length':
                return object.__getattribute__(self, 'axis').mag()
            elif name == 'size':
                return vector(object.__getattribute__(self, 'axis').mag(), object.__getattribute__(self, 'height'), object.__getattribute__(self, 'width'))
        else:
            return super(ellipsoid, self).__getattribute__(name)
        
    def __del__(self):
        cmd = {"cmd": "delete", "idx": self.idx}
        self.appendcmd(cmd)
        super(ellipsoid, self).__del__()


class ring(baseAttrs):
    """see ring documentation at http://vpython.org/contents/docs/ring.html"""    
    
    def __init__(self, pos=(0.,0.,0.), x=0., y=0., z=0., axis=(1.,0.,0.),
                 length=1., radius=1., thickness=0.0, frame=None, display=None, visible=True,
                 up=(0.,1.,0.), color=(1.,1.,1.), red=1., green=1., blue=1.,
                 make_trail=False, trail_type="curve", interval=1, retain=-1, **kwargs):
        if (thickness == 0.0):
            thickness = radius/10.0
        
        size = vector(thickness,radius+thickness,radius+thickness)*2.0
        super(ring, self).__init__(pos=pos, x=x, y=y, z=z, axis=axis, size=size, up=up, color=color, red=red, green=green,
                                   blue=blue, frame=frame, display=display, visible=visible, **kwargs)
        object.__setattr__(self, 'length', length)
        object.__setattr__(self, 'radius', radius)
        object.__setattr__(self, 'thickness', thickness)
        object.__setattr__(self, 'make_trail', make_trail )
        object.__setattr__(self, 'trail_type', trail_type )
        object.__setattr__(self, 'interval', interval)
        object.__setattr__(self, 'retain', retain)
        #object.__setattr__(self, 'trail_object', curve() if self.trail_type == "curve" else pnts())
        cmd = {"cmd": "ring", "idx": self.idx, "guid": self.guid, 
               "attrs": [{"attr": "pos", "value": self.pos.values()},
                         {"attr": "axis", "value": self.axis.values()},
                         {"attr": "size", "value": self.size.values()},
                         {"attr": "up", "value": self.up.values()},
                         {"attr": "color", "value": self.color},
                         {"attr": "canvas", "value": self.display.idx if self.display != None else canvas.get_selected().idx if canvas.get_selected() != None else -1},
                         {"attr": "make_trail", "value": self.make_trail},
                         {"attr": "type", "value": 'curve' if self.trail_type == 'curve' else 'spheres'},
                         {"attr": "interval", "value": self.interval},
                         {"attr": "visible", "value": self.visible},
                         {"attr": "retain", "value": self.retain}]}

        self.appendcmd(cmd)
        
    def __setattr__(self, name, value):
        if name in ['make_trail','trail_type','interval','retain','length','radius','thickness']:
            self.__dict__[name] = value
            if name == 'make_trail':
                self.addattr(name)
            elif name == 'trail_type':
                self.addattr(name)
            elif name == 'interval':
                self.addattr(name)
            elif name == 'retain':
                self.addattr(name)
            elif name == 'radius':
                self.__dict__['size'][1] = (value + self.thickness)*2.0
                self.__dict__['size'][2] = (value + self.thickness)*2.0
                self.addattr('size')
            elif name == 'thickness':
                self.__dict__['size'][0] = value*2.0
                self.addattr('size')
                
        else:
            super(ring, self).__setattr__(name, value)

    def __del__(self):
        cmd = {"cmd": "delete", "idx": self.idx}
        self.appendcmd(cmd)
        super(ring, self).__del__()

class label(baseAttrs2):
    """see label documentation at http://vpython.org/contents/docs/label.html"""    
    
    def __init__(self, pos=(0.,0.,0.), x=0., y=0., z=0., color=(1.,1.,1.), red=1., green=1., blue=1., opacity=0.66, 
                 xoffset=20., yoffset=12., text="", font="sans", height=13, background=(0.,0.,0.),
                 border=5, box=True, line=True, linecolor=(0.,0.,0.), space=0., display=None, frame=None, visible=True, **kwargs):  
        # backgraound = scene.background   # default background color
        # color = scene.foreground  # default color
        super(label, self).__init__(pos=pos, x=x, y=y, z=z, color=color, red=red, green=green, blue=blue, opacity=opacity, 
                                    frame=frame, display=display, visible=visible, **kwargs)

        object.__setattr__(self, 'xoffset', xoffset)
        object.__setattr__(self, 'yoffset', yoffset)
        object.__setattr__(self, 'text', text)
        object.__setattr__(self, 'font', font)
        object.__setattr__(self, 'height', height)
        object.__setattr__(self, 'background', background)
        object.__setattr__(self, 'border', border)
        object.__setattr__(self, 'box', box)
        object.__setattr__(self, 'line', line)
        object.__setattr__(self, 'linecolor', linecolor)
        object.__setattr__(self, 'space', space)
        cmd = {"cmd": "label", "idx": self.idx, "guid": self.guid, 
               "attrs": [{"attr": "pos", "value": self.pos.values()},
                         {"attr": "text", "value": self.text},
                         {"attr": "xoffset", "value": self.xoffset},
                         {"attr": "yoffset", "value": self.yoffset},
                         {"attr": "font", "value": self.font},
                         {"attr": "height", "value": self.height},
                         {"attr": "color", "value": self.color},
                         {"attr": "background", "value": self.background},
                         {"attr": "opacity", "value": self.opacity},
                         {"attr": "border", "value": self.border},
                         {"attr": "box", "value": self.box},
                         {"attr": "line", "value": self.line},
                         {"attr": "linecolor", "value": self.linecolor},
                         {"attr": "space", "value": self.space},
                         {"attr": "visible", "value": self.visible},
                         {"attr": "canvas", "value": self.display.idx if self.display != None else canvas.get_selected().idx if canvas.get_selected() != None else -1}
                         ]}

        self.appendcmd(cmd)
        if (frame != None):
            frame.objects.append(self)
            frame.update_obj_list()
        
    def __setattr__(self, name, value):
        if name in ['xoffset','yoffset','text','font','height','background',
                    'border','box','line','linecolor','space']:
            self.__dict__[name] = value
            self.addattr(name)
        else:
            super(label, self).__setattr__(name, value)

            
class frame(baseAttrs):
    """see frame documentation at http://vpython.org/contents/docs/frame.html"""    

    objects = []
    def __init__(self, pos=(0.,0.,0.), x=0., y=0., z=0., axis=(1.,0.,0.), display=None, visible=True,
                 up=(0.,1.,0.), color=(1.,1.,1.), red=1., green=1., blue=1., **kwargs):
        super(frame, self).__init__(pos=pos, x=x, y=y, z=z, axis=axis, up=up, color=color, red=red, green=green, blue=blue, 
                                    display=display,visible=visible,**kwargs)
        object.__setattr__(self, 'objects', [])
        cmd = {"cmd": "compound", "idx": self.idx, "guid": self.guid,
               "attrs": [{"attr": "pos", "value": self.pos.values()},
                         {"attr": "axis", "value": self.axis.values()},
                         {"attr": "up", "value": self.up.values()},
                         {"attr": "color", "value": self.color},
                         {"attr": "visible", "value": self.visible},
                         {"attr": "canvas", "value": self.display.idx if self.display != None else canvas.get_selected().idx if canvas.get_selected() != None else -1}]}
        
        self.appendcmd(cmd)
        
    def __setattr__(self, name, value):
        super(frame, self).__setattr__(name, value)

    def frame_to_world(self, pos):
        # need to implement this
        return pos

    def world_to_frame(self, pos):
        # need to implement this
        return pos

    def update_obj_list(self):
        # self.visible = False     # we are going to create a new compound in glowscript so remove current one
        obj_idxs = []
        for obj in self.objects:
            obj_idxs.append(obj.idx)
        cmd = {"cmd": "compound", "idx": self.idx, 
               "attrs": [{"attr": "pos", "value": self.pos.values()},
                         {"attr": "axis", "value": self.axis.values()},
                         {"attr": "up", "value": self.up.values()},
                         {"attr": "color", "value": self.color},
                         {"attr": "obj_idxs", "value": obj_idxs},
                         {"attr": "canvas", "value": self.display.idx if self.display != None else canvas.get_selected().idx if canvas.get_selected() != None else -1}]}
        
        self.appendcmd(cmd)

class Mouse(object):
    'Mouse object'

    def __init__(self, pos=(0.,0.,0.), pick=None, pickpos=(0.,0.,0.), camera=None, ray=(0.,0.,1.), alt=False, ctrl=False, shift = False):
        self.pos = pos
        self.pick = pick
        self.pickpos = pickpos
        self.camera = camera
        self.ray = ray
        self.alt = alt
        self.ctrl = ctrl
        self.shift = shift
   
    def getclick(self):
        pass

    def project(self, normal=(0,1,0), point=(0,0,0), d=0):
        normal = vector(normal) if type(normal) in (tuple, list) else normal
        if normal.mag() == 0.:
            return None
        u_n = normal.norm()
        if (d != 0):
            point = d*u_n
        else:
            point = vector(point) if type(point) in (tuple, list) else point
        point2 = vector(self.pos) if type(self.pos) in (tuple, list) else self.pos
        p = point2 - point
        h = p.dot(u_n)
        return point2 - h*u_n


class sceneObj(baseObj):
    visible = True
    foreground = (1,1,1)
    background = (0,0,0)
    ambient = color.gray(0.2)
    stereo = 'redcyan'
    stereodepth = 1.
    x = 0.
    y = 0.
    height = 500
    width = 800
    title = ""
    fullscreen = False
    exit = True
    center = vector(0,0,0)
    autocenter = True
    forward = vector(0,0,-1)
    fov = math.pi/3.
    range = (1.,1.,1.)
    scale = (1.,1.,1.)
    up = vector(0.,1.,0.)
    autoscale = True
    userzoom = True
    userspin = True
    lights = []
    objects = []

    def __init__(self, visible=True, foreground=(1,1,1), background=(0,0,0), ambient=color.gray(0.2), stereo='redcyan',
                    stereodepth=1., x=0., y=0., height=480, width=640, title="", fullscreen=False,
                    exit=True, center=(0.,0.,0.), autocenter=True, forward=(0.,0.,-1.), fov=math.pi/3.,
                    range=(1.,1.,1.), scale=(1.,1.,1.), up=(0.,1.,0.), autoscale=True, userzoom=True, userspin=True, **kwargs):
        super(sceneObj, self).__init__(**kwargs)
        rate.active = False
        if isinstance(range, (int, long, float)):
            range = (range,range,range)
        if isinstance(scale, (int, long, float)):
            scale = (scale,scale,scale)
        if (range[0] != 1.) and (range[0] != 0.):
            scale[0] = 1./range[0]
        if (scale[0] != 1.) and (scale[0] != 0.):
            range[0] = 1./scale[0]
        object.__setattr__(self, 'objects', [])
        object.__setattr__(self, 'visible', visible)
        object.__setattr__(self, 'foreground', foreground)
        object.__setattr__(self, 'background', background)
        object.__setattr__(self, 'ambient', ambient)
        object.__setattr__(self, 'stereo', stereo)
        object.__setattr__(self, 'stereodepth', stereodepth)
        object.__setattr__(self, 'x', x)
        object.__setattr__(self, 'y', y)
        object.__setattr__(self, 'height', height)
        object.__setattr__(self, 'width', width)
        object.__setattr__(self, 'title', title)
        object.__setattr__(self, 'fullscreen', fullscreen)
        object.__setattr__(self, 'exit', exit)
        object.__setattr__(self, 'autocenter', autocenter)
        object.__setattr__(self, 'forward', vector(forward) if type(forward) in [tuple, list, np.ndarray] else forward)
        object.__setattr__(self, 'fov', fov)
        object.__setattr__(self, 'range', vector(range) if type(range) is tuple else range)
        object.__setattr__(self, 'scale', vector(scale) if type(scale) is tuple else scale)
        object.__setattr__(self, 'up', vector(up) if type(up) in [tuple, list, np.ndarray] else up)
        object.__setattr__(self, 'center', vector(center) if type(center) in [tuple, list, np.ndarray] else center)
        object.__setattr__(self, 'autoscale', autoscale)
        object.__setattr__(self, 'userzoom', userzoom)
        object.__setattr__(self, 'userspin', userspin)
        object.__setattr__(self, 'mouse', Mouse())
        
        object.__getattribute__(self, 'forward').add_notification((self.addattr,'forward'))
        object.__getattribute__(self, 'range').add_notification((self.addattr,'range'))
        object.__getattribute__(self, 'scale').add_notification((self.addattr,'scale'))
        object.__getattribute__(self, 'up').add_notification((self.addattr,'up'))
        object.__getattribute__(self, 'center').add_notification((self.addattr,'center'))
        
    def __setattr__(self, name, value):
        if name == 'mouse':
            self.__dict__[name] = value
        elif name in ['visible','foreground','background','ambient','stereo','stereodepth','x','y',
                    'height','width','title','fullscreen','exit','center','autocenter',
                    'forward','fov','range','scale','up','autoscale','userzoom','userspin']:
            if name in ['forward','range','scale','up','center']:
                self.__dict__[name].remove_notification((self.addattr,name))
            if name in ['foreground','background','ambient']:
                self.__dict__[name] = value
            elif name in ['scale','range']:
                if isinstance(value, (int, long, float)):
                    value = (value,value,value)
                self.__dict__[name] = vector(value) if type(value) is tuple else value
                self.__dict__[name].add_notification((self.addattr,name))
            elif name in ['up','center','forward']:
                self.__dict__[name] = vector(value) if type(value) in [tuple, list, np.ndarray] else value
                self.__dict__[name].add_notification((self.addattr,name))
            else:
                self.__dict__[name] = vector(value) if type(value) is tuple else value
            if name in ['background','ambient','height','width','center',
                    'forward','fov','range','scale','up','autoscale','userzoom','userspin']:
                cmd = {}
                if name == 'background':
                    self.addattr(name)
                elif name == 'ambient':
                    self.addattr(name)
                elif name == 'center':
                    self.addattr(name)
                elif name == 'forward':
                    self.addattr(name)
                elif name == 'range':
                    self.addattr(name)
                    if (self.range[0] != 0.):
                        self.__dict__['scale'][0] = 1./self.range[0] 
                elif name == 'scale':
                    self.addattr(name)
                    if (self.scale[0] != 0.):
                        self.__dict__['range'][0] = 1./self.scale[0] 
                else:
                    self.addattr(name)
        else:
            super(sceneObj, self).__setattr__(name, value)

    """
    def __getattribute__(self, name):
        if name in ['range','scale']:
            if name == 'range':
                return object.__getattribute__(self, 'range')[0]
            elif name == 'scale':
                if object.__getattribute__(self, 'range')[0] != 0.0:
                    return 1.0/object.__getattribute__(self, 'range')[0]
                else:
                    return 1.0
        else:
            return super(sceneObj, self).__getattribute__(name)
    """
    
    def bind(self, *args):
        cmd = {"cmd": "bind", "idx": self.idx, "selector": '#' + self.sceneId + ' canvas', "sceneguid": self.guid}
        if callable(args[1]):
            cmd['events'] = args[0]
            guid = str(uuid.uuid4())
            callback_registry[guid] = args[1]
            cmd['callback'] = guid
            if inspect.isfunction(args[1]):
                cmd['events'] = self.evtns(args[0],args[1].__name__)      # add func name namespace to events
            if len(args) > 2:
                obj = args[2]
                if type(obj) in [str, int, long, bool, float, tuple, complex]:
                    cmd['arbArg'] = obj
                elif isinstance(obj, collections.Sequence):
                    cmd['arbArg'] = self.encode_seq(obj)
                elif isinstance(obj, baseObj):
                    cmd['arbArg'] = {'guido': obj.guid}
                else:
                    cmd['arbArg'] = args[2]
            self.appendcmd(cmd)

    def unbind(self, *args):
        cmd = {"cmd": "unbind", "idx": self.idx, "selector": '#' + self.sceneId + ' canvas'}
        if callable(args[1]):
            cmd['events'] = args[0]
            if inspect.isfunction(args[1]):
                cmd['events'] = self.evtns(args[0],args[1].__name__)      # add func name namespace to events
            self.appendcmd(cmd)
            
    def evtns(self,strs, ns):
        evts = strs.split()
        for i, evt in enumerate(evts):
            evts[i] = evt + "." + ns
        ns_evts = " ".join(evts)
        return ns_evts
    
    def encode_seq(self,seq):
        if type(seq) is list:
            for i, item in enumerate(seq):
                if isinstance(item, baseObj):
                    seq[i] = {'guido': item.guid}
            return seq
        if type(seq) is tuple:
            seq2 = list(seq)
            for i, item in enumerate(seq2):
                if isinstance(item, baseObj):
                    seq2[i] = {'guido': item.guid}
            return seq2
        return []

    def __del__(self):
        for attr in ['forward','range','scale','up','center']:
            object.__getattribute__(self, attr).remove_notification((self.addattr,attr))
        super(sceneObj, self).__del__()

    
class canvas(sceneObj):
    sceneCnt = 0
    selected_display = -1
    displays = []
    display_idx = 0
    def __init__(self, visible=True, foreground=(1,1,1), background=(0,0,0), ambient=color.gray(0.2), stereo='redcyan',
                    stereodepth=1., x=0., y=0., height=480, width=640, title="", fullscreen=False,
                    exit=True, center=(0.,0.,0.), autocenter=True, forward=(0.,0.,-1.), fov=math.pi/3.,
                    range=1., scale=1., up=(0.,1.,0.), autoscale=True, userzoom=True, userspin=True, **kwargs):
        super(canvas, self).__init__(visible=visible, foreground=foreground, background=background, ambient=ambient, stereo=stereo,
                                     stereodepth=stereodepth, x=x, y=y, height=height, width=width, title=title, fullscreen=fullscreen,
                                     exit=exit, center=center, autocenter=autocenter, forward=forward, fov=fov,
                                     range=range, scale=scale, up=up, autoscale=autoscale, userzoom=userzoom, **kwargs)
        object.__setattr__(self, 'display_index', canvas.display_idx)
        object.__setattr__(self, 'sceneId', "scene%d" % (canvas.sceneCnt))
        canvas.displays.append(self)
        canvas.selected_display = canvas.display_idx
        canvas.display_idx += 1
        canvas.sceneCnt += 1
        #object.__setattr__(self, 'sceneId', "scene%d" % (canvas.sceneCnt))
        try:
            scene
        except NameError:
            display(HTML("""<div id="%s"><div id="glowscript" class="glowscript"></div></div>""" % (self.sceneId)))
            display(Javascript("""window.__context = { glowscript_container: $("#glowscript").removeAttr("id")}"""))
        else:
            pass
            display(HTML("""<div id="%s"><div id="glowscript" class="glowscript"></div></div>""" % (self.sceneId)))
            display(Javascript("""window.__context = { glowscript_container: $("#glowscript").removeAttr("id")}"""))
            
        cmd = {"cmd": "canvas", "idx": self.idx, "guid": self.guid, 
               "attrs": [{"attr": "visible", "value": self.visible},
                         {"attr": "title", "value": self.title},
                         {"attr": "background", "value": self.background},
                         {"attr": "ambient", "value": self.ambient},
                         {"attr": "height", "value": self.height},
                         {"attr": "width", "value": self.width},
                         {"attr": "forward", "value": self.forward.values()},
                         {"attr": "fov", "value": self.fov},
                         {"attr": "range", "value": self.range[0]},
                         {"attr": "up", "value": self.up.values()},
                         {"attr": "center", "value": self.center.values()},
                         {"attr": "autoscale", "value": self.autoscale},
                         {"attr": "userzoom", "value": self.userzoom},
                         {"attr": "userspin", "value": self.userspin}
                         ]}
        
        self.appendcmd(cmd)

    def __setattr__(self, name, value):
            super(canvas, self).__setattr__(name, value)

    def __getattribute__(self, name):
            return super(canvas, self).__getattribute__(name)
        
    def select(self):
        canvas.selected_display = self.display_index

    @classmethod
    def get_selected(cls):
        return cls.displays[cls.selected_display] if cls.selected_display >= 0 else None

    def _ipython_display_(self):
        display_html('<div id="glowscript2" ><div id="glowscript" class="glowscript"></div></div>', raw=True)
        cmd = {"cmd": "redisplay", "idx": self.idx, "sceneId": self.sceneId}        
        self.appendcmd(cmd)

class idisplay(canvas):
    def __init__(self, visible=True, foreground=(1,1,1), background=(0,0,0), ambient=color.gray(0.2), stereo='redcyan', 
                 stereodepth=1., x=0., y=0., height=480, width=640, title="", fullscreen=False, 
                 exit=True, center=(0.,0.,0.), autocenter=True, forward=(0.,0.,-1.), fov=math.pi/3.,
                 range=1., scale=1., up=(0.,1.,0.), autoscale=True, userzoom=True, userspin=True, **kwargs):
        super(idisplay, self).__init__(visible=visible, foreground=foreground, background=background, ambient=ambient, stereo=stereo,
                                       stereodepth=stereodepth, x=x, y=y, height=height, width=width, title=title, fullscreen=fullscreen,
                                       exit=exit, center=center, autocenter=autocenter, forward=forward, fov=fov, 
                                       range=range, scale=scale, up=up, autoscale=autoscale, userzoom=userzoom, **kwargs)
    def __setattr__(self, name, value):
            super(idisplay, self).__setattr__(name, value)

class defaultscene(sceneObj):

    def __init__(self):
        super(defaultscene, self).__init__()
        object.__setattr__(self, 'sceneId', "scene0")
        cmd = {"cmd": "scene", "idx": self.idx}        
        self.appendcmd(cmd)
        
    def __setattr__(self, name, value):        
        super(defaultscene, self).__setattr__(name, value)

    def __getattribute__(self, name):
            return super(defaultscene, self).__getattribute__(name)

    def _ipython_display_(self):
        display_html('<div id="glowscript2" ><div id="glowscript" class="glowscript"></div></div>', raw=True)
        cmd = {"cmd": "redisplay", "idx": self.idx, "sceneId": self.sceneId}        
        self.appendcmd(cmd)

    
class local_light(baseObj):
    """see lighting documentation at http://vpython.org/contents/docs/lights.html"""
    def __init__(self, pos=(0.,0.,0.), color=(1.,1.,1.), frame=None, display=None, **kwargs):
        super(local_light, self).__init__(**kwargs)
        object.__setattr__(self, 'pos', vector(pos) if type(pos) is tuple else pos)
        object.__setattr__(self, 'color', color)
        object.__setattr__(self, 'display', display)
        object.__setattr__(self, 'frame', frame)
        cmd = {"cmd": "local_light", "idx": self.idx, "guid": self.guid,
               "attrs": [{"attr": "pos", "value": self.pos.values()},
                         {"attr": "color", "value": self.color},
                         {"attr": "canvas", "value": self.display.idx if self.display != None else canvas.get_selected().idx if canvas.get_selected() != None else -1}
                         ]}
        if (canvas.get_selected() != None):
            canvas.get_selected().lights.append(self)
        self.appendcmd(cmd)
        
    def __setattr__(self, name, value):
        if name in ['pos']:
            self.__dict__[name] = vector(value) if type(value) is tuple else value
            cmd = {}
            if name == 'pos':
                cmd = {"idx": self.idx, "attr": name, "val": self.pos.values()}            
                
            baseObj.cmds.append(cmd)
        elif name == 'color':
            self.__dict__[name] = value
            cmd = {"idx": self.idx, "attr": name, "val": self.color}            
                
            baseObj.cmds.append(cmd)
                
        else:
            super(local_light, self).__setattr__(name, value)
        
class distant_light(baseObj):
    """see lighting documentation at http://vpython.org/contents/docs/lights.html"""
    def __init__(self, direction=(0.,0.,0.), color=(1.,1.,1.), frame=None, display=None, **kwargs):
        super(distant_light, self).__init__(**kwargs)
        object.__setattr__(self, 'direction', vector(direction) if type(direction) is tuple else direction)
        object.__setattr__(self, 'color', color)
        object.__setattr__(self, 'display', display)
        object.__setattr__(self, 'frame', frame)
        cmd = {"cmd": "distant_light", "idx": self.idx,  "guid": self.guid,
               "attrs": [{"attr": "direction", "value": self.direction.values()},
                         {"attr": "color", "value": self.color},
                         {"attr": "canvas", "value": self.display.idx if self.display != None else canvas.get_selected().idx if canvas.get_selected() != None else -1}
                         ]}
        if (canvas.get_selected() != None):
            canvas.get_selected().lights.append(self)
        self.appendcmd(cmd)
        
    def __setattr__(self, name, value):
        if name in ['direction']:
            self.__dict__[name] = vector(value) if type(value) is tuple else value
            cmd = {}
            if name == 'direction':
                cmd = {"idx": self.idx, "attr": name, "val": self.direction.values()}            
                
            baseObj.cmds.append(cmd)
        elif name == 'color':
            self.__dict__[name] = value
            cmd = {"idx": self.idx, "attr": name, "val": self.color}            
                
            baseObj.cmds.append(cmd)
                
        else:
            super(distant_light, self).__setattr__(name, value)

scene = None

for i in range(10):
    if (baseObj.glow != None):
        break
    else:
        time.sleep(1.0)
        #if IPython.__version__ >= '3.0.0' :
        with glowlock:
            get_ipython().kernel.do_one_iteration()
        scene = defaultscene()
