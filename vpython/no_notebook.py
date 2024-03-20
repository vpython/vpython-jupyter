from .vpython import GlowWidget, baseObj, vector, canvas, _browsertype
from ._notebook_helpers import _in_spyder, _undo_vpython_import_in_spyder, _in_spyder_or_similar_IDE

from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import platform
import sys
import threading
import json
import webbrowser as _webbrowser
import asyncio
from autobahn.asyncio.websocket import WebSocketServerProtocol, WebSocketServerFactory
import txaio
import copy
import socket
import multiprocessing
import time

import signal
from urllib.parse import unquote

from .rate_control import rate

makeDaemonic = (platform.system() == "Windows")

# Redefine `Thread.run` to not show a traceback for Spyder when stopping
# the server by raising a KeyboardInterrupt or SystemExit.
if _in_spyder_or_similar_IDE:
    def install_thread_stopped_message():
        """
        Workaround to prevent showing a traceback when VPython server stops.

        See:
        https://bugs.python.org/issue1230540
        """
        run_old = threading.Thread.run

        def run(*args, **kwargs):
            try:
                run_old(*args, **kwargs)
            except (KeyboardInterrupt, SystemExit):
                pass
                # ("VPython server stopped.")
            except:
                raise
        threading.Thread.run = run

    install_thread_stopped_message()



# Check for Ctrl+C. SIGINT will also be sent by our code if WServer is closed.
def signal_handler(signal, frame):
    #print("in signal handler, calling stop server")
    try:
        stop_server()
    except (KeyboardInterrupt):
        pass
    except:
        raise

signal.signal(signal.SIGINT, signal_handler)

# Requests from client to http server can be the following:
#    get glowcomm.html, library .js files, images, or font files


def find_free_port(port=0):
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #if hasattr(socket, 'SO_REUSEPORT'):        # This may be required on systems that support it. Needs testing.
    #    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    try :
        s.bind(('', port))  # bind to a port
    except:
        raise
    return s.getsockname()[1]

if "VPYTHON_HTTP_PORT" in os.environ:
    __HTTP_PORT = int(os.environ["VPYTHON_HTTP_PORT"])
else:
    __HTTP_PORT = find_free_port()

__SOCKET_PORT = find_free_port()

try:
    if platform.python_implementation() == 'PyPy':
        # use port number between 9000 and 9999 for PyPy
        __SOCKET_PORT = 9000 + __SOCKET_PORT % 1000
except:
    pass

# try: # machinery for reusing ports
    # fd = open('free_ports')
    # __HTTP_PORT = int(fd.readline())
    # __SOCKET_PORT = int(fd.readline())
# except:
    # __HTTP_PORT = find_free_port()
    # __SOCKET_PORT = find_free_port()
    # fd = open('free_ports', 'w') # this writes to user program's directory
    # fd.write(str(__HTTP_PORT))
    # fd.write('\n')
    # fd.write(str(__SOCKET_PORT))

# Make it possible for glowcomm.html to find out what the websocket port is:
js = __file__.replace(
    'no_notebook.py', 'vpython_libraries' + os.sep + 'glowcomm.html')

with open(js) as fd:
    glowcomm_raw = fd.read()


def glowcomm_with_socket_port(port):
    global glowcomm_raw
    # provide glowcomm.html with socket number
    return glowcomm_raw.replace('XXX', str(port))


glowcomm = glowcomm_with_socket_port(__SOCKET_PORT)

httpserving = False
websocketserving = False


