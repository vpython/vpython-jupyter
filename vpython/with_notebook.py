import os
import time

from jupyter_core.paths import jupyter_data_dir
import notebook
import IPython
from IPython.display import display, Javascript
import ipykernel

from .vpython import GlowWidget, baseObj, canvas
from .rate_control import ws_queue
from . import __version__

import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
import socket
import json
import asyncio
import logging

def find_free_port():
    s = socket.socket()
    s.bind(('',0)) # find an available port
    return s.getsockname()[1]

__SOCKET_PORT = find_free_port()

try:
    if platform.python_implementation() == 'PyPy':
        __SOCKET_PORT = 9000 + __SOCKET_PORT % 1000     # use port number between 9000 and 9999 for PyPy
except:
    pass


#### Setup for Jupyter VPython

# The following file operations check whether nbextensions already has the correct files.
package_dir = os.path.dirname(__file__) # The location in site-packages of the vpython module
datacnt = len(os.listdir(package_dir+"/vpython_data"))     # the number of files in the site-packages vpython data folder
libcnt = len(os.listdir(package_dir+"/vpython_libraries")) # the number of files in the site-packages vpython libraries folder
jd = jupyter_data_dir()
nbdir = jd+'/nbextensions/'
nbdata = nbdir+'vpython_data'
nblib = nbdir+'vpython_libraries'
transfer = True # need to transfer files from site-packages to nbextensions

### If JupyterLab is installed then copy vpython_data directory to static dir in Jupytarlab Application Directory
try:
	import jupyterlab
	import jupyterlab.commands
	from os.path import join
	labextensions_dir = join(jupyterlab.commands.get_app_dir(), u'static')
	notebook.nbextensions.install_nbextension(path = package_dir+"/vpython_data",nbextensions_dir = labextensions_dir,overwrite = False,verbose = 0)
except ImportError:
	#logging.info("Unable to import jupyterlab")
	pass

if 'nbextensions' in os.listdir(jd):
    ldir = os.listdir(nbdir)
    if ('vpython_data' in ldir and len(os.listdir(nbdata)) == datacnt and
       'vpython_libraries' in ldir and len(os.listdir(nblib)) == libcnt and
        'vpython_version.txt' in ldir):
        v = open(nbdir+'/vpython_version.txt').read()
        transfer = (v != __version__) # need not transfer files to nbextensions if correct version's files already there

if transfer:
    if IPython.__version__ >= '4.0.0' :
        notebook.nbextensions.install_nbextension(path = package_dir+"/vpython_data",overwrite = True,user = True,verbose = 0)
        notebook.nbextensions.install_nbextension(path = package_dir+"/vpython_libraries",overwrite = True,user = True,verbose = 0)
    elif IPython.__version__ >= '3.0.0' :
        IPython.html.nbextensions.install_nbextension(path = package_dir+"/vpython_data",overwrite = True,user = True,verbose = 0)
        IPython.html.nbextensions.install_nbextension(path = package_dir+"/vpython_libraries",overwrite = True,user = True,verbose = 0)
    else:
        IPython.html.nbextensions.install_nbextension(files = [package_dir+"/vpython_data", package_dir+"/vpython_libraries"],overwrite=True,verbose=0)

    # Wait for files to be transferred to nbextensions:
    libready = False
    dataready = False
    while True:
        nb = os.listdir(nbdir)
        for f in nb:
            if f == 'vpython_data':
                if len(os.listdir(nbdata)) == datacnt:
                    dataready = True
            if f == 'vpython_libraries':
                if len(os.listdir(nblib)) == libcnt:
                    libready = True
        if libready and dataready: break
    # Mark with the version number that the files have been transferred successfully:
    fd = open(nbdir+'/vpython_version.txt', 'w')
    fd.write(__version__)
    fd.close()

display(Javascript("""if (typeof Jupyter !== "undefined") {require.undef("nbextensions/vpython_libraries/glow.min");}else{element.textContent = ' ';}"""))
display(Javascript("""if (typeof Jupyter !== "undefined") {require.undef("nbextensions/vpython_libraries/glowcomm");}else{element.textContent = ' ';}"""))
display(Javascript("""if (typeof Jupyter !== "undefined") {require.undef("nbextensions/vpython_libraries/jquery-ui.custom.min");}else{element.textContent = ' ';}"""))

display(Javascript("""if (typeof Jupyter !== "undefined") {require(["nbextensions/vpython_libraries/glow.min"], function(){console.log("GLOW LOADED");});}else{element.textContent = ' ';}"""))
display(Javascript("""if (typeof Jupyter !== "undefined") {require(["nbextensions/vpython_libraries/glowcomm"], function(){console.log("GLOWCOMM LOADED");});}else{element.textContent = ' ';}"""))
display(Javascript("""if (typeof Jupyter !== "undefined") {require(["nbextensions/vpython_libraries/jquery-ui.custom.min"], function(){console.log("JQUERY LOADED");});}else{element.textContent = ' ';}"""))

time.sleep(1)      # allow some time for javascript code above to run before attempting to setup Comm Channel

wsConnected = False

class WSHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        global wsConnected
        wsConnected = True

    def on_message(self, message):
        ws_queue.put(message)

    def on_close(self):
        self.stopTornado()

    def stop_tornado(self):
        ioloop = tornado.ioloop.IOLoop.instance()
        ioloop.add_callback(ioloop.stop)

    def check_origin(self, origin):
        return True

def start_server():
    asyncio.set_event_loop(asyncio.new_event_loop())
    application = tornado.web.Application([(r'/ws', WSHandler),])
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(__SOCKET_PORT)
    Log = logging.getLogger('tornado.access')
    level = logging.getLevelName('WARN')
    Log.setLevel(level)
    tornado.ioloop.IOLoop.instance().start()


if (ipykernel.__version__ >= '5.0.0'):
	from threading import Thread
	t = Thread(target=start_server, args=())
	t.start()
	baseObj.glow = GlowWidget(wsport= __SOCKET_PORT, wsuri='/ws')     # Setup Comm Channel and websocket
	while (not wsConnected):
		time.sleep(0.1)          # wait for websocket to connect
else:
	baseObj.glow = GlowWidget()     # Setup Comm Channel

baseObj.trigger()  # start the trigger ping-pong process

if IPython.__version__ >= '4.0.0':
    if (ipykernel.__version__ >= '5.0.0'):
        async def wsperiodic():
            while True:
                if ws_queue.qsize() > 0:
                    data = ws_queue.get()
                    d = json.loads(data)
                    # Must send events one at a time to GW.handle_msg because
                    # bound events need the loop code
                    for m in d:
                        # message format used by notebook
                        msg = {'content': {'data': [m]}}
                        baseObj.glow.handle_msg(msg)

                await asyncio.sleep(0)

        loop = asyncio.get_event_loop()
        loop.create_task(wsperiodic())

# Dummy name to import...
_ = None
