from __future__ import print_function, division, absolute_import

# Cythonize the encode machinery?
import colorsys
from .rate_control import *
try:
    from .cyvector import *
    v = vector(0,0,0)
except:
    from .vector import *
from .shapespaths import *

# Need to import the following for consistency across VPythons
from math import *
from numpy import arange

import inspect
from time import clock
import time
import os
import copy
import sys
from . import __version__, __gs_version__

vec = vector # synonyms in GlowScript

def __checkisnotebook(): # returns True if running in Jupyter notebook
    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':  # Jupyter notebook or qtconsole?
            return True
        elif shell == 'TerminalInteractiveShell':  # Terminal running IPython?
            return False
        else:
            return False  # Other type (?)
    except NameError:
        return False      # Probably standard Python interpreter
_isnotebook = __checkisnotebook()

if _isnotebook:
    #### Imports for Jupyter VPython
    import IPython
    if IPython.__version__ >= '4.0.0' :
        import ipykernel
        import notebook
    else:
        import IPython.html.nbextensions
    from IPython.display import HTML
    from IPython.display import display
    from IPython.display import Javascript
    from IPython.core.getipython import get_ipython
    from jupyter_core.paths import jupyter_data_dir
    from . import __version__, __gs_version__

import platform
__p = platform.python_version()
_ispython3 = (__p[0] == '3')

if _ispython3:
    from inspect import signature # Python 3; needed to allow zero arguments in a bound function
else:
    from inspect import getargspec # Python 2; needed to allow zero arguments in a bound function

# __version__ is the version number of the Jupyter VPython installer, generated in building the installer.
version = [__version__, 'jupyter']
GSversion = [__gs_version__, 'glowscript']

# To print immediately, do this:
#    print(.....)
#    sys.stdout.flush()

##def eprint(*args, **kwargs): # this may output when ordinary print won't
##    print(*args, file=sys.stderr, **kwargs)
##    
##def jprint(s): # prints to terminal, for debugging purposes
##    os.write(1, json.dumps(s, separators=(',', ':')).encode('utf_8')+ b'\n')

# scalar attribute:  { <'a' or 'b'>: string }
# string is str(idx)+attrs[<attributename>]+str(attributevalue) 
# for example:  {'a':'23K1.72'}  thickness of object 23 is 1.72
# vector attrribute: 
# string is str(idx)+ attrs[<attributename>]+str(val.x)+','+str(val.y)+','+str(val.z)
# for example: {'a':'37f23.54678,32.12345,-65.00123'}  axis of object 37
# text attribute:
# string is str(value)
# boolean values are integers (0,1)
# method:  {'m': str(idx)+methods[<methodname>]+<value(s) as above>}

# attrs are X in {'a': '23X....'}
__attrs = {'pos':'a', 'up':'b', 'color':'c', 'trail_color':'d', # don't use single and double quotes; available: +-,
         'ambient':'e', 'axis':'f', 'size':'g', 'origin':'h', 'textcolor':'i',
         'direction':'j', 'linecolor':'k', 'bumpaxis':'l', 'dot_color':'m',
         'foreground':'n', 'background':'o', 'ray':'p', 'center':'E', 'forward':'#', 
         
         # scalar attributes
         'graph':'q', 'canvas':'r', 'trail_radius':'s', 
         'visible':'t', 'opacity':'u','shininess':'v', 'emissive':'w',  
         'make_trail':'x', 'trail_type':'y', 'interval':'z', 'pps':'A', 'retain':'B',  
         'red':'C', 'green':'D', 'blue':'F','length':'G', 'width':'H', 'height':'I', 'radius':'J',
         'thickness':'K', 'shaftwidth':'L', 'headwidth':'M', 'headlength':'N', 'pickable':'O',
         'coils':'P', 'xoffset':'Q', 'yoffset':'R', 
         'border':'S', 'line':'T', 'box':'U', 'space':'V', 'linewidth':'W',
         'xmin':'X', 'xmax':'Y', 'ymin':'Z', 'ymax':'`',
         'ctrl':'~', 'shift':'!', 'alt':'@',
         
         # text attributes:
         'text':'$', 'align':'%', 'caption':'^', 'title':'&', 'xtitle':'*', 'ytitle':'(',
         
         # Miscellany:
         'lights':')', 'objects':'_', 'bind':'=',
         'pixel_pos':'[', 'texpos':']', 
         'v0':'{', 'v1':'}', 'v2':';', 'v3':':', 'vs':'<', 'type':'>',
         'font':'?', 'texture':'/'}
         
# attrsb are X in {'b': '23X....'}; ran out of easily typable one-character codes
__attrsb = {'userzoom':'a', 'userspin':'b', 'range':'c', 'autoscale':'d', 'fov':'e',
          'normal':'f', 'data':'g', 'checked':'h', 'disabled':'i', 'selected':'j',
          'vertical':'k', 'min':'l', 'max':'m', 'step':'n', 'value':'o', 'left':'p',
          'right':'q', 'top':'r', 'bottom':'s', '_cloneid':'t'}

# methods are X in {'m': '23X....'}
# pos is normally updated as an attribute, but for interval-based trails, it is updated (multiply) as a method
__methods = {'select':'a', 'pos':'b', 'start':'c', 'stop':'d', 'clear':'f', # unused eghijklmnopuvxyzCDFAB
             'plot':'q', 'add_to_trail':'s',
             'follow':'t', 'clear_trail':'w',
             'bind':'G', 'unbind':'H', 'waitfor':'I', 'pause':'J', 'pick':'K', 'GSprint':'L',
             'delete':'M'}

__vecattrs = ['pos', 'up', 'color', 'trail_color', 'axis', 'size', 'origin', 
            'direction', 'linecolor', 'bumpaxis', 'dot_color', 'add_to_trail', 'textcolor',
            'foreground', 'background', 'ray', 'ambient', 'center', 'forward', 'normal']
                
__textattrs = ['text', 'align', 'caption', 'title', 'xtitle', 'ytitle', 'selected',
                 'append_to_caption', 'append_to_title', 'bind', 'unbind', 'pause', 'GSprint']

def _encode_attr2(sendval, val, ismethods):
    s = ''
    if sendval in __vecattrs: # it would be good to do some kind of compression of doubles
        s += "{:.16G},{:.16G},{:.16G}".format(val[0], val[1], val[2])
    elif sendval in __textattrs:
        s += val
    elif sendval == 'rotate':
        for p in val:
            s += "{:.16G},".format(p)
        s = s[:-1]
    elif sendval == 'plot' or sendval == 'data':
        for p in val:
            s += "{:.16G},{:.16G},".format(p[0], p[1])
        s = s[:-1]
    elif ismethods:
        #if sendval in ['follow', 'waitfor', 'delete']: val = str(val) # scene.camera.follow(object idx)
        s += str(val)
    else:
        s += "{:.16G}".format(val)
    return s

def _encode_attr(D, ismethods): # ismethods is True if a list of method operations
    # If ismethods is True,  D is [ [idx, method, data], [idx, method, data], etc. ]
    # If ismethods is False: D is {idx:{'pos':vec, etc.}, idx:{'pos':vec, etc.}, etc.}
    # For 'attrs', convert {'opacity': 0.5, 'idx': 3} to 'a(idx)X(value)' or 'b(idx)X(value)'
    # where (idx) is a number, X is the attribute code in attrs, (value) is a number or x,y,z or a string
    # For a method, we have {idx, method, value} to be converted to 'm(idx)X(value)'
    out = []
    if ismethods: # methods; a list
        for d in D:
            s = 'm'+str(d[0])+__methods[d[1]]
            s += _encode_attr2(d[1], d[2], True)
            out.append(s)
    else: # attributes, a dictionary
        for idx,d in D.items():
            for sendval,val in d.items():
                if sendval in __attrs:
                    s = 'a'+str(idx)+__attrs[sendval]
                else:
                    s = 'b'+str(idx)+__attrsb[sendval]
                s += _encode_attr2(sendval, val, False)
                out.append(s)
    return out

class _RateKeeper2(RateKeeper):
    
    def __init__(self, interactPeriod=INTERACT_PERIOD, interactFunc=simulateDelay):
        self.rval = 30
        self.tocall = None
        super(_RateKeeper2, self).__init__(interactPeriod=interactPeriod, interactFunc=self.sendtofrontend)

    def sendtofrontend(self):
        # This is called by the rate() function, through rate_control _RateKeeper callInteract().
        # See the function commsend() for details of how the browser is updated.
        
        # Check if events to process from front end
        if _isnotebook:
            if IPython.__version__ >= '3.0.0' :
                kernel = get_ipython().kernel
                parent = kernel._parent_header
                ident = kernel._parent_ident
                kernel.do_one_iteration()
                kernel.set_parent(ident, parent)
            
    def __call__(self, N): # rate(N) calls this function
        self.rval = N          
        if self.rval < 1: raise ValueError("rate value must be greater than or equal to 1")
        super(_RateKeeper2, self).__call__(self.rval) ## calls __call__ in rate_control.py

if sys.version > '3':
    long = int

# The rate function:
rate = _RateKeeper2(interactFunc = simulateDelay(delayAvg = 0.001))

def list_to_vec(L):
    return vector(L[0], L[1], L[2])

