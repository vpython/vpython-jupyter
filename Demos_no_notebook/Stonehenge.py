import time

from vpython import *
scene.visible = False # while preparing the scene
import time

# Bruce Sherwood

# A surreal scene that illustrates many of the features of GlowScript

# Add instructions below the display
s = "<b>Fly through the scene:</b><br>"
s += "    drag the mouse or your finger above or below the center of the scene to move forward or backward;<br>"
s += "    drag the mouse or your finger right or left to turn your direction of motion.<br>"
s += "(Normal GlowScript rotate and zoom are turned off in this program.)"
scene.caption = s

ycenter = 2
scene.width = 800
scene.height = 400
scene.range = 12
scene.center = vector(0,ycenter,0)
##scene.userspin = False
##scene.userzoom = False
scene.background = color.gray(0.5)
scene.ambient = color.gray(0.4)

def hourminute():
    #GlowScript JavaScript date machinery
    #d = Date()
    #hour = d.getHours() % 12
    #minute = d.getMinutes()
    now = time.localtime(time.time())
    hour = now[3] % 12
    minute = now[4]
    return (hour, minute)

class analog_clock:
    def __init__(self, pos, radius, axis):
        self.pos = pos
        self.axis = axis
        self.radius = radius
        self.spheres = []
        self.hour = 0
        self.minute = -1
        for n in range(12):
            sp = sphere(pos=pos+(radius*scene.up).rotate(angle=-2*pi*n/12, axis=axis),
                    size=(2*radius/20)*vector(1,1,1),
                    color=color.hsv_to_rgb(vector(n/12,1,1)) )
            self.spheres.append(sp)
        self.hand = arrow(pos=self.pos, axis=0.95*radius*scene.up,
                    shaftwidth=radius/10, color=color.cyan)
        self.update()
        
    def update(self):
        hour, minute = hourminute()
        hour = hour % 12
        if self.hour == hour and self.minute == minute: return
        self.hand.axis = (0.95*self.radius*scene.up).rotate(
                    axis=vector(0,0,1), angle=-2*pi*minute/60)
        self.spheres[self.hour].size = (2*self.radius/20)*vector(1,1,1)
        self.spheres[hour].size = (2*self.radius/10)*vector(1,1,1)
        self.hour = hour
        self.minute = minute

grey = color.gray(0.8)
Nslabs = 8
R = 10
w = 5
d = 0.5
h = 5
photocenter = 0.15*w

# The floor, central post, and ball atop the post
floor = box(pos=vector(0,-0.1,0),size=vector(.2,24,24), axis=vector(0,1,0), texture=textures.wood)
pole= cylinder(pos=vector(0,0,0),axis=vector(0,1,0), size=vector(h,0.4,0.4), color=color.red)
sphere(pos=vector(0,h,0), size=vector(1,1,1), color=color.red)

# Set up the gray slabs, including a portal
for i in range(Nslabs):
    theta = i*2*pi/Nslabs
    c = cos(theta)
    s = sin(theta)
    xc = R*c
    zc = R*s
    if i == 2: # Make a portal
        box(pos=vector(-3.*w/8.,0.75*h/2.,R),
            size=vector(0.5*w/2,0.75*h,d), color=grey)
        box(pos=vector(3.*w/8.0,0.75*h/2.,R),
            size=vector(0.5*w/2,0.75*h,d), color=grey)
        box(pos=vector(0,0.85*h,R),
            size=vector(w,0.3*h,d), color=grey)
    else:
        slab = box(pos=vector(R*c, h/2., R*s), axis=vector(c,0,s),
                   size=vector(d,h,w), color=grey)
        if i != 6:
            T = textures.flower
            if (i == 7 or i == 4): T = textures.rug
            box(pos=slab.pos,
                size=vec(1.1*d,0.9*4*photocenter,0.9*4*photocenter), axis=vec(c,0,s),
                    texture=T)

entry = text(pos=vector(0,4.4,R+d/2), text='Surreal\nStonehenge', align='center',
                depth=0.3, height=0.5)
                
B = text(pos=vector(0.4*R,0,-1*R), text='B', height=2, align='center', font='serif',
                color=color.magenta, depth=1)

gh = 1
ga = 1
gr = 0.05
rgear = 0.7
tgear = ga/5 # gear thickness
support = extrusion(pos=vector(7,gh/2,10), path=[vector(0,0,0), vector(0,gh,0), vector(0,gh,ga), vector(0,0,ga)],
            shape=shapes.circle(radius=gr), color=vector(1,.7,0))
