from __future__ import print_function, division, absolute_import
import colorsys
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
import inspect
from time import clock
import os
import datetime, threading
import collections
import copy
import sys
import weakref
from random import random

# To print immediately, do this:
#    print(.....)
#    sys.stdout.flush()

import platform

version = ['0.2.0b15', 'jupyter']
GSversion = ['2.1', 'glowscript']

glowlock = threading.Lock()

class RateKeeper2(RateKeeper):
    
    def __init__(self, interactPeriod=INTERACT_PERIOD, interactFunc=simulateDelay):
        self.active = False
        self.send = False
        self.sz = 0
        self.sendcnt = 0
        self.rval = 1
        super(RateKeeper2, self).__init__(interactPeriod=interactPeriod, interactFunc=self.sendtofrontend)

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

package_dir = os.path.dirname(__file__)
if IPython.__version__ >= '4.0.0' :
    notebook.nbextensions.install_nbextension(path = package_dir+"/data/jquery-ui.custom.min.js",overwrite = True,user = True,verbose = 0)
    notebook.nbextensions.install_nbextension(path = package_dir+"/data/glow."+GSversion[0]+".min.js",overwrite = True,user = True,verbose = 0)
    notebook.nbextensions.install_nbextension(path = package_dir+"/data/glowcomm.js",overwrite = True,user = True,verbose = 0)
elif IPython.__version__ >= '3.0.0' :
    IPython.html.nbextensions.install_nbextension(path = package_dir+"/data/jquery-ui.custom.min.js",overwrite = True,user = True,verbose = 0)
    IPython.html.nbextensions.install_nbextension(path = package_dir+"/data/glow."+GSversion[0]+".min.js",overwrite = True,user = True,verbose = 0)
    IPython.html.nbextensions.install_nbextension(path = package_dir+"/data/glowcomm.js",overwrite = True,user = True,verbose = 0)
else:
    IPython.html.nbextensions.install_nbextension(files = [package_dir+"/data/jquery-ui.custom.min.js",package_dir+"/data/glow."+GSversion[0]+".min.js",package_dir+"/data/glowcomm.js"],overwrite=True,verbose=0)


object_registry = {}    ## idx -> instance

class baseObj(object):
    txtime = 0.0
    idx = 0
    qSize = 512
    qTime = 0.034
    glow = None
    cmds = collections.deque()
    updtobjs = set()
    objCnt = 0
    
    def __init__(self, **kwargs):
        idx = baseObj.objCnt   ## an integer
        object_registry[idx] = self 
        object.__setattr__(self, 'idx', idx)
        object.__setattr__(self, 'attrsupdt', set())
        object.__setattr__(self, 'methodsupdt', [] )
        if kwargs is not None:
            for key, value in kwargs.items():
                object.__setattr__(self, key, value)
        baseObj.incrObjCnt()
        
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
        self.attrsupdt.add(name)
        baseObj.updtobjs.add(self.idx)
        
    def addmethod(self, name, data):
        self.methodsupdt.append( [name, data] )
        baseObj.updtobjs.add(self.idx)
            
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

_sent = False  ## set to True when commsend completes; needed for canvas.waitfor

def commsend():
    global next_call, commcmds, updtobjs2, glowlock, rate, _sent
    _sent = False
    with glowlock:
        try:
            if baseObj.glow != None:
                if (len(baseObj.cmds) > 0) and (not rate.active):
                    a = copy.copy(baseObj.cmds)
                    L = len(a)
                    baseObj.glow.comm.send(list(a))  # Send constructors to glowcomm
                    a.clear()
                    while L > 0:
                        del baseObj.cmds[0]
                        L -= 1 

                L = rate.sz if (rate.send == True) else 0
                
                if L > 0:
                    rate.sendcnt += 1
                    thresh = math.ceil(30.0/rate.rval) * 2 + 1
                    if (rate.sendcnt > thresh ):
                        rate.send = False
                        rate.sz = 0
                        rate.active = False       # rate fnc no longer appears to be being called
                else:
                    rate.sendcnt = 0
                if len(updtobjs2) == 0:
                    updtobjs2 = baseObj.updtobjs.copy()
                    baseObj.updtobjs.clear()
                if L < baseObj.qSize:
                    # print('commsend stuff to update', baseObj.updtobjs)
                    while updtobjs2:
                        idx = updtobjs2.pop()
                        ob = object_registry[idx]
                        #print('commsend object', ob.attrsupdt, ob.methodsupdt)
                        #sys.stdout.flush()
                        if  (ob is not None) and (hasattr(ob,'attrsupdt')) and (len(ob.attrsupdt) > 0 ):
                            while ob.attrsupdt:
                                if 'method' in commcmds[L]: del commcmds[L]['method']
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
                                        elif attr in ['axis','pos', 'up','color', 
                                                      'center','forward', 'direction', 'ambient',
                                                      'texpos', 'normal', 'bumpaxis',
                                                      'background','origin', 'trail_color', 'dot_color', 'size']:
                                            attrvalues = attrval.value
                                            if attrvalues is not None:
                                                commcmds[L]['idx'] = ob.idx
                                                commcmds[L]['attr'] = attr
                                                commcmds[L]['val'] = attrvalues
                                        elif attr in ['v0', 'v1', 'v2', 'v3']:
                                            commcmds[L]['idx'] = ob.idx
                                            commcmds[L]['attr'] = attr
                                            commcmds[L]['val'] = attrval.idx
                                        else:
                                            commcmds[L]['idx'] = ob.idx
                                            commcmds[L]['attr'] = attr
                                            commcmds[L]['val'] = attrval
                                        L += 1
                                        if L >= baseObj.qSize:
                                            if (len(ob.attrsupdt) > 0):
                                                updtobjs2.add(ob.idx)
                                            break
                        if (ob is not None) and (hasattr(ob,'methodsupdt')) and (len(ob.methodsupdt) > 0 ):
                            for m in ob.methodsupdt:
                                if 'attr' in commcmds[L]: del commcmds[L]['attr']
                                method = m[0]
                                data = m[1]
                                commcmds[L]['idx'] = ob.idx
                                commcmds[L]['method'] = method
                                commcmds[L]['val'] = data  
                                #print('commsend methods', ob.idx, method, data)
                                #sys.stdout.flush()
                                L += 1
                                # if L >= baseObj.qSize:   ## put this in
                                    # if (len(ob.methodsupdt) > 0):
                                        # updtobjs2.add(ob.idx)
                                    # break
                            while len(ob.methodsupdt) > 0:
                                del ob.methodsupdt[-1]
                        if L >= baseObj.qSize:
                            #L = 0
                            break
                if L > 0:
                    if not rate.active:
                        L = L if (L <= baseObj.qSize) else baseObj.qSize
                        req = []
                        for item in commcmds[:L]:
                            req.append(item.copy())
                        baseObj.glow.comm.send(req)  # Send attributes and methods to glowcomm
                    else:
                        rate.sz = L if (L <= baseObj.qSize) else baseObj.qSize
                        rate.send = True
#                else:
#                    baseObj.glow.comm.send([]) # make sure canvas updates sent from glowcomm

        finally:
            next_call = next_call+rate.interactionPeriod
            tmr = next_call - time.time()
            if tmr < 0.0:
                tmr = rate.interactionPeriod
                next_call = time.time()+tmr
            threading.Timer(tmr, commsend ).start()
            _sent = True
    
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

##object_registry = {}    ## idx -> instance        
    def handle_msg(self, msg):
        evt = msg['content']['data']['arguments'][0]
        cvs = object_registry[evt['canvas']]
        cvs.handle_event(evt)

    def handle_close(self, data):
        print ("Comm closed")

if IPython.__version__ >= '3.0.0' :
    get_ipython().kernel.comm_manager.register_target('glow', GlowWidget)
else:
    get_ipython().comm_manager.register_target('glow', GlowWidget)   