class baseObj(object):
    glow = None
    objCnt = 0
    sent = True # set to True by a render in the non-notebook case
    
    # 'cmds': list of constructors,
    # 'attrs': {idx:{'pos':vec, etc.}, idx:{'pos':vec, etc.}, etc.},
    # 'methods': [ [idx, method, date], [idx, method, date], etc. ]
    updates = {'cmds':[], 'methods':[], 'attrs':{}}
    object_registry = {}    ## idx -> instance
    attach_arrows = []
    attach_trails = []  ## needed only for functions
    attrs = set()  # each element is (idx, attr name)

    @classmethod
    def initialize(cls):
        cls.updates = {'cmds':[], 'methods':[], 'attrs':{}}
        cls.attrs = set()
            
    @classmethod
    def empty(cls):
        b = cls.updates
        return b['cmds'] == [] and b['methods'] == [] and len(cls.attrs) == 0

    @classmethod
    def handle_attach(cls): # called when about to send data to the browser
        ## update every attach_arrow if relevant vector has changed
        for aa in cls.attach_arrows:
            ob = cls.object_registry[aa._obj]
            vval = getattr(ob, aa._realattr) # could be 'velocity', for example
            if not isinstance(vval, vector):
                continue
            if (isinstance(aa._last_val, vector) and aa._last_val.equals(vval)) :
                continue
            ob.addattr('up') # pretend that the attribute is 'up'
            aa._last_val = vval
        
        ## update every attach_trail that depends on a function
        for aa in cls.attach_trails:
            if aa._obj == '_func':
                fval = aa._func()
                if not isinstance(fval, vector):
                    raise AttributeError('attach_trail value must be a vector')
                aa.addmethod('add_to_trail', fval.value)
            else:
                fval = cls.object_registry[aa._obj].pos
            if ( isinstance(aa._last_val, vector) and aa._last_val.equals(fval) ):
                continue
            aa._last_val = fval
    
    def __init__(self, **kwargs):
        self.idx = baseObj.objCnt   ## an integer
        self.object_registry[self.idx] = self        
        if kwargs is not None:
            for key, value in kwargs.items():
                object.__setattr__(self, key, value)
        baseObj.incrObjCnt()
        
    def delete(self):
        baseObj.decrObjCnt()
        cmd = {"cmd": "delete", "idx": self.idx}
        if (baseObj.glow is not None):
            sender([cmd])
        else:
            self.appendcmd(cmd)
        baseObj.cmds.append(cmd)

    def appendcmd(self,cmd):
        # The following code makes sure that constructors are sent to the front end first.
        cmd['idx'] = self.idx
        while not baseObj.sent: # baseObj.sent is always True in the notebook case
            time.sleep(0.001)
        baseObj.updates['cmds'].append(cmd) # this is an "atomic" (uninterruptable) operation
        
    def addmethod(self, method, data):
        while not baseObj.sent: # baseObj.sent is always True in the notebook case
            time.sleep(0.001)
        baseObj.updates['methods'].append((self.idx, method, data)) # this is an "atomic" (uninterruptable) operation
    
    def addattr(self, attr):
        while not baseObj.sent: # baseObj.sent is always True in the notebook case
            time.sleep(0.001)
        baseObj.attrs.add((self.idx, attr)) # this is an "atomic" (uninterruptable) operation

    @classmethod
    def package(cls, objdata): # package up the data to send to the browser
        if objdata['cmds'] == []: del objdata['cmds']
        if objdata['attrs'] != {}:
            objdata['attrs'] = _encode_attr(objdata['attrs'], False)
        else: del objdata['attrs']
        if objdata['methods'] != []:
            m = _encode_attr(objdata['methods'], True)
            if 'attrs' in objdata:
                objdata['attrs'] += m
            else:
                objdata['attrs'] = m
        del objdata['methods']
        return objdata

    @classmethod
    def trigger(cls): # isnotebook; called by a canvas update event from browser, coming from GlowWidget.handle_msg
        if cls.empty():
            objdata = 'trigger' # handshake with browser
        else:
            for a in baseObj.attrs:
                idx, attr = a
                val = getattr(baseObj.object_registry[idx], attr)
                if type(val) is vec: val = [val.x, val.y, val.z]
                if idx in baseObj.updates['attrs']:
                    baseObj.updates['attrs'][idx][attr] = val
                else:
                    baseObj.updates['attrs'][idx] = {attr:val}                
            objdata = cls.package(baseObj.updates)
        cls.handle_attach()
        sender(objdata)
        cls.initialize()
        baseObj.sent = True
            
    @classmethod
    def incrObjCnt(cls):
        cls.objCnt += 1

    @classmethod
    def decrObjCnt(cls):
        cls.objCnt -= 1

    def __del__(self):
        cmd = {"cmd": "delete", "idx": self.idx}
        if (baseObj.glow is not None):
            sender([cmd])
        else:
            baseObj.appendcmd(cmd)
    
# Jupyter does not immediately transmit data to the browser from a thread,
# which made for an awkward thread in early versions of Jupyter VPython, and
# even caused display mistakes due to losing portions of data sent to the browser
# from within a thread.

# Now there is no threading in Jupyter VPython. Data is sent to the
# browser from the trigger() function, which is called by a
# canvas_update event sent to Python from the browser (glowcomm.js), currently
# every 33 milliseconds. When trigger() is called, it immediately signals
# the browser to set a timeout of 33 ms to send another signal to Python.
# Note that a typical VPython program starts out by creating objects (constructors) and
# specifying their attributes. The 33 ms signal from the browser is adequate to ensure
# prompt data transmissions to the browser.

# The situation with non-notebook use is similar, but the http server is threaded,
# in order to serve glowcomm.html, jpg texture files, and font files, and the
# websocket is also threaded.

# In both the notebook and non-notebook cases output is buffered in baseObj.updates
# and sent as a block to the browser at render times.

class GlowWidget(object):    
    def __init__(self, comm, msg): # msg is passed but not used in notebook case
        global sender
        baseObj.glow = self
        if _isnotebook:
            comm.on_msg(self.handle_msg)
            comm.on_close(self.handle_close)
            sender = comm.send
            self.show = True

    ## baseObj.object_registry = {}
    ## idx -> instance
    def handle_msg(self, msg):
        events = msg['content']['data'] # this is a list of time-ordered events
        for evt in events:
            if 'widget' in evt:
                obj = baseObj.object_registry[evt['idx']]
                if evt['widget'] == 'button':
                    pass
                elif evt['widget'] == 'slider':
                    obj._value = evt['value']
                elif evt['widget'] == 'menu':
                    obj._selected = obj._choices[evt['value']]
                elif evt['widget'] == 'checkbox':
                    obj._checked = evt['value']
                elif evt['widget'] == 'radio':
                    obj._checked = evt['value']
                # inspect the bound function and see what it's expecting
                if _ispython3: # Python 3
                    a = signature(obj._bind)
                    if str(a) != '()': obj._bind( obj )
                    else: obj._bind()
                else: # Python 2
                    a = getargspec(obj._bind)
                    if len(a.args) > 0: obj._bind( obj ) 
                    else: obj._bind()
            else:   ## a canvas event
                if 'trigger' not in evt:
                    cvs = baseObj.object_registry[evt['canvas']]
                    cvs.handle_event(evt)
            if _isnotebook:
                baseObj.trigger()

    def handle_close(self, data):
        print ("comm closed")

