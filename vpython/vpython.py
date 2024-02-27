# Cythonize the encode machinery?
import colorsys
from .rate_control import rate
import platform

from math import sqrt, tan, pi

import time

# vpython provides clock in its namespace
clock = time.perf_counter

def sign(x): # for compatibility with Web VPython
    if x > 0: return 1
    if x < 0: return -1
    return 0

import sys
from . import __version__, __gs_version__
from ._notebook_helpers import _isnotebook
from ._vector_import_helper import (vector, mag, norm, cross, dot, adjust_up,
                                    adjust_axis, object_rotate)
                                    

def Exit():
    # no infinite loop here so build processs can finish.
    # print("in atexit")
    pass

import atexit

if platform.system() == 'Windows':
    atexit.register(Exit)

# List of names that will be imported from this file with import *
__all__ = ['Camera', 'GlowWidget', 'version', 'GSversion', 'Mouse', 'arrow', 'attach_arrow',
           'attach_light', 'attach_trail', 'baseObj', 'box', 'bumpmaps', 'button',
           'canvas', 'checkbox', 'clock', 'color', 'combin', 'compound', 'cone', 'controls',
           'curve', 'curveMethods', 'cylinder', 'distant_light', 'ellipsoid',
           'event_return', 'extrusion', 'faces', 'frame', 'gcurve', 'gdots',
           'ghbars', 'gobj', 'graph', 'gvbars', 'helix', 'label',
           'local_light', 'menu', 'meta_canvas', 'points', 'pyramid',
           'quad', 'radio', 'ring', 'set_browser', 'simple_sphere', 'sleep', 'slider', 'sphere',
           'standardAttributes', 'text', 'textures', 'triangle', 'vertex',
           'wtext', 'winput', 'keysdown', 'sign']


from inspect import signature # Python 3; needed to allow zero arguments in a bound function

# __version__ is the version number of the Jupyter VPython installer, generated in building the installer.
version = [__version__, 'jupyter']
GSversion = [__gs_version__, 'glowscript']

keysdownlist = [] # list of keys currently pressed

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
__attrs = {'pos':'a', 'up':'b', 'color':'c', 'trail_color':'d', # don't use single and double quotes; available: comma, but maybe that would cause trouble
         'ambient':'e', 'axis':'f', 'size':'g', 'origin':'h',
         'direction':'j', 'linecolor':'k', 'bumpaxis':'l', 'dot_color':'m',
         'foreground':'n', 'background':'o', 'ray':'p', 'center':'E', 'forward':'#', 'resizable':'+',

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
         'text':'$', 'align':'%', 'caption':'^',
         'fast':'-', 'title':'&', 'xtitle':'*', 'ytitle':'(',

         # Miscellany:
         'lights':')', 'objects':'_', 'bind':'=',
         'pixel_pos':'[', 'texpos':']',
         'v0':'{', 'v1':'}', 'v2':';', 'v3':':', 'vs':'<', 'type':'>',
         'font':'?', 'texture':'/'}

# attrsb are X in {'b': '23X....'}; ran out of easily typable one-character codes
__attrsb = {'userzoom':'a', 'userspin':'b', 'range':'c', 'autoscale':'d', 'fov':'e',
          'normal':'f', 'data':'g', 'checked':'h', 'disabled':'i', 'selected':'j',
          'vertical':'k', 'min':'l', 'max':'m', 'step':'n', 'value':'o', 'left':'p',
          'right':'q', 'top':'r', 'bottom':'s', '_cloneid':'t',
          'logx':'u', 'logy':'v', 'dot':'w', 'dot_radius':'x',
          'markers':'y', 'legend':'z', 'label':'A', 'delta':'B', 'marker_color':'C',
          'size_units':'D', 'userpan':'E', 'scroll':'F', 'choices':'G', 'depth':'H',
          'round':'I', 'name':'J', 'offset':'K', 'attach_idx':'L', 'ccw':'M'}

# methods are X in {'m': '23X....'}
# pos is normally updated as an attribute, but for interval-based trails, it is updated (multiply) as a method
__methods = {'select':'a', 'pos':'b', 'start':'c', 'stop':'d', 'clear':'f', # unused eghijklmnopvxyzCDFABu
             'plot':'q', 'add_to_trail':'s',
             'follow':'t', 'clear_trail':'w',
             'bind':'G', 'unbind':'H', 'waitfor':'I', 'pause':'J', 'pick':'K',
             'delete':'M', 'capture':'N'}

__vecattrs = ['pos', 'up', 'color', 'trail_color', 'axis', 'size', 'origin',
            'direction', 'linecolor', 'bumpaxis', 'dot_color', 'ambient', 'add_to_trail',
            'foreground', 'background', 'ray', 'ambient', 'center', 'forward', 'normal',
            'marker_color', 'offset']

__textattrs = ['text', 'align', 'caption', 'title', 'xtitle', 'ytitle', 'selected', 'label', 'capture', 'name',
                 'append_to_caption', 'append_to_title', 'bind', 'unbind', 'pause', 'choices']

def _encode_attr2(sendval, val, ismethods):
    s = ''
    if sendval in __vecattrs: # it would be good to do some kind of compression of doubles
        s += "{:.16G},{:.16G},{:.16G}".format(val[0], val[1], val[2])
    elif sendval in __textattrs:
		# '\n' doesn't survive JSON transmission, so we replace '\n' with '<br>' (and convert back in glowcomm)
        if not isinstance(val, str): val = print_to_string(val)
        val = val.replace('\n', '<br>')
        s += val
    elif sendval == 'rotate':
        for p in val:
            s += "{:.16G},".format(p)
        s = s[:-1]
    elif sendval == 'plot' or sendval == 'data':
#        for p in val:
#            s += "{:.16G},{:.16G},".format(p[0], p[1])
        if sendval == 'data' and len(val) == 0: s += "None, None,"
        else:
            for p in val:
                s += "{:.16G},{:.16G},".format(p[0], p[1])
        s = s[:-1]
    elif sendval in ['v0', 'v1', 'v2', 'v3']: # val is the vertex object referenced by triangle or quad
        s += str(val.idx)
    elif sendval == 'vs':
        if len(val) == 3:
            s += "{d},{d},{d}".format(val[0].idx, val[1].idx, val[2].idx)
        else:
            s += "{d},{d},{d},{d}".format(val[0].idx, val[1].idx, val[2].idx, val[3].idx)
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

if sys.version > '3':
    long = int


def list_to_vec(L):
    return vector(L[0], L[1], L[2])

class baseObj(object):
    glow = None
    objCnt = 0
    sent = True # set to True by a render in the non-notebook case
    _view_constructed = False
    _canvas_constructing = False
    # 'cmds': list of constructors,
    # 'attrs': {idx:{'pos':vec, etc.}, idx:{'pos':vec, etc.}, etc.},
    # 'methods': [ [idx, method, date], [idx, method, date], etc. ]
    updates = {'cmds':[], 'methods':[], 'attrs':{}}
    object_registry = {}    ## idx -> instance
    attach_arrows = []
    attach_trails = []  # needed only for functions
    follow_objects = [] # entries are [invisible object to follow, function to call for pos, prevous pos]
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
            if not aa._run: continue
            obj = baseObj.object_registry[aa._object]
            if not hasattr(obj, aa.attr): # no longer an attribute of the object
                continue
            vval = getattr(obj, aa.attr) # could be 'velocity', for example
            if not isinstance(vval, vector):
                raise AttributeError('attach_arrow attribute "'+aa.attr+'" value must be a vector.')
            if aa._last_pos.equals(obj._pos) and aa._last_val.equals(vval): continue
            aa._last_val = vector(vval)      # keep copies of last vectors
            aa._last_pos = vector(obj._pos)
            aa.pos = obj._pos
            aa.axis = aa._scale*vval

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

        ## update every scene.camera.follow(function)
        for aa in cls.follow_objects:
            obj = aa[0]
            val = aa[1]()
            lastpos = aa[2]
            if val != lastpos:
                aa[2] = val 
                obj.pos = val

    def __init__(self, **kwargs):
        if not (baseObj._view_constructed or
                baseObj._canvas_constructing):
            if _isnotebook:
                from .with_notebook import _
            else:
                from .no_notebook import _
            baseObj._view_constructed = True

        self.idx = baseObj.objCnt   ## an integer
        self.object_registry[self.idx] = self
        if kwargs is not None:
            for key, value in kwargs.items():
                object.__setattr__(self, key, value)
        baseObj.incrObjCnt()

    def delete(self):
        # Currently delete decrements the object count but doesn't
        # delete any objects in the browser....so, let's not decrement
        # the count for now.

        # baseObj.decrObjCnt()

        # The body of this and __del__ are the same other than the
        # decrement here, so let's just call __del__.
        self.__del__()


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
        ret = {}
        m = None
        if objdata['cmds'] != []: ret['cmds'] = objdata['cmds']
        if objdata['methods'] != []:
            m = _encode_attr(objdata['methods'], True)
        if objdata['attrs'] != {}:
            ret['attrs'] = _encode_attr(objdata['attrs'], False)
            if m is not None: ret['attrs'] += m
        elif m is not None:
            ret['attrs'] = m
        return ret

    @classmethod
    def trigger(cls): # isnotebook; called by a canvas update event from browser, coming from GlowWidget.handle_msg
        if cls.empty():
            objdata = 'trigger' # handshake with browser
        else:
            cls.handle_attach()
            for a in baseObj.attrs:
                idx, attr = a
                val = getattr(baseObj.object_registry[idx], attr)
                if type(val) is vector: val = [val.x, val.y, val.z]
                if idx in baseObj.updates['attrs']:
                    baseObj.updates['attrs'][idx][attr] = val
                else:
                    baseObj.updates['attrs'][idx] = {attr:val}
            objdata = cls.package(baseObj.updates)
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
        if (baseObj.glow is not None and sender is not None):
            sender([cmd])
        else:
            self.appendcmd(cmd)

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
    def __init__(self, wsport=None, wsuri=None):
        global sender
        baseObj.glow = self
        if _isnotebook:
            from ipykernel.comm import Comm
            if (wsport):
                self.comm = Comm(target_name='glow', data={'wsport':wsport, 'wsuri':wsuri})
            else:
                self.comm = Comm(target_name='glow')
            self.comm.on_close(self.handle_close)
            self.comm.on_msg(self.handle_msg)
            sender = self.comm.send
            self.show = True
        else:
            sender = None

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
                    obj.checked = evt['value']
                elif evt['widget'] == 'winput':
                    obj._text = evt['text']
                    obj._number = evt['value']

                # inspect the bound function and see what it's expecting
                a = signature(obj._bind)
                if str(a) != '()':
                    obj._bind( obj )
                else:
                    obj._bind()

            else:   ## a canvas event
                if 'trigger' not in evt:
                    cvs = baseObj.object_registry[evt['canvas']]
                    cvs.handle_event(evt)
            if _isnotebook:
                baseObj.trigger()

    def handle_close(self, data):
        print ("comm closed")

