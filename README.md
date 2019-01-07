# VPython

This package enables one to run VPython in a browser, using the GlowScript
VPython API, documented in the Help at http://glowscript.org. If the code is
in a cell in a Jupyter notebook, the 3D scene appears in the Jupyter notebook.
If the code is launched outside a notebook (e.g. from the command line), a
browser window will open displaying the scene.

VPython makes it unusually easy to create navigable real-time 3D animations.
The one-line program "sphere()" produces a 3D sphere with appropriate lighting
and with the camera positioned so that the scene fills the view. It also
activates mouse interactions to zoom and rotate the camera view. This
implementation of VPython was begun by John Coady in May 2014. Ruth Chabay and
Bruce Sherwood are assisting in its further development. The repository for
the source code is at https://github.com/BruceSherwood/vpython-jupyter.

## Installation

For more detailed instructions on how to install vpython, see http://vpython.org, where you will also find a link to the VPython forum, which is the preferred place to report issues and to request assistance.

Briefly:

+ If you use the [anaconda python distribution](https://www.continuum.io/anaconda-overview), install like this: `conda install -c vpython vpython`
+ If you use any other python distribution, install this way: `pip install vpython`

## Sample program

Here is a simple example:

```python
from vpython import *
sphere()
```

This will create a canvas containing a 3D sphere, with mouse and touch
controls available to zoom and rotate the camera:

    Right button drag or Ctrl-drag to rotate "camera" to view scene.
    To zoom, drag with middle button or Alt/Option depressed, or use scroll wheel.
         On a two-button mouse, middle is left + right.
    Shift-drag to pan left/right and up/down.
    Touch screen: pinch/extend to zoom, swipe or two-finger rotate.

Currently, to re-run a VPython program you need to click the circular arrow icon to "restart the kernel" and then click the red-highlighted button, then click in the first cell, then click the run icon. Alternatively, if you insert "scene = canvas()" at the start of your program, you can rerun the program without restarting the kernel.

Run example VPython programs: [![Binder](http://mybinder.org/badge.svg)](https://mybinder.org/v2/gh/BruceSherwood/vpython-jupyter/7.4.7?filepath=index.ipynb)

## vpython build status (for the vpython developers)

[![Build Status](https://travis-ci.org/BruceSherwood/vpython-jupyter.svg?branch=master)](https://travis-ci.org/BruceSherwood/vpython-jupyter) [![Build status](https://ci.appveyor.com/api/projects/status/wsdjmh8aehd1o0qg?svg=true)](https://ci.appveyor.com/project/mwcraig/vpython-jupyter)