def _wait(cvs): # wait for an event
    cvs._waitfor = False
    if _isnotebook: baseObj.trigger() # in notebook environment must send methods immediately
    while cvs._waitfor is False:
        rate(30)

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
      return list_to_vec(c)

    @classmethod
    def hsv_to_rgb(cls,v):
      T = [v.x, v.y, v.z]
      c = colorsys.hsv_to_rgb(*T)
      return list_to_vec(c)

    @classmethod
    def rgb_to_grayscale(cls,v):
      luminance = 0.21*v.x + 0.71*v.y + 0.07*v.z
      return vector(luminance, luminance, luminance)
  
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
                         ['visible', 'xoffset', 'yoffset', 'font', 'height', 'opacity', 
                           'border', 'line', 'box', 'space', 'align', 'linewidth', 'pixel_pos'],
                         ['text']],
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
                        ['v0', 'v1', 'v2', 'v3'] ],
                 'attach_arrow': [ [ 'color'],
                        [],
                        ['shaftwidth','scale', '_obj', '_attr'],
                        [] ],
                 'attach_trail': [ ['color'],
                        [],
                        ['radius', 'pps', 'retain', 'type', '_obj'],
                        [] ],
                 'extrusion':[ ['pos', 'up', 'color', 'start_face_color', 'end_face_color'],
                        [ 'axis', 'size' ],
                        ['path', 'shape', 'visible', 'opacity','shininess', 'emissive',  
                         'show_start_face', 'show_end_face',
                         'make_trail', 'trail_type', 'interval', 'show_start_face', 'show_end_face',
                         'retain', 'trail_color', 'trail_radius', 'texture', 'pickable' ],
                        ['red', 'green', 'blue','length', 'width', 'height'] ],
                 'text': [ ['pos', 'up', 'color', 'start_face_color', 'end_face_color'],
                          ['axis', 'size'],
                          ['visible', 'opacity','shininess', 'emissive',  
                         'make_trail', 'trail_type', 'interval', 
                         'retain', 'trail_color', 'trail_radius', 'obj_idxs', 'pickable',
                         'align', 'text', 'font', 'billboard', 'show_start_face', 'show_end_face', 'descender',
                         'vertical_spacing', 'depth', 'length', 'width', 'height'],
                          ['red', 'green', 'blue'] ]
                        }
 
    attrLists['pyramid'] = attrLists['box']
    attrLists['cylinder'] = attrLists['sphere']
    attrLists['cone'] = attrLists['sphere']
    attrLists['ellipsoid'] = attrLists['sphere']
    
    def setup(self, args):
        super(standardAttributes, self).__init__() 
        self._constructing = True  ## calls to setters are from constructor

        objName = self._objName = args['_objName']  ## identifies object type
        if objName[:8] == 'compound': objName = 'compound'
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
        self._interval = 0 # means no interval set
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
        self._oldaxis = None # used in linking axis and up
        self._oldup = None # used in linking axis and up
        cloning = None
        if '_cloneid' in args:
            cloning = args['_cloneid']
            del args['_cloneid']
        
        argsToSend = []  ## send to GlowScript only attributes specified in constructor
        
    ## override defaults for vector attributes without side effects 
        attrs = standardAttributes.attrLists[objName][0]
        for a in attrs:
            if a in args:
                argsToSend.append(a)
                val = args[a]
                if isinstance(val, vector): setattr(self, '_'+a, vector(val))  ## by-passing setters; copy of val
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
                setattr(self, '_'+a, args[a])  ## by-pass setters
                del args[a] 

        scalarInteractions={'red':'color', 'green':'color', 'blue':'color', 'radius':'size', 'thickness':'size',
                                'length':'size', 'height':'size', 'width':'size', 'v0':'v0', 'v1':'v1',
                                'v2':'v2', 'v3':'v3', 'text':'text'}
    
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
        
        cmd = {"cmd": objName, "idx": self.idx}

    # now put all args to send into cmd
        nosize = ['compound', 'extrusion', 'text'] # size will be computed by the constuctor
        for a in argsToSend:
            aval = getattr(self,a)
            if isinstance(aval, vector):
                aval = aval.value
            elif isinstance(aval, vertex):
                aval = aval.idx
            if objName in nosize and a == 'size': continue # do not send superfluous size
            #cmd["attrs"].append({"attr":a, "value": aval})
            cmd[a] = aval
            
            
    # set canvas  
        if self.canvas == None:  ## not specified in constructor
            self.canvas = canvas.get_selected()
        #cmd["attrs"].append({"attr": 'canvas', "value": self.canvas.idx})
        cmd['canvas'] = self.canvas.idx
        self.canvas.objz(self,'add')
                   
        self._constructing = False  ## from now on any setter call will not be from constructor
        #if cloning is not None: cmd["attrs"].append({"attr":"_cloneid", "value":cloning})
        if cloning is not None: cmd["_cloneid"] = cloning
        self.appendcmd(cmd)
       
        # if ('frame' in args and args['frame'] != None):
            # frame.objects.append(self)
            # frame.update_obj_list()

    # attribute vectors have these methods which call self.addattr()
    # The vector class calls a change function when there's a change in x, y, or z.
        noSize = ['points', 'label', 'vertex', 'triangle', 'quad', 'attach_arrow', 'attach_trail']
        if objName not in noSize:
            self._axis.on_change = self._on_axis_change
            self._size.on_change = self._on_size_change
            self._up.on_change = self._on_up_change
        noPos = ['curve', 'points', 'triangle', 'quad', 'attach_arrow']
        if objName not in noPos:
            self._pos.on_change = self._on_pos_change
        elif objName == 'curve':
            self._origin.on_change = self._on_origin_change
        if objName == 'vertex':
            self._bumpaxis.on_change = self._on_bumpaxis_change
            self._normal.on_change = self._on_normal_change
        
    # Ensure that if axis or up is <0,0,0> in constructor, we'll recover eventually:
        if self._axis.mag2 == 0: self._oldaxis = vector(1,0,0)
        if self._up.mag2 == 0: self._oldup = vector(0,1,0)
    
    def adjust_up(self, oldaxis, newaxis): # adjust up when axis is changed
        if abs(newaxis.x) + abs(newaxis.y) + abs(newaxis.z) == 0:
            # If axis has changed to <0,0,0>, must save the old axis to restore later
            if self._oldaxis is None: self._oldaxis = oldaxis
            return
        if self._oldaxis is not None:
            # Restore saved oldaxis now that newaxis is nonzero
            oldaxis = self._oldaxis
            self._oldaxis = None
        if newaxis.dot(self._up) == 0: return # axis and up already orthogonal
        angle = oldaxis.diff_angle(newaxis)
        if angle > 1e-6: # smaller angles lead to catastrophes
            # If axis is flipped 180 degrees, cross(oldaxis,newaxis) is <0,0,0>:
            if abs(angle-pi) < 1e-6:
                newup = -self._up
            else:
                rotaxis = cross(oldaxis,newaxis)
                newup = self._up.rotate(angle=angle, axis=rotaxis)
            self._up = newup

    def adjust_axis(self, oldup, newup): # adjust axis when up is changed
        if abs(newup.x) + abs(newup.y) + abs(newup.z):
            # If up will be set to <0,0,0>, must save the old up to restore later
            if self._oldup is None:
                self._oldup = oldup
        if self._oldup is not None:
            # Restore saved oldup now that newup is nonzero
            oldup = self._oldup
            self._oldup = None
        if newup.dot(self._axis) == 0: return # axis and up already orthogonal
        angle = oldup.diff_angle(newup)
        if angle > 1e-6: # smaller angles lead to catastrophes
            # If up is flipped 180 degrees, cross(oldup,newup) is <0,0,0>:
            if abs(angle-pi) < 1e-6:
                newxis = -self._axis
            else:
                rotaxis = cross(oldup,newup)
                newaxis = self._axis.rotate(angle=angle, axis=rotaxis)
            self._axis = newaxis

    @property
    def pos(self):
        return self._pos    
    @pos.setter
    def pos(self,value):
        self._pos.value = value
        if not self._constructing:
            if self._make_trail and self._interval > 0:
                self.addmethod('pos', value.value)
            else:
                self.addattr('pos')
            
    @property
    def up(self):
        return self._up  
    @up.setter
    def up(self,value):
        oldup = vec(self.up)
        a = self.axis
        self._up.value = value
        self.adjust_axis(norm(oldup), self.up)
        if not self._constructing:
            # must update both axis and up when either is changed
            if not self.axis.equals(a): self.addattr('axis')
            if not self.up.equals(value): self.addattr('up')
            
    @property
    def size(self):
        return self._size   
    @size.setter
    def size(self,value):
        self._size.value = value
        if not self._constructing:
            self.addattr('size')
        if self._objName != 'text':
            a = self._axis.norm() * value.x
            if mag(self._axis) == 0:
                a = vector(value.x,0,0)
            v = self._axis
            if not v.equals(a):
                self._axis.value = a
                if not self._constructing:
                    self.addattr('axis')

    @property
    def axis(self):
        return self._axis
    @axis.setter
    def axis(self,value):
        oldaxis = vec(self.axis)
        u = self.up
        self._axis.value = value
        self.adjust_up(norm(oldaxis), self.axis)
        if not self._constructing:
            # must update both axis and up when either is changed
            if not self.axis.equals(oldaxis): self.addattr('axis')
            if not self.up.equals(u): self.addattr('up')
        if self._objName != 'text':
            m = value.mag
            if abs(self._size._x - m) > 0.0001*self._size._x: # need not update size if very small change
                self._size._x = m
                if not self._constructing:
                    self.addattr('size')
            
    @property
    def length(self): 
        return self._size.x    
    @length.setter
    def length(self,value):
        self._axis = self._axis.norm() * value
        self._size._x = value
        if not self._constructing:
            self.addattr('axis')
            self.addattr('size')

    @property
    def height(self): 
        return self._size.y    
    @height.setter
    def height(self,value):
        self._size._y = value
        if not self._constructing:
            self.addattr('size')

    @property
    def width(self): 
        return self._size.z   
    @width.setter
    def width(self,value):
        self._size._z = value
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
            self.appendcmd({"texture":value})

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
        self._interval = value
        if not self._constructing:
            self.addattr('interval')

    @property
    def retain(self):
        return self._retain    
    @retain.setter
    def retain(self,value):
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
        self._pps = value
        if not self._constructing:
            self.addattr('pps')

    @property
    def frame(self):
        return self._frame    
    @frame.setter
    def frame(self,value):
        self._frame = value
   
    def rotate(self, angle=None, axis=None, origin=None):
        saveorigin = origin
        if angle == 0:
            return
        if angle == None:
            raise TypeError('You must specify an angle through which to rotate')
        if axis == None:
            rotaxis = self.axis
        else:
            rotaxis = axis
        if isinstance(self, curve):
            if origin is None: origin = self.origin
            pos = self.origin
        else:
            if origin is None:
                origin = self.pos
            pos = self.pos
        
        # Update local values of axis and up; setting self._axis and self._up to avoid axis/up connections
        a = vec(self.axis)
        u = vec(self.up)
        if diff_angle(self.axis,rotaxis) > 1e-6:
                self._axis.value = self._axis.rotate(angle=angle, axis=rotaxis)
                self._up.value = self._up.rotate(angle=angle, axis=rotaxis)
                if not self.axis.equals(a): self.addattr('axis')
                if not self.up.equals(u): self.addattr('up')
        else:
            self._up = self._up.rotate(angle=angle, axis=rotaxis)
            if not self.axis.equals(a): self.addattr('axis')
            if not self.up.equals(u): self.addattr('up')

        if saveorigin is not None and not origin.equals(self._pos):
            # This code is done only if origin is not the same as the original pos
            newpos = origin+(pos-origin).rotate(angle, rotaxis)
            if isinstance(self, curve):
                self._origin.value = newpos
                self.addattr('origin')
            else:
                self._pos.value = newpos
                self.addattr('pos')
        
    def _on_size_change(self): # the vector class calls this when there's a change in x, y, or z
        self._axis.value = self._axis.norm() * self._size.x  # update axis length when box.size.x is changed
        self.addattr('size')

    def _on_pos_change(self): # the vector class calls this when there's a change in x, y, or z
        self.addattr('pos')

    def _on_axis_change(self): # the vector class calls this when there's a change in x, y, or z
        if self._objName != 'text':
            self._size.x = self._axis.mag
        self.addattr('axis')

    def _on_up_change(self): # the vector class calls this when there's a change in x, y, or z
        self.addattr('up')        
        
    def clear_trail(self):
        self.addmethod('clear_trail', 'None')

    def _ipython_display_(self): # don't print something when making an (anonymous) object
        pass
        
    def clone(self, **args):
        objName = self._objName
        ## Deal with compound separately -- with its own clone method:
        #if objName[:8] == 'compound': objName = 'compound'
        if objName == 'triangle' or objName == 'quad':
            raise TypeError('Cannot clone a '+objName+' object.')
        elif objName == 'text': # the text object is a wrapper around an extrusion, which is a compound
            newargs = {'pos':self._pos, 'canvas':self.canvas,
                    'color':self._color, 'opacity':self._opacity, 
                    'size':self._size, 'axis':self._axis, 'up':self._up, '_text':self._text,
                    '_length':self._length, '_height':self._height, '_depth':self._depth,
                    '_font':self._font, '_align':self._align, '_billboard':self._billboard,
                    '_show_start_face':self._show_start_face, '_show_end_face':self._show_end_face,
                    '_start_face_color':self._start_face_color, '_end_face_color':self._end_face_color,
                    '_descender':self._descender,
                    '_shininess':self._shininess, '_emissive':self._emissive,
                    '_pickable':self._pickable}
        elif objName == 'curve':
            newargs = {'origin':self._origin, 'pos':self.pos,
                    'color':self._color, r'adius':self._radius,
                    'size':self._size, 'axis':self._axis, 'up':self._up,
                    'shininess':self._shininess, 'emissive':self._emissive, 
                    'visible':True, 'pickable':self._pickable}
        elif objName == 'helix':
            newargs = {'pos':self.pos, 'color':self._color,
                    'thickness':self._thickness, 'coils':self._coils,
                    'size':self._size, 'axis':self._axis, 'up':self._up,
                    'shininess':self._shininess, 'emissive':self._emissive, 
                    'visible':True, 'pickable':self._pickable}
        else:
            newargs = {'pos':self._pos, 'color':self._color,
                    'opacity':self._opacity, 'size':self._size, 'axis':self._axis, 'up':self._up,
                    'texture':self.texture, 'shininess':self._shininess, 'emissive':self._emissive,
                    'visible':True, 'pickable':self._pickable}
            if objName == 'arrow':
                newargs['shaftwidth'] = self._shaftwidth
                newargs['headwidth'] = self._headwidth
                newargs['headlength'] = self._headlength
        if objName == 'text' or objName == 'extrusion' or objName[:8] == 'compound':
            newargs['_cloneid'] = self.idx
        for k, v in args.items():   # overrides and user attrs
            newargs[k] = v
        # wait for cloning objects to exist
        while not baseObj.empty():
            rate(60)
        if objName[:8] == 'compound' or objName == 'extrusion':
            return compound([], **newargs)
        else:
            return type(self)(**newargs)
    
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
    def axis(self,value): # changing a sphere axis should not affect size
        self._axis.value = value
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
    def size(self):
        return self._size
    @size.setter
    def size(self,value): # no need to send to browser both arrow.size and arrow.axis
        self._size.value = value
        if not self._constructing:
            self.addattr('size')
        a = self._axis.norm() * value.x
        if mag(self._axis) == 0:
            a = vector(value.x,0,0)
        v = self._axis
        if not v.equals(a):
            self._axis.value = a

    @property
    def axis(self):
        return self._axis
    @axis.setter
    def axis(self,value): # no need to send to browser both arrow.size and arrow.axis
        oldaxis = norm(self._axis)
        self._axis.value = value
        if not self._constructing:
            self.addattr('axis')
        m = value.mag
        if abs(self._size._x - m) > 0.0001*self._size._x: # need not update size if very small change
            self._size._x = m
        self.adjust_up(oldaxis, self.axis)

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
            
