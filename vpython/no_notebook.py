from .vpython import *

from http.server import BaseHTTPRequestHandler, HTTPServer
from os import sep
import threading
import json
import webbrowser as _webbrowser
import asyncio
from autobahn.asyncio.websocket import WebSocketServerProtocol, WebSocketServerFactory

# Requests from client to http server can be the following:
#    get glowcomm.html, library .js files, images, or font files

GW = None

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
        global GW
        if GW is None: GW = GlowWidget(None, None)
        if self.path == "/":
            self.path = sep+'glowcomm.html'
        elif self.path[0] == "/":
            self.path = sep+self.path[1:]
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
        global GW
        if GW is None: GW = GlowWidget(None, None)

    # For Python 3.5 and later, the newer syntax eliminates "@asyncio.coroutine"
    # in favor of "async def onMessage...", and "yield from" with "await".
    @asyncio.coroutine
    def onMessage(self, data, isBinary): # data includes canvas update, events, pick, compound
        global _sent
        _sent = False
        baseObj.handle_attach() # attach arrow and attach trail
        while True:
            try:
                objdata = copy.deepcopy(baseObj.updates)
                baseObj.initialize() # reinitialize baseObj.updates
                break
            except:
                pass
        objdata = baseObj.package(objdata)
        jdata = json.dumps(objdata, separators=(',', ':')).encode('utf_8')
        self.sendMessage(jdata, isBinary=False)
        _sent = True
        if data != b'trigger': # b'trigger' just asks for updates
            d = json.loads(data.decode("utf_8")) # update_canvas info
            for m in d:
                # Must sent events one at a time to GW.handle_msg because bound events need the loop code:
                msg = {'content':{'data':[m]}} # message format used by notebook=
                if 'bind' in m: # will execute a function that may contain waitfor etc. statements
                    loop = asyncio.get_event_loop()
                    yield from loop.run_in_executor(None, GW.handle_msg, msg)
                else:
                    GW.handle_msg(msg)

    def onClose(self, wasClean, code, reason):
        #print("Server WebSocket connection closed: {0}".format(reason))
        self.connection = None

__SOCKET_PORT = 9001
__factory = WebSocketServerFactory(u"ws://localhost:{}/".format(__SOCKET_PORT))
__factory.protocol = WSserver
__interact_loop = asyncio.get_event_loop()
__coro = __interact_loop.create_server(__factory, '0.0.0.0', __SOCKET_PORT)
__interact_loop.run_until_complete(__coro)
#interact_loop.stop()
#interact_loop.run_forever()
# Need to put interact loop inside a thread in order to get a display
# in the absence of a loop containing a rate statement.
__t = threading.Thread(target=__interact_loop.run_forever)
__t.start()

__HTTP_PORT = 9000
__server = HTTPServer(('', __HTTP_PORT), serveHTTP)
_webbrowser.open('http://localhost:{}'.format(__HTTP_PORT)) # or webbrowser.open_new_tab()
__w = threading.Thread(target=__server.serve_forever)
__w.start()
# server.handle_request() is a single-shot interaction

while baseObj.glow is None: # try to make sure setup is complete
    rate(60)

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

def print_to_string(*args): # treatment of <br> vs. \n not quite right here
    s = ''
    for a in args:
        s += str(a)+' '
    s = s[:-1]
    return(s)

