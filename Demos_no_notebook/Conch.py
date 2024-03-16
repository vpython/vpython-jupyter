from vpython import *
# Kadir Haldenbilen, Feb. 2011

scene.height = scene.width = 600
scene.background = color.gray(0.7)
scene.range = 3
scene.ambient = 0.5*color.white

scene.caption = """To rotate "camera", drag with right button or Ctrl-drag.
To zoom, drag with middle button or Alt/Option depressed, or use scroll wheel.
  On a two-button mouse, middle is left + right.
To pan left/right and up/down, Shift-drag.
Touch screen: pinch/extend to zoom, swipe or two-finger rotate."""

def spiral(nloop=1, tightness=1.0, dir=1, scale=1):
    spr = []
    scale = []
    clrs = []
    zd = 0.01
    for t in range(1, 1024*nloop, 16):
        t *= 0.01
        x = tightness/10 * t * cos(t)*dir
        y = tightness/10 * t * sin(t)
        sc = sqrt(x*x+y*y)
        z = t/7
        spr.append(vector(x,y,z))
        clr = vector(z*cos(t), abs(sin(t)), abs(cos(t*2))).norm()
        clrs.append(clr)
        scale.append(sc)
    return spr, scale, clrs

path, scale, clrs = spiral(nloop=2, tightness=0.8)
elps = shapes.circle(radius=0.69, thickness=0.01)

ee = extrusion(shape=elps, path=path, color=clrs, scale=scale, texture=textures.rock)
ee.rotate(angle=pi/2)
scene.center = ee.pos-vec(0,.5,0)

scene.pause()