class attach_arrow(standardAttributes):
    def __init__(self, obj, attr, **args):
        args['_default_size'] = None
        self._obj = obj.idx
        args['_obj'] = self._obj
        self._realattr = attr # could be for example "velocity"
        self._attr = 'up'     # pretend that the atribute is "up"
        args['_attr'] = self._attr
        args['_objName'] = "attach_arrow"
        self._last_val = None
        self._scale = 1
        self._shaftwidth = 0
        super(attach_arrow, self).setup(args)
        baseObj.attach_arrows.append(self)
        
    @property
    def scale(self):
        return self._scale
    @scale.setter
    def scale(self, value):
        self._scale = value
        if not self._constructing:
            self.addattr("scale")
    
    @property 
    def shaftwidth(self):
        return self._shaftwidth
    @shaftwidth.setter
    def shaftwidth(self, value):
        self._shaftwidth = value
        if not self._constructing:
            self.addattr("shaftwidth")
            
    def stop(self):
        self.addmethod('stop', 'None')
        
    def start(self):
        self.addmethod('start', 'None')
        
class attach_trail(standardAttributes):
    def __init__(self, obj, **args):
        args['_default_size'] = None
        args['_objName'] = "attach_trail"
        self._radius = 0
        if callable(obj): # true if obj is a function
            baseObj.attach_trails.append(self)
            self._obj = "_func"
            self._func = obj
        else:
            self._radius = obj.size.y * 0.1
            self._color = obj.color
            self._obj = obj.idx
        args['_obj'] = self._obj
        self._last_val = None
        self._type = "curve"
        self._retain = -1
        self._pps = 0
        super(attach_trail, self).setup(args)
        
    @property
    def radius(self):
        return self._radius
    @radius.setter
    def radius(self, value):
        self._radius = value
        if not self._constructing:
            self.addattr('radius')
            
    @property
    def retain(self):
        return self._retain
    @retain.setter
    def retain(self, value):
        self._retain = value
        if not self._constructing:
            self.addattr("retain")
            
    @property
    def pps(self):
        return self._pps
    @pps.setter
    def pps(self, value):
        self._pps = value
        if not self._constructing:
            self.addattr("pps")
            
    @property
    def type(self):
        return self._type
    @type.setter
    def type(self, value):
        self._type = value
        if not self._constructing:
            self.addattr("type")
            
    def stop(self):
        self.addmethod('stop', 'None')
        
    def start(self):
        self.addmethod('start', 'None')

    def clear(self):
        self.addmethod('clear', 'None')
        
        
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
        self._thickness = value
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
    compound_idx = 0 # same numbering scheme as in GlowScript
    
    def __init__(self, objList, **args):
        self._obj_idxs = None
        idxlist = []
        ineligible = [label, curve, helix, points]  ## type objects
        cloning =  None
        if '_cloneid' in args:
            cloning = args['_cloneid']
        else:
            cvs = objList[0].canvas
            for obj in objList:
                if obj.canvas is not cvs:
                    raise AttributeError('all objects used in compound must belong to the same canvas')
                if type(obj) in ineligible:
                    raise TypeError('A ' + obj._objName + ' object cannot be used in a compound')
                idxlist.append(obj.idx)
            args['obj_idxs'] = idxlist
        args['_default_size'] = vector(1,1,1) # to keep standardAttributes happy
        savesize = None
        if 'size' in args:
            savesize = args['size']
            del args['size']

        baseObj.sent = False
        while not baseObj.sent: # wait for compounding or cloning objects to exist
            if _isnotebook: rate(1000)
            else: time.sleep(0.001)
        
        self.compound_idx += 1
        args['_objName'] = 'compound'+str(self.compound_idx)
        super(compound, self).setup(args)
        
        for obj in objList:
            # GlowScript will make the objects invisible, so need not set obj.visible
            obj._visible = False  ## ideally these should be deleted
            
        if cloning is None:
            self.canvas._compound = self # used by event handler to update pos and size
            _wait(self.canvas)
        if savesize is not None:
            self._size = savesize

    @property
    def obj_idxs(self):
        return self._obj_idxs
# no setter; must be set in constructor; this is done in standardAttributes
        
    def _world_zaxis(self):
        axis = self._axis
        up = norm(self._up)
        if abs(axis.dot(up)) / sqrt(axis.mag2) > 0.98:
            if abs(norm(axis).dot(vector(-1,0,0))) > 0.98:
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
        if 'canvas' in args:
            cv = args['canvas']
        else:
            cv = canvas.get_selected()
        if cv.vertexCount > canvas.maxVertices-1:
            raise ValueError('too many vertex objects in use for this canvas')        
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
        raise AttributeError('use decrementTriangleCount or incrementTriangleCount')
            
    def decrementTriangleCount(self):
        if self._triangleCount <= 0:
            raise ValueError('triangleCount is already 0')
        self._triangleCount -= 1

    def incrementTriangleCount(self):
        self._triangleCount += 1
           
    @property
    def normal(self):
        return self._normal
    @normal.setter
    def normal(self, value):
        if not isinstance(value, vector):
            raise AttributeError('normal must be a vector')
        self._normal = vector(value)
        if not self._constructing:
            self.addattr('normal')
            
    @property
    def bumpaxis(self):
        return self._bumpaxis
    @bumpaxis.setter
    def bumpaxis(self, value):
        if not isinstance(value, vector):
            raise AttributeError('bumpaxis must be a vector')
        self._bumpaxis = vector(value)
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
        if 'vs' in args:
            vlist = ['v0', 'v1', 'v2']
            for i,val in enumerate(args['vs']):
                args[vlist[i]] = val
            del args['vs']        
        super(triangle, self).setup(args)
        
    def __del__(self):
        self._v0.decrementTriangleCount()
        self._v1.decrementTriangleCount()
        self._v2.decrementTriangleCount()
        super(triangle, self).__del__()
                
    @property
    def v0(self):
        return self._v0
    @v0.setter
    def v0(self, value):
        self._v0 = value    
        if not self._constructing:
            self._v0.decrementTriangleCount()  ## current v0 now used less
            self.addattr('v0')
        self._v0.incrementTriangleCount()   ## new v0 now used more
        
    @property
    def v1(self):
        return self._v1
    @v1.setter
    def v1(self, value):
        self._v1 = value
        if not self._constructing:
            self._v1.decrementTriangleCount()  ## current v1 now used less
            self.addattr('v1')
        self._v1.incrementTriangleCount()   ## new v1 now used more
        
    @property
    def v2(self):
        return self._v2
    @v2.setter
    def v2(self, value):
        self._v2 = value
        if not self._constructing:
            self._v2.decrementTriangleCount()  ## current v2 now used less
            self.addattr('v2')
        self._v2.incrementTriangleCount()   ## new v2 now used more
       
    @property
    def vs(self):
        return [self._v0, self._v1, self._v2]
    @vs.setter
    def vs(self, value):
        if not isinstance(value, list) or len(value) != 3:
            raise AttributeError('A triangle must be a list of 3 vertex objects.') 
        for i in range(3):
            # if not isinstance(value[i], vertex):
                # raise AttributeError('triangle.vs must contain vertex objects.')
            val = value[i]
            if i == 0: self.v0 = val
            elif i == 1: self.v1 = val
            elif i == 2: self.v2 = val