display(Javascript("""require.undef("nbextensions/jquery-ui.custom.min");"""))
display(Javascript('require.undef("nbextensions/glow.'+GSversion[0]+'.min");'))
display(Javascript("""require.undef("nbextensions/glowcomm");"""))
display(Javascript("""require(["nbextensions/glowcomm"], function(){console.log("glowcomm loaded");})"""))
            
get_ipython().kernel.do_one_iteration()

class vector(object):
    'vector class'
    
    @staticmethod 
    def random():
        return vec(-1 + 2*random(), -1 + 2*random(), -1 + 2*random())

    def __init__(self, *args):
        if len(args) == 3:
            self._x = float(args[0]) # make sure it's a float; could be numpy.float64
            self._y = float(args[1])
            self._z = float(args[2])
        elif len(args) == 1 and isinstance(args[0], vector): # make a copy of a vector
            other = args[0]
            self._x = other._x
            self._y = other._y
            self._z = other._z
        else:
            raise TypeError('A vector needs 3 components.')
        
    def __str__(self):
        return '<%f, %f, %f>' % (self._x, self._y, self._z)
   
    def __repr__(self):
        return '<%f, %f, %f>' % (self._x, self._y, self._z)
   
    def __add__(self,other):
        return vector(self._x + other._x, self._y + other._y, self._z + other._z)
    
    def __sub__(self,other):
        return vector(self._x - other._x, self._y - other._y, self._z - other._z)
    
    def __mul__(self, other):
        if isinstance(other, (int, long, float)):
            return vector(self._x * other, self._y * other, self._z * other)
        raise TypeError('a vector can only be multiplied by a scalar')
    
    def __rmul__(self, other):
        if isinstance(other, (int, long, float)):
            return vector(self._x * other, self._y * other, self._z * other)
        raise TypeError('a vector can only be multiplied by a scalar')

    def __div__(self, other):
        if isinstance(other, (int, long, float)):
            return vector(self._x / other, self._y / other, self.vz / other)
        raise TypeError('a vector can only be divided by a scalar')
    
    def __truediv__(self, other):
        if isinstance(other, (int, long, float)):
            return vector(self._x / other, self._y / other, self._z / other)
        raise TypeError('a vector can only be divided by a scalar')

    def __neg__(self):
        return vector(-1.*self._x, -1.*self._y, -1.*self._z)
        
    def norm(self):
        smag = self.mag
        if (smag > 0.):
            return self / smag
        else:
            return vector(0.,0.,0.)

    def dot(self,other):
        return ( self._x*other._x + self._y*other._y + self._z*other._z )

    def cross(self,other):
        return vector( self._y*other._z-self._z*other._y, 
                       self._z*other._x-self._x*other._z,
                       self._x*other._y-self._y*other._x )

    def proj(self,other):
        normB = other.norm()
        return self.dot(normB) * normB
        
    def equals(self,other):
        return self._x == other._x and self._y == other._y and self._z == other._z

    def comp(self,other):  ## result is a scalar
        normB = other.norm()
        return self.dot(normB)

    def diff_angle(self, other):
        a = self.norm().dot(other.norm())
        if a > 1:  # avoid roundoff problems
            return 0
        if a < -1:
            return math.pi
        return math.acos(a)
        
    def rotate(self,angle = 0., axis = None):
        if axis == None:
            u = vector(0,0,1)
        else:
            u = norm(axis)
        c = math.cos(angle)
        s = math.sin(angle)
        t = 1.0 - c
        x = u.x
        y = u.y
        z = u.z
        sx = self.x
        sy = self.y
        sz = self.z
        m11 = t*x*x+c
        m12 = t*x*y-z*s
        m13 = t*x*z+y*s
        m21 = t*x*y+z*s
        m22 = t*y*y+c
        m23 = t*y*z-x*s
        m31 = t*x*z-y*s
        m32 = t*y*z+x*s
        m33 = t*z*z+c
        return vector( (m11*sx + m12*sy + m13*sz),
                    (m21*sx + m22*sy + m23*sz),
                    (m31*sx + m32*sy + m33*sz) )

    @property
    def value(self):  ## attribute vectors
        return [self._x, self._y, self._z]
    @value.setter
    def value(self,other):  ## ensures a copy; other is a vector
        self._x = other._x
        self._y = other._y
        self._z = other._z
    
    @property
    def x(self):
        return self._x
    @x.setter
    def x(self,value):
        self._x = value
        self.on_change()
    
    @property
    def y(self):
        return self._y
    @y.setter
    def y(self,value):
        self._y = value
        self.on_change()
    
    @property
    def z(self):
        return self._z
    @z.setter
    def z(self,value):
        self._z = value
        self.on_change()

    @property
    def mag(self):
        return math.sqrt(self._x**2+self._y**2+self._z**2)
    @mag.setter
    def mag(self,value):
        normA = self.norm()
        self._x = value * normA._x
        self._y = value * normA._y
        self._z = value * normA._z
        self.on_change()

    @property
    def mag2(self):
        return self._x**2+self._y**2+self._z**2
    @mag2.setter
    def mag2(self,value):
        normA = self.norm()
        v = math.sqrt(value)
        self._x = v * normA._x
        self._y = v * normA._y
        self._z = v * normA._z
        self.on_change()
     
    def on_change(self):
        pass

def mag(A):
    return A.mag

def mag2(A):
    return A.mag2

def norm(A):
    return A.norm()

def dot(A,B):
    return A.dot(B)

def cross(A,B):
    return A.cross(B)

def proj(A,B):
    return A.proj(B)

def comp(A,B):
    return A.comp(B)

def diff_angle(A,B):
    return A.diff_angle(B)
                            
def rotate(A,angle = 0., axis = None):
    return A.rotate(angle,axis)

class color(object):
    black = vector(0,0,0)
    white = vector(1,1,1)

    red = vector(1,0,0)
    green = vector(0,1,0)
    blue = vector(0,0,1)

    yellow = vector(1,1,0)
    cyan = vector(0,1,1)
    magenta = vector(1,0,1)

    orange = vector(1,0.6,0)

    @classmethod
    def gray(cls,luminance):
      return vector(luminance,luminance,luminance)

    @classmethod
    def rgb_to_hsv(cls,v):
      T = [v.x, v.y, v.z]
      c = colorsys.rgb_to_hsv(*T)
      return vector(c[0], c[1], c[2])

    @classmethod
    def hsv_to_rgb(cls,v):
      T = [v.x, v.y, v.z]
      c = colorsys.hsv_to_rgb(*T)
      return vector(c[0], c[1], c[2])

    @classmethod
    def rgb_to_grayscale(cls,v):
      luminance = 0.21*v.x + 0.71*v.y + 0.07*v.z
      return vector(luminance, luminance, luminance)

vec = vector # synonyms in GlowScript
  
class textures(object):
    flower = ":flower_texture.jpg"
    granite=":granite_texture.jpg"
    gravel=":gravel_texture.jpg"
    earth=":earth_texture.jpg"
    metal=":metal_texture.jpg"
    rock=":rock_texture.jpg"
    rough=":rough_texture.jpg"
    rug=":rug_texture.jpg"
    stones=":stones_texture.jpg"
    stucco=":stucco_texture.jpg"
    wood=":wood_texture.jpg"
    wood_old=":wood_old_texture.jpg"
    
class bumpmaps(object):
    gravel=":gravel_bumpmap.jpg"
    rock=":rock_bumpmap.jpg"
    stones=":stones_bumpmap.jpg"
    stucco=":stucco_bumpmap.jpg"
    wood_old=":wood_old_bumpmap.jpg"

