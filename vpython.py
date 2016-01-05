from __future__ import print_function, division, absolute_import
from . import materials
import colorsys
import numpy as np   #### should get rid of this; no longer needed with GlowScript engine
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

# To print immediately, do this:
#    print(.....)
#    sys.stdout.flush()

from numpy import zeros, random   #### namespace conflict here; numpy should not be imported here
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
                        L = len(a)
                        baseObj.glow.comm.send(list(a))
                        a.clear()
                        while L > 0:
                            del baseObj.cmds[0]
                            L -= 1                

                    L = self.sz
                    req = commcmds[:L]
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
    notebook.nbextensions.install_nbextension(path = package_dir+"/data/glow.1.2.min.js",overwrite = True,user = True,verbose = 0)
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
    qSize = 512            # default to 500
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
            baseObj.glow.comm.send([cmd])
        else:
            baseObj.cmds.append(cmd)


    def addattr(self, name):
        # New-way to use a lock
        #with glowlock:
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

commcmds = []
for i in range(baseObj.qSize):
    commcmds.append({"idx": -1, "attr": 'dummy', "val": 0})
updtobjs2 = set()
next_call = time.time()

def commsend():
    global next_call, commcmds, updtobjs2, glowlock, rate
    with glowlock:
        try:
            if (baseObj.glow != None):
                if (len(baseObj.cmds) > 0) and (not rate.active):
                    a = copy.copy(baseObj.cmds)
                    L = len(a)
                    baseObj.glow.comm.send(list(a))
                    a.clear()
                    while L > 0:
                        del baseObj.cmds[0]
                        L -= 1 

                L = rate.sz if (rate.send == True) else 0
                if (L > 0):
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
                if L < baseObj.qSize:
                    while updtobjs2:
                        oid = updtobjs2.pop()
                        ob = id2obj(oid)
                        if  (ob is not None) and (hasattr(ob,'attrsupdt')) and (len(ob.attrsupdt) > 0 ):
                            while ob.attrsupdt:
                                attr = ob.attrsupdt.pop()
                                if attr is not None:
                                    attrval = getattr(ob,attr)
                                    if attrval is not None:
                                        if attr == 'pos' and isinstance(attrval, list):  ## curve or points
                                            poslist = []
                                            for aa in attrval:
                                                poslist.append(aa.value)
                                            commcmds[L]['idx'] = ob.idx
                                            commcmds[L]['attr'] = attr
                                            commcmds[L]['val'] = poslist                                                
                                        elif attr in ['axis','pos', 'up','color','center','forward',
                                                      'background','origin', 'trail_color', 'dot_color']:
                                            attrvalues = attrval.value
                                            if attrvalues is not None:
                                                commcmds[L]['idx'] = ob.idx
                                                commcmds[L]['attr'] = attr
                                                commcmds[L]['val'] = attrvalues
                                        elif attr == 'size':
                                            if hasattr(ob,'size_units'):
                                                commcmds[L]['idx'] = ob.idx
                                                commcmds[L]['attr'] = attr
                                                commcmds[L]['val'] = attrval
                                            else:
                                                attrvalues = attrval.value
                                                if attrvalues is not None:
                                                    commcmds[L]['idx'] = ob.idx
                                                    commcmds[L]['attr'] = attr
                                                    commcmds[L]['val'] = attrvalues
                                        elif attr in ['range','scale']:
                                            attrvalues = attrval[0]
                                            if attrvalues is not None:
                                                commcmds[L]['idx'] = ob.idx
                                                commcmds[L]['attr'] = attr
                                                commcmds[L]['val'] = attrvalues
                                        elif attr == '_plot':
                                            commcmds[L]['idx'] = ob.idx
                                            commcmds[L]['attr'] = attr
                                            commcmds[L]['val'] = attrval
                                            ob.clearData()
                                        elif attr == '_cpos':
                                            commcmds[L]['idx'] = ob.idx
                                            commcmds[L]['attr'] = attr
                                            commcmds[L]['val'] = attrval[:]
                                            ob.clearData()
                                        else:
                                            commcmds[L]['idx'] = ob.idx
                                            commcmds[L]['attr'] = attr
                                            commcmds[L]['val'] = attrval
                                        L += 1
                                        if L >= baseObj.qSize:
                                            if (len(ob.attrsupdt) > 0):
                                                updtobjs2.add(ob.oid)
                                            break
                                    elif attr == 'clear_trail':
                                        commcmds[L]['idx'] = ob.idx
                                        commcmds[L]['attr'] = attr
                                        commcmds[L]['val'] = 0  # will be ignored
                        if L >= baseObj.qSize:
                            #L = 0
                            break
                if L > 0:
                    if not rate.active:
                        L = L if (L <= baseObj.qSize) else baseObj.qSize
                        baseObj.glow.comm.send(commcmds[:L])
                    else:
                        rate.sz = L if (L <= baseObj.qSize) else baseObj.qSize
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
    def __init__(self, x=(0.,0.,0.), y=0., z=0.):
        if isinstance(x, (int, long, float)) and isinstance(y, (int, long, float)) and isinstance(z, (int, long, float)):
            self._value = [x,y,z]
        elif isinstance(x, (complex)) or isinstance(y, (complex)) or isinstance(z, (complex)):
            raise Exception("ArgumentError: complex argument not supported for vector(arg0,arg1,arg2)")
        else:
            self._value = [x[0],x[1],x[2]]
        #self.__dict__['shape'] = (3L,)          # python 2
        #self.__dict__['shape'] = (3,)           # python 3K
        self.shape = (3,)           # python 3K
        
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
            return self._value[0]
        elif key == 1:
            return self._value[1]
        elif key == 2:
            return self._value[2]
        else:
            return

    def __setitem__(self,key,value):
        if key == 0:
            if self._value[0] != value:
                self._value[0] = value
                self.on_change()
        elif key == 1:
            if self._value[1] != value:
                self._value[1] = value
                self.on_change()
        elif key == 2:
            if self._value[2] != value:
                self._value[2] = value
                self.on_change()
        
    def norm(self):
        smag = self.mag
        if (smag > 0.):
            return self / self.mag
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

    def set_values(self, xyz=(0.,0.,0.)):
        self._value = [value[0], value[1], value[2]]
        
    def mag(self):
        return math.sqrt(self.x**2+self.y**2+self.z**2)
   
    @property
    def value(self):
        return self._value
    
    @value.setter
    def value(self,value):
        self._value = [value[0], value[1], value[2]]
    
    @property
    def x(self):
        return self._value[0]
    
    @x.setter
    def x(self,value):
        if self._value[0] != value:
            self._value[0] = value
            self.on_change()
    
    @property
    def y(self):
        return self._value[1]
    
    @y.setter
    def y(self,value):
        if self._value[1] != value:
            self._value[1] = value
            self.on_change()
    
    @property
    def z(self):
        return self._value[2]
    
    @z.setter
    def z(self,value):
        if self._value[2] != value:
            self._value[2] = value
            self.on_change()

    @property
    def mag(self):
        return math.sqrt(self.x**2+self.y**2+self.z**2)

    @mag.setter
    def mag(self,value):
        normA = self.norm()
        self._value[0] = value * normA.x
        self._value[1] = value * normA.y
        self._value[2] = value * normA.z
        self.on_change()

    @property
    def mag2(self):
        return self.x**2+self.y**2+self.z**2

    @mag2.setter
    def mag2(self,value):
        normA = self.norm()
        self._value[0] = math.sqrt(value) * normA.x
        self._value[1] = math.sqrt(value) * normA.y
        self._value[2] = math.sqrt(value) * normA.z
        self.on_change()
     
    def on_change(self):
        pass

def mag(A):
    if (type(A) is np.ndarray) or (type(A) is tuple) or (type(A) is list):
        return vector(A).mag
    else:
        return A.mag

def mag2(A):
    if (type(A) is np.ndarray) or (type(A) is tuple) or (type(A) is list):
        return vector(A).mag2
    else:
        return A.mag2

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

