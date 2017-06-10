from .vpython import *
from . import __version__, __gs_version__

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

if 'nbextensions' in os.listdir(jd):
    ldir = os.listdir(nbdir)
    if ('vpython_data' in ldir and len(os.listdir(nbdata)) == datacnt and
       'vpython_libraries' in ldir and len(os.listdir(nblib)) == libcnt and
        'vpython_version.txt' in ldir):
        v = open(nbdir+'/vpython_version.txt').read()
        transfer = (v != __version__) # need not transfer files to nbextensions if correct version's files already there

#transfer = True ### use when testing, so that changes are active
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

if IPython.__version__ >= '3.0.0' :
    get_ipython().kernel.comm_manager.register_target('glow', GlowWidget)
else:
    get_ipython().comm_manager.register_target('glow', GlowWidget) 

display(Javascript("""require.undef("nbextensions/vpython_libraries/glow.min");"""))
display(Javascript("""require.undef("nbextensions/vpython_libraries/glowcomm");"""))
display(Javascript("""require.undef("nbextensions/vpython_libraries/jquery-ui.custom.min");"""))

display(Javascript("""require(["nbextensions/vpython_libraries/glow.min"], function(){console.log("GLOW LOADED");})"""))
display(Javascript("""require(["nbextensions/vpython_libraries/glowcomm"], function(){console.log("GLOWCOMM LOADED");})"""))
display(Javascript("""require(["nbextensions/vpython_libraries/jquery-ui.custom.min"], function(){console.log("JQUERY LOADED");})"""))
            
get_ipython().kernel.do_one_iteration()

while baseObj.glow is None: # try to make sure setup is complete
    rate(60)

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

baseObj.trigger() # start the trigger ping-pong process