class standardAttributes(baseObj):
# vector-no-interactions, vector-interactions, scalar-no-interactions, scalar-interactions

    attrLists = {'box':[['pos', 'up', 'color', 'trail_color'], 
                        ['axis', 'size'],
                        ['visible', 'opacity','shininess', 'emissive',  
                         'make_trail', 'trail_type', 'interval', 
                         'retain', 'trail_color', 'trail_radius', 'texture', 'pickable'],
                        ['red', 'green', 'blue','length', 'width', 'height']],
                 'sphere':[['pos', 'up', 'color', 'trail_color'], 
                        ['axis', 'size'],
                        ['visible', 'opacity','shininess', 'emissive',  
                         'make_trail', 'trail_type', 'interval', 
                         'retain', 'trail_color', 'trail_radius', 'texture', 'pickable'],
                        ['red', 'green', 'blue','length', 'width', 'height', 'radius']],                        
                 'arrow':[['pos', 'up', 'color', 'trail_color'],
                         ['axis', 'size'],
                         ['visible', 'opacity',
                          'shininess', 'emissive', 'texture', 'frame', 'material',
                          'make_trail', 'trail_type', 'interval', 
                          'retain', 'trail_color', 'trail_radius', 'texture',
                          'shaftwidth', 'headwidth', 'headlength', 'pickable'],
                         ['red', 'green', 'blue','length', 'width', 'height']],
                 'ring':[['pos', 'up', 'color', 'trail_color', 'axis', 'size'],  
                        [],
                        ['visible', 'opacity','shininess', 'emissive', 
                         'make_trail', 'trail_type', 'interval', 
                         'retain', 'trail_color', 'trail_radius', 'texture', 'pickable'],
                        ['red', 'green', 'blue','length', 'width', 'height', 'thickness']],                       
                 'helix':[['pos', 'up', 'color', 'trail_color'],
                         ['axis', 'size'],
                         ['visible', 'opacity','shininess', 'emissive', 
                         'make_trail', 'trail_type', 'interval', 
                         'retain', 'trail_color', 'trail_radius', 'coils', 'thickness', 'pickable'],
                         ['red', 'green', 'blue','length', 'width', 'height']],
                 'curve':[['origin', 'up', 'color'],  
                         ['axis', 'size'],
                         ['visible', 'shininess', 'emissive', 'radius', 'retain', 'pickable'],
                         ['red', 'green', 'blue','length', 'width', 'height']],
                 'points':[['color'],  
                         [],
                         ['visible', 'shininess', 'emissive', 'radius', 'retain'],
                         ['red', 'green', 'blue']],
                 'label':[['pos', 'color', 'background', 'linecolor'],  
                         [],
                         ['visible', 'text', 'xoffset', 'yoffset', 'font', 'height', 'opacity', 
                           'border', 'line', 'box', 'space'],
                         []],
                 'local_light':[['pos', 'color'],  
                         [],
                         ['visible'],
                         []],
                 'distant_light':[['direction', 'color'],  
                         [],
                         ['visible'],
                         []],
                 'compound':[['pos', 'up', 'color', 'trail_color'], 
                         ['axis', 'size'],
                         ['visible', 'opacity','shininess', 'emissive',  
                         'make_trail', 'trail_type', 'interval', 'texture', 
                         'retain', 'trail_color', 'trail_radius', 'obj_idxs', 'pickable'],
                         ['red', 'green', 'blue', 'length', 'width', 'height']],
                 'vertex':[['pos', 'color', 'normal', 'bumpaxis', 'texpos'], 
                        [],
                        ['visible', 'opacity','shininess', 'emissive'],
                        ['red', 'green', 'blue']],
                 'triangle': [ [],
                        [],
                        ['texture', 'bumpmap', 'visible', 'pickable'],
                        ['v0', 'v1', 'v2'] ],
                 'quad': [ [],
                        [],
                        ['texture', 'bumpmap', 'visible', 'pickable'],
                        ['v0', 'v1', 'v2', 'v3'] ]
                        }
 
    attrLists['pyramid'] = attrLists['box']
    attrLists['cylinder'] = attrLists['sphere']
    attrLists['cone'] = attrLists['sphere']
    attrLists['ellipsoid'] = attrLists['sphere']
    

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
        defaultSize = args['_default_size'] 
        if defaultSize is not None: # is not points or vertex or triangle or quad 
            self._size = defaultSize  ## because VP differs from JS
            del args['_default_size']        
        self._texture = None
        self._opacity = 1.0
        self._shininess = 0.6
        self._emissive = False      
        self._make_trail = False
        self._trail_type = 'curve'
        self._trail_color = self._color
        self._interval = 1
        self._retain = -1
        self._trail_radius = None  # set by default after size set
        self._canvas = None
        if 'canvas' in args:  ## converted to idx below
            self._canvas = args['canvas']  
        self._visible = True
        self._frame = None
        self._size_units = 'pixels'
        self._texture = None
        self._pickable = True
        
        argsToSend = []  ## send to GlowScript only attributes specified in constructor
        
    ## override defaults for vector attributes without side effects 
        attrs = standardAttributes.attrLists[objName][0]
        for a in attrs:
            if a in args:
                argsToSend.append(a)
                val = args[a]
                if isinstance(val, vector): setattr(self, '_'+a, vector(val))  ## bypassing setters; copy of val
                else: raise AttributeError(a+' must be a vector')
                del args[a]
                
        vectorInteractions = {'size':'axis', 'axis':'size'}
                
    # override defaults for vector attributes with side effects
        attrs = standardAttributes.attrLists[objName][1]
        for a in attrs:
            if a in args:
                val = args[a]
                if isinstance(val, vector): 
                    setattr(self, a, vector(val))   ## use setter to take care of side effects; copy of val
                    if a not in argsToSend:
                        argsToSend.append(a)
                    if vectorInteractions[a] not in argsToSend:
                        argsToSend.append(vectorInteractions[a])  
                elif objName == 'points' and a == 'size':  ## in this case size is a scalar
                    argsToSend.append(a)
                else: raise AttributeError(a+' must be a vector')
                del args[a]

        if defaultSize is not None:
##        if objName != 'points' and objName != 'label': # these objects have no size
            if 'size' not in argsToSend:  ## always send size because Python size differs from JS size
                argsToSend.append('size')
            self._trail_radius = 0.1 * self._size.y  ## default depends on size
        elif objName == 'points':
            self._trail_radius = self._radius # points object
                
    # override defaults for scalar attributes without side effects       
        attrs = standardAttributes.attrLists[objName][2]
        for a in attrs:
            if a in args:
                argsToSend.append(a)
                setattr(self, '_'+a, args[a])  ## bypass setters
                del args[a] 

        scalarInteractions={'red':'color', 'green':'color', 'blue':'color', 'radius':'size', 'thickness':'size',
                                'length':'size', 'height':'size', 'width':'size', 'v0':'v0', 'v1':'v1',
                                'v2':'v2', 'v3':'v3'}
    
    # override defaults for scalar attributes with side effects       
        attrs = standardAttributes.attrLists[objName][3]
        for a in attrs:
            if a in args:
                setattr(self, a, args[a])  ## use setter to take care of side effects
                if scalarInteractions[a] not in argsToSend:
                    argsToSend.append(scalarInteractions[a])  # e.g. if a is radius, send size
                del args[a]                
                 
    # set values of user-defined attributes
        for key, value in args.items(): # Assign all other properties
            setattr(self, key, value)
        
        cmd = {"cmd": objName, "idx": self.idx, "attrs":[]}

    # now put all args to send into cmd
        for a in argsToSend:
            aval = getattr(self,a)
            if isinstance(aval, vector):
                aval = aval.value
            elif isinstance(aval, vertex):
                aval = aval.idx
            cmd["attrs"].append({"attr":a, "value": aval})
            
    # set canvas  
        if self.canvas == None:  ## not specified in constructor
            self.canvas = canvas.get_selected()
        cmd["attrs"].append({"attr": 'canvas', "value": self.canvas.idx})
        self.canvas.objz(self,'add')
                   
        self._constructing = False  ## from now on any setter call will not be from constructor        
        self.appendcmd(cmd)
       
        # if ('frame' in args and args['frame'] != None):
            # frame.objects.append(self)
            # frame.update_obj_list()

    # attribute vectors have these methods which call self.addattr()
        noSize = ['points', 'label', 'vertex', 'triangle', 'quad']
        if objName not in noSize:
