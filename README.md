# VPython
This package enables one to run VPython in a Jupyter notebook, using the GlowScript VPython API, documented in the Help at http://glowscript.org. VPython makes it unusually easy to create navigable real-time 3D animations. The one-line program "sphere()" produces a 3D sphere with appropriate lighting and with the camera positioned so that the scene fills the view. It also activates mouse interactions to zoom and rotate the camera view. The 3D scene appears in the Jupyter notebook, using the WebGL-based GlowScript 3D graphics library. This implementation of VPython was begun by John Coady in May 2014. Ruth Chabay and Bruce Sherwood are assisting in its further development. The repository for the source code is at https://github.com/BruceSherwood/vpython-jupyter.

For instructions on how to install Jupyter VPython, see http://vpython.org.

Here is a simple example that will run in a Jupyter Notebook cell:

```python
from vpython import *
sphere()
```

This will create a 3D window in the Notebook containing a 3D sphere, with mouse and touch controls available to zoom and rotate the camera:

    Right button drag or Ctrl-drag to rotate "camera" to view scene.
    To zoom, drag with middle button or Alt/Option depressed, or use scroll wheel.
         On a two-button mouse, middle is left + right.
    Touch screen: pinch/extend to zoom, swipe or two-finger rotate.

Run example VPython programs: [![Binder](http://mybinder.org/badge.svg)](http://mybinder.org/repo/BruceSherwood/vpython-jupyter)
