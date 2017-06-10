from .vpython import *

from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import threading
import json
import webbrowser as _webbrowser
import asyncio
from autobahn.asyncio.websocket import WebSocketServerProtocol, WebSocketServerFactory

# Requests from client to http server can be the following:
#    get glowcomm.html, library .js files, images, or font files

import socket

def find_free_port():
    s = socket.socket()
    s.bind(('',0)) # find an available port
    return s.getsockname()[1]

__HTTP_PORT = find_free_port()
__SOCKET_PORT = find_free_port()
# Make it possible for glowcomm.html to find out what the websocket port is:
js = __file__.replace('no_notebook.py','vpython_libraries'+os.sep+'socket_port.js')
fd = open(js,'w')
fd.write('function socket_port() {'+'return {}'.format(__SOCKET_PORT)+'}')
fd.close()

httpserving = False
websocketserving = False

class serveHTTP(BaseHTTPRequestHandler):
    serverlib = __file__.replace('no_notebook.py','vpython_libraries')
    serverdata = __file__.replace('no_notebook.py','vpython_data')
    mimes = {'html':['text/html', serverlib],
              'js' :['application/javascript', serverlib],
              'css':['text/css', serverlib],
              'jpg':['image/jpg', serverdata],
              'png':['image/png', serverlib],
              'otf':['application/x-font-otf', serverdata],
              'ttf':['application/x-font-ttf', serverdata],
              'ico':['image/x-icon', serverdata]}
        
    def do_GET(self):
        global httpserving
        httpserving = True
        if self.path == "/":
            self.path = os.sep+'glowcomm.html'
        elif self.path[0] == "/":
            self.path = os.sep+self.path[1:]
        f = self.path.rfind('.')
        fext = None
        if f > 0: fext = self.path[f+1:]
        try:
            if fext in self.mimes:
                mime = self.mimes[fext]
                loc = mime[1] + self.path
                fd = open(loc, 'rb') 
                self.send_response(200)
                self.send_header('Content-type', mime[0])
                self.end_headers()
                self.wfile.write(fd.read())
                fd.close()
        except IOError:
                self.send_error(404,'File Not Found: {}'.format(self.path))
                    
    def log_message(self, format, *args): # this overrides server stderr output
        return

# Requests from client to websocket server can be the following:
# trigger event; return data (constructors, attributes, methods)
# other event; pause, waitfor, pick, compound

class WSserver(WebSocketServerProtocol):
    # Data sent and received must be type "bytes", so use string.encode and string.decode
    connection = None

    def onConnect(self, request):
        self.connection = self

    def onOpen(self):
        global websocketserving
        websocketserving = True

    # For Python 3.5 and later, the newer syntax eliminates "@asyncio.coroutine"
    # in favor of "async def onMessage...", and "yield from" with "await".
    # Attempting to use the older Python 3.4 syntax was not successful, so this
    # no-notebook version of VPython requires Python 3.5 or later.
    #@asyncio.coroutine
    #def onMessage(self, data, isBinary): # data includes canvas update, events, pick, compound
    async def onMessage(self, data, isBinary): # data includes canvas update, events, pick, compound
        baseObj.handle_attach() # attach arrow and attach trail

        baseObj.sent = False # tell main thread that we're preparing to send data to browser
        while True:
            try:
                objdata = copy.deepcopy(baseObj.updates)
                attrdata = copy.deepcopy(baseObj.attrs)
                baseObj.initialize() # reinitialize baseObj.updates
                break
            except:
                pass
        for a in attrdata: # a is [idx, attr]
            idx, attr = a
            val = getattr(baseObj.object_registry[idx], attr)
            if type(val) is vec: val = [val.x, val.y, val.z]
            if idx in objdata['attrs']:
                objdata['attrs'][idx][attr] = val
            else:
                objdata['attrs'][idx] = {attr:val}
        objdata = baseObj.package(objdata)
        jdata = json.dumps(objdata, separators=(',', ':')).encode('utf_8')
        self.sendMessage(jdata, isBinary=False)
        baseObj.sent = True
        
        if data != b'trigger': # b'trigger' just asks for updates
            d = json.loads(data.decode("utf_8")) # update_canvas info
            for m in d:
                # Must sent events one at a time to GW.handle_msg because bound events need the loop code:
                msg = {'content':{'data':[m]}} # message format used by notebook=
                if 'bind' in m: # will execute a function that may contain waitfor etc. statements
                    loop = asyncio.get_event_loop()
                    #yield from loop.run_in_executor(None, GW.handle_msg, msg)
                    await loop.run_in_executor(None, GW.handle_msg, msg)
                else:
                    GW.handle_msg(msg)

    def onClose(self, wasClean, code, reason):
        #print("Server WebSocket connection closed: {0}".format(reason))
        self.connection = None

__server = HTTPServer(('', __HTTP_PORT), serveHTTP)
_webbrowser.open('http://localhost:{}'.format(__HTTP_PORT)) # or webbrowser.open_new_tab()
__w = threading.Thread(target=__server.serve_forever)
__w.start()

__factory = WebSocketServerFactory(u"ws://localhost:{}/".format(__SOCKET_PORT))
__factory.protocol = WSserver
__interact_loop = asyncio.get_event_loop()
__coro = __interact_loop.create_server(__factory, '0.0.0.0', __SOCKET_PORT)
__interact_loop.run_until_complete(__coro)
# server.handle_request() is a single-shot interaction
# one-shot interact:
#interact_loop.stop()
#interact_loop.run_forever()
# Need to put interact loop inside a thread in order to get a display
# in the absence of a loop containing a rate statement.
__t = threading.Thread(target=__interact_loop.run_forever)
__t.start()

while not (httpserving and websocketserving): # try to make sure setup is complete
    rate(60)

GW = GlowWidget(None, None)

scene = canvas()

# This must come after creating a canvas
class MISC(baseObj):
    def __init__(self):
        super(MISC, self).__init__() 
    
    def prnt(self, s):
        self.addmethod('GSprint', s)

__misc = MISC()

def GSprint(*args):
    s = ''
    for a in args:
        s += str(a)+' '
    s = s[:-1]
    __misc.prnt(s)