#        if objName != 'points' and objName != 'label':
            self._axis.on_change = self._on_axis_change
            self._size.on_change = self._on_size_change
            self._up.on_change = self._on_up_change
        noPos = ['curve', 'points', 'triangle', 'quad']
        if objName not in noPos:
        # if objName != 'curve' and objName != 'points':
            self._pos.on_change = self._on_pos_change
        elif objName == 'curve':
            self._origin.on_change = self._on_origin_change
        if objName == 'vertex':
            self._bumpaxis.on_change = self._on_bumpaxis_change
            self._normal.on_change = self._on_normal_change
            
    @property
    def up(self):
        return self._up  
    @up.setter
    def up(self,other):
        self._up.value = other
        if not self._constructing:
            self.addattr('up')

    @property
    def pos(self):
        return self._pos    
    @pos.setter
    def pos(self,other):
        self._pos.value = other
        if not self._constructing:
            self.addattr('pos')
            
    @property
    def size(self):
        return self._size   
    @size.setter
    def size(self,other):
        self._axis.value = self.axis.norm() * other._x
        self._size.value = other
        if not self._constructing:
            self.addattr('size')

    @property
    def axis(self):
        return self._axis
    @axis.setter
    def axis(self,other):
        self._axis.value = other
        self._size.x = other.mag
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
    def pickable(self):
        return self._pickable    
    @pickable.setter
    def pickable(self,value):
        self._pickable = value
        if not self._constructing:
            self.addattr('pickable')

    @property
    def canvas(self):
        return self._canvas    
    @canvas.setter
    def canvas(self,value):
        self._canvas = value
        if not self._constructing:
            raise AttributeError('canvas cannot be modified')
      
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
##        if not self._constructing: raise AttributeError('"trail_type" cannot be modified')
        if (value not in ['curve', 'points']):
            raise Exception("ArgumentError: trail_type must be 'curve' or 'points'")
        self._trail_type = value   
        if not self._constructing:
            self.addattr('trail_type')
        
    @property
    def trail_color(self):
        return self._trail_color
    @trail_color.setter
    def trail_color(self, value):
        if isinstance(value, vector):
            self._trail_color.value = value
        else:
            raise TypeError('trail_color must be a vector')
        if not self._constructing: 
            self.addattr('trail_color')

    @property
    def interval(self):
        return self._interval    
    @interval.setter
    def interval(self,value):
##        if not self._constructing: raise AttributeError('"interval" cannot be modified')
        self._interval = value
        if not self._constructing:
            self.addattr('interval')

    @property
    def retain(self):
        return self._retain    
    @retain.setter
    def retain(self,value):
##        if not self._constructing: raise AttributeError('"retain" cannot be modified')
        self._retain = value
        if not self._constructing:
            self.addattr('retain')

    @property
    def trail_radius(self):
        return self._trail_radius    
    @trail_radius.setter
    def trail_radius(self,value):
        self._trail_radius = value
        if not self._constructing:
            self.addattr('trail_radius')
        
    @property
    def pps(self):
        return self._pps
    @pps.setter
    def pps(self, value):
##        if not self._constructing: raise AttributeError('"pps" cannot be modified')
        self._pps = value
        if not self._constructing:
            self.addattr('pps')

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

    def _on_size_change(self):
        self._axis.value = self._axis.norm() * self._size.x  # update axis length when box.size.x is changed
        self.addattr('size')

    def _on_pos_change(self):
        self.addattr('pos')

    def _on_axis_change(self):
        self._size.x = self._axis.mag
        self.addattr('axis')

    def _on_up_change(self):
        self.addattr('up')        
        
    def clear_trail(self):
        self.addmethod('clear_trail', 'None')

    def _ipython_display_(self): # don't print something when making an (anonymous) object
        pass
        
    def clone(self, **args):
        newAtts = {}
        #exclude = ['guid', 'idx', 'attrsupdt', 'oid', '_constructing']
        exclude = ['idx', 'attrsupdt', '_constructing']
        for k,v in vars(self).items():
            if k not in exclude:
                key = k[:]
                if k[0] == '_':
                    key = k[1:]     ## get rid of underscore
                newAtts[key] = v  
        for k, v in args.items():   ## overrides and user attrs
            newAtts[k] = v
        dup = type(self)(**newAtts)
        return dup
           
    def __del__(self):
        super(standardAttributes, self).__del__()
        

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

    @property
    def axis(self):
        return self._axis
    @axis.setter
    def axis(self,other): # changing a sphere axis should not affect size
        self._axis.value = other
        if not self._constructing:
            self.addattr('axis')
        
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
        super(ellipsoid, self).setup(args)
        
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
        
class compound(standardAttributes):
    def __init__(self, objList, **args):
        args['_objName'] = 'compound'
        args['_default_size'] = vector(1,1,1)
        self._obj_idxs = None
        idxlist = []
        clonelist = []
        ineligible = [label, curve, helix, points]  ## type objects
        cvs = objList[0].canvas
        for obj in objList:
            if obj.canvas is not cvs:
                raise AttributeError('all objects used in compound must belong to the same canvas')
            if type(obj) in ineligible:
                raise TypeError(str(type(obj)) + ' cannot be used in a compound')
            clonelist.append(obj.clone())  ## make sure to get current values of attributes
            idxlist.append(clonelist[-1].idx)
        args['obj_idxs'] = idxlist
        
        super(compound, self).setup(args)
        
        for obj in objList:
            obj.visible = False         ## ideally these should be deleted
        for obj in clonelist:
            obj._visible = False

    @property
    def obj_idxs(self):
        return self._obj_idxs
# no setter; must be set in constructor; this is done in standardAttributes
        
    def _world_zaxis(self):
        axis = self._axis
        up = norm(self._up)
        if abs(axis.dot(up)) / math.sqrt(axis.mag2) > 0.98:
            if math.abs(norm(axis).dot(vector(-1,0,0))) > 0.98:
                z_axis = axis.cross(vector(0,0,1)).norm()
            else:
                z_axis = axis.cross(vector(-1,0,0)).norm()
        else:
            z_axis = axis.cross(up).norm()
        return z_axis
    
    def world_to_compound(self, v):
        axis = self._axis
        z_axis = self._world_zaxis()
        y_axis = z_axis.cross(axis).norm()
        x_axis = axis.norm()
        v = v - self._pos
        return vector(v.dot(x_axis), v.dot(y_axis), v.dot(z_axis))
    
    def compound_to_world(self, v):
        axis = self._axis        
        z_axis = self._world_zaxis()
        y_axis = z_axis.cross(axis).norm()
        x_axis = axis.norm()
        return self._pos+(v.x*x_axis) + (v.y*y_axis) + (v.z*z_axis)
        
class vertex(standardAttributes):   
    def __init__(self, **args):
        args['_default_size'] = None
        args['_objName'] = "vertex"
        self._triangleCount = 0
        self._normal = vector(0,0,1)
        self._bumpaxis = vector(1,0,0)
        self._texpos = vector(0,0,0)
        super(vertex, self).setup(args)
      
    @property
    def triangleCount(self):
        return self._triangleCount
    @triangleCount.setter
    def triangleCount(self, val):
        tc = self._triangleCount
        if self._triangleCount + val < 0:
            raise ValueError('value too large')
        else:
            self._triangleCount += val
        if tc == 0 and self._triangleCount == 1:
            self.canvas.vertexCount += 1
            if self.canvas.vertexCount > canvas.maxVertices:
                raise ValueError('too many vertex objects in use for this canvas')
        if tc == 1 and self._triangleCount == 0:
            self.canvas.vertexCount -= 1
                        
    @property
    def normal(self):
        return self._normal
    @normal.setter
    def normal(self, value):
        if not isinstance(value, vector):
            raise AttributeError('normal must be a vector')
        self._normal = value
        if not self._constructing:
            self.addattr('normal')
            
    @property
    def bumpaxis(self):
        return self._bumpaxis
    @bumpaxis.setter
    def bumpaxis(self, value):
        if not isinstance(value, vector):
            raise AttributeError('bumpaxis must be a vector')
        self._bumpaxis = value
        if not self._constructing:
            self.addattr('bumpaxis')
            
    @property
    def texpos(self):
        return self._texpos
    @texpos.setter
    def texpos(self, value):
        if not isinstance(value, vector):
            raise AttributeError('texpos must be a 3D vector with a zero z component')
        if value.z != 0:
            raise AttributeError('the z component of texpos must currently be zero')
        self._texpos = value
        if not self._constructing:
            self.addattr('texpos')
            
    def _on_normal_change(self):
        self.addattr('normal')
        
    def _on_bumpaxis_change(self):
        self.addattr('bumpaxis')

            