class quad(triangle):
    def __init__(self, **args):
        args['_default_size'] = None
        args['_objName'] = "quad"
        self._v0 = None
        self._v1 = None
        self._v2 = None
        self._v3 = None
        if 'vs' in args:
            vlist = ['v0', 'v1', 'v2', 'v3']
            for i,val in enumerate(args['vs']):
                args[vlist[i]] = val
            del args['vs']  
        super(quad, self).setup(args)
        
    def __del__(self):
        self._v0.decrementTriangleCount()
        self._v1.decrementTriangleCount()
        self._v2.decrementTriangleCount()
        self._v3.decrementTriangleCount()
        super(triangle, self).__del__()
        
    @property
    def v3(self):
        return self._v3
    @v3.setter
    def v3(self, value):
        self._v3 = value
        if not self._constructing:
            self._v3.decrementTriangleCount()  ## current v3 now used less
            self.addattr('v3')
        self._v3.incrementTriangleCount()   ## new v3 now used more
        
    @property
    def vs(self):
        return [self._v0, self._v1, self._v2, self._v3]
    @vs.setter
    def vs(self, value):
        if not isinstance(value, list) or len(value) != 4:
            raise AttributeError('A quad must be a list of 4 vertex objects.') 
        for i in range(4):
            # if not isinstance(value[i], vertex):
                # raise AttributeError('quad.vs must contain vertex objects.')
            val = value[i]
            if i == 0: self.v0 = val
            elif i == 1: self.v1 = val
            elif i == 2: self.v2 = val
            elif i == 4: self.v3 = val
    
class curveMethods(standardAttributes):
    def curveSetup(self, *args1, **args):
        self._constructing = True
        
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
                    v = list_to_vec(v)
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
        self.appendcmd({"val":cps[:],"method":"append","idx":self.idx})
    
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
        self._radius = value
        if not self._constructing:
            self.addattr('radius')   
                             
    def pop(self):
        if len(self._pts) == 0: return None
        val = self._pts[-1]
        self._pts = self._pts[0:-1]
        self.appendcmd({"val":"None","method":"pop","idx":self.idx})
        return val

    def point(self,N):
        if N >= len(self._pts) or (N < 0 and -N >= len(self.pts)):
            raise ValueError('N = {} is outside the bounds 0-{} of the curve points'.format(N, len(self._pos)))
        info = self._pts[N]
        if 'color' not in info: info['color'] = self.color
        if 'radius' not in info: info['radius'] = self.radius
        if 'visible' not in info: info['visible'] = self.visible
        if 'retain' not in info: info['retain'] = self.retain
        return info

    def clear(self):
        self._pts = []
        self.appendcmd({"val":"None","method":"clear","idx":self.idx})

    def shift(self):
        if len(self._pts) == 0: return None
        val = self._pts[0]
        self._pts = self._pts[1:]
        self.appendcmd({"val":"None","method":"shift","idx":self.idx})
        return val

    def unshift(self, *args1, **args):
        pts, cps = self.process_args(*args1, **args)
        self._pts = pts+self._pts
        self.appendcmd({"val":cps[:], "method":"unshift","idx":self.idx})
        
    def slice(self, start, end):
        return self._pts[start:end]
        
    def splice(self, start, howmany, *args1): # args1 could be p1, p2, p3 or [p1, p2, p3]
        if howmany < 0:
            raise ValueError('You cannot delete a negative number of points'.format(howmany))
        if start >= len(self._pts) or (start < 0 and -start >= len(self._pts)):
            raise ValueError('The starting location, {}, is outside the bounds of the list of points'.format(start))
        if start >= 0:
            if start+howmany > len(self._pts):
                raise ValueError('The starting position plus deletions is beyond the list of points'.format(howmany))
        else:
            if start+howmany >= 0:
                raise ValueError('The starting position plus deletions is beyond the list of points'.format(howmany))
        pts, cps = self.process_args(*args1)
        self.pts = self._pts[:start]+pts+self._pts[start+howmany:]
        self.appendcmd({"val":[start, howmany, cps[:]], "method":"splice","idx":self.idx})
    
    def modify(self, N, *arg1, **args):
        attrs = ['pos', 'color', 'radius', 'visible', 'retain']
        if N >= len(self._pts) or (N < 0 and -N >= len(self._pts)):
            raise ValueError('N = {} is outside the bounds 0-{} of the curve points'.format(N, len(self._pts)))
        p = self._pts[N]
        cp = {}
        if len(arg1) == 1 and isinstance(arg1[0], vector):
            p['pos'] = arg1[0]
            cp['pos'] = arg1[0].value
        else:
            pos = p['pos']
            for a in args:
                if a == 'x':
                    pos.x = args[a]
                elif a == 'y':
                    pos.y = args[a]
                elif a == 'z':
                    pos.z = args[a]
                elif a in attrs:
                    p[a] = args[a]
                    if a == 'pos':
                        pos = args[a]
                    elif a == 'color':
                        cp[a] = args[a].value
                    else:
                        cp[a] = args[a]
            cp['pos'] = pos.value
            
        self.appendcmd({"val":[N, [cp]], "method":"modify","idx":self.idx})
        
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
        raise AttributeError('use object methods to change its shape')        
     
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
        raise AttributeError('The points object does not have an origin')
    @origin.setter
    def origin(self,value):
        raise AttributeError('The points object does not have an origin')

    def rotate(self, **args):
        raise AttributeError('The points object has no rotate method.')        
        
class gobj(baseObj):
    def setup(self, args):
        super(gobj, self).__init__()
    ## default values of shared attributes
        self._color = vector(0,0,0)
        self._interval = -1
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
               
        cmd = {"cmd": objName, "idx": self.idx}
           
        for a in argsToSend:
            aval = getattr(self,a)
            if isinstance(aval, vector):
                aval = aval.value
            cmd[a] = aval
            
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

    @property
    def interval(self): return self._interval
    @interval.setter
    def size(self,val): 
        self._interval = val
        self.addattr('interval')

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
        self._dot_color = vector(value)
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
        self._align = 'none'
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
        scalarAttributes = ['width', 'height', 'title', 'xtitle', 'ytitle','align',
                            'xmin', 'xmax', 'ymin', 'ymax']
        for a in scalarAttributes:
            if a in args:
                argsToSend.append(a)
                setattr(self, '_'+a, args[a])
                del args[a]
                
        # user defined attributes
        for a in args:
            setattr(self, '_'+a, args[a])

        cmd = {"cmd": objName, "idx": self.idx}
        
        ## send only args specified in constructor
        for a in argsToSend:
            aval = getattr(self,a)
            if isinstance(aval, vector):
                aval = aval.value
            cmd[a] = aval
            
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
    def align(self): return self._align
    @align.setter
    def align(self,val):
        if not (val == 'left' or val == 'right' or val == 'none'):
            raise NameError("align must be 'left', 'right', or 'none' (the default).")
        self._align = val
        self.addattr('align')

    @property
    def title(self): 
        return self._title
    @title.setter
    def title(self,val): 
        self._title = val
        #self.appendcmd({attr='title', 'idx'=self.idx})
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
        self._foreground = vector(value)
        self.addattr('foreground')

    @property
    def background(self): return self._background
    @background.setter
    def background(self,val):
        if not isinstance(val,vector): raise TypeError('background must be a vector')
        self._background = vector(value)
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

    def delete(self):
        self.addmethod('delete','None')

    def _ipython_display_(self): # don't print something when making an (anonymous) graph
        pass
    
#    def __del__(self):
#        cmd = {"cmd": "delete", "idx": self.idx}
#        self.appendcmd(cmd)
#        super(graph, self).__del__()

class faces(object):
    def __init__(self, **args):
        raise NameError('faces is no longer supported; use vertex with triangle or quad')      