class standard_colors(object):
    black = vector(0,0,0)
    white = vector(1,1,1)

    red = vector(1,0,0)
    green = vector(0,1,0)
    blue = vector(0,0,1)

    yellow = vector(1,1,0)
    cyan = vector(0,1,1)
    magenta = vector(1,0,1)

    orange = vector(1,0.6,0)

    def gray(self,luminance):
      return vector(luminance,luminance,luminance)

    def rgb_to_hsv(self,T):
      if len(T) > 3:
        T = T[:3]
      return vector(colorsys.rgb_to_hsv(*T))

    def hsv_to_rgb(self,T):
      if len(T) > 3:
        T = T[:3]
      return vector(colorsys.hsv_to_rgb(*T))

    def rgb_to_grayscale(self,T):
      if len(T) > 3:
        T = T[:3]
      luminance = 0.21*T[0] + 0.71*T[1] + 0.07*T[2]
      return vector(luminance, luminance, luminance)

color = standard_colors()

class standardAttributes(baseObj):
# vector-no-interactions, vector-interactions, scalar-no-interactions, scalar-interactions

    attrLists = {'box':[['pos', 'up', 'color', 'trail_color'], 
                        ['axis', 'size'],
                        ['visible', 'opacity','shininess', 'emissive', 'canvas', 
                         'make_trail', 'trail_type', 'interval', 
                         'retain', 'trail_color', 'trail_radius'],
                        ['red', 'green', 'blue','length', 'width', 'height']],
                 'sphere':[['pos', 'up', 'color', 'trail_color'], 
                        ['axis', 'size'],
                        ['visible', 'opacity','shininess', 'emissive', 'canvas', 
                         'make_trail', 'trail_type', 'interval', 
                         'retain', 'trail_color', 'trail_radius'],
                        ['red', 'green', 'blue','length', 'width', 'height', 'radius']],                        
                 'arrow':[['pos', 'up', 'color', 'trail_color'],
                         ['axis', 'size'],
                         ['visible', 'opacity',
                          'shininess', 'emissive', 'canvas', 'texture', 'frame', 'material',
                          'make_trail', 'trail_type', 'interval', 
                          'retain', 'trail_color', 'trail_radius',
                          'shaftwidth', 'headwidth', 'headlength'],
                         ['red', 'green', 'blue','length', 'width', 'height']],
                 'ring':[['pos', 'up', 'color', 'trail_color', 'axis', 'size'],  
                        [],
                        ['visible', 'opacity','shininess', 'emissive', 'canvas', 
                         'make_trail', 'trail_type', 'interval', 
                         'retain', 'trail_color', 'trail_radius'],
                        ['red', 'green', 'blue','length', 'width', 'height', 'thickness']],                       
                 'helix':[['pos', 'up', 'color', 'trail_color'],
                         ['axis', 'size'],
                         ['visible', 'opacity','shininess', 'emissive', 'canvas', 
                         'make_trail', 'trail_type', 'interval', 
                         'retain', 'trail_color', 'trail_radius', 'coils', 'thickness'],
                         ['red', 'green', 'blue','length', 'width', 'height']],
                 'curve':[['origin', 'up', 'color'],  
                         ['axis', 'size'],
                         ['visible', 'shininess', 'emissive', 'canvas', 'radius', 'retain', 'pos'],
                         ['red', 'green', 'blue','length', 'width', 'height']]}
    attrLists['pyramid'] = attrLists['box']
    attrLists['cylinder'] = attrLists['sphere']
    attrLists['cone'] = attrLists['sphere']
    attrLists['ellipsoid'] = attrLists['sphere']
    attrLists['points'] = attrLists['curve']

    def setup(self, args):
        super(standardAttributes, self).__init__() 
        self._constructing = True  ## calls to setters are from constructor

        objName = args['_objName']  ## identifies object type
        del args['_objName']
        
    # default values
        self._pos = vector(0,0,0)  
        self._axis = vector(1,0,0)
        self._up = vector(0,1,0)
        self._color = vector(1,1,1)
        self._size = args['_default_size']  ## because VP differs from JS
        del args['_default_size']        
        self._texture = None
        self._opacity = 1.0
        self._shininess = 0.6
        self._emissive = False
        self._material = None       
        self._make_trail = False
        self._trail_type = 'curve'
        self._trail_color = self._color
        self._interval = 1
        self._retain = -1
        self._trail_radius = None  # set by default after size set
        self._canvas = None
        self._visible = True
        self._frame = None
        self._size_units = 'pixels'
        
        argsToSend = []  ## send to GlowScript only attributes specified in constructor
        
    ## override defaults for vector attributes without side effects 
        attrs = standardAttributes.attrLists[objName][0]
        for a in attrs:
            if a in args:
                argsToSend.append(a)
                val = args[a]
                if isinstance(val, vector): setattr(self, '_'+a, val)
                else: raise AttributeError(a+' must be a vector')
                del args[a]
                
        vectorInteractions = {'size':'axis', 'axis':'size'}
                
    # override defaults for vector attributes with side effects
        attrs = standardAttributes.attrLists[objName][1]
        for a in attrs:
            if a in args:
                val = args[a]
                if isinstance(val, vector): 
                    setattr(self, a, val)
                    if a not in argsToSend:
                        argsToSend.append(a)
                    if vectorInteractions[a] not in argsToSend:
                        argsToSend.append(vectorInteractions[a])  
                elif objName == 'points' and a == 'size':  ## in this case size is a scalar
                    argsToSend.append(a)
                else: raise AttributeError(a+' must be a vector')
                del args[a]
    
        if 'size' not in argsToSend:  ## always send size because Python size differs from JS size
            argsToSend.append('size')
        self._trail_radius = 0.1 * self._size.y  ## default depends on size
                
    # override defaults for scalar attributes without side effects       
        attrs = standardAttributes.attrLists[objName][2]
        for a in attrs:
            if a in args:
                argsToSend.append(a)
                setattr(self, '_'+a, args[a])
                # if isinstance(args[a], list):
                    # while len(args[a]) > 0 :
                        # del args[a][-1]
                del args[a] 

        scalarInteractions={'red':'color', 'green':'color', 'blue':'color', 'radius':'size', 'thickness':'size',
                                'length':'size', 'height':'size', 'width':'size'}
    
    # override defaults for scalar attributes with side effects       
        attrs = standardAttributes.attrLists[objName][3]
        for a in attrs:
            if a in args:
                setattr(self, a, args[a])
                if scalarInteractions[a] not in argsToSend:
                    argsToSend.append(scalarInteractions[a])  # e.g. if a is radius, send size
                del args[a]                
                 
    # set values of user-defined attributes
        for key, value in args.items(): # Assign all other properties
            setattr(self, key, value)
            
        cmd = {"cmd": objName, "idx": self.idx, "guid": self.guid, 
           "attrs":[]}
           
        for a in argsToSend:
            aval = getattr(self,a)
            if isinstance(aval, vector):
                aval = aval.value
            cmd["attrs"].append({"attr":a, "value": aval})
            
        if self.canvas != None:
            cvs = self.canvas.idx
        elif canvas.get_selected() != None:
            cvs = canvas.get_selected().idx
        else:
            cvs = None
        if cvs is not None:
            cmd["attrs"].append({"attr": 'canvas', "value": cvs})
                    
        self._constructing = False  ## from now on any setter call will not be from constructor        
        self.appendcmd(cmd)
       
        if ('frame' in args and args['frame'] != None):
            frame.objects.append(self)
            frame.update_obj_list()

    # attribute vectors have these methods which call self.addattr()
        self._axis.on_change = self._on_axis_change
        self._size.on_change = self._on_size_change
        self._up.on_change = self._on_up_change
        if objName != 'curve':
            self._pos.on_change = self._on_pos_change
        else:
            self._origin.on_change = self._on_origin_change
            
    @property
    def size(self):
        return self._size   
    @size.setter
    def size(self,value):
        self._axis.value = self.axis.norm() * value.x
        self._size.value = value
        if not self._constructing:
            self.addattr('size')

    @property
    def axis(self):
        return self._axis
    @axis.setter
    def axis(self,value):
        self._axis.value = value
        self._size.x = mag(value)
        if not self._constructing:
            self.addattr('axis')

    @property
    def length(self): 
        return self._size.x    
    @length.setter
    def length(self,value):
        self._axis = self._axis.norm() * value
        self._size.x = value
        if not self._constructing:
            self.addattr('size')

    @property
    def height(self): 
        return self._size.y    
    @height.setter
    def height(self,value):
        self._size.y = value
        if not self._constructing:
            self.addattr('size')

    @property
    def width(self): 
        return self._size.z   
    @width.setter
    def width(self,value):
        self._size.z = value
        if not self._constructing:
            self.addattr('size')

    def _on_size_change(self):
        self._axis.value = self._axis.norm() * self._size.x           # update axis length when box.size.x is changed
        self.addattr('size')

    def _on_pos_change(self):
        self.addattr('pos')

    def _on_axis_change(self):
        self._size.x = self._axis.mag()
        self.addattr('axis')

    def _on_up_change(self):
        self.addattr('up')
        
    def _on_origin_change(self):  ## for curve and points
        self.addattr('origin')

        
    @property
    def up(self):
        return self._up  
    @up.setter
    def up(self,value):
        self._up.value = value
        if not self._constructing:
            self.addattr('up')

    @property
    def pos(self):
        return self._pos    
    @pos.setter
    def pos(self,value):
        self._pos.value = value
        if not self._constructing:
            self.addattr('pos')
        
    @property    
    def color(self):
        return self._color    
    @color.setter
    def color(self,value):
        self._color.value = value
        if not self._constructing:
            self.addattr('color')

    @property
    def red(self):
        return self._color[0]    
    @red.setter
    def red(self,value):
        self._color = (value,self.green,self.blue)
        if not self._constructing:
            self.addattr('color')

    @property
    def green(self):
        return self._color[1]    
    @green.setter
    def green(self,value):
        self._color = (self.red,value,self.blue)
        if not self._constructing:
            self.addattr('color')

    @property
    def blue(self):
        return self._color[2]    
    @blue.setter
    def blue(self,value):
        self._color = (self.red,self.green,value)
        if not self._constructing:
            self.addattr('color')

    @property
    def visible(self):
        return self._visible    
    @visible.setter
    def visible(self,value):
        self._visible = value
        if not self._constructing:
            self.addattr('visible')

    @property
    def canvas(self):
        return self._canvas    
    @canvas.setter
    def canvas(self,value):
        if not self._constructing:
            raise AttributeError('canvas cannot be modified')


    @property
    def frame(self):
        return self._frame    
    @frame.setter
    def frame(self,value):
        self._frame = value

    
    def rotate(self, angle=math.pi/4, axis=None, origin=None):
        if axis == None:
            rotaxis = self.axis
        else:
            if not isinstance(axis, vector): raise TypeError('axis must be a vector')
            rotaxis = axis
        if origin == None:
            rorigin = self.pos
        else:
            if not isinstance(origin, vector): raise TypeError('origin must be a vector')
            rorigin = origin
            self.pos = rorigin+(self.pos-rorigin).rotate(angle, rotaxis)
        axis = self.axis
        X = norm(axis)
        Y = self.up
        Z = X.cross(Y)
        if Z.dot(Z) < 1e-10:
            Y = vector(1,0,0)
            Z = X.cross(Y)
            if Z.dot(Z) < 1e-10:
                Y = vector(0,1,0)            
        self.axis = axis.rotate(angle, rotaxis)          
        self.up = Y.rotate(angle, rotaxis)
        
       
    @property
    def opacity(self):
        return self._opacity    
    @opacity.setter
    def opacity(self,value):
        self._opacity = value
        if not self._constructing:
            self.addattr('opacity')

    @property
    def emissive(self):
        return self._emissive    
    @emissive.setter
    def emissive(self,value):
        self._emissive = value
        if not self._constructing:
            self.addattr('emissive')

    @property
    def texture(self):
        return self._texture    
    @texture.setter
    def texture(self,value):
        self._texture = value
        if not self._constructing:
            self.addattr('texture')

    @property
    def shininess(self):
        return self._shininess    
    @shininess.setter
    def shininess(self,value):
        self._shininess = value
        if not self._constructing:
            self.addattr('shininess')

    @property
    def material(self):
        return self._material    
    @material.setter
    def material(self,value):
        self._material = value
        if (value == materials.emissive):
            self.emissive = True
        elif (value == materials.plastic):
            self.emissive = False
        else:
            self.emissive = False
            
    @property
    def make_trail(self):
        return self._make_trail    
    @make_trail.setter
    def make_trail(self,value):
        self._make_trail = value
        if not self._constructing:
            self.addattr('make_trail')

    @property
    def trail_type(self):
        return self._trail_type    
    @trail_type.setter
    def trail_type(self,value):
        if not self._constructing: raise AttributeError('"trail_type" cannot be modified')
        if (value not in ['curve', 'points']):
            raise Exception("ArgumentError: trail_type must be 'curve' or 'points'")
        self._trail_type = value   
        
    @property
    def trail_color(self):
        return self._trail_color
    @trail_color.setter
    def trail_color(self, value):
        if not self._constructing: raise AttributeError('"trail_color" cannot be modified')
        if isinstance(value, vector):
            self._trail_color = value
        else:
            raise TypeError('trail_color must be a vector')

    @property
    def interval(self):
        return self._interval    
    @interval.setter
    def interval(self,value):
        if not self._constructing: raise AttributeError('"interval" cannot be modified')
        self._interval = value

    @property
    def retain(self):
        return self._retain    
    @retain.setter
    def retain(self,value):
        if not self._constructing: raise AttributeError('"retain" cannot be modified')
        self._retain = value

    @property
    def trail_radius(self):
        return self._trail_radius    
    @trail_radius.setter
    def trail_radius(self,value):
        if not self._constructing: raise AttributeError('"trail_radius" cannot be modified')
        self._trail_radius = value
        
    @property
    def pps(self):
        return self._pps
    @pps.setter
    def pps(self, value):
        if not self._constructing: raise AttributeError('"pps" cannot be modified')
        self._pps = value
        
    def clear_trail(self):
        self.addattr('clear_trail')
           
    def __del__(self):
        super(standardAttributes, self).__del__()
        