class triangle(standardAttributes):   
    def __init__(self, **args):
        args['_default_size'] = None
        args['_objName'] = "triangle"
        self._v0 = None
        self._v1 = None
        self._v2 = None
        super(triangle, self).setup(args)
        
    def __del__(self):
        self._v0.triangleCount = -1
        self._v1.triangleCount = -1
        self._v2.triangleCount = -1
        super(triangle, self).__del__()
        
        
    @property
    def v0(self):
        return self._v0
    @v0.setter
    def v0(self, value):
        if not self._constructing:
            self._v0.triangleCount = -1
            self.addattr('v0')
        self._v0 = value
        self._v0.triangleCount = 1
        
    @property
    def v1(self):
        return self._v1
    @v1.setter
    def v1(self, value):
        if not self._constructing:
            self._v1.triangleCount = -1
            self.addattr('v1')
        self._v1 = value
        self._v1.triangleCount = 1
        
    @property
    def v2(self):
        return self._v2
    @v2.setter
    def v2(self, value):
        if not self._constructing:
            self._v2.triangleCount = -1
            self.addattr('v2')
        self._v2 = value
        self._v2.triangleCount = 1

class quad(triangle):
    def __init__(self, **args):
        args['_default_size'] = None
        args['_objName'] = "quad"
        self._v0 = None
        self._v1 = None
        self._v2 = None
        self._v3 = None
        super(quad, self).setup(args)
        
    def __del__(self):
        self._v0.triangleCount = -1
        self._v1.triangleCount = -1
        self._v2.triangleCount = -1
        self._v3.triangleCount = -1
        super(triangle, self).__del__()
        
    @property
    def v3(self):
        return self._v3
    @v3.setter
    def v3(self, value):
        if not self._constructing:
            self._v3.triangleCount = -1
            self.addattr('v3')
        self._v3 = value
        self._v3.triangleCount = 1

    
class curveMethods(standardAttributes):
    def curveSetup(self, *args1, **args):
        self._constructing = True
        
        # print('curveSetup1, args=', args)
        # print('curveSetup1, args1=', list(args1))
        self.append(list(args))
        self.append(list(args1))

        self._constructing = False

    def process_args(self, *args1, **args):
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
        if len(args1) > 0: 
            if len(args1) == 1:
                tpos = self.parse_pos(args1[0])
            else:  ## avoid nested tuples
                tlist = list(args1)
                tpos = self.parse_pos(tlist)
        elif 'pos' in args:
            pos = args['pos']
            tpos = self.parse_pos(pos)  ## resolve pos arguments into a list
        if len(tpos) == 0:
            raise AttributeError("To add a point to a curve or points object, specify pos information.")
        pts = []
        cps = []
        for pt in tpos:
            cp = {'pos':pt['pos'].value}
            if 'color' in pt:
                c = pt['color']
            if 'radius' in pt:
                r = pt['radius']
            if 'visible' in pt:
                vis = pt['visible']
            if c is not None:
                pt['color'] = c
                cp['color'] = c.value
            if r is not None:
                pt['radius'] = r
                cp['radius'] = r
            if vis is not None:
                pt['visible'] = vis
                cp['visible'] = vis
            pts.append(pt)
            cps.append(cp)
        return [pts, cps]
        
    def parse_pos(self, *vars): # return a list of dictionaries of the form {pos:vec, color:vec ....}
        # In constructor can have pos=[vec, vec, .....]; no dictionaries
        ret = []
        if isinstance(vars, tuple) and len(vars) > 1 :  
            vars = vars[0]
        if isinstance(vars, tuple) and isinstance(vars[0], list):
            vars = vars[0]
        for v in vars:
            if isinstance(v, vector) or isinstance(v, list) or isinstance(v, tuple):
                if not isinstance(v, vector): # legal in GlowScript: pos=[(x,y,z), (x,y,z)] and pos=[[x,y,z], [x,y,z]]
                    v = vec(v[0], v[1], v[2])
                if not self._constructing:
                    ret.append({'pos':v})
                else:
                    ret.append(v)
            elif isinstance(v, dict) and not self._constructing: ret.append(v)
            else: 
                if not self._constructing:
                    raise AttributeError("Point information must be a vector or a dictionary")
                else:
                    raise AttributeError("Point pos must be a vector")
        return ret

    def append(self, *args1, **args):
        pts, cps = self.process_args(*args1, **args)
        self._pts.extend(pts)
        self.addmethod('append', cps[:])
    
    def _on_origin_change(self):
        self.addattr('origin')

    @property
    def npoints(self):
        return len(self._pts)
    @npoints.setter
    def npoints(self,value):
        raise ValueError('npoints cannot be set')
        
    @property
    def radius(self): 
        return self._radius
    @radius.setter
    def radius(self,value):
        self._radius =value
        if not self._constructing:
            self.addattr('radius')   
                             
    def pop(self):
        if len(self._pts) == 0: return None
        val = self._pts[-1]
        self._pts = self._pts[0:-1]
        self.addmethod('pop', 'None')
        return val

    def point(self,N):
        if N >= len(self._pts) or (N < 0 and -N >= len(self.pts)):
            raise ValueError('N = {} is outside the bounds 0-{} of the curve points'.format(N, len(self._pos)))
        return self._pts[N]

    def clear(self):
        self._pts = []
        self.addmethod('clear', 'None' )

    def shift(self):
        if len(self._pts) == 0: return None
        val = self._pts[0]
        self._pts = self._pts[1:]
        self.addmethod( 'shift', 'None' )
        return val

    def unshift(self, *args1, **args):
        pts, cps = self.process_args(*args1, **args)
        self._pts = pts+self._pts
        self.addmethod( 'unshift', cps[:] )
        
    def slice(self, start, end):
        return self._pts[start:end]
        
    def splice(self, start, howmany, *args1): # args1 could be p1, p2, p3 or [p1, p2, p3]
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
        pts, cps = self.process_args(*args1)
        self.pts = self._pts[:start]+pts+self._pts[start+howmany:]
        self.addmethod( 'splice', [start, howmany, cps[:]] )
    
    def modify(self, N, *arg1, **args):
        attrs = ['color', 'radius', 'visible']
        if N >= len(self._pts) or (N < 0 and -N >= len(self._pts)):
            raise ValueError('N = {} is outside the bounds 0-{} of the curve points'.format(N, len(self._pts)))
        p = self._pts[N]
        cp = {}
        if len(arg1) == 1 and isinstance(arg1[0], vector):
            p['pos'] = arg1[0]
            cp['pos'] = arg1[0].value
        else:
            for a in args:
                if a == 'x':
                    p['pos'].x = args[a]
                    cp['pos'][0] = args[a]
                elif a == 'y':
                    p['pos'].y = args[a]
                    cp['pos'][1] = args[a]
                elif a == 'z':
                    p['pos'].z = args[a]
                    cp['pos'][2] = args[a]
                elif a in attrs:
                    p[a] = args[a]
                    if a == 'color':
                        cp[a] = args[a].value
                    else:
                        cp[a] = args[a]
        self.addmethod( 'modify', [N, [cp]])
        
    @property
    def origin(self):
        return self._origin    
    @origin.setter
    def origin(self,value):
        self._origin.value = value
        if not self._constructing:
            self.addattr('origin')

    @property
    def pos(self):
        raise AttributeError('object does not have a "pos" attribute')
    @pos.setter
    def pos(self,val):
        raise AttributeError('object does not have a "pos" attribute')
     
    # def __del__(self):
        # pass
        
        