class label(standardAttributes):
    def __init__(self, **args):
        args['_objName'] = 'label'
        args['_default_size'] = None
        self._xoffset = 0
        self._yoffset = 0
        self._text = " "
        self._font = "sans"
        self._height = 13
        self._background = None
        self._border = 5
        self._align = None
        self._box = True
        self._line = True
        self._linecolor = None
        self._linewidth = 1
        self._space = 0
        self._pixel_pos = False
        
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
            self.addattr("text")

    @property
    def align(self):
        return self._align
    @align.setter
    def align(self,value):
        self._align = value
        if not self._constructing:
            self.addattr('align')

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
    def background(self,value):
        if isinstance(value, vector):
            self._background.value = value
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
    def linewidth(self):
        return self._linewidth
    @linewidth.setter
    def linewidth(self,value):
        self._linewidth = value
        if not self._constructing:
            self.addattr('linewidth')

    @property
    def linecolor(self):
        return self._linecolor
    @linecolor.setter
    def linecolor(self,value):
        if isinstance(value, vector):
            self._linecolor = vector(value)
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

    @property
    def pixel_pos(self):
        return self._pixel_pos
    @pixel_pos.setter
    def pixel_pos(self,value):
        self._pixel_pos = value
        if not self._constructing:
            self.addattr('pixel_pos')  

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
        
        super(Mouse, self).__init__()
        
    @property
    def pos(self):
        if self._pos is None: # can be none if mouse has never been inside canvas
            self._pos = vector(0,0,0)
        return self._pos    
    @pos.setter
    def pos(self,value):
        raise AttributeError('Cannot set position of the mouse')
        
    @property
    def ray(self):
        if self._ray is None: # can be none if mouse has never been inside canvas
            self._ray = vector(0,0,-1)
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
        #self.appendcmd({"val":self._canvas.idx, "method":"pick", "idx":1 })
        self.addmethod('pick', self._canvas.idx)
        _wait(self._canvas) # wait for render to finish and call setpick
        return self._pick            
    @pick.setter
    def pick(self, value):
        raise AttributeError('Cannot set mouse.pick')  
                
    def setpick(self, value):  # value is the entire event
        p = value['pick']
        if p is not None:
            po = baseObj.object_registry[p]
            if 'segment' in value:
                 po.segment = value['segment']
            self._pick = po
        else:
            self._pick = None

    def project(self, **args):
        if 'normal' not in args:
            raise AttributeError('scene.mouse.project() must specify a normal')
        normal = norm(args['normal'])
        dist = 0
        if 'd' in args:
            dist = args['d']
        elif 'point' in args:
            point = args['point']
            dist = dot(normal, point)
        ndc = dot(normal, self._canvas.camera.pos) - dist
        ndr = dot(normal, self._ray)
        if ndr == 0: return None
        t = -ndc/ndr
        return self._canvas.camera.pos + t*self._ray
        
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
        return c.center-(norm(c.forward)*(c.range / tan(c.fov/2)))
    @pos.setter
    def pos(self, value):
        c = self._canvas
        c.center = value+self.axis
        
    @property
    def axis(self):
        c = self._canvas
        return norm(c.forward)*( c.range / tan(c.fov/2) )
    @axis.setter
    def axis(self, value):
        c = self._canvas
        c.center = self.pos+value # use current self.pos before it is changed by change in c.forward
        c.forward = norm(value)
        c.range = mag(value)*tan(c.fov/2)
    
    @property
    def up(self):   ## but really this should not exist:  should be scene.up
        return self._canvas.up
    @up.setter
    def up(self, value):
        self._canvas.up = value
        
    def rotate(self, angle=0, axis=None, origin=None):
        c = self._canvas
        if axis is None: axis = c.up
        newaxis = self.axis.rotate(angle=angle, axis=axis)
        newpos = self.pos
        if origin is not None:
            newpos = origin + (self.pos-origin).rotate(angle=angle, axis=axis)
        c.center = newpos + newaxis
        c.forward = norm(newaxis)

class canvas(baseObj):
    selected_canvas = None
    hasmouse = None
    maxVertices = 65535  ## 2^16 - 1  due to GS weirdness
    
    def __init__(self, **args):
        if _isnotebook:
            display(HTML("""<div id="glowscript" class="glowscript"></div>"""))
            display(Javascript("""window.__context = { glowscript_container: $("#glowscript").removeAttr("id")}"""))

        super(canvas, self).__init__()   ## get idx, attrsupdt
        
        self._constructing = True        
        canvas.selected_canvas = self
            
        self._objz = set()
        self.lights = []
        self.vertexCount = 0
        self._visible = True
        self._background = vector(0,0,0)
        self._ambient = vector(0.2, 0.2, 0.2)
        self._height = 480
        self._width = 640
        self._align = 'none'
        self._fov = pi/3
        
        # The following determine the view:
        self._range = 1 # user can alter with zoom
        self._forward = vector(0,0,-1) # user can alter with spin
        self._up = vector(0,1,0) # user with touch screen can rotate around z
        self._autoscale = True # set False if user zooms
        self._center = vector(0,0,0) # cannot be altered by user
        # Reject JavaScript canvas_update user values immediately following Python setting of values:
        self._set_range = False
        self._set_forward = False
        self._set_up = False
        self._set_autoscale = False
        
        self._userzoom = True
        self._userspin = True
        self._pixel_to_world = 0
        self._title = ''
        self._caption = ''
        self._mouse = Mouse(self)
        self._binds = {'mousedown':[], 'mouseup':[], 'mousemove':[],'click':[],
                        'mouseenter':[], 'mouseleave':[], 'keydown':[], 'keyup':[],
                        'redraw':[], 'draw_complete':[]}
                        #'_compound':[]}
            # no key events unless notebook command mode can be disabled
        self._camera = Camera(self)
        self.title_anchor = 1  ## used by buttons etc.
        self.caption_anchor = 2
        cmd = {"cmd": "canvas", "idx": self.idx}
        
    # send only nondefault values to GlowScript
        
        canvasVecAttrs = ['background', 'ambient','forward','up', 'center']
        canvasNonVecAttrs = ['visible', 'height', 'width', 'title','fov', 'range','align',
                             'autoscale', 'userzoom', 'userspin', 'title', 'caption']
 
        for a in canvasNonVecAttrs:
            if a in args:
                if args[a] != None:
                    setattr(self, '_'+a, args[a])
                    cmd[a]= args[a]
                del args[a]
                
        for a in canvasVecAttrs:
            if a in args:
                aval = args[a]
                if not isinstance(aval, vector):
                    raise TypeError(a, 'must be a vector')
                setattr(self, '_'+a, vector(aval))
                cmd[a] = aval.value
                del args[a]
                
    # set values of user-defined attributes
        for key, value in args.items(): # Assign all other properties
            setattr(self, key, value)
        
        self._forward.on_change = self._on_forward_change
        self._up.on_change = self._on_up_change
        self._center.on_change = self._on_center_change
        
        self.appendcmd(cmd)
        self._constructing = False
        
        self._camera.follow = self.follow
        
    def follow(self, obj):    ## should allow a function also
        self.addmethod('follow', obj.idx)

    def select(self):
        canvas.selected_canvas = self
        self.addmethod('select','None')

    def delete(self):
        self.addmethod('delete','None')

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
            self.appendcmd({'title':value})

    @property
    def caption(self):
        return self._caption 
    @caption.setter
    def caption(self,value):
        self._caption = value
        if not self._constructing:
            self.appendcmd({'caption':value})
            
    def append_to_title(self, *args):
        t = print_to_string(*args)
        self._title += t
        if not self._constructing:
            self.appendcmd({'append_to_title':t})
        
    def append_to_caption(self, *args):
        t = print_to_string(*args)
        self._caption += t
        if not self._constructing:
            self.appendcmd({'append_to_caption':t})

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
            self.appendcmd({"background":value.value})

    @property
    def ambient(self):
        return self._ambient    
    @ambient.setter
    def ambient(self,value):
        self._ambient = vector(value)
        if not self._constructing:
            self.addattr('ambient')

    @property
    def width(self):
        return self._width    
    @width.setter
    def width(self,value):
        self._width = value
        if not self._constructing:
            self.appendcmd({"width":value})

    @property
    def height(self):
        return self._height   
    @height.setter
    def height(self,value):
        self._height = value
        if not self._constructing:
            self.appendcmd({"height":value})

    @property
    def align(self): return self._align
    @align.setter
    def align(self,val):
        if not (val == 'left' or val == 'right' or val == 'none'):
            raise NameError("align must be 'left', 'right', or 'none' (the default).")
        self._align = val
        self.appendcmd({"align":val})

    @property
    def center(self):
        return self._center   
    @center.setter
    def center(self,value):
        if isinstance(value, vector):
            self._center = vector(value)
            if not self._constructing:
                self.appendcmd({"center":value.value})
        else:
            raise TypeError('center must be a vector')

    @property
    def forward(self):
        return self._forward    
    @forward.setter
    def forward(self,value):
        self._forward = self._set_forward = vector(value)
        if not self._constructing:
            self.appendcmd({"forward":value.value})

    @property
    def range(self):
        return self._range    
    @range.setter
    def range(self,value):
        self._range = self._set_range = value
        if not self._constructing:
            self.appendcmd({"range":value})

    @property
    def up(self):
        return self._up   
    @up.setter
    def up(self,value):
        self._up = self._set_up = value
        if not self._constructing: 
            self.appendcmd({"up":value.value})

    @property
    def autoscale(self):
        return self._autoscale    
    @autoscale.setter
    def autoscale(self,value):
        self._autoscale = self._set_autoscale = value
        if not self._constructing:
            self.appendcmd({"autoscale":value})

    @property
    def fov(self):
        return self._fov    
    @fov.setter
    def fov(self,value):
        self._fov = value
        if not self._constructing:
            self.appendcmd({"fov":value})

    @property
    def userzoom(self):
        return self._userzoom    
    @userzoom.setter
    def userzoom(self,value):
        self._userzoom = value
        if not self._constructing:
            self.appendcmd({"userzoom":value})

    @property
    def userspin(self):
        return self._userspin    
    @userspin.setter
    def userspin(self,value):
        self._userspin = value
        if not self._constructing:
            self.appendcmd({"userspin":value})
            
    @property
    def lights(self):
        return self._lights
    @lights.setter
    def lights(self, value):
        self._lights = value[:]
        if not self._constructing:
            s = self._lights
            if len(s) == 0:
                s = 'empty_list' # JSON doesn't like an empty list
            self.appendcmd({"lights":s}) # don't encode this unusual statement
            
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
            self.mouse.setpick( evt )
            self._waitfor = True # what pick is looking for
        elif ev == 'waitfor':
            self._waitfor = True # what pause/waitfor is looking for
        elif ev == '_compound': # compound, text, extrusion
            obj = self._compound
            p = evt['pos']
            if obj._objName == 'text':
                obj._size._x = p[0]
                obj._descender = p[1]
            else:
                # Set attribute_vector.value, which avoids nullifying the
                # on_change functions that detect changes in e.g. obj.pos.y
                obj._pos.value = list_to_vec(p)
                s = evt['size']
                obj._size.value = list_to_vec(s)
                obj._axis.value = obj._size._x*norm(obj._axis)
            self._waitfor = True # what compound and text and extrusion are looking for
        else:
            if 'pos' in evt:
                pos = evt['pos']
                evt['pos'] = list_to_vec(pos)
                self.mouse._pos = evt['pos']
            if 'ray' in evt:
                ray = evt['ray']
                evt['ray'] = list_to_vec(ray)
                self.mouse._ray = evt['ray']
            canvas.hasmouse = self  
            if ev != 'update_canvas':   ## mouse events bound to functions, and pause/waitfor
                evt['canvas'] = self
                self.mouse._alt = evt['alt']
                self.mouse._shift = evt['shift']
                self.mouse._ctrl = evt['ctrl']
                evt1 = event_return(evt)  ## turn it into an object
                for fct in self._binds[ev]:
                    # inspect the bound function and see what it's expecting
                    if _ispython3: # Python 3
                        a = signature(fct)
                        if str(a) != '()': fct( evt1 )
                        else: fct()
                    else: # Python 2
                        a = getargspec(fct)
                        if len(a.args) > 0: fct( evt1 ) 
                        else: fct()
                self._waitfor = True # what pause and waitfor are looking for
            else:  ## user can change forward with spin, range/autoscale with zoom, up with touch gesture
                if 'forward' in evt and self.userspin and not self._set_forward:
                    fwd = evt['forward']
                    self._forward = list_to_vec(fwd)
                self._set_forward = False
                if 'up' in evt and self.userspin and not self._set_up:
                    cup = evt['up']
                    self._up = list_to_vec(cup)
                self._set_up = False
                if 'range' in evt and self.userzoom and not self._set_range:
                    self._range = evt['range']
                self._set_range = False
                if 'autoscale' in evt and self.userzoom and not self._set_autoscale:
                    self._autoscale = evt['autoscale']
                self._set_autoscale = False

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
        
    def waitfor(self, eventtype):
        if 'textures' in eventtype: # textures are local; no need to wait
            eventtype = eventtype.replace('textures', '')
            if eventtype == '': return
        evts = ['redraw', 'draw_complete'] # wait for a render
        if eventtype in evts:
            baseObj.sent = False
            while baseObj.sent is False:
                rate(60)
        else:
            self.addmethod('waitfor', eventtype)
            _wait(self)
        
    def pause(self,*s):
        if len(s) > 0:
            s = s[0]
            self.addmethod('pause', s)
        else:
            self.addmethod('pause', '')
        _wait(self)

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
        self._direction = vector(0,0,1)
        super(distant_light, self).setup(args)

        if (canvas.get_selected() != None):
            canvas.get_selected().lights.append(self)
        
    @property
    def direction(self):
        return self._direction
    @direction.setter
    def direction(self,value):
        self._direction = vector(value)
        if not self._constructing:
            self.addattr('direction')
   
