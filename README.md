# VPython
The IPython/Jupyter version of VPython, the VPython API available in a Jupyter Notebook. This implementation of VPython was begun by John Coady in May 2014. Ruth Chabay and Bruce Sherwood are assisting in its further development. Work is in progress to follow the API of GlowScript VPython (glowscript.org). Some features are not yet fully implemented. An experimental alpha version is available through the Python Package Index by executing "pip install vpython".

Here is a simple example that will run in a Jupyter Notebook cell:

from vpython import *
sphere()

This will create a 3D window in the Notebook containing a 3D sphere, with mouse controls available to zoom and rotate the camera:

    Right button drag or Ctrl-drag to rotate "camera" to view scene.
    To zoom, drag with middle button or Alt/Option depressed, or use scroll wheel.
         On a two-button mouse, middle is left + right.
    Touch screen: pinch/extend to zoom, swipe or two-finger rotate.""")