class curve(curveMethods):
    def __init__(self,*args1, **args):
        args['_objName'] = "curve"
        args['_default_size'] = vector(1,1,1)
        self._origin = vector(0,0,0)  
        self._radius = 0
        self._pts = []  ## cumulative list of dicts of the form {pos:vec, color=vec, radius=r, visible=T/F} python side
        
        tpos = None
        if 'pos' in args:
            tpos = args['pos']
            del args['pos']
  
        super(curveMethods, self).setup(args)
        
        if tpos != None:
            if len(args1) > 0: raise AttributeError('Malformed constructor')
            self.append(tpos)
        if len(args1) > 0:
            self.append(*args1)

    def _on_origin_change(self): 
        self.addattr('origin')
            

class points(curveMethods):
    def __init__(self,*args1, **args):
        args['_objName'] = "points"
        args['_default_size'] = None  ##vector(1,1,1)  ##None
        self._radius = 0
        self._pts = []  ## cumulative list of dicts of the form {pos:vec, color=vec, radius=r, visible=T/F} python side
  
        tpos = None
        if 'pos' in args:
            tpos = args['pos']
            del args['pos']
  
        super(curveMethods, self).setup(args)
        
        if tpos != None:
            if len(args1) > 0: raise AttributeError('Malformed constructor')
            self.append(tpos)
        if len(args1) > 0:
            self.append(*args1)    
                
    @property
    def origin(self):   
        raise AttributeError('points object does not have an origin')
    @origin.setter
    def origin(self,value):
        raise AttributeError('points object does not have an origin')
        


class gobj(baseObj):
    def setup(self, args):
        super(gobj, self).__init__()
    ## default values of shared attributes
        self._color = vector(0,0,0)
        self._graph = None
        #self._plot = []
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
               
        #cmd = {"cmd": objName, "idx": self.idx, "guid": self.guid, "attrs":[]}      
        cmd = {"cmd": objName, "idx": self.idx, "attrs":[]}
           
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
        self.addmethod('plot', p)
        
    def delete(self):
        self.addmethod('delete', 'None')
    
    def data(self, value): # replace existing data with value
        self.addmethod('data', value)

    @property
    def data(self): return self._data
    @data.setter
    def data(self,val): 
        self._data = val
        self.addattr('data')

    def _ipython_display_(self): # don't print something when making an (anonymous) graph object
        pass
        
class gcurve(gobj):
    def __init__(self, **args):
        args['_objName'] = "gcurve"
    ## default values of unshared attributes
        self._dot = False
        self._dot_color = vector(0,0,0)
        self._size = 8
        
        super(gcurve, self).setup(args)

    @property
    def width(self): return self._width
    @width.setter
    def width(self,val): 
        self._width = val
        self.addattr('width')

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
        scalarAttributes = ['width', 'height', 'title', 'xtitle', 'ytitle',
                            'xmin', 'xmax', 'ymin', 'ymax']
        for a in scalarAttributes:
            if a in args:
                argsToSend.append(a)
                setattr(self, '_'+a, args[a])
                del args[a]
                
        # user defined attributes
        for a in args:
            setattr(self, '_'+a, args[a])

        #cmd = {"cmd": objName, "idx": self.idx, "guid": self.guid, "attrs":[]}
        cmd = {"cmd": objName, "idx": self.idx, "attrs":[]}
        
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
        
    @property
    def xmin(self): return self._xmin
    @xmin.setter
    def xmin(self,val): 
        self._xmin = val
        self.addattr('xmin')
        
    @property
    def xmax(self): return self._xmax
    @xmax.setter
    def xmax(self,val): 
        self._xmax = val
        self.addattr('xmax')
        
    @property
    def ymin(self): return self._ymin
    @ymin.setter
    def ymin(self,val): 
        self._ymin = val
        self.addattr('ymin')
        
    @property
    def ymax(self): return self._ymax
    @ymax.setter
    def ymax(self,val): 
        self._ymax = val
        self.addattr('ymax')

    def _ipython_display_(self): # don't print something when making an (anonymous) graph
        pass
    
#    def __del__(self):
#        cmd = {"cmd": "delete", "idx": self.idx}
#        self.appendcmd(cmd)
#        super(graph, self).__del__()

class faces(object):
    def __init__(self, **args):
        raise NameError('faces is no longer supported; use vertex and triangle and quad, which will be available soon')      

class label(standardAttributes):
    def __init__(self, **args):
        args['_objName'] = 'label'
        args['_default_size'] = None
        self._xoffset = 20
        self._yoffset = 12
        self._text = " "
        self._font = "sans"
        self._height = 13
        self._background = vector(0,0,0)
        self._border = 5
        self._box = True
        self._line = True
        self._linecolor = vector(1,1,1)
        self._space = 0
        
        super(label, self).setup(args)

            
    @property
    def xoffset(self):
        return self._xoffset
    @xoffset.setter
    def xoffset(self,value):
        self._xoffset = value
        if not self._constructing:
            self.addattr('xoffset')

    @property
    def yoffset(self):
        return self._yoffset
    @yoffset.setter
    def yoffset(self,value):
        self._yoffset = value
        if not self._constructing:
            self.addattr('yoffset')

    @property
    def text(self):
        return self._text
    @text.setter
    def text(self,value):
        self._text = print_to_string(value)
        if not self._constructing:
            self.addattr('text')

    @property
    def font(self):
        return self._font
    @font.setter
    def font(self,value):
        self._font = value
        if not self._constructing:
            self.addattr('font')

    @property
    def height(self):
        return self._height
    @height.setter
    def height(self,value):
        self._height = value
        if not self._constructing:
            self.addattr('height')

    @property
    def background(self):
        return self._background
    @background.setter
    def background(self,other):
        if isinstance(other, vector):
            self._background.value = other
        else:
            raise TypeError('background must be a vector')
        if not self._constructing:
            self.addattr('background')

    @property
    def border(self):
        return self._border
    @border.setter
    def border(self,value):
        self._border = value
        if not self._constructing:
            self.addattr('border')

    @property
    def box(self):
        return self._box
    @box.setter
    def box(self,value):
        self._box = value
        if not self._constructing:
            self.addattr('box')

    @property
    def line(self):
        return self._line
    @line.setter
    def line(self,value):
        self._line = value
        if not self._constructing:
            self.addattr('line')

    @property
    def linecolor(self):
        return self._linecolor
    @linecolor.setter
    def linecolor(self,other):
        if isinstance(other, vector):
            self._linecolor.value = other
        else:
            raise TypeError('linecolor must be a vector')
        if not self._constructing:
            self.addattr('linecolor')

    @property
    def space(self):
        return self._space
    @space.setter
    def space(self,value):
        self._space = value
        if not self._constructing:
            self.addattr('space')    

             
class frame(object):
    def __init__(self, **args):
        raise NameError('frame is not yet implemented')
    