class serveHTTP(BaseHTTPRequestHandler):
    serverlib = __file__.replace('no_notebook.py', 'vpython_libraries')
    serverdata = __file__.replace('no_notebook.py', 'vpython_data')
    mimes = {'html': ['text/html', serverlib],
             'js': ['application/javascript', serverlib],
             'css': ['text/css', serverlib],
             'jpg': ['image/jpg', serverdata],
             'png': ['image/png', serverlib],
             'otf': ['application/x-font-otf', serverdata],
             'ttf': ['application/x-font-ttf', serverdata],
             'ico': ['image/x-icon', serverdata]}

    def do_GET(self):
        global httpserving
        httpserving = True
        html = False
        if self.path == "/":
            self.path = 'glowcomm.html'
            html = True
        elif self.path[0] == "/":
            self.path = os.sep + self.path[1:]
        f = self.path.rfind('.')
        fext = None
        if f > 0:
            fext = self.path[f + 1:]
        if fext in self.mimes:
            mime = self.mimes[fext]
            # For example, mime[0] is image/jpg,
            # mime[1] is C:\Users\Bruce\Anaconda3\lib\site-packages\vpython\vpython_data
            self.send_response(200)
            self.send_header('Content-type', mime[0])
            self.end_headers()
            if not html:
                path = unquote(self.path)  # convert %20 to space, for example
                # Now path can be for example \Fig 4.6.jpg
                # user current working directory, e.g. D:\Documents\0GlowScriptWork\LocalServer
                cwd = os.getcwd()
                loc = cwd + path
                if not os.path.isfile(loc):
                    loc = mime[1] + path  # look in vpython_data
                fd = open(loc, 'rb')
                self.wfile.write(fd.read())
            else:
                # string.encode() is not available in Python 2.7, but neither is async
                self.wfile.write(glowcomm.encode('utf-8'))

    def log_message(self, format, *args):  # this overrides server stderr output
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
    # no-notebook version of VPython requires Python 3.5.3 or later.
    # @asyncio.coroutine
    # def onMessage(self, data, isBinary): # data includes canvas update, events, pick, compound
    # data includes canvas update, events, pick, compound
    async def onMessage(self, data, isBinary):
        baseObj.handle_attach()  # attach arrow and attach trail

        baseObj.sent = False  # tell main thread that we're preparing to send data to browser
        while True:
            try:
                objdata = copy.deepcopy(baseObj.updates)
                attrdata = copy.deepcopy(baseObj.attrs)
                baseObj.initialize()  # reinitialize baseObj.updates
                break
            except:
                pass
        for a in attrdata:  # a is [idx, attr]
            idx, attr = a
            val = getattr(baseObj.object_registry[idx], attr)
            if type(val) is vector:
                val = [val.x, val.y, val.z]
            if idx in objdata['attrs']:
                objdata['attrs'][idx][attr] = val
            else:
                objdata['attrs'][idx] = {attr: val}
        objdata = baseObj.package(objdata)
        jdata = json.dumps(objdata, separators=(',', ':')).encode('utf_8')
        self.sendMessage(jdata, isBinary=False)
        baseObj.sent = True

        if data != b'trigger':  # b'trigger' just asks for updates
            d = json.loads(data.decode("utf_8"))  # update_canvas info
            for m in d:
                # Must send events one at a time to GW.handle_msg because bound events need the loop code:
                # message format used by notebook
                msg = {'content': {'data': [m]}}
                loop = asyncio.get_event_loop()
                try:
                    await loop.run_in_executor(None, GW.handle_msg, msg)
                except:
                    #
                    # this will throw a runtime exception after the main Thread
                    # has stopped, but we don't really case since the main thread
                    # is no longer there to do anything anyway.
                    if threading.main_thread().is_alive():
                        raise
                    else:
                        pass
                    
    def onClose(self, wasClean, code, reason):
        """Called when browser tab is closed."""
        global websocketserving

        self.connection = None

        # We r done serving, let everyone else know...
        websocketserving = False

        # The cleanest way to get a fresh browser tab going in spyder
        # is to force vpython to be reimported each time the code is run.
        #
        # Even though this code is repeated in stop_server below we also
        # need it here because in spyder the script may have stopped on its
        # own ( because it has no infinite loop in it ) so the only signal
        # that the tab has been closed comes via the websocket.
        if _in_spyder_or_similar_IDE:
            _undo_vpython_import_in_spyder()

        # We want to exit, but the main thread is running.
        # Only the main thread can properly call sys.exit, so have a signal
        # handler call it on the main thread's behalf.
        if platform.system() == 'Windows':
            if threading.main_thread().is_alive() and not _in_spyder_or_similar_IDE:
                # On windows, if we get here then this signal won't be caught
                # by our signal handler. Just call it ourselves.
                os.kill(os.getpid(), signal.CTRL_C_EVENT)
            else:
                stop_server()
        else:
            os.kill(os.getpid(), signal.SIGINT)


try:
    no_launch = os.environ.get("VPYTHON_NO_LAUNCH_BROWSER", False)
    if no_launch=="0":
        no_launch=False
    if platform.python_implementation() == 'PyPy':
        server_address = ('', 0)      # let HTTPServer choose a free port
        __server = HTTPServer(server_address, serveHTTP)
        port = __server.server_port   # get the chosen port
        # Change the global variable to store the actual port used
        __HTTP_PORT = port
        if not no_launch:
            _webbrowser.open('http://localhost:{}'.format(port)
                         )  # or webbrowser.open_new_tab()
    else:
        __server = HTTPServer(('', __HTTP_PORT), serveHTTP)
        # or webbrowser.open_new_tab()
        if not no_launch:
            if _browsertype == 'default':  # uses default browser
                _webbrowser.open('http://localhost:{}'.format(__HTTP_PORT))