class baseAttrs(baseObj):
    
    def __init__(self, pos=vector(0.,0.,0.), axis=vector(1.,0.,0.), size=vector(1.,1.,1.), visible=True,
                 up=vector(0.,1.,0.), color=vector(1.,1.,1.), red=1., green=1., blue=1., frame=None, canvas=None, **kwargs):
        super(baseAttrs, self).__init__(**kwargs)
        x = pos[0]
        y = pos[1]
        z = pos[2]
        if (red != 1.) or (green != 1.) or (blue != 1.):
            color = (red,green,blue)
        else:
            red = color[0]
            green = color[1]
            blue = color[2]
        
        self._pos = vector(pos)
        self._axis = vector(axis)
        self._size = vector(size)
        self._up = vector(up)
        self._color = vector(color)
        self._red = red
        self._green = green
        self._blue = blue        
        self._visible = visible
        self._canvas = canvas
        self._frame = frame
 
        self._pos.on_change = self._on_pos_change
        self._axis.on_change = self._on_axis_change
        self._size.on_change = self._on_size_change
        self._up.on_change = self._on_up_change
            
    @property
    def size(self):
        return self._size
    
    @size.setter
    def size(self,value):
        self._size.value = value
        self.addattr('size')

    @property
    def axis(self):
        return self._axis
    
    @axis.setter
    def axis(self,value):
        self._axis.value = value
        self.addattr('axis')

    @property
    def up(self):
        return self._up
    
    @up.setter
    def up(self,value):
        self._up.value = value
        self.addattr('up')

    @property
    def pos(self):
        return self._pos
    
    @pos.setter
    def pos(self,value):
        self._pos.value = value
        self.addattr('pos')

    @property
    def color(self):
        return self._color
    
    @color.setter
    def color(self,value):
        self._color = value
        self.addattr('color')

    @property
    def red(self):
        return self._color[0]
    
    @red.setter
    def red(self,value):
        self._color = (value,self.green,self.blue)
        self.addattr('color')

    @property
    def green(self):
        return self._color[1]
    
    @green.setter
    def green(self,value):
        self._color = (self.red,value,self.blue)
        self.addattr('color')

    @property
    def blue(self):
        return self._color[2]
    
    @blue.setter
    def blue(self,value):
        self._color = (self.red,self.green,value)
        self.addattr('color')

    @property
    def visible(self):
        return self._visible
    
    @visible.setter
    def visible(self,value):
        self._visible = value
        self.addattr('visible')

    @property
    def canvas(self):
        return self._canvas
    
    @canvas.setter
    def canvas(self,value):
        self._canvas = value

    @property
    def frame(self):
        return self._frame
    
    @frame.setter
    def frame(self,value):
        self._frame = value

    
    def rotate(self, angle=math.pi/4, axis=None, origin=None):
        if axis == None:
            rotaxis = self.axis
        else:
            rotaxis = norm(vector(axis)) if type(axis) in [tuple, list, np.ndarray] else axis
        if origin == None:
            origin = self.pos
        else:
            origin = vector(origin) if type(origin) in [tuple, list, np.ndarray] else origin
        self.pos = origin+(self.pos-origin).rotate(angle, rotaxis)
        axis = self.axis
        X = norm(axis)
        Y = self.up
        Z = X.cross(Y)
        if Z.dot(Z) < 1e-10:
            Y = vector(1,0,0)
            Z = X.cross(Y)
            if Z.dot(Z) < 1e-10:
                Y = vector(0,1,0)            
        self.axis = axis.rotate(angle, rotaxis)          
        self.up = Y.rotate(angle, rotaxis)
        
    def _on_pos_change(self):
        self.addattr('pos')

    def _on_axis_change(self):
        self.addattr('axis')

    def _on_size_change(self):
        self.addattr('size')

    def _on_up_change(self):
        self.addattr('up')

        