support.clone(pos=vector(7+2*rgear,gh/2,10))
gear1 = extrusion(pos=support.pos+vector(0,gh/2,0), path=[vector(0,0,-tgear/2), vector(0,0,tgear/2)],
            shape=shapes.gear(radius=rgear), color=color.gray(0.85), texture=textures.metal)
gear2 = gear1.clone(pos=gear1.pos+vector(2*rgear,0,0))
gear1.rotate(angle=-0.4*2*pi/20, axis=vector(0,0,1)) # default is 20 teeth

# Decorate back slab with a wood box and a clock
box(pos=vector(0,h/2.,-R+d/2+0.1), size=vector(w/2.,w/2.,0.2), texture=textures.wood)
clock = analog_clock(vector(0,h/2.,-R+d/2+0.2+0.2*h/10), 0.2*w, vector(0,0,1))

# Draw guy wires from the top of the central post
Nwires = 32
for i in range(Nwires):
    theta = i*2*pi/Nwires
    L = vector(R * cos(theta), -h - 0.1, R * sin(theta))
    cylinder(pos=vector(0,h,0), axis=L, size=vector(mag(L),.04,.04), color=vector(1,0.7,0))

# Display a pyramid
pyramid(pos=vector(-4,0,-5), size=vector(2,2,2), axis=vector(0,3,0), color=vector(0,.5,0), texture=textures.rough)

# Display smoke rings rising out of a black tube
smoke = []
Nrings = 20
x0, y0, z0 = -5, 1.5, -2
r0 = 0.075
spacing = 0.2
thick = r0/3
dr = 0.0075
dthick = thick/Nrings
gray = 1
cylinder(pos=vector(x0,0,z0), axis=vector(0,y0+r0,0), radius=1.5*(r0+thick), color=color.black)

# Create the smoke rings
for i in range(Nrings):
  smoke.append(ring(pos=vector(x0,y0+spacing*i,z0), axis=vector(0,1,0),
                radius=r0+dr*i, thickness=thick-dthick*i))
y = 0
dy = spacing/20
top = Nrings-1

# Log rolls back and forth between two stops
rlog = 1
wide = 4
zpos = 2
zface = 5
tlogend = 0.2
v0 = 0.3
v = v0
omega = -v0 / rlog
theta = 0
dt = 0.1
tstop = 0.3
logcyl = cylinder(pos=vector(-wide, rlog, zpos), size=vector(zface - zpos, 2, 2),
    axis=vector(0, 0, 1), texture=textures.granite)
leftstop = box(pos=vector(-wide-rlog-tstop/2,0.6*rlog,(zpos+zface)/2),
    size=vector(tstop, 1.2*rlog, (zface-zpos)), color=color.red, emissive=True)
rightstop = box(pos=vector(wide+rlog+tstop/2,0.6*rlog,(zpos+zface)/2),
    size=vector(tstop, 1.2*rlog, (zface-zpos)), color=color.red, emissive=True)

# Run a ball up and down the pole
y1 = 0.2*h
y2 = 0.7*h
rball = 0.4
Dband = 1.3 * pole.size.y
cylinder(pos=vector(0,y1-0.9*rball,0), axis=vector(0,1,0), size=vector(0.1,Dband,Dband), color=color.green)
cylinder(pos=vector(0,y2+0.9*rball,0), axis=vector(0,1,0), size=vector(0.1,Dband,Dband), color=color.green)
vball0 = 0.3*v0
vball = vball0
ballangle = 0.05*pi
ball = []
ball.append(sphere(pos=vector(0,0,0), size=2*rball*vector(1,1,1), color=color.blue))
for nn in range(4):
    cc = cone(pos=vector(0,0,0)+vector(0.8*rball,0,0), axis=vector(3*rball,0,0),
              size=rball*vector(3,1,1), color=color.yellow)
    cc.rotate(angle=0.5*nn*pi, axis=vector(0,1,0), origin=vector(0,0,0))
    ball.append(cc)
ball = compound(ball)
ball.pos = vector(0,y1,0)

# A table with a mass-spring object sliding on it
table = cone(pos=vector(0.4*R, h/4, -.3*R), size=vector(h/4, 0.6 * R, 0.6 * R), 
  axis=vector(0, -1, 0), texture={'file':textures.wood_old, 'turn':1})
