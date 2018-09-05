from vpython import *
# John Coady

title = "Click and drag the mouse in the 3D canvas to insert and drag a small sphere."
scene.title = title

scene.range = 3

b = box(pos=vector(0,0,0), color=color.green)

drag = True
s = None

def grab(evt):
    global s, drag
    scene.title = 'Drag the sphere.'
    drag = True
    s = sphere(pos=evt.pos, radius=0.1, color=color.red)

def move(evt):
    if drag:
        s.pos = scene.mouse.pos #evt.pos
        
def drop(evt):
    global drag
    scene.title = title
    s.color = color.cyan
    drag = False

scene.bind('mousedown',grab)
scene.bind('mousemove',move)
scene.bind('mouseup',drop)

while True:
    rate(1)
