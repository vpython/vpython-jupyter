from vpython import *

# Written by Bruce Sherwood, licensed under Creative Commons 4.0.
# All uses permitted, but you must not claim that you wrote it, and
# you must include this license information in any copies you make.
# For details see http://creativecommons.org/licenses/by/4.0

# Gyroscope hanging from a spring

scene.width = scene.height = 600
scene.title = 'Hanging gyroscope'
scene.background = color.white
scene.range = 1.5

top = vector(0,1,0) # where top of spring is held
ks = 100 # spring stiffness
Lspring = 1 # unstretched length of spring
Rspring = 0.03 # radius of spring
Dspring = 0.03 # thickness of spring wire
Lshaft = 1 # length of gyroscope shaft
Rshaft = 0.03 # radius of gyroscope shaft
M = 1 # mass of gyroscope (massless shaft)
Rrotor = 0.4 # radius of gyroscope rotor
Drotor = 0.1 # thickness of gyroscope rotor
Dsquare = 1.4*Drotor # thickness of square that turns with rotor
I = 0.5*M*Rrotor**2 # moment of inertia of gyroscope
omega = 40 # angular velocity of rotor along axis
g = 9.8
Fgrav = vector(0,-M*g,0)
precession = M*g*(Lshaft/2)/(I*abs(omega)) # exact precession angular velocity
phi = atan(precession**2*(Lshaft/2)/g) # approximate angle of spring to vertical
s = M*g/(ks*cos(phi)) # approximate stretch of spring
# Refine estimate of angle of spring to vertical:
phi = 1/( ((I*abs(omega))/(M*Lshaft/2))**2/(g*Lshaft/2)-(Lspring+s)/(Lshaft/2) )
# Refine again:
s = M*g/(ks*cos(phi))
phi = 1/( ((I*abs(omega))/(M*Lshaft/2))**2/(g*Lshaft/2.)-(Lspring+s)/(Lshaft/2) )

support = box(pos=top+vector(0,0.01,0), size=vector(0.2,0.02,0.2), color=color.green)
spring = helix(pos=top, axis=vector(-(Lspring+s)*sin(phi),-(Lspring+s)*cos(phi),0), coils=10,
               radius=Rspring, thickness=Dspring, color=vector(1,0.7,0.2))
a = vector(1,0,0)
shaft = cylinder(axis=Lshaft*a, radius=Rshaft, color=vector(0.85,0.85,0.85))
rotor = cylinder(pos=0.5*a*(Lshaft-Drotor), opacity=0.2,
                 axis=Drotor*a, radius=Rrotor, color=vector(0.5,0.5,0.5))
stripe = box(pos=rotor.pos+0.5*vector(Drotor,0,0),
              size=vector(0.03*Rrotor,2*Rrotor,0.03*Rrotor), color=color.black)
gyro = compound([rotor, shaft, stripe])
gyro.rotate(axis=vector(0,1,0), angle=-pi)
gyro.pos = top+spring.axis+0.5*Lshaft*norm(gyro.axis)

#cm = gyro.pos+0.5*Lshaft*gyro.axis # center of mass of shaft
Lrot = I*omega*gyro.axis
dt = 0.005

Lrotarrow = arrow(length=0, shaftwidth=Rshaft, color=color.red, visible=False)
Lrotscale = 0.07
torquearrow = arrow(length=0, shaftwidth=Lrotarrow.shaftwidth, color=color.cyan, visible=False)
torquescale = 0.11
visLrot = False
visTorque = False

def Runb(r):
    global run
    run = not run
    if run:
        r.text = "Pause"
    else:
        r.text = "Run"

Runbutton = button(text="Run", bind=Runb)

def ResetRunbutton():
    global run
    run = False
    Runbutton.text = "Run"

scene.append_to_caption('   ')

def SPINbutton(s):
    global omega
    omega = -omega
    reset()

button(text='Flip spin direction', bind=SPINbutton)
scene.append_to_caption("   ")

def Lbutton(b):
    global visLrot
    visLrot = not visLrot

checkbox(bind=Lbutton)
scene.append_to_caption(" Show Lrot (red)   ")

def Tbutton(b):
    global visTorque
    visTorque = not visTorque

checkbox( bind=Tbutton)
scene.append_to_caption(" Show torque about CM (cyan)")

scene.append_to_caption("\n\nChoose initial conditions:  ")

# Create a drop-down menu (a "select" object). Set up the options to appear:
menu_options = []
menu_options.append("Pure precession")
menu_options.append("More general motion")

def handlemenu(m): # come here when a change is made in the menu choice
    global pureprecession
    val = m.index
    pureprecession = (val == 0)
    reset()

menu(choices=menu_options, selected=menu_options[0], bind=handlemenu)

pureprecession = True
initial = []

run = False

def reset(first=False):
    global p, pureprecession, t, initial, Lrot
    if first: # take advantage of the existing initializations at the start of the program
        # vector(vector) to make nonmutable copies of the initial vslues
        initial = [vector(gyro.pos), vector(gyro.axis), vector(spring.axis), vector(Lrot),\
                   vector(Lrotarrow.pos), vector(Lrotarrow.axis),\
                   vector(torquearrow.pos), vector(torquearrow.axis)]
    else:
        gyro.pos = initial[0]
        gyro.axis = initial[1]
        spring.axis = initial[2]
        Lrot = initial[3]
        Lrotarrow.pos = initial[4]
        Lrotarrow.axis = initial[5]
        torquearrow.pos = initial[6]
        torquearrow.axis = initial[7]
    t = 0
    if pureprecession:
        p = vector(0, 0, M*precession*(Lshaft/2+(Lspring+s)*sin(phi)))
    else:
        p = vector(0,-1,M*precession*(Lshaft/2+(Lspring+s)*sin(phi)))
    if omega < 0:
        p = -p
        Lrot = -Lrot
    Lrotarrow.visible = False
    torquearrow.visible = False
    ResetRunbutton()

reset(True)

while True:
    rate(100)
    if not run: continue
    
    Fspring = -ks*norm(spring.axis)*(mag(spring.axis)-Lspring)
    # Calculate torque about center of mass:
    torque = cross(-0.5*Lshaft*gyro.axis,Fspring)
    Lrot = Lrot + torque*dt
    p = p + (Fgrav+Fspring)*dt
    gyro.pos = gyro.pos+(p/M)*dt

    # Update positions of shaft, rotor, spring, stripes
    if omega > 0:
        gyro.axis = norm(Lrot)
    else:
        gyro.axis = -norm(Lrot)
    # shaft rotated, adjust connection to spring
    #gyro.pos = cm-0.5*Lshaft*gyro.axis 
    spring.axis = gyro.pos-0.5*Lshaft*norm(gyro.axis) - top
    # spin easier to see if slower than actual omega
    gyro.rotate(angle=omega*dt/4)

    # Update arrows representing angular momentum and angular impulse
    Lrotarrow.visible = visLrot
    torquearrow.visible = visTorque
    if omega > 0:
        Lrotarrow.pos = gyro.pos + 0.5*Lshaft*gyro.axis
    else:
        Lrotarrow.pos = gyro.pos - 0.5*Lshaft*gyro.axis
    Lrotarrow.axis = Lrot*Lrotscale
    torquearrow.pos = gyro.pos
    torquearrow.axis = torque*torquescale
    t = t+dt
