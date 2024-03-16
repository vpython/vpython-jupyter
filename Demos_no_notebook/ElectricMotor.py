from vpython import *
# Kadir Haldenbilen, February 2011
# Converted to Web VPython by Bruce Sherwood, May 2022

scene.width = 1024
scene.height = 768
scene.center = vec(-2,0,0)
scene.range = 7

motor = []      # elements that rotate
cl = 2
ns = 24

def makearc(center=[0,0], radius=1, angle1=2*pi-pi/4, angle2=2*pi+pi/4, ccw=True):
    # Specify angle1 and angle2 as positive numbers, with angle2 > angle1
    if angle2 < angle1:
        raise Exception("Both angles must be positive, with angle2 > angle1") 
    n = 20
    dtheta = abs(angle2-angle1)/n
    ret = []
    for i in range(n+1):
        if ccw:
            #print(center, angle1, angle2, radius, ccw)
            ret.append([center[0]+radius*cos(angle1+i*dtheta), center[1]+radius*sin(angle1+i*dtheta)])
        else:
            #print(center, angle1, angle2, radius, ccw)
            ret.append([center[0]+radius*cos(angle2-i*dtheta), center[1]+radius*sin(angle2-i*dtheta)])
    return ret

def rotatepoints(points=[[1,0],[0,1]], angle=0, origin=vec(0,0,0)):
    s = sphere(visible=False)
    ret = []
    for p in points:
        s.pos = vec(p[0],p[1],0)
        s.rotate(angle=angle, axis=vec(0,0,1), origin=origin)
        ret.append([s.pos.x,s.pos.y])
    return ret 

#=====================================================================
# Create contactor

p2 = makearc(center=[0,0], radius=0.5, angle1=0, angle2=pi/20, ccw=False)
p1 = makearc(center=[0,0], radius=1.2, angle1=0, angle2=pi/15, ccw=True)
p = p1+p2+[p1[0]]
c = extrusion(path=[vec(0,0,0),vec(2,0,0)], shape=p, color=vec(1,0.5,0.3))
cont = [c]
for i in range(1,24):
    con = c.clone()
    con.rotate(angle=i*2*pi/24, axis=vec(-1,0,0), origin=vec(0,0,0))
    cont.append(con)
motor.append(compound(cont))
#==========================================================================
# Create contactor soldering tips

p1 = makearc(center=[0,0], radius=1.4, angle1=2*pi-0.5*pi/24, angle2=2*pi+0.4*pi/24, ccw=True)
p2 = makearc(center=[0,0], radius=0.7, angle1=2*pi-0.5*pi/30, angle2=2*pi+0.4*pi/30, ccw=False)
p = p1+p2+[p1[0]]
c = extrusion(path=[vec(-0.4,0,0),vec(0,0,0)], shape=p, color=vec(1,0.5,0.3))
s = sphere(pos=vec(-0.2,0,1.195), radius=0.1, shininess=1)
cont = [c]
balls = []
for i in range(23):
    con = c.clone()
    con.rotate(angle=(i+1)*2*pi/24, axis=vec(1,0,0), origin=vec(0,0,0))
    cont.append(con)
    con = s.clone()
    con.rotate(angle=(i+1)*2*pi/24, axis=vec(1,0,0), origin=vec(0,0,0))
    balls.append(con)
    
motor.append(compound(cont))
motor.append(compound(balls))
#=========================================================================
# Add shaft insulator material
# Define a circular ring of thickness=0.05
sc = shapes.circle(radius=0.53, thickness=0.05)
# Extrude the ring to get a thin hollow cylinder insulator over the shaft
sce = extrusion(path=[vec(-7,0,0),vec(2.5,0,0)], shape=sc, color=vec(0.8,0,0),
                emissive=True) # plastic

# The Rotor Shaft, defined by a simple cylinder
shaft = cylinder(pos=vec(3.5,0,0), axis=vec(-11.25,0,0), radius=0.495, color=color.gray(.6), texture=textures.metal)

# Add a piece of gear at one end of the shaft
# Use the gear shape to define the shape, note radius, addendum, dedendum sizes
gr = shapes.gear(n=9, radius=0.455, addendum=0.04, dedendum=0.06, fradius=0.01)
# Extrude the gear shape appending it to the shaft end
gre = extrusion(path=[vec(3.5,0,0),vec(5,0,0)], shape=gr, color=color.gray(.6),
                texture=textures.metal)

