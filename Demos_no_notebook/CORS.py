from vpython import *
scene.range = 1
scene.forward = vector(-1,-.5,-1)
box(texture="https://s3.amazonaws.com/glowscript/textures/flower_texture.jpg")

s = 'This illustrates the use of an image from another web site as a texture.\n'
s += 'This is an example of CORS, "Cross-Origin Resource Sharing".\n'
scene.caption = s

scene.append_to_caption("""
To rotate "camera", drag with right button or Ctrl-drag.
To zoom, drag with middle button or Alt/Option depressed, or use scroll wheel.
  On a two-button mouse, middle is left + right.
To pan left/right and up/down, Shift-drag.
Touch screen: pinch/extend to zoom, swipe or two-finger rotate.""")

scene.pause()
