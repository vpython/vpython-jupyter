from vpython import *
# This program displays most GlowScript 3D objects.

#It also illustrates key features such as mouse handling, rate, and sleep.

# Bruce Sherwood, August 2011; VPython version November 2014

s = sphere(color=color.magenta, radius=0.5, visible=False)
drag = False

def down(ev):
    global drag
    s.pos = scene.mouse.pos
    s.visible = True
    drag = True

def move(ev):
    global drag
    if not drag: return
    s.pos = scene.mouse.pos

def up(ev):
    global drag
    s.visible = False
    drag = False

scene.bind("mousedown", down)

scene.bind("mousemove", move)

scene.bind("mouseup", up)

scene.title = "A display of most GlowScript 3D objects"
scene.width = 640
scene.height = 400
#scene.range = 5
scene.background = color.gray(0.7)
scene.center = vector(0,0.5,0)
scene.forward = vector(-.3,0,-1)
gslabel = label(pos=vector(1.1,2,0), text='GlowScript', 
    xoffset=40, height=16, color=color.yellow)
box(pos=vector(-2,0,0), size=vector(.3,2.5,2.5), color=color.red)
box(pos=vector(.25,-1.4,0), size=vector(4.8,.3,2.5), color=color.red)
cylinder(pos=vector(-2,2,1.25), radius=0.7, axis=vector(0,0,-2.5), color=color.blue)
ball = sphere(pos=vector(2,1,0), radius=0.5, color=color.cyan)
ptr = arrow(pos=vector(0,0,2), axis=vector(2,0,0), color=color.yellow)
cone(pos=vector(-2,0,0), radius=1, length=3, color=color.green, opacity=0.3)
ring(pos=vector(.2,0,0), radius=.6, axis=vector(1,0,0), thickness=0.12, color=color.gray(0.4))
ellipsoid(pos=vector(-.3,2,0), color=color.orange, size=vector(.3,1.5,1.5))
pyramid(pos=vector(.3,2,0), color=vector(0,0.5,.25), size=vector(0.8,1.2,1.2))
spring = helix(pos=vector(2,-1.25,0), radius=0.3, axis=vector(0,1.8,0),
        color=color.orange, thickness=.1)
angle = 0
da = .01

trail = curve(color=color.magenta, radius= .02)
trail.append(vector(1,0,0))
trail.append(vector(1,0,2))
trail.append(vector(2,0,2))

while angle < 3*pi/4:
  rate(100)
  ptr.rotate(angle=da, axis=vector(0,0,1), origin=ptr.pos)
  trail.append(ptr.pos+ptr.axis)
  angle += da

sleep(1) # sleep for 1 second
scene.autoscale = False
scene.append_to_caption("""Drag the mouse and you'll drag a sphere.
On a touch screen, press and hold, then drag.""")

t = 0
dt = .01
y0 = gslabel.pos.y
ball_yo = ball.pos.y
while t < 10:
  rate(1/dt)
  ball.pos.y = ball_yo+0.5*sin(-4*t)
  spring.length = ball.pos.y-spring.pos.y-ball.radius+0.15
  gslabel.yoffset = 28*sin(-4*t)
  t += dt
