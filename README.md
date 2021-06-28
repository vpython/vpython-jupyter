# VPython

This package enables one to run VPython in a browser, using the GlowScript
VPython API, documented in the Help at https://www.glowscript.org. If the code is
in a cell in a Jupyter notebook, the 3D scene appears in the Jupyter notebook.
If the code is launched outside a notebook (e.g. from the command line), a
browser window will open displaying the scene.

VPython makes it unusually easy to create navigable real-time 3D animations.
The one-line program "sphere()" produces a 3D sphere with appropriate lighting
and with the camera positioned so that the scene fills the view. It also
activates mouse interactions to zoom and rotate the camera view. This
implementation of VPython was begun by John Coady in May 2014. Ruth Chabay,
Matt Craig, and Bruce Sherwood are assisting in its further development.

## Installation

For more detailed instructions on how to install vpython, see https://vpython.org, where you will also find a link to the VPython forum, which is a good place to report issues and to request assistance.

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

Currently, to re-run a VPython program in a Jupyter notebook you need to click the circular arrow icon to "restart the kernel" and then click the red-highlighted button, then click in the first cell, then click the run icon. Alternatively, if you insert `scene = canvas()` at the start of your program, you can rerun the program without restarting the kernel.

Run example VPython programs: [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/vpython/vpython-jupyter/7.6.1?filepath=index.ipynb)

## Installation for developers from package source

You should install Cython (`conda install cython` or `pip install cython`) so
that the fast version of the vector class can be generated and compiled. You
may also need to install a compiler (command line tools on Mac, community
edition on Visual Studio on Windows).

If you don't have a compilier vpython should still work, but code that
generates a lot of vectors may run a little slower.

To install vpython from source run this command from the source directory
after you have downloaded it:

```
pip install -e .
```

The `-e` option installs the code with symbolic links so that change you make
show up without needing to reinstall.

If you also need the JupyterLab extension, please see the instructions
in the `labextension` folder.

## vpython build status (for the vpython developers)

![Testing workfloww](https://github.com/vpython/vpython-jupyter/actions/workflows/build.yml/badge.svg)


## Working with the source code

Here is an overview of the software architecture:

https://vpython.org/contents/VPythonArchitecture.pdf

The vpython module uses the GlowScript library (vpython/vpython_libraries/glow.min.js). The GlowScript repository is here:

https://github.com/vpython/glowscript

In the GlowScript repository's docs folder, GlowScriptOverview.txt provides more details on the GlowScript architecture.

Here is information on how to run GlowScript VPython locally, which makes possible testing changes to the GlowScript library:

https://www.glowscript.org/docs/GlowScriptDocs/local.html

If you execute build_original_no_overload.py, and change the statement "if True:" to "if False", you will generate into the ForInstalledPython folder an un-minified glow.min.js which can be copied to site-packages/vpython/vpython_libraries and tested by running your test in (say) idle or spyder. (Running in Jupyter notebook or Jupyterlab requires additional fiddling.)

Note that in site-packages/vpython/vpython_libraries it is glowcomm.html that is used by launchers such as idle or spyder; glowcomm.js is used with Jupyter notebook (and a modified version is used in Jupyterlab).

Placing console.log(....) statements in the GlowScript code or in the JavaScript section of glowcomm.html can be useful in debugging. You may also need to put debugging statements into site-packages/vpython/vpython.py.
