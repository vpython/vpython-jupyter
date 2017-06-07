from vpython import *

# Gyroscope sitting on a pedestal

# The analysis is in terms of Lagrangian mechanics.
# The Lagrangian variables are polar angle theta,
# azimuthal angle phi, and spin angle psi.

scene.width = 800
scene.height = 600
scene.range = 1.2
scene.title = "A precessing, nutating gyroscope"
scene.visible = False

Lshaft = 1 # length of gyroscope shaft
r = Lshaft/2 # distance from support to center of mass
Rshaft = 0.03 # radius of gyroscope shaft
M = 1 # mass of gyroscope (massless shaft)
Rrotor = 0.4 # radius of gyroscope rotor
Drotor = 0.1 # thickness of gyroscope rotor
I3 = 0.5*M*Rrotor**2 # moment of inertia of gyroscope about its own axis
I1 = M*r**2 + .5*I3 # moment of inertia about a line through the support, perpendicular to the axis
hpedestal = Lshaft # height of pedestal
wpedestal = 0.1 # width of pedestal
tbase = 0.05 # thickness of base
wbase = 3*wpedestal # width of base
g = 9.8
Fgrav = vector(0,-M*g,0)
top = vector(0,0,0) # top of pedestal

shaft = cylinder(length=Lshaft, radius=Rshaft, color=color.orange)
rotor = cylinder(pos=vector(Lshaft/2-Drotor/2,0,0), axis=vector(Drotor, 0, 0),
                 radius=Rrotor, color=color.gray(0.9))
base = sphere(color=shaft.color, radius=Rshaft)
end = sphere(pos=vector(Lshaft,0,0), color=shaft.color, radius=Rshaft)
gyro = compound([shaft, rotor, base, end])
gyro_center = gyro.pos
gyro.texture = textures.metal
tip = sphere(pos=shaft.axis, radius=shaft.radius/2,  make_trail=True, retain=250)
tip.trail_color = color.green
tip.trail_radius = 0.15*Rshaft

pedestal = box(pos=top-vector(0,hpedestal/2+shaft.radius/2,0), 
               height=hpedestal-shaft.radius, length=wpedestal, width=wpedestal, texture=textures.wood)
pedestal_base = box(pos=top-vector(0,hpedestal+tbase/2,0), 
                    height=tbase, length=wbase, width=wbase, texture=textures.wood)

theta = 0
thetadot = 0
psi = 0
psidot = 0
phi = 0
phidot = 0
pureprecession = False

def reset():
    global theta, thetadot, psi, psidot, phi, phidot
    theta = 0.3*pi # initial polar angle of shaft (from vertical)
    thetadot = 0 # initial rate of change of polar angle
    psi = 0 # initial spin angle
    psidot = 30 # initial rate of change of spin angle (spin ang. velocity)
    phi = -pi/2 # initial azimuthal angle
    phidot = 0 # initial rate of change of azimuthal angle
    if pureprecession: # Set to True if you want pure precession, without nutation
        a = (1-I3/I1)*sin(theta)*cos(theta)
        b = -(I3/I1)*psidot*sin(theta)
        c = M*g*r*sin(theta)/I1
        phidot = (-b+sqrt(b**2-4*a*c))/(2*a)
    gyro.axis = gyro.length*vector(sin(theta)*sin(phi),cos(theta),sin(theta)*cos(phi))
    A = norm(gyro.axis)
    gyro.pos = 0.5*Lshaft*A
    tip.pos = Lshaft*A
    tip.clear_trail()

reset()
scene.waitfor('textures')
scene.visible = True

dt = 0.0001
t = 0
Nsteps = 20 # number of calculational steps between graphics updates

while True:
    rate(200)
    for step in range(Nsteps): # multiple calculation steps for accuracy
        # Calculate accelerations of the Lagrangian coordinates:
        atheta = sin(theta)*cos(theta)*phidot**2+( M*g*r*sin(theta)-I3*(psidot+phidot*cos(theta))*phidot*sin(theta))/I1
        aphi = (I3/I1)*(psidot+phidot*cos(theta))*thetadot/sin(theta)-2*cos(theta)*thetadot*phidot/sin(theta)
        apsi = phidot*thetadot*sin(theta)-aphi*cos(theta)
        # Update velocities of the Lagrangian coordinates:
        thetadot += atheta*dt
        phidot += aphi*dt
        psidot += apsi*dt
        # Update Lagrangian coordinates:
        theta += thetadot*dt
        phi += phidot*dt
        psi += psidot*dt

    gyro.axis = gyro.length*vector(sin(theta)*sin(phi),cos(theta),sin(theta)*cos(phi))
    # Display approximate rotation of rotor and shaft:
    gyro.rotate(angle=psidot*dt*Nsteps)
    A = norm(gyro.axis)
    gyro.pos = 0.5*Lshaft*A
    tip.pos = Lshaft*A
    t = t+dt*Nsteps
    