class baseAttrs2(baseAttrs):
    
    def __init__(self, pos=vector(0.,0.,0.), axis=vector(1.,0.,0.), size=vector(1.,1.,1.), visible=True,
                 up=vector(0.,1.,0.), color=vector(1.,1.,1.), red=1., green=1., blue=1., frame=None, canvas=None, material=None,
                 opacity=1.0, **kwargs):
        super(baseAttrs2, self).__init__(pos=pos, axis=axis, size=size, up=up, color=color, red=red, green=green, blue=blue,
                                         frame=frame, canvas=canvas, visible=visible, **kwargs)

        self._texture = None
        self._opacity = opacity
        self._shininess = 0.6
        self._emissive = False
        self._material = material

        if (material != None):
            if (material == materials.emissive):
                self._emissive = True
            elif (material == materials.plastic):
                self._emissive = False
            else:
                pass
    
    @property
    def opacity(self):
        return self._opacity
    
    @opacity.setter
    def opacity(self,value):
        self._opacity = value
        self.addattr('opacity')

    @property
    def emissive(self):
        return self._emissive
    
    @emissive.setter
    def emissive(self,value):
        self._emissive = value
        self.addattr('emissive')

    @property
    def texture(self):
        return self._texture
    
    @texture.setter
    def texture(self,value):
        self._texture = value

    @property
    def shininess(self):
        return self._shininess
    
    @shininess.setter
    def shininess(self,value):
        self._shininess = value

    @property
    def material(self):
        return self._material
    
    @material.setter
    def material(self,value):
        self._material = value
        if (value == materials.emissive):
            self.emissive = True
        elif (value == materials.plastic):
            self.emissive = False
        else:
            self.emissive = False
           
    
    def __del__(self):
        super(baseAttrs2, self).__del__()


class box(standardAttributes):
    def __init__(self, **args):
        args['_default_size'] = vector(1,1,1)
        args['_objName'] = "box"
        super(box, self).setup(args)
        
class sphere(standardAttributes):
    def __init__(self, **args):
        args['_default_size'] = vector(2,2,2)
        args['_objName'] = "sphere"
        super(sphere, self).setup(args)
        
    @property
    def radius(self):
        return self._size.y/2
    @radius.setter
    def radius(self,value):
        d = 2*value
        self.size = vector(d,d,d) # size will call addattr
        
class cylinder(standardAttributes):
    def __init__(self, **args):
        args['_default_size'] = vector(1,2,2)
        args['_objName'] = "cylinder"
        super(cylinder, self).setup(args)
        
    @property
    def radius(self):
        return self._size.y/2
    @radius.setter
    def radius(self,value):
        d = 2*value
        self.size = vector(self._size.x,d,d) # size will call addattr
        
class cone(standardAttributes):
    def __init__(self, **args):
        args['_default_size'] = vector(1,2,2)
        args['_objName'] = "cone"
        super(cone, self).setup(args)
        
    @property
    def radius(self):
        return self._size.y/2
    @radius.setter
    def radius(self,value):
        d = 2*value
        self.size = vector(self._size.x,d,d) # size will call addattr
        
class pyramid(standardAttributes):
    def __init__(self, **args):
        args['_default_size'] = vector(1,1,1)
        args['_objName'] = "pyramid"
        super(pyramid, self).setup(args)
        
class ellipsoid(standardAttributes):
    def __init__(self, **args):
        args['_default_size'] = vector(1,1,1)
        args['_objName'] = "ellipsoid"
        super(ellipoid, self).setup(args)
        
    @property
    def radius(self):
        return self._size.y/2
    @radius.setter
    def radius(self,value):
        d = 2*value
        self.size = vector(d,d,d) # size will call addattraddattr
        
class ring(standardAttributes):
    def __init__(self, **args):
        args['_default_size'] = vector(0.2,2.2,2.2)
        args['_objName'] = "ring"
        super(ring, self).setup(args)
        
    @property
    def thickness(self):
        return self._size.x/2
    @thickness.setter
    def thickness(self,value):
        R1 = self.radius
        self._size.x = 2*value
        self._size.y = self._size.z = 2*(R1+value)
        if not self._constructing:
            self.addattr('size')
        
    @property
    def radius(self):
        return (self._size.y-self._size.x)/2
    @radius.setter
    def radius(self,value):
        R2 = self.thickness
        self._size.y = self._size.z = 2*(value+R2)
        if not self._constructing:
            self.addattr('size')
    
    @property        ## override methods of parent class
    def axis(self):
        return self._axis
    @axis.setter
    def axis(self,value):
        if not isinstance(value, vector): raise TypeError('axis must be a vector')
        self._axis = value
        if not self._constructing:
            self.addattr('axis')
 
    @property        ## override methods of parent class
    def size(self):
        return self._size
    @size.setter
    def size(self,value):
        if not isinstance(value, vector): raise TypeError('axis must be a vector')
        self._size = value
        if not self._constructing:
            self.addattr('size') 
        
class arrow(standardAttributes): 
    def __init__(self, **args):
        args['_default_size'] = vector(1,0.2,0.2)
        args['_objName'] = "arrow"
        self._shaftwidth = 0
        self._headwidth = 0
        self._headlength = 0
        
        super(arrow, self).setup(args)

    @property
    def shaftwidth(self): 
        return self._shaftwidth
    @shaftwidth.setter
    def shaftwidth(self,value):
        self._shaftwidth = value
        if not self._constructing:
            self.addattr('shaftwidth')
        
    @property
    def headwidth(self): 
        return self._headwidth
    @headwidth.setter
    def headwidth(self,value):
        self._headwidth =value
        if not self._constructing:
            self.addattr('headwidth')
        
    @property
    def headlength(self): 
        return self._headlength
    @headlength.setter
    def headlength(self,value):
        self._headlength =value
        if not self._constructing:
            self.addattr('headlength')
        
class helix(standardAttributes):
    def __init__(self,**args):
        args['_objName'] = 'helix'
        args['_default_size'] = vector(1,2,2)
        self._coils = 5
        self._thickness = 1/20  ## radius/20
            
        super(helix, self).setup(args)
        
    @property
    def thickness(self): 
        return self._thickness
    @thickness.setter
    def thickness(self,value):
        self._thickness =value
        if not self._constructing:
            self.addattr('thickness')
            
    @property
    def coils(self): 
        return self._coils
    @coils.setter
    def coils(self,value):
        self._coils =value
        if not self._constructing:
            self.addattr('coils')   
            
    @property
    def radius(self):
        return self._size.y/2
    @radius.setter
    def radius(self,value):
        d = 2*value
        self.size = vector(self._size.x,d,d) # size will call addattr if appropriate
        