motor.append(gre)
#for o in scene.objects: o.visible = False
#==========================================================================
# Define Rotor Core
# Normally the core should have been built of many very thin sheets
# For performance reasons, a single block is built
# First define the outer circle

r0 = 0.495  # radius of shaft
r1 = 1.3    # radius of disk
r2 = 2.7  # radius of inner portion of top of the T
r3 = 3 # radius of outer portion of top of the T
theta = pi/12 # angle between Ts
d = 0.25*theta # half angle width of upright of T
dlt = 0.05
thk = 5.04

p1 = makearc(center=[0,0], radius=r1, angle1=2*pi-pi/12+d, angle2=2*pi+pi/12-d, ccw=True)
start = r1*vec(cos(-pi/12+d), sin(-pi/12+d),0)
# From middle of bottom of T base to middle of top of T upright:
middledir = vec(cos(pi/12),sin(pi/12), 0)
perp = middledir.rotate(angle=pi/2, axis=vec(0,0,1))
p1end = vec(p1[-1][0], p1[-1][1],0)
endpt1 = p1end+(r2-r1)*middledir # top right of T upright
nextstart = start.rotate(angle=pi/6, axis=vec(0,0,1))
endpt2 = nextstart + (r2-r1)*middledir
a = atan(endpt1.y/endpt1.x)
p2 = makearc(center=[0,0], radius=r2, angle1=0.3*a, angle2=a, ccw=False)
p1.extend(p2)
p3 = makearc(center=[0,0], radius=r3, angle1=0.3*a, angle2=1.5*a+2*d, ccw=True)
p1.extend(p3)
b = atan(endpt2.y/endpt2.x)
p4 = makearc(center=[0,0], radius=r2, angle1=b, angle2=1.5*a+2*d, ccw=False)
p1.extend(p4)

pc = p1.copy()
for i in range(1,12):
    p = rotatepoints(p1, angle=i*pi/6)
    pc.extend(p)
pc.append(pc[0])

ex = extrusion(path=[vec(-6,0,0), vec(-6+thk,0,0)], shape=[pc, shapes.circle(radius=r0)] , color=color.gray(0.7))
motor.append(ex)

#==========================================================================
# Do the core wire windings
x = -3.5
n = 20
L = 1.3
thk = L/50
con = []
for i in range(n):
    r = r1+i*thk*2.5
    inner = shapes.rectangle(width=5.2, height=.35, roundness=0.4)
    outer = shapes.rectangle(width=5.3+i*0.7/n, height=0.4+i*0.6/n, roundness=0.4)
    p = [vec(x,r*sin(pi/12),r*cos(pi/12)), vec(x,(r+thk)*sin(pi/12),(r+thk)*cos(pi/12))]
    ex = extrusion(path=p, shape=[outer,inner], color=vec(.7,.5,.15))
    con.append(ex)
ex = compound(con)
con = [ex]

for i in range(1,12):
    c = ex.clone()
    c.rotate(angle=i*pi/6, axis=vec(1,0,0), origin=vec(0,0,0))
    con.append(c)

motor.append(compound(con))

#==========================================================================
# Connect contactor surfaces to windings with cables
pos = vec(-1.3,1.1,0)
c0 = cylinder(pos=pos, axis=vec(-0.25,1.2,0.25)-pos, radius=0.05, color=color.blue)
con = [c0]
for i in range(1,24):
    c = c0.clone()
    c.rotate(angle=i*pi/6, axis=vec(1,0,0), origin=vec(c0.pos.x,0,0))
    con.append(c)
motor.append(compound(con))

#==========================================================================
# Create Brushes
# From a rectangular cross section, subtract rotor contactor circle, leaving us two
# brushes on each sides of the contactor, with circular profile
#br = shapes.rectangle(width=5, height=0.4)
br = makearc(center=[0,0], radius=1.21, angle1=2*pi-atan(0.2/1.21), angle2=2*pi+atan(0.2/1.21), ccw=True)
d = 1+1.21*cos(atan(.2/1.21))
br.append([d,0.2])
br.append([d,-0.2])
br.append(br[0])
bre = extrusion(path=[vec(0.4,0,0),vec(1.6,0,0)], color=vec(0.1,0.1,0.15),
                texture=textures.rough, shape=br)
d = bre.clone()
d.rotate(angle=pi, axis=vec(1,0,0), origin=vec(1,0,0))