tabletop = table.pos
rspring = 0.02 * h
Lspring = .15 * R
Lspring0 = .1 * R
hmass = 4 * rspring
post = cylinder(pos=tabletop, axis=vector(0, 1, 0), size=vector(2 * hmass, .4, .4), color=color.gray(.6))
spring = helix(pos=post.pos + vector(0, hmass/2, 0), size=vector(Lspring, 2 * rspring, 2 * rspring),
               color=color.orange, thickness=rspring)
mass = cylinder(pos=post.pos + vector(Lspring, 0, 0), axis=vector(0, 1, 0),
                size=vector(hmass, .04 * R, .04 * R), color=color.orange)
mass.p = vector(10, 0, 5)
mass.m = 1
kspring = 200
deltat = .01

# Display an ellipsoid
Rcloud = 0.8*R
omegacloud =3*v0/Rcloud
cloud = sphere(pos=vector(0,0.7*h,-Rcloud), size=vector(5,2,2),
                  color=color.green, opacity=0.3)

rhairs = 0.025 # half-length of crosshairs
dhairs = 2 # how far away the crosshairs are
maxcosine = dhairs/sqrt(rhairs**2+dhairs**2) # if ray inside crosshairs, don't move
haircolor = color.black
roam = 0

scene.waitfor("textures")
scene.visible = True # finished preparing the scene

roam = False

def setroam(evt):
    global roam
    roam = not roam

scene.bind("mousedown mouseup", setroam)

hue = 0
dhue = 0.01
gangle = 0.03 # incremental rotation of the gears

while True:
    rate(30)

    # If in roaming mode, change center and forward according to mouse position
    if roam:
        ray = scene.mouse.ray
        if abs(ray.dot(scene.forward)) < maxcosine: # do something only if outside crosshairs
            newray = norm(vector(ray.x, 0, ray.z))
            angle = asin(scene.forward.cross(newray).dot(scene.up))
            scene.camera.rotate(angle=angle/30, axis=scene.up)
            scene.camera.pos = scene.camera.pos + (ray.y/2)*norm(scene.camera.axis)
    
    hue += dhue
    entry.color = color.hsv_to_rgb(vector(hue,1,1))
    
    B.rotate(angle=0.05, axis=scene.up)
    
    gear1.rotate(angle=gangle, axis=vector(0,0,1))
    gear2.rotate(angle=-gangle, axis=vector(0,0,1))

    # Roll the log
    theta = theta + omega*dt
    logcyl.pos.x = logcyl.pos.x+v*dt
    logcyl.rotate(angle=omega*dt, axis=vector(0,0,1))
    if logcyl.pos.x >= wide:
        v = -v0
        omega = -v/rlog
        if rightstop.color.equals(color.red):
            rightstop.color = color.cyan
        else:
            rightstop.color = color.red
    if logcyl.pos.x <= -wide:
        v = +v0
        omega = -v/rlog
        if leftstop.color.equals(color.red):
            leftstop.color = color.cyan
        else:
            leftstop.color = color.red

    # Move the cloud
    cloud.rotate(angle=omegacloud*dt, origin=vector(0,0,0), axis=vector(0,1,0))

    # Run the ball up and down
    ball.pos.y = ball.pos.y+vball*dt
    ball.rotate(angle=ballangle, axis=vector(0,1,0))
    if ball.pos.y >= y2:
        vball = -vball0
        ballangle = -ballangle
    if ball.pos.y <= y1:
        vball = +vball0
        ballangle = -ballangle

    # Move the smoke rings
    for i in range(Nrings):
        # Raise the smoke rings
        smoke[i].pos = smoke[i].pos+vector(0,dy,0)
        smoke[i].radius = smoke[i].radius+(dr/spacing)*dy
        smoke[i].thickness = smoke[i].thickness - (dthick/spacing)*dy
    y = y+dy
    if y >= spacing:
        # Move top ring to the bottom
        y = 0
        smoke[top].pos = vector(x0, y0, z0)
        smoke[top].radius = r0
        smoke[top].thickness = thick
        top = top-1
    if top < 0:
        top = Nrings-1
        
    # Update the mass-spring motion
    F = -kspring * (spring.size.x - Lspring0) * spring.axis.norm()
    mass.p = mass.p + F * deltat
    mass.pos = mass.pos + (mass.p / mass.m) * deltat
    spring.axis = mass.pos + vector(0, hmass / 2, 0) - spring.pos

    # Update the analog clock on the back slab
    clock.update()