class curve(standardAttributes):
    def __init__(self,**args):
        args['_objName'] = "curve"
        args['_default_size'] = vector(1,1,1)
        self._origin = vector(0,0,0)  
        self._cpos = []  ## temporary list of dicts containing lists, not vectors, to be sent to commsend
        self._pts = []  ## cumulative list of dicts of the form {pos:vec, color=vec, radius=r, visible=T/F} python side
     
        pos = []  ## default
        if 'pos' in args:
            pos = args['pos']
            pos = self.parse_pos(pos)  ## resolve pos arguments into a list of vectors
            
        ptcolor = ptradius = ptvisible = ptretain = None
        if 'color' in args: ptcolor = args['color']
        if 'radius' in args: ptradius = args['radius']
        if 'visible' in args: ptvisible = args['visible']
        if 'retain' in args: ptretain = args['retain']
        tpos = []
        for p in pos:
            pt = {'pos': p}
            if ptcolor != None: pt['color'] = ptcolor
            if ptradius != None: pt['radius'] = ptradius
            if ptvisible != None: pt['visible'] = ptvisible
            if ptretain != None: pt['retain'] = ptretain
            self._pts.append(pt)
            tpos.append(p.value)
        args['pos'] = tpos
        super(curve, self).setup(args)
        
        #tpos = pos
        # while len(pos) > 0:
            # del pos[-1]


    def append(self, *args1, **args):
        c = None
        r = None
        vis = None
        ret = None
        if 'color' in args:
            c = args['color']
        if 'radius' in args:
            r = args['radius']
        if 'visible' in args:
            vis = args['visible']
        if 'retain' in args:
            ret = args['retain']
        if len(args1) > 0:
            tpos = self.parse_pos(args1)
        elif 'pos' in args:
            pos = args['pos']
            tpos = self.parse_pos(pos)  ## resolve pos arguments into a list
        if len(tpos) == 0:
            raise AttributeError("To append a point to a curve or points object, specify pos information.")
        for p in tpos:
            pt = {'pos':p}
            cp = {'pos':p.value}
            if c is not None:
                cp['color'] = c.value
                pt['color'] = c
            if r is not None: cp['radius'] = pt['radius'] = r
            if vis is not None: cp['visible'] = pt['visible'] = vis
            if ret is not None: cp['retain'] = pt['ret'] = ret
            self._pts.append(pt)
            self._cpos.append(cp)          
        self.addattr('_cpos')
        
    def clearData(self):
        while len( self._cpos ) > 0:
            del self._cpos[-1]
            
    
    def _on_origin_change(self):
        self.addattr('origin')

    @property
    def npoints(self):
        return len(self._pts)
    @npoints.setter
    def npoints(self,value):
        raise ValueError('npoints cannot be set')
                             
    def pop(self):
        if len(self._pts) == 0: return None
        val = self._pts[-1]
        self._pts = self._pts[0:-1]
        return val

    def point(self,N):
        if N >= len(self._pts) or (N < 0 and -N >= len(self.pts)):
            raise ValueError('N = {} is outside the bounds 0-{} of the curve points'.format(N, len(self._pos)))
        return self._pts[N]

    def clear(self):
        self._pts = []

    def shift(self):
        if len(self._pts) == 0: return None
        val = self._pts[0]
        self._pts = self._pts[1:]
        return val

    def unshift(self, pts):
        # process pts into a list; need to check whether pts is a list of positions or pts such as {pos:..., color...}
        gather = []
        for p in pts:
            gather.append({'pos':p, 'color':self._color, 'radius':self._radius, 'visible':self._visible})
        gather.extend(self._pts)
        self._pts = gather

    def splice(self, start, howmany, args): # args could be p1, p2, p3 or [p1, p2, p3]
        # process args into a list
        if howmany < 0:
            raise ValueError('You cannot delete a negative number of points'.format(howmany))
        if start >= len(self._pts) or (start < 0 and -start >= len(self._pts)):
            raise ValueError('The starting location, {}, is outside the bounds of the list of points'.format(start))
        if start >= 0:
            if start+howmany >= len(self._pts):
                raise ValueError('The starting position plus deletions is beyond the list of points'.format(howmany))
        else:
            if start+howmany >= 0:
                raise ValueError('The starting position plus deletions is beyond the list of points'.format(howmany))
        gather = self._pts[:start]
        for p in args:
            gather.append({'pos':p, 'color':self._color, 'radius':self._radius, 'visible':self._visible})
        gather.extend(self._pts[start+howmany:])
        self._pts = gather
    
    def modify(self, N, *arg1, **args):
        attrs = ['color', 'radius', 'visible']
        if N >= len(self._pts) or (N < 0 and -N >= len(self._pts)):
            raise ValueError('N = {} is outside the bounds 0-{} of the curve points'.format(N, len(self._pts)))
        p = self._pts[N]
        if len(arg1) == 1 and isinstance(arg1[0], vector):
            p['pos'] = arg1[0]
        else:
            for a in args:
                if a == 'x':
                    p['pos'].x = args[a]
                elif a == 'y':
                    p['pos'].y = args[a]
                elif a == 'z':
                    p['pos'].z = args[a]
                elif a in attrs:
                    p[a] = args[a]
        
    def parse_pos(self, *vars):
        ret = []
        if (isinstance(vars[0], list) or isinstance(vars[0], tuple)):
            if len(vars) == 1: # ([vector, vector, ....])
                for v in vars[0]:
                    if isinstance(v, vector):
                        ret.append(v)
                    else: raise AttributeError("Point pos must be a vector")
            else:
                raise AttributeError("Point pos is not a list or vectors")
        else:                           # (vector, vector, ....)
            for v in vars:
                if isinstance(v,vector): ret.append(v)
                else: raise AttributeError("Point pos data must be vectors")
        return ret
        
    @property
    def origin(self):
        return self._origin    
    @origin.setter
    def origin(self,value):
        self._origin.value = value
        if not self._constructing:
            self.addattr('origin')

     
    # def __del__(self):
        # pass