#==========================================================================
# Create Brush Housings
# Define a rectangular frame, with a thickness of 0.1
bh = shapes.rectangle(width=1.3, height=0.5, thickness=0.1)
# Extrude the rectangular frame to obtain hollow boxes for each housing
bhe1 = extrusion(path=[vec(1,0,1.4),vec(1,0,2.9)], shape=bh, color=vec(0.9,1,0.8),
                 texture=textures.rough)
bhe2 = extrusion(path=[vec(1,0,-1.4),vec(1,0,-2.9)], shape=bh, color=vec(0.9,1,0.8),
                 texture=textures.rough)

#==========================================================================
# Place a screw on each housing to fix the power cables
# Create a screw head profile by subtracting a cross from a circle
scrh = [shapes.circle(radius=0.15)]
scrh.append(shapes.cross(width=0.2, thickness=0.04))
# Extrude a little to get the screw head
scrhw1path = [vec(1,0.2,2.7),vec(1,0.3,2.7)]
scrhw2path = [vec(1,0.2,-2.7),vec(1,0.3,-2.7)]
scrhw1 = extrusion(path=scrhw1path, shape=scrh, texture=textures.metal)
scrhw2 = extrusion(path=scrhw2path, shape=scrh, texture=textures.metal)

#==========================================================================
# Create the screw bodies
# Use a square to create the body with teeth
scrb = shapes.rectangle(scale=0.05)
yi = .2
yf = -.3
dy = (yi-yf)/20
pts = []
for i in range(20):
    pts.append(vec(1, yi-i*dy, 2.7))
# Extrude the square with twist parameter to get the teeth of the screw
# It appears that paths.line() is broken.
#scrbe1 = extrusion(path=paths.line(start=vec(2.7,0.2,1), end=vec(2.7,-0.3,1),
scrbe1 = extrusion(path=pts, shape=scrb, twist=0.4, color=vec(1,1,0.9),
                 texture=textures.rough)

pts = []
for i in range(20):
    pts.append(vec(1, yi-i*dy, -2.7))
scrbe2 = extrusion(path=pts, shape=scrb, twist=0.4, color=vec(1,1,0.9),
                 texture=textures.rough)

#==========================================================================

crdl = [ [2.8,-0.2], [2.8,-1.6], [-2.8,-1.6], [-2.8,-0.2] ] # ccw
a = acos(0.2/1.1) # starting angle for near half-circle
c = makearc(center=[0,0], radius=1.25, angle1=1.5*pi-a, angle2=1.5*pi+a, ccw=True)
crdl.extend(c)
crdl.append(crdl[0])
crdl = [crdl, shapes.circle(pos=[-2.2,-0.9], radius=0.1)]
crdle = extrusion(path=[vec(1.8,-0.05,0),vec(0.2,-0.05,0)], shape=crdl,
            color=0.7*color.white, emissive=True)

#==========================================================================
# Connect power cables to the brushes
# Use simple curves to define cables
col = vec(1,0.5,0.3)
cbl1i = curve(pos=[scrhw1path[0], scrhw1path[0]- vec(0,0,-2)],
            radius=0.03, color=col)
cbl1o = curve(pos=[scrhw1path[0], scrhw1path[0]- vec(0,0,-1.5)],
            radius=0.05, color=vec(0,0,1))
cb12ipos = [scrhw2path[0], scrhw2path[0], scrhw2path[0]+vec(0,0,-0.5), 
            scrhw2path[0]+vec(0,0,-0.5)+vec(0,-2,0),
            scrhw2path[0]+vec(0,0,-0.5)+vec(0,-2,0)+vec(0,0,7)]
cbl2i = curve(pos=cb12ipos, radius=0.03, color=col)

#==========================================================================
# Add ball-bearings at both ends of the shaft
bra = shapes.circle(radius=0.6, thickness=0.2)
brb = shapes.circle(radius=1.1, thickness=0.2)
br1 = extrusion(path=[vec(2.5,0,0), vec(3.25,0,0)], shape=bra, color=color.gray(.7))
br1 = extrusion(path=[vec(2.5,0,0), vec(3.25,0,0)], shape=brb, color=color.gray(.7))
br2 = extrusion(path=[vec(-7,0,0), vec(-7.75,0,0)], shape=bra, color=color.gray(.7),
    shininess=1, texture=textures.metal)
br2 = extrusion(path=[vec(-7,0,0), vec(-7.75,0,0)], shape=brb, color=color.gray(.7),
    shininess=1, texture=textures.metal)

