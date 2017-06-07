from vpython import *
from numpy import arange, clip

# David Scherer

scene.caption = """Right button drag or Ctrl-drag to rotate "camera" to view scene.
Middle button to drag or Alt-drag to zoom in or out.
  On a two-button mouse, middle is left + right."""
scene.title = "Lorenz differential equation"
scene.center = vector(25,0,0)
scene.background = color.white
scene.forward = vector(0,-.2,-1)
scene.range = 35

lorenz = curve( color = color.black, radius=0.3 )

# Draw grid
for x in arange(0,51,10):
    box(pos=vector(x,0,0), axis=vector(0,0,50), height=0.4, width=0.4, color=color.gray(0.6) )
for z in arange(-25,26,10):
    box(pos=vector(25,0,z), axis=vector(50,0,0), height=0.4, width=0., color=color.gray(0.6) )

dt = 0.01
y = vector(35, -10, -7)

for t in arange(0,10,dt):
    # Integrate a funny differential equation
    dydt = vector( - 8.0/3*y.x           +   y.y*y.z,
                              - 10*y.y +   10*y.z,
                 -  y.y*y.x +   28*y.y -   y.z );
    y = y + dydt*dt

    # Draw lines colored by speed
    c = clip( [mag(dydt) * 0.005], 0, 1 )[0]

    lorenz.append( pos=y, color=vector(c,0, 1-c) )

    rate( 500 )
