from vpython import *
scene.width = 600
scene.height = 600
scene.background = color.gray(0.9)
scene.range = 1.3
s = 'Pixel-level transparency using "depth-peeling."\n'
s += "Note the correct transparencies of the intersecting slabs.\n"
scene.title = s

box(pos=vec(0,0,0), opacity=1, size=vec(1,1,1), texture=textures.flower)
sphere(pos=vector(0,0,.9), opacity=0.3, shininess=0, radius=0.2, color=color.green)
s = sphere(pos=vector(0.1,0,1.2), opacity=0.2, shininess=0, radius=0.1, color=color.cyan)
box(pos=s.pos, size=0.06*vector(1,1,1), color=color.gray(.2))
box(pos=vector(0,.5,1), color=color.red,  opacity=0.2, size=vector(.05,.2,.8), axis=vector(1,0,1) )
box(pos=vector(0,.5,1), color=color.cyan, opacity=0.2, size=vector(.05,.2,.8), axis=vector(1,0,-1))

scene.caption = """Right button drag or Ctrl-drag to rotate "camera" to view scene.
To zoom, drag with middle button or Alt/Option depressed, or use scroll wheel.
     On a two-button mouse, middle is left + right.
Touch screen: pinch/extend to zoom, swipe or two-finger rotate."""