## title_anchor = 1 and caption_anchor = 2 are attributes of canvas
print_anchor = 3  ## problematic -- intended to point at print area

class controls(baseObj):
    attrlists = { 'button': ['text', 'textcolor', 'background', 'disabled'],
                  'checkbox':['checked', 'text'],
                  'radio':['checked', 'text'],
                  'menu':['selected', 'choices', 'index'],
                  'slider':['vertical', 'min', 'max', 'step', 'value', 'length',
                            'width', 'left', 'right', 'top', 'bottom', 'align']
                }
    def setup(self, args):
        super(controls, self).__init__()  ## get idx, attrsupdt from baseObj
        ## default values of common attributes
        self._constructing = True
        argsToSend = []
        objName = args['_objName']
        del args['_objName']
        if 'pos' in args:
            self.location = args['pos']
            argsToSend.append('location')
            del args['pos']
        if 'canvas' in args:  ## specified in constructor
            self.canvas = args['canvas']
            del args['canvas']
        else:
            self.canvas = canvas.get_selected()
        if 'bind' in args:
            self._bind = args['bind']
            del args['bind']
        else:
            raise AttributeError('bind missing')
            
        ## override default vector attributes        
        vectorAttributes = ['textcolor', 'background']        
        for a in vectorAttributes:
            if a in args:
                argsToSend.append(a)
                val = args[a]
                if isinstance(val, vector): setattr(self, '_'+a, val)
                else: raise AttributeError(a+' must be a vector')
                del args[a]        
        ## override default scalar attributes

        for a,val in args.items():
            if a in controls.attrlists[objName]:
                argsToSend.append(a)
                setattr(self, '_'+a, val)
            else:
                setattr(self, a, val)
        cmd = {"cmd": objName, "idx": self.idx}
        cmd["canvas"] = self.canvas.idx
                
        ## send only args specified in constructor
        for a in argsToSend:  ## all shared attributes are scalars
            aval = getattr(self,a)
            if isinstance(aval, vector):
                aval = aval.value
            cmd[a] = aval
            
        self.appendcmd(cmd)                     
        self._constructing = False
        
    @property
    def bind(self):
        return self._bind
    @bind.setter
    def bind(self, value):
        raise AttributeError('bind cannot be changed')
        
    @property
    def pos(self):
        return None

    def _ipython_display_(self): # don't print something when making an (anonymous) object
        pass
        
class button(controls):
    def __init__(self, **args):
        args['_objName'] = 'button'
        self._text = ""
        self._textcolor = color.black
        self._background = color.white
        self._disabled = False
        super(button, self).setup(args)
        
    @property
    def text(self):
        return self._text
    @text.setter
    def text(self, value):
        self._text = value
        if not self._constructing:
            self.addattr('text')   

    @property
    def textcolor(self):
        return self._textcolor
    @textcolor.setter
    def textcolor(self, value):
        self._textcolor = vector(value)
        if not self._constructing:
            self.addattr('textcolor')
    
    @property
    def background(self):
        return self._background
    @background.setter
    def background(self, value):
        self._background = vector(value)
        if not self._constructing:
            self.addattr('background')
            
    @property
    def disabled(self):
        return self._disabled
    @disabled.setter
    def disabled(self, value):
        self._disabled = value
        if not self._constructing:
            self.addattr('disabled')

class checkbox(controls): 
    def __init__(self, **args):
        args['_objName'] = 'checkbox'
        self._checked = False
        self._text = ''
        super(checkbox, self).setup(args)
        
    @property
    def text(self):
        return self._text
    @text.setter
    def text(self, value):
        self._text = value
        if not self._constructing:
            self.addattr('text')
            
    @property
    def checked(self):
        return self._checked
    @checked.setter
    def checked(self, value):
        self._checked = value
        if not self._constructing:
            self.addattr('checked')
            
class radio(controls):
    def __init__(self, **args):
        args['_objName'] = 'radio'
        self._checked = False
        self._text = ''
        super(radio, self).setup(args)
        
    @property
    def text(self):
        return self._text
    @text.setter
    def text(self, value):
        self._text = value
        if not self._constructing:
            self.addattr('text')
            
    @property
    def checked(self):
        return self._checked
    @checked.setter
    def checked(self, value):
        self._checked = value
        if not self._constructing:
            self.addattr('checked')
            
class menu(controls):
    def __init__(self, **args):
        args['_objName'] = 'menu'
        self._selected = "None"
        self._choices = args['choices']
        if 'index' in args:
            args['selected'] = self._choices[ args['index'] ]
            del args['index']
        super(menu, self).setup(args)
        
    @property
    def choices(self):
        return self._choices
    @choices.setter
    def choices(self, value):
        raise AttributeError('choices cannot be modified after a menu is created')
        
    @property
    def index(self):
        if self._selected == "None":
            return None
        else:
            return self._choices.index(self._selected)
    @index.setter
    def index(self, value):
        self.selected = self._choices[value]
            
    @property
    def selected(self):
        if self._selected == "None":
            return None
        else:
            return self._selected
    @selected.setter
    def selected(self, value):
        if value is None:
            value = "None"
        self._selected = value
        if not self._constructing:
            self.addattr('selected')
            