class Mouse(baseObj):

    def __init__(self, canvas):
        self._pos = None
        self._ray = None
        self._alt = False
        self._ctrl = False
        self._shift = False
        self._canvas = canvas
        self._pick = None
        
        super(Mouse, self).__init__()   ## get guid, idx, attrsupdt, oid
        
    @property
    def pos(self):
        return self._pos    
    @pos.setter
    def pos(self,value):
        raise AttributeError('Cannot set position of the mouse')
        
    @property
    def ray(self):
        return self._ray
    @ray.setter
    def ray(self,value):
        raise AttributeError('Cannot set ray')
        
    @property
    def ctrl(self):
        return self._ctrl
    @ctrl.setter
    def ctrl(self, value):
        raise AttributeError('Cannot set mouse.ctrl')
        
    @property
    def shift(self):
        return self._shift
    @shift.setter
    def shift(self, value):
        raise AttributeError('Cannot set mouse.shift')
    
    @property
    def alt(self):
        return self._alt
    @alt.setter
    def alt(self, value):
        raise AttributeError('Cannot set mouse.alt')
       
    @property
    def pick(self):
        self.appendcmd({"val":self._canvas.idx, "method":"pick", "idx":1 }) # fast send
        self._pick_ready = False
        while self._pick_ready == False:
            rate(120)  ## wait for render to finish and call setpick
        return self._pick            
    @pick.setter
    def pick(self, value):
        raise AttributeError('Cannot set mouse.pick')  
                
    def setpick(self, value):  # value is the entire event
        p = value['pick']
        if p is not None:
            po = object_registry[p]
            if 'segment' in value:
                 po.segment = value['segment']
            self._pick = po
        else:
            self._pick = None
        self._pick_ready = True

    def project(self, **args):
        if 'normal' not in args:
            raise AttributeError('scene.mouse.project() must specify a normal')
        normal = norm(args['normal'])
        dist = 0
        if 'd' in args:
            dist = args['d']
        elif 'point' in args:
            point=args['point']
            dist = dot(normal, point)
        ndc = dot(normal, self._canvas.camera.pos) - dist
        ndr = dot(normal, self._ray)
        t = -ndc/ndr
        return self._canvas.camera.pos.add(self._ray.multiply(t))
        
class Camera(object):
    def __init__(self, canvas):
        self._canvas = canvas
        self._followthis = None
        self._pos = None
    
    @property
    def canvas(self):
        return self._canvas
    @canvas.setter
    def canvas(self, value):
        raise AttributeError('Cannot assign camera to a different canvas')
        
    @property
    def pos(self):
        c = self._canvas
        return c.center-(norm(c.forward)*(c.range / math.tan(c.fov/2)))
    @pos.setter
    def pos(self, value):
        c = self._canvas
        c.center = value+self.axis
        
    @property
    def axis(self):
        c = self._canvas
        return norm(c.forward)*( c.range / math.tan(c.fov/2) )
    @axis.setter
    def axis(self, value):
        c = self._canvas
        c.center = self.pos+value # use current self.pos before it is changed by change in c.forward
        c.forward = norm(value)
        c.range = mag(value)*math.tan(c.fov/2)
    
    @property
    def up(self):   ## but really this should not exist:  should be scene.up
        return self._canvas.up
    @up.setter
    def up(self, value):
        self._canvas.up = value
        
    def rotate(self, **args):
        if args == {} or 'angle' not in args:
            raise AttributeError("object.rotate() requires an angle") 
        angle = args['angle']
        X = self.axis.norm()
        rotaxis = X
        if 'axis' in args: rotaxis = args['axis'].norm()
        origin = self.pos
        if 'origin' in args: origin = args['origin']
        
        Y = self._canvas.up.norm()
        Z = X.cross(Y)
        if Z.dot(Z) < 1e-10:
            Y = vector(1,0,0)
            Z = X.cross(Y)
            if Z.dot(Z) < 1e-10:
                Y = vec(0,1,0)
        
        #self.pos = origin.add(self.pos.sub(origin).rotate(angle=angle, axis=rotaxis))
        #self.axis = self.axis.rotate(angle=angle, axis=rotaxis)
        self.pos = origin + (self.pos-origin).rotate(angle=angle, axis=rotaxis)
        self.axis = self.axis.rotate(angle=angle, axis=rotaxis)
        
    @property
    def follow(self):
        return self._followthis
    @follow.setter
    def follow(self, obj):    ## should allow a function also
        self._followthis = obj
        self.addmethod('follow', obj.idx)

class canvas(baseObj):
    selected_canvas = None
    hasmouse = None
    maxVertices = 65535  ## 2^16 - 1  due to GS weirdness
    
    def __init__(self, **args):
        display(HTML("""<div id="glowscript" class="glowscript"></div>"""))
        display(Javascript("""window.__context = { glowscript_container: $("#glowscript").removeAttr("id")}"""))

        super(canvas, self).__init__()   ## get idx, attrsupdt
        
        self._constructing = True        
        canvas.selected_canvas = self

        rate.active = False  ## ??
            
        self._objz = set()
        self.lights = []
        self.vertexCount = 0
        self._visible = True
        self._background = vector(0,0,0)
        self._ambient = vector(0.2, 0.2, 0.2)
        self._height = 480
        self._width = 640
        self._forward = vector(0,0,-1)
        self._fov = math.pi/3.
        self._range = 1
        self._scale = 1
        self._up = vector(0,1,0)
        self._center = vector(0,0,0)
        self._autoscale = True
        self._userzoom = True
        self._userspin = True
        self._pixel_to_world = 0
        self._title = ''
        self._caption = ''
        self._mouse = Mouse(self)
        self._binds = {'mousedown':[], 'mouseup':[], 'mousemove':[],'click':[],
                        'mouseenter':[], 'mouseleave':[]}
            # no key events unless notebook command mode can be disabled
        self._camera = Camera(self)
        cmd = {"cmd": "canvas", "idx": self.idx, "attrs":[]}
        
        # Make sure that the scene canvas is created before anything else
        if self.idx == 0: # this is scene, idx is 0
            while baseObj.glow == None:
                rate(30)
            self.appendcmd(cmd) # make sure scene exists immediately
            return
        
    # send only nondefault values to GlowScript
        
        canvasVecAttrs = ['background', 'ambient','forward','up', 'center']
        canvasNonVecAttrs = ['visible', 'height', 'width', 'title','fov', 'range', 'scale',
                             'autoscale', 'userzoom', 'userspin', 'title', 'caption']
 
        for a in canvasNonVecAttrs:
            if a in args:
                if args[a] != None:
                    setattr(self, '_'+a, args[a])
                    cmd["attrs"].append({"attr":a, "value": args[a]})
                del args[a]
                
        for a in canvasVecAttrs:
            if a in args:
                aval = args[a]
                if not isinstance(aval, vector):
                    raise TypeError(a, 'must be a vector')
                setattr(self, '_'+a, vector(aval))
                cmd["attrs"].append({"attr":a, "value": aval.value})
                del args[a]
                
    # set values of user-defined attributes
        for key, value in args.items(): # Assign all other properties
            setattr(self, key, value)                
        
        self._forward.on_change = self._on_forward_change
        self._up.on_change = self._on_up_change
        self._center.on_change = self._on_center_change
        
        self.appendcmd(cmd)
        self._constructing = False

    def select(self):
        canvas.selected_canvas = self
        self.addmethod('select','None')

    @classmethod
    def get_selected(cls):
        return cls.selected_canvas

    @property
    def title(self):
        return self._title
    @title.setter
    def title(self,value):
        self._title = value
        if not self._constructing:
            self.addattr('title')

    @property
    def caption(self):
        return self._caption 
    @caption.setter
    def caption(self,value):
        self._caption = value
        if not self._constructing:
            self.addattr('caption')
            
    def append_to_title(self, *args):
        t = print_to_string(*args)
        self._title += t
        self.addmethod('append_to_title', t)
        
    def append_to_caption(self, *args):
        t = print_to_string(*args)
        self._caption += t
        self.addmethod('append_to_caption', t)

    @property
    def mouse(self):
        return self._mouse    
    @mouse.setter
    def mouse(self,value):
        raise AttributeError('Cannot set scene.mouse')
        
    @property
    def camera(self):
        return self._camera
    @camera.setter
    def camera(self,value):
        raise AttributeError('Cannot set scene.camera')
        
    @property
    def visible(self):
        return self._visible    
    @visible.setter
    def visible(self,value):
        self._visible = value
        if not self._constructing:
            self.addattr('visible')

    @property
    def background(self):
        return self._background    
    @background.setter
    def background(self,value):
        self._background = value
        if not self._constructing:
            self.addattr('background')

    @property
    def ambient(self):
        return self._ambient    
    @ambient.setter
    def ambient(self,value):
        self._ambient = value
        if not self._constructing:
            self.addattr('ambient')

    @property
    def height(self):
        return self._height   
    @height.setter
    def height(self,value):
        self._height = value
        if not self._constructing:    
            self.addattr('height')

    @property
    def width(self):
        return self._width    
    @width.setter
    def width(self,value):
        self._width = value
        if not self._constructing:    
            self.addattr('width')

    @property
    def center(self):
        return self._center   
    @center.setter
    def center(self,value):
        if isinstance(value, vector):
            self._center = value
            if not self._constructing:
                self.addattr('center')
        else:
            raise TypeError('center must be a vector')

    @property
    def forward(self):
        return self._forward    
    @forward.setter
    def forward(self,value):
        self._forward = value
        if not self._constructing:    
            self.addattr('forward')

    @property
    def fov(self):
        return self._fov    
    @fov.setter
    def fov(self,value):
        self._fov = value
        if not self._constructing:    
            self.addattr('fov')

    @property
    def range(self):
        return self._range    
    @range.setter
    def range(self,value):
        self._range = value
        if not self._constructing:    
            self.addattr('range')

    @property
    def up(self):
        return self._up   
    @up.setter
    def up(self,value):
        self._up = value
        if not self._constructing:    
            self.addattr('up')

    @property
    def autoscale(self):
        return self._autoscale    
    @autoscale.setter
    def autoscale(self,value):
        self._autoscale = value
        if not self._constructing:    
            self.addattr('autoscale')

    @property
    def userzoom(self):
        return self._userzoom    
    @userzoom.setter
    def userzoom(self,value):
        self._userzoom = value
        if not self._constructing:    
            self.addattr('userzoom')

    @property
    def userspin(self):
        return self._userspin    
    @userspin.setter
    def userspin(self,value):
        self._userspin = value
        if not self._constructing:    
            self.addattr('userspin')
            
    @property
    def lights(self):
        return self._lights
    @lights.setter
    def lights(self, value):
        self._lights = value[:]
        if not self._constructing:
            self.addattr('lights')
            
    @property
    def pixel_to_world(self):
        return self._pixel_to_world
    @pixel_to_world.setter
    def pixel_to_world(self, value):
        raise AttributeError('pixel_to_world is read-only')
            
    @property
    def objects(self):
        obs = []
        for ob in self._objz:
            if ob.visible:
                obs.append(ob)
        return obs
    @objects.setter
    def objects(self, *args1, **args ):
        raise AttributeError('objects is read-only')
        
    def objz(self, obj, operation):
        try:
            ii = (obj.idx > 0)  ## invalid object will not have .idx attribute
            if operation == 'add':
                self._objz.add(obj)
            elif operation == 'delete':
                self._objz.remove(obj)
        except:
            raise TypeError(obj + ' is not an object belonging to a canvas')
            