class gobj(baseObj):
    def setup(self, args):
        super(gobj, self).__init__()
    ## default values of shared attributes
        self._color = vector(0,0,0)
        self._graph = None
        self._plot = []
        objName = args['_objName']
        del args['_objName']
        self._constructing = True ## calls are from constructor
        
        argsToSend = [] ## send to GlowScript only attributes specified in constructor
                        ## default values will be used for others    

        ## process pos here   
        if 'pos' in args:
            postemp = args['pos'][:] ## make a copy
            self.plot(postemp)  ## call plot to resolve pos arguments into self._plot
            del args['pos']

        ## override default vector attributes        
        vectorAttributes = ['color', 'dot_color']        
        for a in vectorAttributes:
            if a in args:
                argsToSend.append(a)
                val = args[a]
                if isinstance(val, vector): setattr(self, '_'+a, val)
                else: raise AttributeError(a+' must be a vector')
                del args[a]
        
        ## override default scalar attributes
        for a,val in args.items():
            argsToSend.append(a)
            if a == 'graph':
                val = val.idx
            setattr(self, '_'+a, val)
                
        cmd = {"cmd": objName, "idx": self.idx, "guid": self.guid, 
           "attrs":[]}
           
        for a in argsToSend:
            aval = getattr(self,a)
            if isinstance(aval, vector):
                aval = aval.value
            cmd["attrs"].append({"attr":a, "value": aval})
            
        self._constructing = False
        self.appendcmd(cmd)        
         
    @property
    def color(self): return self._color
    @color.setter
    def color(self,val): 
        if not isinstance(val, vector): raise TypeError('color must be a vector')
        self._color = val
        self.addattr('color')
        
    @property
    def graph(self): return self._graph
    @graph.setter
    def graph(self,val):
        if not self._constructing:
            raise AttributeError('graph cannot be modified')
        else:
            self._graph = val.idx

    def __del__(self):
        cmd = {"cmd": "delete", "idx": self.idx}
        self.appendcmd(cmd)
        super(gcurve, self).__del__()
        
    def resolveargs(self, *vars):
        ret = []
        if isinstance(vars[0], list) or isinstance(vars[0],tuple):
            if not isinstance(vars[0][0], list) and not isinstance(vars[0][0],tuple):  # plot([x,y], [x,y])
                for v in vars:
                    if isinstance(v,tuple): v = list(v)
                    if isinstance(v, list) and len(v) == 2: ret.append(v)
                    else: raise AttributeError("Plot data must be 2-dimensional, like [x,y].")
            else:                           # plot([ [x,y], [x,y] ]
                for v in vars[0]:
                    if isinstance(v,tuple): v = list(v)
                    if isinstance(v, list) and len(v) == 2: ret.append(v)
                    else: raise AttributeError("Plot data must be 2-dimensional, like [x,y].")
        return ret

    def preresolve1(self, *args):
        if isinstance(args[0], list) or isinstance(args[0], tuple):
            if len(args) == 1 and len(args[0]) == 1: return self.resolveargs(args[0][0])
            a = []
            for arg in args[0]: a.append(arg)
            return self.resolveargs(a)
        else:
            return self.resolveargs(args) # plot(x,y)

    def preresolve2(self, args):
        if 'color' in args:
            raise AttributeError("Cannot currently change color in a plot statement.")
        if 'pos' in args:
            return self.resolveargs(args['pos'])
        else:
            raise AttributeError("Must be plot(x,y) or plot(pos=[x,y]) or plot([x,y]) or plot([x,y], ...) or plot([ [x,y], ... ])")

    def plot(self, *args1, **args2):
        if len(args1) > 0:
            p = self.preresolve1(args1)
        else:
            p = self.preresolve2(args2)
        self._plot.extend(p)
 #       if not self._constructing:
        self.addattr('_plot')
        
    def clearData(self):
        self._plot = []
        
class gcurve(gobj):
    def __init__(self, **args):
        args['_objName'] = "gcurve"
    ## default values of unshared attributes
        self._dot = False
        self._dot_color = vector(0,0,0)
        self._size = 8
        
        super(gcurve, self).setup(args)

    @property
    def size(self): return self._size
    @size.setter
    def size(self,val): 
        self._size = val
        self.addattr('size')
        
    @property
    def dot(self): return self._dot
    @dot.setter
    def dot(self,val): 
        self._dot = val
        self.addattr('dot')
        
    @property
    def dot_color(self): return self._dot_color
    @dot_color.setter
    def dot_color(self,val): 
        if not isinstance(val, vector): raise TypeError('dot_color must be a vector')
        self._dot_color = val
        self.addattr('dot_color')
        
class gdots(gobj):
    def __init__(self, **args):
        args['_objName'] = "gdots"
        self._size = 5
        super(gdots, self).setup(args)
       
    @property
    def size(self): return self._size
    @size.setter
    def size(self,val): 
        self._size = val
        self.addattr('size')
        
class gvbars(gobj):
    def __init__(self, **args):
        args['_objName'] = "gvbars"
        self._delta = 1
        super(gvbars, self).setup(args)
        
    @property
    def delta(self): return self._delta
    @delta.setter
    def delta(self,val): 
        self._delta = val
        self.addattr('delta')

class ghbars(gvbars):
    def __init__(self, **args):
        args['_objName'] = "ghbars"
        self._delta = 1
        super(ghbars, self).setup(args)


class graph(baseObj):  
    def __init__(self, **args):
        objName = 'graph'
        super(graph,self).__init__()
        
    ## default values
        self._width = 640
        self._height = 400
        self._foreground = vector(0,0,0)
        self._background = vector(1,1,1)
        self._title = ""
        self._xtitle = ""
        self._ytitle = ""
        argsToSend = []

        ## override default vector attributes        
        vectorAttributes = ['foreground', 'background']        
        for a in vectorAttributes:
            if a in args:
                argsToSend.append(a)
                val = args[a]
                if isinstance(val, vector): setattr(self, '_'+a, val)
                else: raise AttributeError(a+' must be a vector')
                del args[a]
        
        ## override default scalar attributes
        scalarAttributes = ['width', 'height', 'title', 'xtitle', 'ytitle']
        for a in scalarAttributes:
            if a in args:
                argsToSend.append(a)
                setattr(self, '_'+a, args[a])
                del args[a]
                
        # user defined attributes
        for a in args:
            setattr(self, '_'+a, args[a])

        cmd = {"cmd": objName, "idx": self.idx, "guid": self.guid, 
           "attrs":[]}
        
        ## send only args specified in constructor
        for a in argsToSend:
            aval = getattr(self,a)
            if isinstance(aval, vector):
                aval = aval.value
            cmd["attrs"].append({"attr":a, "value": aval})
            
        self.appendcmd(cmd)                
        
    @property
    def width(self): return self._width
    @width.setter
    def width(self,val): 
        self._width = val
        self.addattr('width')

    @property
    def height(self): return self._height
    @height.setter
    def height(self,val): 
        self._height = val
        self.addattr('height')

    @property
    def title(self): 
        return self._title
    @title.setter
    def title(self,val): 
        self._title = val
        self.addattr('title')              

    @property
    def xtitle(self): return self._xtitle
    @xtitle.setter
    def xtitle(self,val): 
        self._xtitle = val
        self.addattr('xtitle')

    @property
    def ytitle(self): return self._ytitle
    @ytitle.setter
    def ytitle(self,val): 
        self._ytitle = val
        self.addattr('ytitle')

    @property
    def foreground(self): return self._foreground
    @foreground.setter
    def foreground(self,val): 
        if not isinstance(val, vector): raise TypeError('foreground must be a vector')
        self._foreground = val
        self.addattr('foreground')

    @property
    def background(self): return self._background
    @background.setter
    def background(self,val): 
        if not isinstance(val,vector): raise TypeError('background must be a vector')
        self._background = val
        self.addattr('background')
    
#    def __del__(self):
#        cmd = {"cmd": "delete", "idx": self.idx}
#        self.appendcmd(cmd)
#        super(graph, self).__del__()

        
    

class faces(baseAttrs2):
    """see faces documentation at http://www.glowscript.org/docs/VPythonDocs/index.html"""    
    xs = np.array([],float)
    ys = np.array([],float)
    zs = np.array([],float)
    def __init__(self, pos=[], x=[], y=[], z=[], axis=(1.,0.,0.), radius=0., canvas=None, visible=True,
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

        super(faces, self).__init__(axis=axis, up=up, material=material, canvas=canvas, visible=visible, **kwargs)
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
               "attrs": [#{"attr": "pos", "value": self.pos.value},
                         #{"attr": "axis", "value": self.axis.value},
                         #{"attr": "size", "value": self.size.value},
                         #{"attr": "up", "value": self.up.value},
                         #{"attr": "color", "value": self.color},
                         #{"attr": "shininess", "value": self.shininess},
                         #{"attr": "emissive", "value": self.emissive},
                         #{"attr": "pnts", "value": [{"pos": [0, 0, 0]}, {"pos": [1, 0, 0]}]},
                         #{"attr": "pnts", "value": pntsa.tolist()},
                         {"attr": "pnts", "value": pnts},
                         {"attr": "radius", "value": self.radius},
                         {"attr": "canvas", "value": self.canvas.idx if self.canvas != None else canvas.get_selected().idx if canvas.get_selected() != None else -1}]}
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
        

