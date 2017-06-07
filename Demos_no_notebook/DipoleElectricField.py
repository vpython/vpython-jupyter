from vpython import *

scale = 4e-14/1e17
ec = 1.6e-19  # electron charge
kel = 9e9     # Coulomb constant
scene.range = 2e-13

charges = [ sphere( pos=vector(-1e-13,0,0), Q=ec,  color=color.red,  size=1.2e-14*vector(1,1,1) ),
            sphere( pos=vector( 1e-13,0,0), Q=-ec, color=color.blue, size=1.2e-14*vector(1,1,1) )]

s = "Click or drag to plot an electric field vector produced by the two charges.\n"
s += "On a touch screen, tap, or press and hold, then drag.\n"
s += "Arrows representing the field are bluer if low magnitude, redder if high."
scene.caption = s

def getfield(p):
    f = vec(0,0,0)
    for c in charges:
        f = f + (p-c.pos) * kel * c.Q / mag(p-c.pos)**3
    return f

def mouse_to_field(a):
    p = scene.mouse.pos
    f = getfield(p)
    m = mag(f)
    red = max( 1-1e17/m, 0 )
    blue = min(  1e17/m, 1 )
    if red >= blue:
        blue = blue/red
        red = 1.0
    else:
        red = red/blue
        blue = 1.0
    a.pos = p
    a.axis = scale*f
    a.color = vector(red,0,blue)
    a.visible = True

drag = False
a = None

def down(ev):
    global a, drag
    a = arrow(shaftwidth=6e-15, visible=False)
    mouse_to_field(a)
    drag = True

def move(ev):
    global a, drag
    if not drag: return
    mouse_to_field(a)
    
def up(ev):
    global a, drag
    mouse_to_field(a)
    drag = False

scene.bind("mousedown", down)

scene.bind("mousemove", move)

scene.bind("mouseup", up)