def _wait(cvs): # wait for an event
    cvs._waitfor = None
    if _isnotebook: baseObj.trigger() # in notebook environment must send methods immediately
    while cvs._waitfor is None:
        rate(30)
    return cvs._waitfor

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
    purple = vector(0.4,0.2,0.6)

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

    attrLists = {'box':[['pos', 'color', 'trail_color'],
                        ['axis', 'size', 'up'],
                        ['visible', 'opacity','shininess', 'emissive',
                         'make_trail', 'trail_type', 'interval',
                         'retain', 'trail_color', 'trail_radius', 'texture', 'pickable'],
                        ['red', 'green', 'blue','length', 'width', 'height']],
                 'group':[['pos', 'color', 'trail_color'],
                        ['axis', 'size', 'up'],
                        ['visible', 'make_trail', 'trail_type', 'interval',
                         'retain', 'trail_color', 'trail_radius'],
                        ['red', 'green', 'blue','length', 'width', 'height']],
                 'sphere':[['pos', 'color', 'trail_color'],
                        ['axis', 'size', 'up'],
                        ['visible', 'opacity','shininess', 'emissive',
                         'make_trail', 'trail_type', 'interval',
                         'retain', 'trail_color', 'trail_radius', 'texture', 'pickable'],
                        ['red', 'green', 'blue','length', 'width', 'height', 'radius']],
                 'simple_sphere':[['pos', 'color', 'trail_color'],
                        ['axis', 'size', 'up'],
                        ['visible', 'opacity','shininess', 'emissive',
                         'make_trail', 'trail_type', 'interval',
                         'retain', 'trail_color', 'trail_radius', 'texture', 'pickable'],
                        ['red', 'green', 'blue','length', 'width', 'height', 'radius']],
                 'arrow':[['pos', 'color', 'trail_color'],
                         ['axis', 'size', 'up'],
                         ['visible', 'opacity',
                          'shininess', 'emissive', 'texture', 'frame', 'material',
                          'make_trail', 'trail_type', 'interval',
                          'retain', 'trail_color', 'trail_radius', 'texture',
                          'round', 'shaftwidth', 'headwidth', 'headlength', 'pickable'],
                         ['red', 'green', 'blue','length', 'width', 'height']],
                 'ring':[['pos', 'color', 'trail_color', 'size'],
                        ['axis', 'up'],
                        ['visible', 'opacity','shininess', 'emissive',
                         'make_trail', 'trail_type', 'interval',
                         'retain', 'trail_color', 'trail_radius', 'texture', 'pickable'],
                        ['red', 'green', 'blue','length', 'width', 'height', 'thickness']],
                 'helix':[['pos', 'color', 'trail_color'],
                         ['axis', 'size', 'up'],
                         ['visible', 'opacity','shininess', 'emissive',
                         'make_trail', 'trail_type', 'interval', 'ccw',
                         'retain', 'trail_color', 'trail_radius', 'coils', 'thickness', 'pickable'],
                         ['red', 'green', 'blue','length', 'width', 'height', 'radius']],
                 'curve':[['origin', 'color'],
                         ['axis', 'size', 'up'],
                         ['visible', 'shininess', 'emissive', 'radius', 'retain', 'pickable'],
                         ['red', 'green', 'blue','length', 'width', 'height']],
                 'points':[['color'],
                         [],
                         ['visible', 'opacity', 'shininess', 'emissive', 'radius', 'retain', 'pickable', 'size_units'],
                         ['red', 'green', 'blue']],
                 'label':[['pos', 'color', 'background', 'linecolor'],
                         [],
                         ['visible', 'xoffset', 'yoffset', 'font', 'height', 'opacity',
                           'border', 'line', 'box', 'space', 'align', 'linewidth', 'pixel_pos'],
                         ['text']],
                 'local_light':[['pos', 'color', 'offset'],
                         [],
                         ['visible', 'attach_idx'],
                         []],
                 'distant_light':[['direction', 'color'],
                         [],
                         ['visible'],
                         []],
                 'compound':[['pos', 'color', 'trail_color'],
                         ['axis', 'size', 'up', 'origin'],
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
                 'attach_trail': [ ['color'],
                        [],
                        ['radius', 'pps', 'retain', 'type', '_obj'],
                        [] ],
                 'wtext': [[],
                         [],
                         ['location', 'text'],
                         []],
                 'extrusion':[ ['pos', 'color', 'start_face_color', 'end_face_color',
                        'start_normal', 'end_normal'],
                        [ 'axis', 'size', 'up' ],
                        ['path', 'shape', 'visible', 'opacity','shininess', 'emissive',
                         'show_start_face', 'show_end_face', 'smooth', 'smooth_joints', 'sharp_joints',
                         'scale', 'xscale', 'yscale', 'twist',
                         'make_trail', 'trail_type', 'interval', 'show_start_face', 'show_end_face',
                         'retain', 'trail_color', 'trail_radius', 'texture', 'pickable' ],
                        ['red', 'green', 'blue','length', 'width', 'height'] ],
                 'text': [ ['pos', 'up', 'color', 'start_face_color', 'end_face_color', 'axis'],
                          [],
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
        self._sizing = True # axis/size connection is the default; False for sphere, ring, text, compound
        self._pos = vector(0,0,0)
        self._axis = vector(1,0,0)
        self._up = vector(0,1,0)
        self._color = vector(1,1,1)
        defaultSize = args['_default_size']
        if defaultSize is not None: # is not points or vertex or triangle or quad
            self._size = defaultSize
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
        self._offset = vector(0,0,0)
        self._attach_idx = None
        self._save_oldaxis = None # used in linking axis and up
        self._save_oldup = None # used in linking axis and up
        _special_clone = None
        if '_cloneid' in args: # text, extrusion, or compound is being cloned
            _special_clone = args['_cloneid']
            del args['_cloneid']

        argsToSend = []  ## send to GlowScript only attributes specified in constructor

    ## override defaults for vector attributes without side effects
        attrs = standardAttributes.attrLists[objName][0]
        for a in attrs:
            if a in args:
                argsToSend.append(a)
                val = args[a]
                if objName == 'extrusion' and a == 'color':
                    setattr(self, '_'+a, val)  # '_' bypasses setters
                else:
                    if isinstance(val, vector): setattr(self, '_'+a, vector(val))  # '_' bypasses setters; copy of val
                    else: raise AttributeError(a+' must be a vector')
                del args[a]

    # Track side effects of modifying size, axis, or up
    # For consistency with GlowScript, axis is listed before up in the attrLists,
    # so that setting axis may affect up, but then setting up can affect axis afterwards.
        attrs = standardAttributes.attrLists[objName][1] # vector attributes with interactions
        for a in attrs:
            if a in args:
                val = args[a]
                if isinstance(val, vector):
                    setattr(self, a, vector(val))
                    if a not in argsToSend:
                        argsToSend.append(a)
                    if a == 'size':
                        self._axis = self._axis.norm()*val.x
                    elif a == 'axis':
                        self._size.x = mag(val)
                        self.axis = val # this will have the side effect of modifying up
                    elif a == 'up':
                        self.up = val # this will have the side effect of modifying axis
                else: raise AttributeError(a+' must be a vector')
                del args[a]

        if defaultSize is not None:
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
                    # The following makes sure that size.x is nonzero.
                    # It will be reset when axis is no longer zero.
                    if defaultSize is not None and self._size._x == 0: self._size._x = 1
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
            cmd[a] = aval

    # set canvas
        if self.canvas is None:  ## not specified in constructor
            self.canvas = canvas.get_selected()
        #cmd["attrs"].append({"attr": 'canvas', "value": self.canvas.idx})
        cmd['canvas'] = self.canvas.idx
        # Lights are listed in canvas.lights, not canvas.objects
        if not (objName == 'distant_light' or objName == 'local_light'):
            self.canvas.objz(self,'add')

        self._constructing = False  ## from now on any setter call will not be from constructor
        # _special_clone is True if text, extrusion, or compound objects
        if _special_clone is not None: cmd["_cloneid"] = _special_clone
        self.appendcmd(cmd)

    # attribute vectors have these methods which call self.addattr()
    # The vector class calls a change function when there's a change in x, y, or z.
        noSize = ['points', 'label', 'vertex', 'triangle', 'quad', 'attach_trail']
        if not (objName == 'extrusion'): # 
            self._color.on_change = self._on_color_change
        if objName not in noSize:
            self._axis.on_change = self._on_axis_change
            self._size.on_change = self._on_size_change
            self._up.on_change = self._on_up_change
        noPos = ['curve', 'points', 'triangle', 'quad']
        if objName not in noPos:
            self._pos.on_change = self._on_pos_change
        elif objName == 'curve':
            self._origin.on_change = self._on_origin_change
        if objName == 'vertex':
            self._bumpaxis.on_change = self._on_bumpaxis_change
            self._normal.on_change = self._on_normal_change

    # Ensure that if axis or up is <0,0,0> in constructor, we'll recover eventually:
        if self._axis.mag2 == 0: self._save_oldaxis = vector(1,0,0)
        if self._up.mag2 == 0: self._save_oldup = vector(0,1,0)

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
        self._save_oldup = adjust_axis(self._up, value, self._axis, self._save_oldup) # this sets self._axis and self._up
        if not self._constructing:
            self.addattr('up')

    @property
    def axis(self):
        return self._axis
    @axis.setter
    def axis(self,value): # sphere or ring or text or compound have no axis/size link
        if value.mag2 == 0:
            if self._save_oldaxis is None: self._save_oldaxis = self._axis
            self._axis = value
        else:   
            self._save_oldaxis = adjust_up(self._axis, value, self._up, self._save_oldaxis) # this sets self._axis and self._up
        if not self._constructing:
            self.addattr('axis')
        if self._sizing:
            self._size._x = value.mag # changing axis length changes size.x

    @property
    def size(self):
        return self._size
    @size.setter
    def size(self,value): # sphere or ring or text or compound have no axis/size link        
        currentaxis = self._axis
        self._size = value
        if value.x == 0:
            if self._save_oldaxis is not None:
                currentaxis = self._save_oldaxis
                self._save_oldaxis = None
            else:
                currentaxis = vector(1,0,0)
        if not self._constructing:
            self.addattr('size') 
        if self._sizing:
            self._axis = currentaxis.norm()*value.x            

    @property
    def length(self):
        return self._size.x
    @length.setter
    def length(self,value):
        if value == 0:
            if self._save_oldaxis is None: self._save_oldaxis = vector(self._axis.x, self._axis.y, self._axis.z)
            self._axis = vector(0,0,0)
            self._size._x = 0
        else:
            if self._save_oldaxis is not None:
                self._axis = self._save_oldaxis
                self._save_oldaxis = None
            if self._size._x == 0:
                self.axis = vector(value, 0, 0)
            else:
                if self._sizing:
                    self.axis = value*self._axis.norm() # this will set length if self._sizing
                else:
                    self._size._x = value # for objects whose axis and size are not linked
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
        if isinstance(self._color, list): # may be a list of extrusion colors of the form [ [1,0,0], [0,1,0] ]
            self._color = vector(0,0,0)   # change list to a vector
            self._color.value = value     # modify the vector
        self._color.value = value
        if not self._constructing:
            self.addattr('color')

    @property
    def red(self):
        return self._color.x
    @red.setter
    def red(self,value):
        self._color = (value,self.green,self.blue)
        if not self._constructing:
            self.addattr('color')

    @property
    def green(self):
        return self._color.y
    @green.setter
    def green(self,value):
        self._color = (self.red,value,self.blue)
        if not self._constructing:
            self.addattr('color')

    @property
    def blue(self):
        return self._color.z
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
        if angle is None:
            raise TypeError('You must specify an angle through which to rotate')
        if axis is None:
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
        object_rotate(self._axis, self._up, angle, rotaxis)
        self.addattr('axis')
        self.addattr('up')

        if saveorigin is not None and not origin.equals(self._pos):
            # This code is done only if origin is not the same as the original pos
            newpos = origin+(pos-origin).rotate(angle, rotaxis)
            if isinstance(self, curve):
                self._origin.value = newpos
                self.addattr('origin')
            else:
                self._pos.value = newpos
                self.addattr('pos')

    def bounding_box(self):
        centered = ['box', 'compound', 'ellipsoid', 'sphere', 'simple_sphere', 'ring']
        x = norm(self._axis)
        y = norm(self._up)
        z = norm(cross(x,y))
        L = self._size.x
        H = self._size.y
        W = self._size.z
        p = vector(self._pos) # make a copy of pos, so changes to p won't affect the object
        if self._objName not in centered:
            p = p + 0.5*L*x # move to center
        pts = []
        for dx in [-L/2, L/2]:
            for dy in [-H/2, H/2]:
                for dz in [-W/2, W/2]:
                    pts.append(p + dx*x + dy*y + dz*z)
        return pts

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

    def _on_color_change(self): # the vector class calls this when there's a change in x, y, or z
        self.addattr('color')

    def clear_trail(self):
        self.addmethod('clear_trail', 'None')

    def _ipython_display_(self): # don't print something when making an (anonymous) object
        pass

    def clone(self, **args):
        objName = self._objName
        if objName == 'triangle' or objName == 'quad':
            raise TypeError('Cannot clone a '+objName+' object.')
        elif objName == 'text': # the text object is a wrapper around an extrusion, which is a compound
            oldargs = {'pos':self._pos, 'canvas':self.canvas,
                    'color':self._color, 'opacity':self._opacity,
                    'axis':self._axis, 'up':self._up, '_text':self._text,
                    '_length':self._length, '_height':self._height, '_depth':self._depth,
                    '_font':self._font, '_align':self._align, '_billboard':self._billboard,
                    '_show_start_face':self._show_start_face, '_show_end_face':self._show_end_face,
                    '_start_face_color':self._start_face_color, '_end_face_color':self._end_face_color,
                    '_descender':self._descender,
                    '_shininess':self._shininess, '_emissive':self._emissive,
                    '_pickable':self._pickable}
        elif objName == 'curve':
            oldargs = {'origin':self._origin, 'pos':self.pos,
                    'color':self._color, 'radius':self._radius,
                    'size':self._size, 'axis':self._axis, 'up':self._up,
                    'shininess':self._shininess, 'emissive':self._emissive,
                    'visible':True, 'pickable':self._pickable}
        elif objName == 'helix':
            oldargs = {'pos':self.pos, 'color':self._color,
                    'thickness':self._thickness, 'coils':self._coils, 'ccw':self._ccw,
                    'size':self._size, 'axis':self._axis, 'up':self._up,
                    'shininess':self._shininess, 'emissive':self._emissive,
                    'visible':True, 'pickable':self._pickable}
        else:
            oldargs = {'pos':self._pos, 'color':self._color,
                    'opacity':self._opacity, 'size':self._size, 'axis':self._axis, 'up':self._up,
                    'texture':self.texture, 'shininess':self._shininess, 'emissive':self._emissive,
                    'visible':True, 'pickable':self._pickable}
            if objName == 'arrow':
                oldargs['shaftwidth'] = self._shaftwidth
                oldargs['headwidth'] = self._headwidth
                oldargs['headlength'] = self._headlength
        if objName == 'text' or objName == 'extrusion' or objName[:8] == 'compound':
            oldargs['_cloneid'] = self.idx
        # wait for objects being cloned to exist
        while not baseObj.empty():
            rate(60)
        if objName[:8] == 'compound' or objName == 'extrusion':
            ret = compound([], **oldargs)
        else:
            ret = type(self)(**oldargs)
        for k, v in args.items():   # overrides and user attrs
            setattr(ret, k, v)
        return ret

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
        self._sizing = False # no axis/size connection

    @property
    def radius(self):
        return self._size.y/2
    @radius.setter
    def radius(self,value):
        d = 2*value
        self.size = vector(d,d,d) # size will call addattr

    @property
    def size(self):
        return self._size
    @size.setter
    def size(self,value):
        if not isinstance(value, vector): raise TypeError('size must be a vector')
        self._size = value
        if not self._constructing:
            self.addattr('size') # changing a sphere size should not affect axis

    @property
    def axis(self):
        return self._axis
    @axis.setter
    def axis(self,value): # changing a sphere axis should not affect size
        self._save_oldaxis = adjust_up(self._axis, value, self._up, self._save_oldaxis) # this sets self._axis and self._up
        self._axis.value = value
        if not self._constructing:
            # must update both axis and up when either is changed
            self.addattr('axis')
            self.addattr('up')

class simple_sphere(sphere):
    def __init__(self, **args):
        args['_default_size'] = vector(2,2,2)
        args['_objName'] = "simple_sphere"
        super(simple_sphere, self).setup(args)

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
        self._sizing = False # no axis/size connection

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
        self._save_oldaxis = adjust_up(self._axis, value, self._up, self._save_oldaxis) # this sets self._axis and self._up
        self._axis = value
        if not self._constructing:
            # must update both axis and up when either is changed
            self.addattr('axis')
            self.addattr('up')

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
        self._round = False
        self._shaftwidth = 0
        self._headwidth = 0
        self._headlength = 0

        super(arrow, self).setup(args)
            
    @property
    def round(self):
        return self._round
    @round.setter
    def round(self,value):
        raise AttributeError('Cannot change the "round" attribute of an arrow.')

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

    @property
    def round(self):
        return self._round
    @round.setter
    def round(self,value):
        raise AttributeError('Cannot change the "round" attribute of an arrow.')

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
        self._run = self.visible = False

    def start(self):
        self._run = self.visible = True
    
def attach_arrow(o, attr, **args): # factory function returns arrow with special attributes
    '''
    The object "o" with a vector attribute "p" will have an arrow attached with options such as "color".
    The length of the arrow will be args.scale*o.p", updated with every render of the scene.
    If one creates a new attachment with "arr = attach_arrow(obj, attr, options)" you
    can later change (for example) its color with "arr.color = ..."
    '''
    if not hasattr(o, attr): raise AttributeError('Cannot attach an arrow to an object that has no "'+attr+'" attribute.')
    if not isinstance(getattr(o, attr), vector): raise AttributeError('The attach_arrow attribute "'+attr+ '" is not a vector.')
    if not isinstance(o.pos, vector): raise AttributeError("The object's pos attribute is not a vector.")
    
    scale = 1
    if 'scale' in args: scale = args['scale']
    shaftwidth = 0.5*o._size.y
    if 'shaftwidth' in args: shaftwidth = args['shaftwidth']
    c = o.color
    if 'color' in args: c = args['color']
    # Set _last_val to strange values so that the first update to WebGL won't match:
    a = arrow(canvas=o.canvas, pickable=False, _object=o.idx, attr=attr, color=c,
              scale=scale, shaftwidth=shaftwidth, _run=True,
              _last_val=vector(134.472, 789.472, 465.472), _last_pos=vector(134.472, 789.472, 465.472))
    baseObj.attach_arrows.append(a)
    return a
    
def attach_light(o, **args): # factory function returns local_light with special attributes
    '''
    The object "o" will have a local_light attached with options "offset" and "color".
    The local_light will constantly be positioned at o.pos plus the offset.
    '''
    if not isinstance(o.pos, vector): raise AttributeError("Cannot attach a light to an object that has no pos attribute.")
    if 'color' in args:
        if not isinstance(args['color'], vector): raise AttributeError("The color attribute must be a vector.")
    else:
        args['color'] = o.color # default color
    if 'offset' in args:
        if not isinstance(args['offset'], vector): raise AttributeError('The attach_light attribute "offset" must be a vector.')
    else:
        args['offset'] = vector(0,0,0) # default offset
    a = local_light(pos=o.pos+args['offset'], attach_idx=o.idx, color=args['color'], offset=args['offset'])
    return a

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
        self._ccw = True
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
    def ccw(self):
        return self._ccw
    @ccw.setter
    def ccw(self,value):
        self._ccw =value
        if not self._constructing:
            self.addattr('ccw')

    @property
    def radius(self):
        return self._size.y/2
    @radius.setter
    def radius(self,value):
        d = 2*value
        self._size = vector(self._size.x,d,d)
        if not self._constructing:
            self.addattr('size')

class compound(standardAttributes):
    compound_idx = 0 # same numbering scheme as in GlowScript

    def __init__(self, objList, **args):
        self._obj_idxs = None
        idxlist = []
        ineligible = [label, curve, helix, points]  ## type objects
        _special_clone =  None
        if '_cloneid' in args:
            _special_clone = args['_cloneid']
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
        while not baseObj.sent: # wait for compounding objects to exist
            if _isnotebook: rate(1000)
            else: time.sleep(0.001)

        self.compound_idx += 1
        args['_objName'] = 'compound'+str(self.compound_idx)
        super(compound, self).setup(args)
        self._sizing = False # no axis/size connection except that changing axis.mag changes compound length

        for obj in objList:
            # GlowScript will make the objects invisible, so need not set obj.visible
            obj._visible = False  ## ideally these should be deleted

        if _special_clone is None:
            self.canvas._compound = self # used by event handler to update pos and size
            _wait(self.canvas)
        if savesize is not None:
            self._size = savesize

    @property
    def obj_idxs(self):
        return self._obj_idxs
# no setter; must be set in constructor; this is done in standardAttributes

    @property
    def axis(self):
        return self._axis
    @axis.setter
    def axis(self,value): # compound axis and size don't interact
        self._save_oldaxis = adjust_up(self._axis, value, self._up, self._save_oldaxis) # this sets self._axis and self._up
        if not self._constructing:
            # must update both axis and up when either is changed
            self.addattr('axis')
            self.addattr('up')

    @property
    def size(self):
        return self._size
    @size.setter
    def size(self,value): # compound axis and size don't interact
        self._size.value = value
        if not self._constructing:
            self.addattr('size')

    @property
    def origin(self):
        return self._origin
    @origin.setter
    def origin(self,value): # compound origin cannot be reset
        if not self._constructing:
            raise AttributeError('The compound "origin" attribute is read-only; change "pos" instead.')
        self._origin = value

    def world_to_compound(self, v):
            v = v-self._pos
            x_axis = self._axis.hat
            y_axis = self._up.hat
            z_axis = x_axis.cross(y_axis)
            ox = self._size0.x/self._size.x # _size0 is the original size
            oy = self._size0.y/self._size.y
            oz = self._size0.z/self._size.z
            return self._origin + vector(v.dot(x_axis)*ox, v.dot(y_axis)*oy, v.dot(z_axis)*oz)

    def compound_to_world(self, v):
            v = v-self._origin
            x_axis = self._axis.hat
            y_axis = self._up.hat
            z_axis = x_axis.cross(y_axis)
            ox = self._size.x/self._size0.x # _size0 is the original size
            oy = self._size.y/self._size0.y
            oz = self._size.z/self._size0.z
            return self._pos + v.x*ox*x_axis + v.y*oy*y_axis + v.z*oz*z_axis

class vertex(standardAttributes):
    def __init__(self, **args):
        if 'canvas' in args:
            cv = args['canvas']
        else:
            cv = canvas.get_selected()
        if cv.vertexCount >= canvas.maxVertices:
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
        if not self._constructing:
            self._v0.decrementTriangleCount()  ## current v0 now used less
            self.addattr('v0')
        self._v0 = value
        self._v0.incrementTriangleCount()   ## new v0 now used more

    @property
    def v1(self):
        return self._v1
    @v1.setter
    def v1(self, value):
        if not self._constructing:
            self._v1.decrementTriangleCount()  ## current v1 now used less
            self.addattr('v1')
        self._v1 = value
        self._v1.incrementTriangleCount()   ## new v1 now used more

    @property
    def v2(self):
        return self._v2
    @v2.setter
    def v2(self, value):
        if not self._constructing:
            self._v2.decrementTriangleCount()  ## current v2 now used less
            self.addattr('v2')
        self._v2 = value
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
        if not self._constructing:
            self._v3.decrementTriangleCount()  ## current v3 now used less
            self.addattr('v3')
        self._v3 = value
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
            elif i == 3: self.v3 = val

class curveMethods(standardAttributes):

    def process_args(self, *args1, **args):
        c = None
        r = None
        vis = None
        op = None
        if 'color' in args:
            c = args['color']
        if 'radius' in args:
            r = args['radius']
        if 'visible' in args:
            vis = args['visible']
        if 'opacity' in args:
            op = args['opacity']
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
            col = c
            rad = r
            vi = vis
            opaq = None
            cp = {'pos':pt['pos'].value}
            if 'color' in pt:
                col = pt['color']
            if 'opacity' in pt:
                opaq = pt['opacity']
            if 'radius' in pt:
                rad = pt['radius']
            if 'visible' in pt:
                vi = pt['visible']
            if col is not None:
                pt['color'] = col
                cp['color'] = col.value
            if rad is not None:
                pt['radius'] = rad
                cp['radius'] = rad
            if vi is not None:
                pt['visible'] = vi
                cp['visible'] = vi
            if opaq is not None:
                pt['opacity'] = opaq
                cp['opacity'] = opaq
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
                    ret.append({'pos':vector(v)}) # make a copy of the vector; it could be (and often is, e.g. in a trail) object.pos
                else:
                    ret.append(vector(v))
            elif isinstance(v, dict) and not self._constructing:
                ret.append(v)
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

    def pop(self, *args):
        if len(self._pts) == 0: return None
        if len(args) == 0:
            index = -1
        else:
            index = args[0]
        val = self._pts.pop(index)
        self.appendcmd({"val":index,"method":"pop","idx":self.idx})
        return val

    def point(self,N):
        if N >= len(self._pts) or (N < 0 and -N > len(self._pts)):
            raise ValueError('N = {} is outside the bounds 0-{} of the curve points'.format(N, len(self._pts)-1))
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

        if tpos is not None:
            if len(args1) > 0: raise AttributeError('Malformed constructor')
            self.append(tpos)
        if len(args1) > 0:
            self.append(*args1, color=self.color, radius=self.radius, visible=self.visible)

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

        if tpos is not None:
            if len(args1) > 0: raise AttributeError('Malformed constructor')
            self.append(tpos)
        if len(args1) > 0:
            self._pts.append(*args1)

    @property
    def origin(self):
        raise AttributeError('The points object does not have an origin')
    @origin.setter
    def origin(self,value):
        raise AttributeError('The points object does not have an origin')

    @property
    def size_units(self):
        return self._size_units
    @size_units.setter
    def size_units(self,value):
        self._size_units = value

    def rotate(self, **args):
        raise AttributeError('The points object has no rotate method.')

class gobj(baseObj):
    def setup(self, args):
        super(gobj, self).__init__()
    ## default values of shared attributes
        self._color = vector(0,0,0)
        self._marker_color = vector(0,0,0)
        self._dot_color = vector(0,0,0)
        self._dot = False
        self._delta = 1
        self._width = 2
        self._radius = 3
        self._label = ''
        self._legend = False
        self._interval = -1
        self._iterations = 0
        self._firstplot = True
        self._graph = None
        self._data = []
        self._visible = True
        objName = args['_objName']
        del args['_objName']
        self._constructing = True ## calls are from constructor

        argsToSend = [] ## send to GlowScript only attributes specified in constructor
                        ## default values will be used for others

        ## process data here
        if 'data' in args:
            datatemp = args['data'][:] ## make a copy
            self.plot(datatemp)  ## call plot to resolve pos arguments into self._plot
            del args['data']
        elif 'pos' in args: ## process pos here, an old synonym for data
            postemp = args['pos'][:] ## make a copy
            self.plot(postemp)  ## call plot to resolve pos arguments into self._plot
            del args['pos']

        ## override default vector attributes
        vectorAttributes = ['color', 'dot_color', 'marker_color']
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
            # elif a == 'fast' and _isnotebook and not val:
                # raise AttributeError('"fast = False" is currently not available in a Jupyter notebook.')
            setattr(self, '_'+a, val)

        cmd = {"cmd": objName, "idx": self.idx}

        for a in argsToSend:
            if a == 'interval': continue # do not send to browser; handle here instead
            aval = getattr(self,a)
            if isinstance(aval, vector):
                aval = aval.value
            cmd[a] = aval

        self._constructing = False
        self.appendcmd(cmd)
        
    @property
    def visible(self): return self._visible
    @visible.setter
    def visible(self,val):
        if self._visible and not val:
           self.delete()
        elif val and not self._visible:
            self.plot(self._data)
        self._visible = val
        #self.addattr('visible') # currently GlowScript ignores the visible attribute
    
    @property
    def radius(self): return self._radius
    @radius.setter
    def radius(self,val):
        self._radius = val
        self.addattr('radius')

    @property
    def size(self): return 2*self._radius
    @size.setter
    def size(self,val):
        self._radius = val/2
        self.addattr('radius')

    @property
    def width(self): return self._width
    @width.setter
    def width(self,val):
        self._width = val
        self.addattr('width')

    @property
    def color(self): return self._color
    @color.setter
    def color(self,val):
        if not isinstance(val, vector): raise TypeError('color must be a vector')
        self._color = val
        self.addattr('color')

    @property
    def fast(self): return self._fast
    @fast.setter
    def fast(self,val):
        # if _isnotebook and not val:
            # raise AttributeError('"fast = False" is currently not available in a Jupyter notebook.')
        self._fast = val
        self.addattr('fast')

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
    def interval(self,val):
        self._interval = val
        self._iterations = 0

    def __del__(self):
        cmd = {"cmd": "delete", "idx": self.idx}
        self.appendcmd(cmd)
        super(gobj, self).__del__()

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
        elif 'data' in args:
            return self.resolveargs(args['data'])
        else:
            raise AttributeError("Must be plot(x,y) or plot(pos=[x,y]) or plot([x,y]) or plot([x,y], ...) or plot([ [x,y], ... ])")

    def plot(self, *args1, **args2):
        if self._interval == 0:
            return
        if self._interval > 0:
            self._iterations += 1
            if self._firstplot:
                self._firstplot = False
            elif self._iterations < self._interval:
                return
            self._iterations = 0
        if len(args1) > 0:
            p = self.preresolve1(args1)
        else:
            p = self.preresolve2(args2)
        self._data = self._data + p
        self.addmethod('plot', p)
        
    def delete(self):
        self.addmethod('delete', 'None')
        self._firstplot = True
        self._iterations = 0

    @property
    def label(self): return self._label
    @label.setter
    def label(self,val):
        self._label = val
        self.addattr('label')

    @property
    def legend(self): return self._legend
    @legend.setter
    def legend(self,val):
        self._legend = val
        self.addattr('legend')

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

        super(gcurve, self).setup(args)

    @property
    def markers(self): return self._markers
    @markers.setter
    def markers(self,val):
        self._markers = val
        self.addattr('markers')

    @property
    def marker_color(self): return self._marker_color
    @marker_color.setter
    def marker_color(self,val):
        if not isinstance(val, vector): raise TypeError('marker_color must be a vector')
        self._marker_color = vector(val)
        self.addattr('marker_color')

    @property
    def dot(self): return self._dot
    @dot.setter
    def dot(self,val):
        self._dot = val
        self.addattr('dot')

    @property
    def dot_radius(self): return self._dot_radius
    @dot_radius.setter
    def dot_radius(self,val):
        self._dot_radius = val
        self.addattr('dot_radius')

    @property
    def dot_color(self): return self._dot_color
    @dot_color.setter
    def dot_color(self,val):
        if not isinstance(val, vector): raise TypeError('dot_color must be a vector')
        self._dot_color = vector(val)
        self.addattr('dot_color')

class gdots(gobj):
    def __init__(self, **args):
        args['_objName'] = "gdots"
        super(gdots, self).setup(args)

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
        self._fast = True
        self._foreground = vector(0,0,0)
        self._background = vector(1,1,1)
        self._title = ""
        self._xtitle = ""
        self._ytitle = ""
        self._scroll = False
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
                            'xmin', 'xmax', 'ymin', 'ymax', 'logx', 'logy', 'fast', 'scroll']
        for a in scalarAttributes:
            if a in args:
                argsToSend.append(a)
                setattr(self, '_'+a, args[a])
                del args[a]

        # user defined attributes
        for a in args:
            setattr(self, '_'+a, args[a])

        cmd = {"cmd": objName, "idx": self.idx}

        if self._scroll:
            if not ('xmin' in argsToSend and 'xmax' in argsToSend):
                raise AttributeError("For a scrolling graph, both xmin and xmax must be specified.")
            if self._xmax <= self._xmin:
                raise AttributeError("For a scrolling graph, xmax must be greater than xmin.")

        ## send only args specified in constructor
        for a in argsToSend:
            aval = getattr(self,a)
            if isinstance(aval, vector):
                aval = aval.value
            cmd[a] = aval

        self.appendcmd(cmd)

    @property
    def fast(self): return self._fast
    @fast.setter
    def fast(self,val):
        self._fast = val
        self.addattr('fast')

    @property
    def scroll(self): return self._scroll
    @scroll.setter
    def scroll(self,val):
        self._scroll = val
        self.addattr('scroll')

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
        self._foreground = vector(val)
        self.addattr('foreground')

    @property
    def background(self): return self._background
    @background.setter
    def background(self,val):
        if not isinstance(val,vector): raise TypeError('background must be a vector')
        self._background = vector(val)
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

    @property
    def logx(self): return self._logx
    @logx.setter
    def logx(self,val):
        self._logx = val
        self.addattr('logx')

    @property
    def logy(self): return self._logy
    @logx.setter
    def logy(self,val):
        self._logy = val
        self.addattr('logy')

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
        return c.center-(norm(c.axis)*(c.range / tan(c.fov/2)))
    @pos.setter
    def pos(self, value):
        c = self._canvas
        c.autoscale = False
        c.center = value+self.axis

    @property
    def axis(self):
        c = self._canvas
        return norm(c._axis)*( c.range / tan(c.fov/2) )
    @axis.setter
    def axis(self, value):
        c = self._canvas
        c.autoscale = False
        c.center = self.pos+value # use current self.pos before it is changed by change in c.axis
        c.axis = norm(value)
        c.range = mag(value)*tan(c.fov/2)

    @property
    def up(self):   ## but really this should not exist:  should be scene.up
        return self._canvas.up
    @up.setter
    def up(self, value):
        self._canvas.up = value

    def rotate(self, angle=0, axis=None, origin=None):
        if angle == 0: return
        c = self._canvas
        if axis is None: axis = c.up
        if origin is not None and origin != self.pos:
            origin = self.pos + (self.pos-origin).rotate(angle=angle, axis=axis)
        else:
            origin = self.pos
        if c._axis.diff_angle(axis) > 1e-6:
            c.axis = c._axis.rotate(angle=angle, axis=axis)
        c.up = c._up.rotate(angle=angle, axis=axis)
        c.center = origin + self.axis

class meta_canvas(object):
    @property
    def selected(self):
        return getattr(self, '_selected')
    @selected.setter
    def selected(self, value):
        self._selected = value

class canvas(baseObj):
    selected = None
    hasmouse = None
    maxVertices = 4.2e9  ## 2^32

    def __init__(self, **args):
        baseObj._canvas_constructing = True
        if _isnotebook:
            from IPython.display import display, HTML, Javascript
            display(HTML("""<div id="glowscript" class="glowscript"></div>"""))
            display(Javascript("""if (typeof Jupyter !== "undefined") { window.__context = { glowscript_container: $("#glowscript").removeAttr("id")};}else{ element.textContent = ' ';}"""))

        super(canvas, self).__init__()   ## get idx, attrsupdt

        self._constructing = True
        canvas.selected = self

        if 'lights' in args:
            raise AttributeError("Lights for a canvas can be assigned only after the canvas has been created.")

        self._objz = set()
        self.vertexCount = 0
        self._visible = True
        self._background = vector(0,0,0)
        self._ambient = vector(0.2, 0.2, 0.2)
        self._height = 400 # to match the GlowScript default
        self._width = 640
        self._align = 'none'
        self._fov = pi/3
        self._resizable = True

        # The following determine the view:
        self._range = 1 # user can alter with zoom
        self._axis = vector(0,0,-1) # user can alter with spin
        self._forward = vector(0,0,-1) # self.axis is primal internally; self._forward is now a synonym
        self._up = vector(0,1,0) # user with touch screen can rotate around z
        self._autoscale = True # set False if user zooms
        self._center = vector(0,0,0) # cannot be altered by user
        # Reject JavaScript canvas_update user values immediately following Python setting of values:
        self._set_range = False
        self._set_forward = False
        self._set_center = False
        self._set_up = False
        self._set_autoscale = False

        self._userzoom = True
        self._userspin = True
        self._userpan = True
        self._pixel_to_world = 0
        self._title = ''
        self._caption = ''
        self._mouse = Mouse(self)
        self._binds = {'mousedown':[], 'mouseup':[], 'mousemove':[],'click':[],
                        'mouseenter':[], 'mouseleave':[], 'keydown':[], 'keyup':[],
                        'redraw':[], 'draw_complete':[], 'resize':[]}
                        #'_compound':[]}
            # no key events unless notebook command mode can be disabled
        self._camera = Camera(self)
        self.title_anchor   = [self.idx, 1]  ## used by buttons etc.
        self.caption_anchor = [self.idx, 2]
        cmd = {"cmd": "canvas", "idx": self.idx}

    # send only nondefault values to GlowScript

        canvasVecAttrs = ['background', 'ambient','forward','up', 'center']
        canvasNonVecAttrs = ['visible', 'height', 'width', 'title','fov', 'range','align',
                             'autoscale', 'userzoom', 'userspin', 'userpan', 'title', 'caption']

        for a in canvasNonVecAttrs:
            if a in args:
                if args[a] is not None:
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

        self.lights = [] # delete all lights created by glowcomm.js
        # Add the standard lighting (these lights will be added to self._lights):
        distant_light(direction=vector( 0.22,  0.44,  0.88), color=color.gray(0.8))
        distant_light(direction=vector(-0.88, -0.22, -0.44), color=color.gray(0.3))
        baseObj._canvas_constructing = False

    def follow(self, obj):
        if obj is None:
            self.addmethod('follow', 'None')
        elif callable(obj):
            b = box(visible=False)
            baseObj.follow_objects.append([b, obj, vector(1.2e15,3.4e14,-5.6e13)])
            self.addmethod('follow', b.idx)
        else:
            self.addmethod('follow', obj.idx)

    def select(self):
        canvas.selected = self
        self.addmethod('select','None')

    @classmethod
    def get_selected(cls):
        return cls.selected

    def delete(self):
        self.addmethod('delete','None')

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
    def resizable(self):
        return self._resizable
    @resizable.setter
    def resizable(self,value):
        self._resizable = value
        if not self._constructing:
            self.addattr('resizable')

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
            self._center = self._set_center = vector(value)
            if not self._constructing:
                self.appendcmd({"center":value.value})
        else:
            raise TypeError('center must be a vector')

    @property
    def axis(self):
        return self._axis
    @axis.setter
    def axis(self,value):
        self._axis = self._set_forward = vector(value)
        if not self._constructing:
            self.appendcmd({"forward":value.value})

    @property
    def forward(self): # scene.forward is an external synonym for scene.axis
        return self._axis
    @forward.setter
    def forward(self,value):
        self._axis = self._set_forward = vector(value)
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
    def userpan(self):
        return self._userpan
    @userpan.setter
    def userpan(self,value):
        self._userpan = value
        if not self._constructing:
            self.appendcmd({"userpan":value})

    @property
    def lights(self):
        return self._lights
    @lights.setter
    def lights(self, value):
        if type(value) is list and len(value) == 0:
            # JSON doesn't like an empty list
            self._lights = []
            self.appendcmd({"lights":'empty_list'}) # don't encode this unusual statement
        else:
            raise AttributeError("canvas.lights can be set only to [].")

    @property
    def pixel_to_world(self):
        # Convert number of pixels into distance in real-world coordinates
        w = self._width
        h = self._height
        d = 2*self._range
        if w >= h:
            return d/h
        else:
            return d/w
    @pixel_to_world.setter
    def pixel_to_world(self, value):
        raise AttributeError('pixel_to_world is read-only')

    def capture(self, filename, capture_labels=True):
        if not isinstance(filename, str):
            raise TypeError("'filename' for Capture must be a string.")

        if filename.endswith(".png"):
            filename += ".png"

        include_labels = "T" if capture_labels else "F"
        self.addmethod("capture", include_labels + filename)

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
        global keysdownlist
        ev = evt['event']
        if ev == 'pick':
            self.mouse.setpick( evt )
            self._waitfor = True # what pick is looking for
        elif ev == '_compound': # compound, text, extrusion
            obj = self._compound
            p = evt['pos']
            if obj._objName == 'text':
                obj._length = p[0]
                obj._descender = p[1]
                obj._up.value = list_to_vec(evt['up'])
            else:
                if obj._objName == 'extrusion':
                    obj._color = obj._firstcolor # use the first segment color to represent multicolor extrusions
                # Set attribute_vector.value, which avoids nullifying the
                # on_change functions that detect changes in e.g. obj.pos.y
                obj._pos.value = list_to_vec(p)
                obj._origin = obj._pos
                s = evt['size']
                obj._size.value = obj._size0 = list_to_vec(s)
                obj._axis.value = obj._size._x*norm(obj._axis)
                obj._up.value = list_to_vec(evt['up'])
            self._waitfor = True # what compound and text and extrusion are looking for in _wait()
        elif ev == 'resize':
            if self.resizable and ('resize' in self._binds):
                self.width = evt['width']
                self.height = evt['height']
                del evt['width']
                del evt['height']
                for fct in self._binds['resize']:
                    # inspect the bound function and see what it's expecting
                    a = signature(fct)
                    if str(a) != '()':
                        fct(evt)
                    else:
                        fct()

        else: # pause/waitfor, update_canvas
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
                if ev[:3] != 'key':  # not a key event
                    self.mouse._alt = evt['alt']
                    self.mouse._shift = evt['shift']
                    self.mouse._ctrl = evt['ctrl']
                evt1 = event_return(evt)  ## turn it into an object
                for fct in self._binds[ev]:
                    # inspect the bound function and see what it's expecting
                    a = signature(fct)
                    if str(a) != '()':
                        fct( evt1 )
                    else:
                        fct()

                self._waitfor = evt1 # what pause and waitfor are looking for
            else:  ## user can change forward (spin), range/autoscale (zoom), up (touch), center (pan)
                if 'forward' in evt and self.userspin and not self._set_forward:
                    fwd = evt['forward']
                    self._axis = list_to_vec(fwd) # the fundamental meaning of scene.forward is scene.axis
                self._set_forward = False
                if 'up' in evt and self.userspin and not self._set_up:
                    cup = evt['up']
                    self._up = list_to_vec(cup)
                self._set_up = False
                if 'center' in evt and self.userpan and not self._set_center:
                    center = evt['center']
                    self._center = list_to_vec(center)
                self._set_center = False
                if 'range' in evt and self.userzoom and not self._set_range:
                    self._range = evt['range']
                self._set_range = False
                if 'autoscale' in evt and self.userzoom and not self._set_autoscale:
                    self._autoscale = evt['autoscale']
                self._set_autoscale = False
                if 'keysdown' in evt: keysdownlist = evt['keysdown']


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
        if 'textures' in eventtype: # textures are local; little need to wait
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
            return self._waitfor

    def pause(self,*s):
        if len(s) > 0:
            s = s[0]
            self.addmethod('pause', s)
        else:
            self.addmethod('pause', '')
        _wait(self)
        return self._waitfor

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
        self.which = args['which']
        self.shift = args['shift']
        self.ctrl = args['ctrl']
        self.alt = args['alt']
        if self.event[:3] == 'key':
            self.key = args['key']
        else:
            self.pos = args['pos']
            self.press = args['press']
            self.release = args['release']

class local_light(standardAttributes):
    def __init__(self, **args):
        args['_default_size'] = vector(1,1,1)
        args['_objName'] = "local_light"
        super(local_light, self).setup(args)

        if (canvas.get_selected() is not None):
            canvas.get_selected()._lights.append(self)

    @property
    def offset(self):
        return self._offset
    @offset.setter
    def offset(self, value):
        self._offset = vector(value)
        if not self._constructing:
            self.addattr('offset')

    @property
    def attach_idx(self):
        return self._attach_idx
    @attach_idx.setter
    def attach_idx(self, value):
        self._attach_idx = vector(value)
        if not self._constructing:
            self.addattr('attach_idx')

class distant_light(standardAttributes):
    def __init__(self, **args):
        args['_default_size'] = vector(1,1,1)
        args['_objName'] = "distant_light"
        self._direction = vector(0,0,1)
        super(distant_light, self).setup(args)

        if (canvas.get_selected() is not None):
            canvas.get_selected()._lights.append(self)

    @property
    def direction(self):
        return self._direction
    @direction.setter
    def direction(self, value):
        self._direction = vector(value)
        if not self._constructing:
            self.addattr('direction')

## title_anchor = [canvas.idx, 1] and caption_anchor = [canvas.idx, 2] are attributes of canvas
print_anchor = 3  ## problematic -- intended to point at print area

class wtext(standardAttributes):
    def __init__(self, **args):
        super(wtext, self).__init__()  ## get idx, attrsupdt from baseObj
        argsToSend = ['location', 'text']
        self._constructing = True
        objName = 'wtext'
        self._text = ''
        if 'text' in args:
            self._text = str(args['text'])
        self.location = None
        if 'pos' in args:
            self.location = args['pos']
            if self.location == print_anchor:
                #self.location = [-1, print_anchor]
                raise AttributeError('wtext: Cannot specify "print_anchor" in VPython 7.')
            argsToSend.append('location')
        cmd = {"cmd": objName, "idx": self.idx, "text":self._text}
        if self.location is not None: cmd['location'] = self.location
        self.appendcmd(cmd)
        self._constructing = False

    @property
    def text(self):
        return self._text
    @text.setter
    def text(self, value):
        self._text = str(value)
        if not self._constructing:
            self.addattr('text')

class controls(baseObj):
    attrlists = { 'button': ['text', 'color', 'textcolor', 'background', 'disabled'],
                  'checkbox':['checked', 'text', 'disabled'],
                  'radio':['checked', 'text', 'disabled', 'name'],
                  'menu':['selected', 'choices', 'index', 'disabled'],
                  'slider':['vertical', 'min', 'max', 'step', 'value', 'length',
                            'width', 'left', 'right', 'top', 'bottom', 'align', 'disabled'],
                  'winput':['width', 'height', 'text', 'type', 'disabled']
                }
    def setup(self, args):
        super(controls, self).__init__()  ## get idx, attrsupdt from baseObj
        ## default values of common attributes
        self._constructing = True
        argsToSend = []
        self.objName = args['_objName']
        del args['_objName']
        if 'pos' in args:
            self.location = args['pos']
            if self.location == print_anchor:
                #self.location = [-1, print_anchor]
                raise AttributeError(self.objName+': Cannot specify "print_anchor" in VPython 7.')
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
        vectorAttributes = ['color', 'textcolor', 'background']
        for a in vectorAttributes:
            if a in args:
                val = args[a]
                if a == 'textcolor':
                    del args[a]
                    a = 'color' # textcolor is a legacy attribute; now use color
                argsToSend.append(a)
                if isinstance(val, vector): setattr(self, '_'+a, val)
                else: raise AttributeError(a+' must be a vector')

        ## override default scalar attributes
        for a,val in args.items():
            if a in controls.attrlists[self.objName]:
                argsToSend.append(a)
                setattr(self, '_'+a, val)
            else:
                setattr(self, a, val)
        cmd = {"cmd": self.objName, "idx": self.idx}
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
        raise AttributeError(self.objName+' pos attribute is not available.')
    @pos.setter
    def pos(self, value):
        raise AttributeError(self.objName+' pos attribute cannot be changed.')

    @property
    def disabled(self):
        return self._disabled
    @disabled.setter
    def disabled(self, value):
        self._disabled = value
        if not self._constructing:
            self.addattr('disabled')

    def delete(self):
        self.addmethod('delete', 'None')

    def _ipython_display_(self): # don't print something when making an (anonymous) object
        pass

class button(controls):
    def __init__(self, **args):
        args['_objName'] = 'button'
        self._text = ""
        self._color = color.black
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
    def textcolor(self): # legacy; now use color instead of textcolor
        return self._color
    @textcolor.setter
    def textcolor(self, value):
        self._color = vector(value)
        if not self._constructing:
            self.addattr('color')

    @property
    def color(self): # legacy; now use color instead of textcolor
        return self._color
    @color.setter
    def color(self, value):
        self._color = vector(value)
        if not self._constructing:
            self.addattr('color')

    @property
    def background(self):
        return self._background
    @background.setter
    def background(self, value):
        self._background = vector(value)
        if not self._constructing:
            self.addattr('background')

class checkbox(controls):
    def __init__(self, **args):
        args['_objName'] = 'checkbox'
        self._checked = False
        self._text = ''
        self._name = ''
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

_radio_groups = {} # radio buttons grouped by name

class radio(controls):
    def __init__(self, **args):
        args['_objName'] = 'radio'
        self._checked = False
        self._text = ''
        self._name = ''
        super(radio, self).setup(args)
        if type(self._name) != str:
            raise AttributeError("A radio group name must be a string.")
        if self._name != '':
            if self._name in _radio_groups:
                _radio_groups[self._name].append(self)
            else:
                _radio_groups[self._name] = [self]

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
        if self._checked == value: return
        if len(self._name) > 0:
            for r in _radio_groups[self.name]:
                r._checked = False
        self._checked = value
        if not self._constructing:
            self.addattr('checked')

    @property
    def name(self):
        return self._name
    @name.setter
    def name(self, value):
        if not self._constructing:
            raise AttributeError('Cannot change the name attribute of a radio widget.')

class winput(controls):
    def __init__(self, **args):
        args['_objName'] = 'winput'
        self._checked = False
        self._text = ''
        self._type = 'numeric'
        self._number = None
        self._width = 100
        self._height = 20
        super(winput, self).setup(args)

    @property
    def text(self):
        return self._text
    @text.setter
    def text(self, value):
        self._text = value
        if not self._constructing:
            self.addattr('text')

    @property
    def number(self):
        return self._number
    @number.setter
    def number(self, value):
        raise AttributeError('Cannot change the winput number attribute.')

    @property
    def width(self):
        return self._width
    @width.setter
    def width(self, value):
        raise AttributeError('Cannot change the winput width attribute.')

    @property
    def type(self):
        return self._type
    @type.setter
    def type(self, value):
        raise AttributeError('Cannot change the winput type attribute.')

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
        self._choices = value
        self.addattr('choices')

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
        self._disabled = False
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
        if 'path' not in args:
            raise AttributeError("An extrusion must have a path.")
        if 'shape' not in args:
            raise AttributeError("An extrusion must have a shape.")
        self.check_shape(args['shape'])
        savesize = None
        if 'size' in args:
            savesize = args['size']
            del args['size']
        self._shape = [ ]
        self._pathlength = len(args['path'])
        args['path'] = self.vecs_to_list(args, 'path')
        if 'color' in args:
            if isinstance(args['color'], vector): args['_firstcolor'] = args['color']
            else: args['_firstcolor'] = args['color'][0]
            args['color'] = self.vecs_to_list(args, 'color')
        else:
            args['_firstcolor'] = vector(1,1,1)
        for attr in ['scale', 'xscale', 'yscale', 'twist']:
            if attr in args and isinstance(args[attr],list) and len(args[attr]) != self._pathlength:
                raise AttributeError("The "+attr+" list must be the same length as the list of points on the path ("+str(self._pathlength)+").")

        super(extrusion, self).setup(args)

        self.canvas._compound = self # used by event handler to update pos and size
        _wait(self.canvas)
        if savesize is not None:
            self._size = savesize

    def vecs_to_list(self, a, attr):
        pozz = a[attr]
        if isinstance(pozz, vector): return pozz.value
        if len(pozz) != self._pathlength:
            raise AttributeError("The "+attr+" list must be the same length as the list of points on the path ("+str(self._pathlength)+").")
        npozz = []
        for pp in pozz:
            npozz.append(pp.value)  ## convert vectors to lists
        return npozz[:]

    @property
    def axis(self):
        return self._axis
    @axis.setter
    def axis(self,value): # extrusion axis and size don't interact
        self._save_oldaxis = adjust_up(self._axis, value, self._up, self._save_oldaxis) # this sets self._axis and self._up
        if not self._constructing:
            # must update both axis and up when either is changed
            self.addattr('axis')
            self.addattr('up')

    @property
    def size(self):
        return self._size
    @size.setter
    def size(self,value): # extrusion axis and size don't interact
        self._size.value = value
        if not self._constructing:
            self.addattr('size')

    def level(self,a):
    	# Determine format of shape specification:
        #    return 1 if a = [S, S, ...] where S is [x,y]
        #    return 2 if a = [ [S, S, ... ], [S, S, ...], [S, S, ...] ]
        #    return 3 if a = [ [ [S, S, ... ], [S, S, ...], [S, S, ...] ],
        #                      [ [S, S, ... ], [S, S, ...], [S, S, ...] ], ... ]
        if not (type(a) is list or type(a) is tuple): raise AttributeError("A shape must be a list of [x,y] elements.")
        if not (type(a[0]) is list or type(a[0]) is tuple): raise AttributeError("A shape must be a list of [x,y] elements.")
        if type(a[0][0]) is int or type(a[0][0]) is float: return 1
        if type(a[0][0][0]) is int or type(a[0][0][0]) is float: return 2
        if type(a[0][0][0][0]) is int or type(a[0][0][0][0]) is float: return 3
        raise AttributeError("A shape must be a list of lists of [x,y] elements.")

    def check_shape(self, a): # check that all shapes are closed
        n = self.level(a)
        if n == 1:
            p1 = a[0]
            p2 = a[-1]
            if not (p1[0] == p2[0] and p1[1] == p2[1]):
                raise AttributeError("An extrusion shape must be closed.")
        elif n == 2:
            for b in a:
                p1 = b[0]
                p2 = b[-1]
                if not (p1[0] == p2[0] and p1[1] == p2[1]):
                    raise AttributeError("An extrusion shape must be closed.")
        else:
            for c in a:
                for b in c:
                    p1 = b[0]
                    p2 = b[-1]
                    if not (p1[0] == p2[0] and p1[1] == p2[1]):
                        raise AttributeError("An extrusion shape must be closed.")

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
    def smooth(self):
        if self._constructing:
            return self._smooth
        else:
            return None
    @smooth.setter
    def smooth(self, value):
        raise AttributeError('smooth cannot be changed after extrusion is created')

    def checkjointlist(self, js, name):
        if not isinstance(js, list): raise AttributeError(name+' must be a list of joint indices.')
        for k in js:
            if k < 0 or k > self._pathlength:
               raise AttributeError(str(k)+' is not in the range of joints in the path (0-'+str(self._pathlength-1)+').')
        
    @property
    def smooth_joints(self):
        if self._constructing:
            self.checkjointlist(self._smooth_joints, 'smooth_joints')
            return self._smooth_joints
        else:
            return None
    @smooth_joints.setter
    def smooth_joints(self, value):
        raise AttributeError('smooth_joints cannot be changed after extrusion is created')
        
    @property
    def sharp_joints(self):
        if self._constructing:
            self.checkjointlist(self._sharp_joints, 'sharp_joints')
            return self._sharp_joints
        else:
            return None
    @sharp_joints.setter
    def sharp_joints(self, value):
        raise AttributeError('sharp_joints cannot be changed after extrusion is created')

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

    @property
    def start_normal(self):
        if self._constructing:
            return self._start_normal
        else:
            return None
    @start_normal.setter
    def start_normal(self,value):
        raise AttributeError('start_normal cannot be changed after extrusion is created')

    @property
    def end_normal(self):
        if self._constructing:
            return self._end_normal
        else:
            return None
    @end_normal.setter
    def end_normal(self,value):
        raise AttributeError('end_normal cannot be changed after extrusion is created')

    @property
    def twist(self):
        if self._constructing:
            return self._twist
        else:
            return None
    @twist.setter
    def twist(self,value):
        raise AttributeError('twist cannot be changed after extrusion is created')

    @property
    def scale(self):
        if self._constructing:
            return self._scale
        else:
            return None
    @scale.setter
    def scale(self,value):
        raise AttributeError('scale cannot be changed after extrusion is created')

    @property
    def xscale(self):
        if self._constructing:
            return self._xscale
        else:
            return None
    @xscale.setter
    def xscale(self,value):
        raise AttributeError('xscale cannot be changed after extrusion is created')

    @property
    def yscale(self):
        if self._constructing:
            return self._yscale
        else:
            return None
    @yscale.setter
    def yscale(self,value):
        raise AttributeError('xscale cannot be changed after extrusion is created')

    @property
    def yscale(self):
        if self._constructing:
            return self._yscale
        else:
            return None
    @yscale.setter
    def yscale(self,value):
        raise AttributeError('xscale cannot be changed after extrusion is created')

class text(standardAttributes):

    def __init__(self, **args):
        self._sizing = False # no axis/size connection
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
        _special_clone = None
        if ('size' in args): raise AttributeError("The text object has no size attribute.")
        if '_cloneid' in args:
            _special_clone = args['_cloneid']
            self._lines = len(args['_text'].split('\n'))
        else:
            if 'text' in args:
                self._lines = len(args['text'].split('\n'))
            else:
                raise AttributeError('A text object must have a text attribute')
        if 'color' in args:
            self._start_face_color = args['color']
            self._end_face_color = args['color']

        super(text, self).setup(args)

        if _special_clone is None:
            self.canvas._compound = self # used by event handler to update pos and size
            _wait(self.canvas) # sets _length, _descender, up

    @property
    def size(self):
        raise AttributeError("The text object has no size attribute.")
        raise AttributeError("The text object has no size attribute.")
    @size.setter
    def size(self, val):
        raise AttributeError("The text object has no size attribute.")

    @property
    def axis(self):
        return self._axis
    @axis.setter
    def axis(self,value): # changing axis does not affect size
        old = vector(self.axis)
        u = self.up
        self._axis.value = value
        self._save_oldaxis = adjust_up(norm(old), self._axis, self._up, self._save_oldaxis)
        self.addattr('axis')
        self.addattr('up')

    @property
    def length(self):
        return self._length
    @length.setter
    def length(self, val):
        if self._constructing:
            raise AttributeError("text length can't be set when creating a text object")
        else:
            self._length = val
            self.addattr('length')

    @property
    def height(self):
        return self._height
    @height.setter
    def height(self, val):
        if self._constructing:
            self._height = val
        else:
            if val == self._height: return
            self._height = val
            self.addattr('height')

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
            self._depth = val
            self.addattr('depth')

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

def keysdown():
    global keysdownlist
    keys = []
    for k in keysdownlist: # return a copy of keysdownlist
        keys.append(k)
    return keys

# global variable for type of web browser to display vpython
_browsertype = 'default'
def set_browser(type='default'):
    global _browsertype
    if type=='pyqt':
        _browsertype='pyqt'
    else:
        _browsertype='default'