class label(baseAttrs2):
    """see label documentation at http://www.glowscript.org/docs/VPythonDocs/index.html"""    
    
    def __init__(self, pos=(0.,0.,0.), x=0., y=0., z=0., color=(1.,1.,1.), red=1., green=1., blue=1., opacity=0.66, 
                 xoffset=20., yoffset=12., text="", font="sans", height=13, background=(0.,0.,0.),
                 border=5, box=True, line=True, linecolor=(0.,0.,0.), space=0., canvas=None, frame=None, visible=True, **kwargs):  
        # backgraound = scene.background   # default background color
        # color = scene.foreground  # default color
        super(label, self).__init__(pos=pos, x=x, y=y, z=z, color=color, red=red, green=green, blue=blue, opacity=opacity, 
                                    frame=frame, canvas=canvas, visible=visible, **kwargs)

        self._xoffset = xoffset
        self._yoffset = yoffset
        self._text = text
        self._font = font
        self._height = height
        self._background = background
        self._border = border
        self._box = box
        self._line = line
        self._linecolor = linecolor
        self._space = space
                
        cmd = {"cmd": "label", "idx": self.idx, "guid": self.guid, 
               "attrs": [{"attr": "pos", "value": self.pos.value},
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
                         {"attr": "canvas", "value": self.canvas.idx if self.canvas != None else canvas.get_selected().idx if canvas.get_selected() != None else -1}
                         ]}

        self.appendcmd(cmd)
        if (frame != None):
            frame.objects.append(self)
            frame.update_obj_list()
            
    @property
    def xoffset(self):
        return self._xoffset
    
    @xoffset.setter
    def xoffset(self,value):
        self._xoffset = value
        self.addattr('xoffset')

    @property
    def yoffset(self):
        return self._yoffset
    
    @yoffset.setter
    def yoffset(self,value):
        self._yoffset = value
        self.addattr('yoffset')

    @property
    def text(self):
        return self._text
    
    @text.setter
    def text(self,value):
        self._text = value
        self.addattr('text')

    @property
    def font(self):
        return self._font
    
    @font.setter
    def font(self,value):
        self._font = value
        self.addattr('font')

    @property
    def height(self):
        return self._height
    
    @height.setter
    def height(self,value):
        self._height = value
        self.addattr('height')

    @property
    def background(self):
        return self._background
    
    @background.setter
    def background(self,value):
        self._background = value
        self.addattr('background')

    @property
    def border(self):
        return self._border
    
    @border.setter
    def border(self,value):
        self._border = value
        self.addattr('border')

    @property
    def box(self):
        return self._box
    
    @box.setter
    def box(self,value):
        self._box = value
        self.addattr('box')

    @property
    def line(self):
        return self._line
    
    @line.setter
    def line(self,value):
        self._line = value
        self.addattr('line')

    @property
    def linecolor(self):
        return self._linecolor
    
    @linecolor.setter
    def linecolor(self,value):
        self._linecolor = value
        self.addattr('linecolor')

    @property
    def space(self):
        return self._space
    
    @space.setter
    def space(self,value):
        self._space = value
        self.addattr('space')

             
class frame(baseAttrs):
    """see frame documentation at http://www.glowscript.org/docs/VPythonDocs/index.html"""    

    objects = []
    def __init__(self, pos=(0.,0.,0.), x=0., y=0., z=0., axis=(1.,0.,0.), canvas=None, visible=True,
                 up=(0.,1.,0.), color=(1.,1.,1.), red=1., green=1., blue=1., **kwargs):
        super(frame, self).__init__(pos=pos, x=x, y=y, z=z, axis=axis, up=up, color=color, red=red, green=green, blue=blue, 
                                    canvas=canvas,visible=visible,**kwargs)
        object.__setattr__(self, 'objects', [])
        cmd = {"cmd": "compound", "idx": self.idx, "guid": self.guid,
               "attrs": [{"attr": "pos", "value": self.pos.value},
                         {"attr": "axis", "value": self.axis.value},
                         {"attr": "up", "value": self.up.value},
                         {"attr": "color", "value": self.color},
                         {"attr": "visible", "value": self.visible},
                         {"attr": "canvas", "value": self.canvas.idx if self.canvas != None else canvas.get_selected().idx if canvas.get_selected() != None else -1}]}
        
        self.appendcmd(cmd)
    
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
               "attrs": [{"attr": "pos", "value": self.pos.value},
                         {"attr": "axis", "value": self.axis.value},
                         {"attr": "up", "value": self.up.value},
                         {"attr": "color", "value": self.color},
                         {"attr": "obj_idxs", "value": obj_idxs},
                         {"attr": "canvas", "value": self.canvas.idx if self.canvas != None else canvas.get_selected().idx if canvas.get_selected() != None else -1}]}
        
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
        if normal.mag == 0.:
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
    # visible = True
    # foreground = (1,1,1)
    # background = (0,0,0)
    # ambient = (0.2,0.2,0.2)  ##color.gray(0.2)
    # stereo = 'redcyan'
    # stereodepth = 1.
    # x = 0.
    # y = 0.
    # height = 500
    # width = 800
    # title = ""
    # fullscreen = False
    # exit = True
    # center = vector(0,0,0)
    # autocenter = True
    # forward = vector(0,0,-1)
    # fov = math.pi/3.
    # range = (1.,1.,1.)
    # scale = (1.,1.,1.)
    # up = vector(0.,1.,0.)
    # autoscale = True
    # userzoom = True
    # userspin = True
    lights = []
    objects = []

    def __init__(self, visible=True, foreground=(1,1,1), background=(0,0,0), ambient=(0.2,0.2,0.2), stereo='redcyan',
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
            
        self._objects = []
        self._visible = visible
        self._foreground = foreground
        self._background = background
        self._ambient = ambient
        self._stereo = stereo
        self._stereodepth = stereodepth
        self._x = x
        self._y = y
        self._height = height
        self._width = width
        self._title = title
        self._fullscreen = fullscreen
        self._exit = exit
        self._autocenter = autocenter
        self._forward = vector(forward) if type(forward) in [tuple, list, np.ndarray] else forward
        self._fov = fov
        self._range = vector(range) if type(range) is tuple else range
        self._scale = vector(scale) if type(scale) is tuple else scale
        self._up = vector(up) if type(up) in [tuple, list, np.ndarray] else up
        self._center = vector(center) if type(center) in [tuple, list, np.ndarray] else center
        self._autoscale = autoscale
        self._userzoom = userzoom
        self._userspin = userspin
        self._mouse = Mouse()
        
        self._forward.on_change = self._on_forward_change
        self._range.on_change = self._on_range_change
        self._scale.on_change = self._on_scale_change
        self._up.on_change = self._on_up_change
        self._center.on_change = self._on_center_change

    @property
    def mouse(self):
        return self._mouse
    
    @mouse.setter
    def mouse(self,value):
        self._mouse = value

        
    @property
    def visible(self):
        return self._visible
    
    @visible.setter
    def visible(self,value):
        self._visible = value
        self.addattr('visible')

    @property
    def foreground(self):
        return self._foreground
    
    @foreground.setter
    def foreground(self,value):
        self._foreground = value

    @property
    def background(self):
        return self._background
    
    @background.setter
    def background(self,value):
        self._background = value
        self.addattr('background')

    @property
    def ambient(self):
        return self._ambient
    
    @ambient.setter
    def ambient(self,value):
        self._ambient = value
        self.addattr('ambient')

    @property
    def stereo(self):
        return self._stereo
    
    @stereo.setter
    def stereo(self,value):
        self._stereo = value

    @property
    def stereodepth(self):
        return self._stereodepth
    
    @stereodepth.setter
    def stereo(self,value):
        self._stereodepth = value

    @property
    def x(self):
        return self._x
    
    @x.setter
    def x(self,value):
        self._x = value

    @property
    def y(self):
        return self._y
    
    @y.setter
    def y(self,value):
        self._y = value

    @property
    def height(self):
        return self._height
    
    @height.setter
    def height(self,value):
        self._height = value
        self.addattr('height')

    @property
    def width(self):
        return self._width
    
    @width.setter
    def width(self,value):
        self._width = value
        self.addattr('width')

    @property
    def title(self):
        return self._title
    
    @title.setter
    def title(self,value):
        self._title = value

    @property
    def fullscreen(self):
        return self._fullscreen
    
    @fullscreen.setter
    def fullscreen(self,value):
        self._fullscreen = value

    @property
    def exit(self):
        return self._exit
    
    @exit.setter
    def exit(self,value):
        self._exit = value

    @property
    def autocenter(self):
        return self._autocenter
    
    @autocenter.setter
    def autocenter(self,value):
        self._autocenter = value

    @property
    def center(self):
        return self._center
    
    @center.setter
    def center(self,value):
        self._center = vector(value) if type(value) in [tuple, list, np.ndarray] else value
        self.addattr('center')

    @property
    def forward(self):
        return self._forward
    
    @forward.setter
    def forward(self,value):
        self._forward = vector(value) if type(value) in [tuple, list, np.ndarray] else value
        self.addattr('forward')

    @property
    def fov(self):
        return self._fov
    
    @fov.setter
    def fov(self,value):
        self._fov = value
        self.addattr('fov')

    @property
    def range(self):
        return self._range
    
    @range.setter
    def range(self,value):
        if isinstance(value, (int, long, float)):
            value = (value,value,value)
        self._range = vector(value) if type(value) is tuple else value
        if (self._range[0] != 0.):
            self._scale[0] = 1./self._range[0] 
        self.addattr('range')

    @property
    def scale(self):
        return self._scale
    
    @scale.setter
    def scale(self,value):
        if isinstance(value, (int, long, float)):
            value = (value,value,value)
        self._scale = vector(value) if type(value) is tuple else value
        if (self._scale[0] != 0.):
            self._range[0] = 1./self._scale[0] 
        self.addattr('scale')

    @property
    def up(self):
        return self._up
    
    @up.setter
    def up(self,value):
        self._up = vector(value) if type(value) in [tuple, list, np.ndarray] else value
        self.addattr('up')

    @property
    def autoscale(self):
        return self._autoscale
    
    @autoscale.setter
    def autoscale(self,value):
        self._autoscale = value
        self.addattr('autoscale')

    @property
    def userzoom(self):
        return self._userzoom
    
    @userzoom.setter
    def userzoom(self,value):
        self._userzoom = value
        self.addattr('userzoom')

    @property
    def userspin(self):
        return self._userspin
    
    @userspin.setter
    def userspin(self,value):
        self._userspin = value
        self.addattr('userspin')


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

    def _on_forward_change(self):
        self.addattr('forward')
        
    def _on_range_change(self):
        self.addattr('range')
        
    def _on_scale_change(self):
        self.addattr('scale')
        
    def _on_up_change(self):
        self.addattr('up')
        
    def _on_center_change(self):
        self.addattr('center')
        
    
class canvas(sceneObj):
    sceneCnt = 0
    selected_canvas = -1
    canvases = []
    canvas_idx = 0
    def __init__(self, visible=True, background=vector(0,0,0), ambient=vector(0.2,0.2,0.2), 
                    height=480, width=640, title=" ", fullscreen=False,
                    exit=True, center=vector(0.,0.,0.), forward=vector(0.,0.,-1.), fov=math.pi/3.,
                    range=1., scale=1., up=vector(0.,1.,0.), autoscale=True, userzoom=True, userspin=True, **kwargs):
        super(canvas, self).__init__(visible=visible, background=background, ambient=ambient,
                                     height=height, width=width, title=title, 
                                     fullscreen=fullscreen,
                                     exit=exit, center=center, forward=forward, fov=fov,
                                     range=range, scale=scale, up=up, autoscale=autoscale, userzoom=userzoom, **kwargs)
        object.__setattr__(self, 'canvas_index', canvas.canvas_idx)
        object.__setattr__(self, 'sceneId', "scene%d" % (canvas.sceneCnt))
        canvas.canvases.append(self)
        canvas.selected_canvas = canvas.canvas_idx
        canvas.canvas_idx += 1
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
                         {"attr": "background", "value": self.background.value},
                         {"attr": "ambient", "value": self.ambient.value},
                         {"attr": "height", "value": self.height},
                         {"attr": "width", "value": self.width},
                         {"attr": "forward", "value": self.forward.value},
                         {"attr": "fov", "value": self.fov},
                         {"attr": "range", "value": self.range[0]},
                         {"attr": "up", "value": self.up.value},
                         {"attr": "center", "value": self.center.value},
                         {"attr": "autoscale", "value": self.autoscale},
                         {"attr": "userzoom", "value": self.userzoom},
                         {"attr": "userspin", "value": self.userspin}
                         ]}
        self.appendcmd(cmd)
        
    def select(self):
        canvas.selected_canvas = self.canvas_index

    @classmethod
    def get_selected(cls):
        return cls.canvases[cls.selected_canvas] if cls.selected_canvas >= 0 else None

    def _ipython_display_(self):
        display_html('<div id="glowscript2" ><div id="glowscript" class="glowscript"></div></div>', raw=True)
        cmd = {"cmd": "redisplay", "idx": self.idx, "sceneId": self.sceneId}        
        self.appendcmd(cmd)