class slider(controls):
    def __init__(self, **args): 
        args['_objName'] = 'slider'
        self._vertical = False
        if 'min' in args:  ## set here in order to set step
            self._min = args['min']
        else:
            self._min = 0
        if 'max' in args:
            self._max = args['max']
        else:
            self._max = 1
        self._step = 0.001*(self._max - self._min)
        self._value = self._min
        self._length = 400
        self._width = 10
        self._left = 0
        self._right = 0
        self._top = 0
        self._bottom = 0
        self._align = 'left'
        super(slider, self).setup(args)

    @property
    def vertical(self):
        return self._vertical
    @vertical.setter
    def vertical(self, value):
        raise AttributeError('vertical cannot be changed after creating a slider')
        
    @property
    def min(self):
        return self._min
    @min.setter
    def min(self, value):
        raise AttributeError('min cannot be changed after creating a slider')
        
    @property
    def max(self):
        return self._max
    @max.setter
    def max(self, value):
        raise AttributeError('max cannot be changed after creating a slider')
        
    @property
    def step(self):
        return self._step
    @step.setter
    def step(self, value):
        raise AttributeError('step cannot be changed after creating a slider')
          
    @property
    def value(self):
        return self._value
    @value.setter
    def value(self, val):
        self._value = val
        if not self._constructing:
            self.addattr('value')
            
    @property
    def length(self):
        return self._length
    @length.setter
    def length(self, value):
        raise AttributeError('length cannot be changed after creating a slider')
            
    @property
    def width(self):
        return self._width
    @width.setter
    def width(self, value):
        raise AttributeError('width cannot be changed after creating a slider')
            
    @property
    def left(self):
        return self._left
    @left.setter
    def left(self, value):
        raise AttributeError('left cannot be changed after creating a slider')
       
    @property
    def right(self):
        return self._right
    @right.setter
    def right(self, value):
        raise AttributeError('right cannot be changed after creating a slider')

    @property
    def top(self):
        return self._top
    @top.setter
    def top(self, value):
        raise AttributeError('top cannot be changed after creating a slider')
            
    @property
    def bottom(self):
        return self._bottom
    @bottom.setter
    def bottom(self, value):
        raise AttributeError('bottom cannot be changed after creating a slider')
            
    @property
    def align(self):
        return self._align
    @align.setter
    def align(self, value):
        raise AttributeError('align cannot be changed after creating a slider') 
        
class extrusion(standardAttributes):
    def __init__(self, **args):
        args['_default_size'] = vector(1,1,1) # to keep standardAttributes happy
        args['_objName'] = "extrusion"
        savesize = None
        if 'size' in args:
            savesize = args['size']
            del args['size']
        self._shape = [ ]
        pozz = args['path']
        npozz = []
        for pp in pozz:
            npozz.append(pp.value)  ## convert vectors to lists
        args['path'] = npozz[:]
        self._show_start_face = True
        self._show_end_face = True
        if 'color' in args:
            self._start_face_color = args['color']
            self._end_face_color = args['color']

        super(extrusion, self).setup(args)
        
        self.canvas._compound = self # used by event handler to update pos and size
        _wait(self.canvas)
        if savesize is not None:
            self._size = savesize
        
    @property
    def path(self):
        if self._constructing:
            return self._path
        else:
            return None
    @path.setter
    def path(self,value):
        raise AttributeError('path cannot be changed after extrusion is created')
        
    @property
    def shape(self):
        if self._constructing:
            return self._shape
        else:
            return None
    @shape.setter
    def shape(self, value):
        raise AttributeError('shape cannot be changed after extrusion is created')
            
    @property
    def show_start_face(self):
        if self._constructing:
            return self._show_start_face
        else:
            return None
    @show_start_face.setter
    def show_start_face(self,value):
        raise AttributeError('show_start_face cannot be changed after extrusion is created')
        
    @property
    def show_end_face(self):
        if self._constructing:
            return self._show_end_face
        else:
            return None
    @show_end_face.setter
    def show_end_face(self,value):
        raise AttributeError('show_end_face cannot be changed after extrusion is created')
            
    @property
    def start_face_color(self):
        if self._constructing:
            return self._start_face_color
        else:
            return None
    @start_face_color.setter
    def start_face_color(self,value):
        raise AttributeError('start_face_color cannot be changed after extrusion is created')
        
    @property
    def end_face_color(self):
        if self._constructing:
            return self._end_face_color
        else:
            return None
    @end_face_color.setter
    def end_face_color(self,value):
        raise AttributeError('end_face_color cannot be changed after extrusion is created')
        
class text(standardAttributes):

    def __init__(self, **args):
        args['_default_size'] = vector(1,1,1) # to keep standardAttributes happy
        args['_objName'] = "text"
        self._height = 1  ## not derived from size
        self._length = 1  ## calculated from actual object and returned to vpython
        self._depth = 0.2 ## default is 0.2*height
        self._align = "left"
        self._text = ""
        self._font = "sans"
        self._billboard = False
        self._start_face_color = vector(1,1,1)
        self._end_face_color = vector(1,1,1)
        self._show_start_face = True
        self._show_end_face = True
        self._descender = 0.3
        self._vertical_spacing = 1.3
        self._upper_left = vector(0,0,0)
        self._upper_right = vector(0,0,0)
        self._lower_left = vector(0,0,0)
        self._lower_right = vector(0,0,0)
        self._start = vector(0,0,0)
        self._end = vector(0,0,0)
        cloning = None
        if '_cloneid' in args:
            cloning = args['_cloneid']
            self._lines = len(args['_text'].split('\n'))
        else:
            if 'text' in args:
                self._lines = len(args['text'].split('\n'))
            else:
                raise AttributeError('A text object must have a text attribute')
        if 'color' in args:
            self._start_face_color = args['color']
            self._end_face_color = args['color']
        savesize = None
        if 'size' in args:
            savesize = args['size']
            del args['size']

        super(text, self).setup(args)
        
        if cloning is None:
            self.canvas._compound = self # used by event handler to update pos and size
            _wait(self.canvas)
            if savesize is not None:
                self._size = savesize
        
    @property
    def height(self):
        return self._height
    @height.setter
    def height(self, val):
        if self._constructing:
            self._height = val
        else:
            if val == self._height: return
            m = val/self._height
            self._size.y *= m
            self._descender *= m
            self._height = val
            self.addattr('size')
        
    @property
    def length(self):
        return self._size.x
    @length.setter
    def length(self, val):
        if self._constructing:
            raise AttributeError("text length can't be set when creating a text object")
        else:
            self._size.x = val
            self.addattr('size')
        
    @property
    def depth(self):
        return self._depth
    @depth.setter
    def depth(self, val): # sign issue ??
        if self._constructing:
            self._depth = val
        else:
            if abs(val) < 0.01*self._height:
                if val < 0: val = -0.01*self._height
                else: val = 0.01*self._height
            self._size.z *= abs(value)
            self._pos.z = val/2
            self._depth = val
            self.addattr('pos')
            self.addattr('size')
        
    @property
    def align(self):
        return self._align
    @align.setter
    def align(self,val):
        self._align = val
        if not self._constructing:
            self.addattr('align')
            
    @property
    def font(self):
        return self._font
    @font.setter
    def font(self, val):
        if not (val=='sans' or val=='serif'):
            raise AttributeError("text font must be either 'sans' or 'serif' ")
        self._font = val
        if not self._constructing:
            self.addattr('font')
            
    @property
    def text(self):
        return self._text
    @text.setter
    def text(self, val):
        self._text = val
        if not self._constructing:
            self.addattr('text')
            
    @property
    def billboard(self):
        return self._billboard
    @billboard.setter
    def billboard(self, val):
        raise AttributeError("billboard cannot be modified")
    
    @property
    def start_face_color(self):
        return self._start_face_color
    @start_face_color.setter
    def start_face_color(self, val):
        raise AttributeError("start_face_color cannot be modified")
        
    @property
    def end_face_color(self):
        return self._end_face_color
    @end_face_color.setter
    def end_face_color(self, val):
        raise AttributeError("end_face_color cannot be modified")
        
    @property 
    def show_start_face(self):
        return self._show_start_face
    @show_start_face.setter
    def show_start_face(self,val):
        raise AttributeError("show_start_face cannot be modified")
        
    @property 
    def show_end_face(self):
        return self._show_end_face
    @show_end_face.setter
    def show_end_face(self,val):
        raise AttributeError("show_end_face cannot be modified")
        
    @property
    def descender(self):
        return self._descender
    @descender.setter
    def descender(self, val):
        raise AttributeError("descender cannot be modified")
        
    @property
    def upper_left(self):
        if self.align == "right":
            dx = -self.length
        elif self.align == "center":
            dx = -self.length/2
        else:
            dx = 0
        ul = self.pos + (self.height * norm(self.up)) + dx*norm(self.axis)
        return ul
    @upper_left.setter
    def upper_left(self, val):
        raise AttributeError("upper_left cannot be modified")
        
    @property
    def upper_right(self):
        return self.upper_left + norm(self.axis)*self.length
    @upper_right.setter
    def upper_right(self, val):
        raise AttributeError("upper_right cannot be modified")
        
    @property
    def lower_left(self):
        return self.upper_left + norm(self.up)*(-self.height -self._descender - 1.5*self.height*(self._lines-1) )
    @lower_left.setter
    def lower_left(self, val):
        raise AttributeError("lower_left cannot be modified")
        
    @property
    def lower_right(self):
        return self.lower_left + norm(self.axis)*self.length
    @lower_right.setter
    def lower_right(self, val):
        raise AttributeError("lower_right cannot be modified")
        
    @property
    def start(self):
        return self.upper_left - norm(self.up)*self.height
    @start.setter
    def start(self, val):
        raise AttributeError("start cannot be modified")
        
    @property
    def end(self):
        return self.upper_right - norm(self.up)*self.height
    @end.setter
    def end(self, val):
        raise AttributeError("end cannot be modified")
        
    @property
    def vertical_spacing(self):
        return 1.5*self.height
    @vertical_spacing.setter
    def vertical_spacing(self, val):
        raise AttributeError("vertical_spacing cannot be modified")
                    
# primary attrs are height, length, depth, descender

## pos, align, text, font, billboard, height, length, depth, color, start_face_color, 
## end_face_color, show_start_face, show_end_face, descender, upper_left, upper_right,
## lower_left, lower_right, start, end, vertical_spacing, size, axis, up, 
## opacity, shininess, emissive
    # def __init__(self, **args):
        # super(text, self).__init__() 
        # cmd = {"cmd": 'text', "idx": self.idx, "attrs":[]}
        # cmd["attrs"].append({"attr": 'text', "value": 'ABC'})
        # self.appendcmd(cmd)
                        
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


def print_to_string(*args): # treatment of <br> vs. \n not quite right here
    s = ''
    for a in args:
        s += str(a)+' '
    s = s[:-1]
    return(s)