## key events conflict with notebook command mode; not permitted for now
        
    def handle_event(self, evt):  ## events and scene info updates
        ev = evt['event']
        if ev == 'pick':
##            self.mouse.setpick( evt['pick'] )
            self.mouse.setpick( evt )
        else:
            pos = evt['pos']
            evt['pos'] = vector( pos[0], pos[1], pos[2] )
            self.mouse._pos = evt['pos']
            ray = evt['ray']
            evt['ray'] = vector( ray[0], ray[1], ray[2] )
            self.mouse._ray = evt['ray']
            canvas.hasmouse = self  
            if ev != 'update_canvas':   ## mouse events bound to functions
                evt['canvas'] = self
                self.mouse._alt = evt['alt']
                self.mouse._shift = evt['shift']
                self.mouse._ctrl = evt['ctrl']
                evt1 = event_return(evt)  ## turn it into an object
                for fct in self._binds[ev]: fct( evt1 ) 
            elif ('forward' in evt):  ## ignore user changes to forward, up, range; changes made w/ mouse 
                fwd = evt['forward']
                cup = evt['up']
                self._range = evt['range']
                self._forward = vector(fwd[0], fwd[1], fwd[2])
                self._up = vector( cup[0], cup[1], cup[2] )
                self._autoscale = evt['autoscale']

    def bind(self, eventtype, whattodo):
        evts = eventtype.split()
        for evt in evts:
            if evt in self._binds:
                self._binds[evt].append(whattodo)
            else:
                raise TypeError(evt + ' is an illegal event type')
        self.addmethod('bind', eventtype)
                
    def unbind(self, eventtype, whatnottodo):
        evts = eventtype.split()
        for evt in evts:
            if evt in self._binds and whatnottodo in self._binds[evt]:
                self._binds[evt].remove(whatnottodo)
        self.addmethod('unbind', eventtype)
        
    def fwaitfor(self, event):
        self._waitfor = True       
        
    def waitfor(self, eventtype):
        global _sent
        evts = ['redraw', 'draw_complete'] 
        if eventtype in evts:
            _sent = False  
            while _sent is False:    ## set by commsend
                rate(60)
        else:
            self._waitfor = False    
            self.bind(eventtype, self.fwaitfor)
            while self._waitfor is False:
                rate(60)
            self.unbind(eventtype, self.fwaitfor)
        
    def pause(self,*s):
        if len(s) > 0:
            s = s[0]
            self.addmethod('pause', [s])
        else:
            self.addmethod('pause', [])
        self._waitfor = False
        self.bind('click', self.fwaitfor)
        while self._waitfor is False:
            rate(60)        

    def _on_forward_change(self):
        self.addattr('forward')
        
    def _on_up_change(self):
        self.addattr('up')
        
    def _on_center_change(self):
        self.addattr('center')

    def _ipython_display_(self): # don't print something when making an (anonymous) canvas
        pass
        
class event_return(object):
    def __init__(self, args):
        self.canvas = args['canvas']
        self.event = args['event']
        self.pos = args['pos']
        self.press = args['press']
        self.release = args['release']
        self.which = args['which']

                
class local_light(standardAttributes):
    def __init__(self, **args):
        args['_default_size'] = vector(1,1,1)
        args['_objName'] = "local_light"
        super(local_light, self).setup(args)

        if (canvas.get_selected() != None):
            canvas.get_selected().lights.append(self)
                
class distant_light(standardAttributes):
    def __init__(self, **args):
        args['_default_size'] = vector(1,1,1)
        args['_objName'] = "distant_light"
        super(distant_light, self).setup(args)

        if (canvas.get_selected() != None):
            canvas.get_selected().lights.append(self)
        
    @property
    def direction(self):
        return self._direction
    @direction.setter
    def direction(self,other):
        self._direction.value = other
        if not self._constructing:
            self.addattr('direction')
            
# factorial and combin functions needed in statistical computations            
def factorial(x):
    if x <= 0:
        if x == 0: return 1
        else: raise ValueError('Cannot take factorial of negative number %d' % x)
    fact = 1.0
    nn = 2
    while nn <= x:
        fact = fact*nn
        nn += 1
    if nn != x+1: raise ValueError('Argument of factorial must be an integer, not %0.1f' % x)
    return fact

def combin(x, y):
    # combin(x,y) = factorial(x)/[factorial(y)*factorial(x-y)]
    z = x-y
    num = 1.0
    if y > z:
        y,z = z,y
    nn = z+1
    ny = 1
    while nn <= x:
        num = num*nn/ny
        nn += 1
        ny += 1
    if nn != x+1: raise ValueError('Illegal arguments (%d, %d) for combin function' % (x, y))
    return num

def sleep(dt): # don't use time.sleep because it delays output queued up before the call to sleep
    t = clock()+dt
    while clock() < t:
        rate(60)
    
radians = math.radians
degrees = math.degrees

scene = canvas()

# This must come after creating a canvas
class MISC(baseObj):
    def __init__(self):
        super(MISC, self).__init__() 
    
    def print(self, s):
        self.addmethod('GSprint', s)

__misc = MISC()

def GSprint(*args):
    s = ''
    for a in args:
        s += str(a)+' '
    s = s[:-1]
    __misc.print(s)
    
def print_to_string(*args):
    s = ''
    for a in args:
        s += str(a)+' '
    s = s[:-1]
    return(s)