class defaultscene(sceneObj):

    def __init__(self):
        super(defaultscene, self).__init__()
        object.__setattr__(self, 'sceneId', "scene0")
        cmd = {"cmd": "scene", "idx": self.idx}        
##        cmd = {"cmd": "canvas", "idx": self.idx}        
        self.appendcmd(cmd)
        
    
    def _ipython_display_(self):
        display_html('<div id="glowscript2" ><div id="glowscript" class="glowscript"></div></div>', raw=True)
        cmd = {"cmd": "redisplay", "idx": self.idx, "sceneId": self.sceneId}        
        self.appendcmd(cmd)
    
class local_light(baseObj):
    """see lighting documentation at http://www.glowscript.org/docs/VPythonDocs/index.html"""
    def __init__(self, pos=(0.,0.,0.), color=(1.,1.,1.), frame=None, canvas=None, **kwargs):
        super(local_light, self).__init__(**kwargs)
                
        self._pos = vector(pos) if type(pos) in [tuple, list, np.ndarray] else pos
        self._color = color
        self._canvas = canvas
        self._frame = frame

        cmd = {"cmd": "local_light", "idx": self.idx, "guid": self.guid,
               "attrs": [{"attr": "pos", "value": self.pos.value},
                         {"attr": "color", "value": self.color},
                         {"attr": "canvas", "value": self.canvas.idx if self.canvas != None else canvas.get_selected().idx if canvas.get_selected() != None else -1}
                         ]}
        if (canvas.get_selected() != None):
            canvas.get_selected().lights.append(self)
        self.appendcmd(cmd)
            
    @property
    def pos(self):
        return self._pos
    
    @pos.setter
    def pos(self,value):
        self._pos.value = value
        self.addattr('pos')

    @property
    def color(self):
        return self._color
    
    @color.setter
    def color(self,value):
        self._color = value
        self.addattr('color')

    @property
    def canvas(self):
        return self._canvas
    
    @canvas.setter
    def canvas(self,value):
        self._canvas = value

    @property
    def frame(self):
        return self._frame
    
    @frame.setter
    def frame(self,value):
        self._frame = value

        
class distant_light(baseObj):
    """see lighting documentation at http://www.glowscript.org/docs/VPythonDocs/index.html"""
    def __init__(self, direction=(0.,0.,0.), color=(1.,1.,1.), frame=None, canvas=None, **kwargs):
        super(distant_light, self).__init__(**kwargs)
        
        self._direction = vector(direction) if type(direction) in [tuple, list, np.ndarray] else direction
        self._color = color
        self._canvas = canvas
        self._frame = frame

        cmd = {"cmd": "distant_light", "idx": self.idx,  "guid": self.guid,
               "attrs": [{"attr": "direction", "value": self.direction.value},
                         {"attr": "color", "value": self.color},
                         {"attr": "canvas", "value": self.canvas.idx if self.canvas != None else canvas.get_selected().idx if canvas.get_selected() != None else -1}
                         ]}
        if (canvas.get_selected() != None):
            canvas.get_selected().lights.append(self)
        self.appendcmd(cmd)
        
    @property
    def direction(self):
        return self._direction
    
    @direction.setter
    def pos(self,value):
        self._direction.value = value
        self.addattr('direction')

    @property
    def color(self):
        return self._color
    
    @color.setter
    def color(self,value):
        self._color = value
        self.addattr('color')

    @property
    def canvas(self):
        return self._canvas
    
    @canvas.setter
    def canvas(self,value):
        self._canvas = value

    @property
    def frame(self):
        return self._frame
    
    @frame.setter
    def frame(self,value):
        self._frame = value


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
##        scene = canvas()