except:
    pass


if _browsertype == 'pyqt':
    if platform.python_implementation() == 'PyPy':
        raise RuntimeError('The pyqt browser cannot be used PyPy. Please use '
                           'the default browser instead by removing '
                           'set_browser("pyqt") from your code.')
    elif sys.platform.startswith('win'):
        raise RuntimeError('The pyqt browser cannot be used on Windows. '
                           'Please use the default browser instead by '
                           'removing set_browser("pyqt") from your code.')
    elif sys.version_info.major == 3 and sys.version_info.minor >= 8:
        raise RuntimeError('The pyqt browser cannot be used on Python 3.8. '
                           'Please use the default browser instead by '
                           'removing set_browser("pyqt") from your code.')


def start_Qapp(port):
    # creates a python browser with PyQt5
    # runs qtbrowser.py in a separate process
    filepath = os.path.dirname(__file__)
    filename = filepath + '/qtbrowser.py'
    os.system('python ' + filename + ' http://localhost:{}'.format(port))


# create a browser in its own process
if _browsertype == 'pyqt':
    __m = multiprocessing.Process(target=start_Qapp, args=(__HTTP_PORT,))
    __m.start()

__w = threading.Thread(target=__server.serve_forever, daemon=makeDaemonic)
__w.start()


def start_websocket_server():
    """
    Function to get the websocket server going and run the event loop
    that feeds it.
    """
    # We need a new loop in case some other process has already started the
    # main loop. In principle we might be able to do a check for a running
    # loop but this works whether or not a loop is running.
    __interact_loop = asyncio.new_event_loop()

    # Need to do two things before starting the server factory:
    #
    # 1. Set our loop to be the default event loop on this thread
    asyncio.set_event_loop(__interact_loop)
    # 2. Line below is courtesy of
    # https://github.com/crossbario/autobahn-python/issues/1007#issuecomment-391541322
    txaio.config.loop = __interact_loop

    # Now create the factory, start the server then run the event loop forever.
    __factory = WebSocketServerFactory(u"ws://localhost:{}/".format(__SOCKET_PORT))
    __factory.protocol = WSserver
    __coro = __interact_loop.create_server(__factory, '0.0.0.0', __SOCKET_PORT)
    __interact_loop.run_until_complete(__coro)
    __interact_loop.run_forever()


# Put the websocket server in a separate thread running its own event loop.
# That works even if some other program (e.g. spyder) already running an
# async event loop.
__t = threading.Thread(target=start_websocket_server, daemon=makeDaemonic)
__t.start()


def stop_server():
    """Shuts down all threads and exits cleanly."""
    #print("in stop server")
    global __server
    __server.shutdown()

    event_loop = txaio.config.loop
    event_loop.stop()
    # We've told the event loop to stop, but it won't shut down until we poke
    # it with a simple scheduled task.
    event_loop.call_soon_threadsafe(lambda: None)

    # If we are in spyder, undo our import. This gets done in the websocket
    # server onClose above if the browser tab is closed but is not done
    # if the user stops the kernel instead.
    if _in_spyder_or_similar_IDE:
        _undo_vpython_import_in_spyder()

    # We don't want Ctrl-C to try to sys.exit inside spyder, i.e.
    # in an ipython console with a separate python kernel running.
    if _in_spyder_or_similar_IDE:
        raise KeyboardInterrupt

    if threading.main_thread().is_alive():
        #print("main is alive...")
        sys.exit(0)
    else:
        #
        # check to see if the event loop is still going, if so join it.
        #
        #print("main is dead..")
        if __t.is_alive():
            #print("__t is alive still")
            if threading.get_ident() != __t.ident:
                #print("but it's not my thread, so I'll join...")
                __t.join()
            else:
                #print("__t is alive, but that's my thread! So skip it.")
                pass
        else:
            if makeDaemonic:
                sys.exit(0)

        # If the main thread has already stopped, the python interpreter
        # is likely just running .join on the two remaining threads (in
        # python/threading.py:_shutdown). Since we just stopped those threads,
        # we'll now exit.
        
GW = GlowWidget()

while not (httpserving and websocketserving):  # try to make sure setup is complete
    time.sleep(0.1)


# Dummy variable to import
_ = None