#==========================================================================
# Do not forget to add the balls
bbrs1 = []
bbrs2 = []
for i in range(7):
    ex1 = sphere(pos=vec(3, 0.75*cos(i*2*pi/7.0), 0.75*sin(i*2*pi/7.0)),
                        radius=0.25)
    bbrs1.append(ex1)
    
    ex2 = sphere(pos=vec(-7.375, 0.75*cos(i*2*pi/7.0), 0.75*sin(i*2*pi/7.0)),
                        radius=0.25)
    bbrs2.append(ex2)
motor.append(compound(bbrs1, texture=textures.rough))
motor.append(compound(bbrs2, texture=textures.rough))

#==========================================================================
# Here is a complex path definition for stator winding, which is not planar.
# The path is made up of an arc in YZ + line in ZX + arc in ZY + line in XZ
pp = paths.arc(angle1=-pi/3.5, angle2=pi/3.5, radius=3.4)
for p in pp:
    p.y = -p.x
    p.x = -1
tt = []
for p in pp:
    tt.append(vec(-6,p.y,p.z))
tt.reverse()
pp.extend(tt)
pp.append(pp[0])
extrusion(path=pp, shape=shapes.circle(radius=0.3), color=color.red)
    
#==========================================================================
# Make stator base:
# We did not include all stator parts here for better visualisation
# Use a rounded rectangle for the stator base.
# Subtract a large circle in the middle to allow for the rotor
# Subtract circular holes to place the stator windings
# Subtract some more holes for fixing the stator core on the motor body

#def makearc(center=[0,0], radius=1, angle1=2*pi-pi/4, angle2=2*pi+pi/4, ccw=True):
    # Specify angle1 and angle2 as positive numbers, with angle2 > angle1
p1 = makearc(center=[1.5,0], radius=1.5, angle1=3*pi/2, angle2=2*pi, ccw=True)
p2 = makearc(center=[2.7,0.22], radius=0.3, angle1=pi+pi/4, angle2=2*pi-pi/4, ccw=False)
p3 = makearc(center=[0,2.1], radius=3.1, angle1=pi+0.95*pi/4, angle2=2*pi-0.95*pi/4, ccw=False)
p4 = makearc(center=[-2.7,0.22], radius=0.3, angle1=pi+pi/4, angle2=2*pi-pi/4, ccw=False)
p5 = makearc(center=[-1.5,0], radius=1.5, angle1=pi, angle2=1.5*pi, ccw=True)

p1.extend(p2)
p1.extend(p3)
p1.extend(p4)
p1.extend(p5)
p1.append(p1[0])

h1 = shapes.circle(pos=[2,-1.07], radius=0.15)
h2 = shapes.circle(pos=[-2,-1.07], radius=0.15)

extrusion(path=[vec(-6,-2.3,0), vec(-1,-2.3,0)], shape=[p1,h1,h2])

#==========================================================================
# Create the motor cover as a rotational extrusion along the mootor
# Add two rounded rectangles which will cover all the rotor and stator.
# Leave the tips of shaft outside the cover
L = 11
r = 2
R = 5
t = 0.25
x = 3*t
s = [ [-L/2, -r/2-t], [-L/2,-r/2], [-L/2+x,-r/2], [-L/2+x,R/2], [L/2-x,R/2], [L/2-x,-r/2], [L/2,-r/2],
     [L/2,-r/2-t], [L/2-x-t,-r/2-t], [L/2-x-t,R/2-t], [-L/2+x+t,R/2-t], 
     [-L/2+x+t,-r/2-t], [-L/2+t,-r/2-t], [-L/2,-r/2-t] ]

p = paths.arc(radius=R/2, angle1=0, angle2=pi+pi/4)
ex = extrusion(path=p, shape=s, color=0.6*color.green, up=vec(1,0,0), texture=textures.rough)
ex.rotate(angle=pi/2, axis=vec(0,0,1))
ex.pos = vec(-2.2,0,-0.65)

run = True
def running(b):
    global run
    if b.text == 'Run': b.text = 'Pause'
    else: b.text = 'Run'
    run = not run
    
button(text='Pause', bind=running)

scene.append_to_caption("""\nTo rotate "camera", drag with right button or Ctrl-drag.
To zoom, drag with middle button or Alt/Option depressed, or use scroll wheel.
  On a two-button mouse, middle is left + right.
To pan left/right and up/down, Shift-drag.
Touch screen: pinch/extend to zoom, swipe or two-finger rotate.""")

# Connect power cables
angl = pi/400
# Turn on the motor
while True:
    rate(100)
    if run:
        for o in motor:
            o.rotate(angle=angl, axis=vec(-1,0,0))
            
