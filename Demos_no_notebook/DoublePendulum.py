from vpython import *
# Double pendulum

# The analysis is in terms of Lagrangian mechanics.
# The Lagrangian variables are angle of upper bar, angle of lower bar,
# measured from the vertical.

# Bruce Sherwood

# Corrections to the Lagrangian calculations by Owen Long, UC. Riverside

scene.width = scene.height = 600
scene.range = 1.8
scene.title = "A double pendulum"

def display_instructions():
    s = "In VPython programs:\n"
    s += "    Rotate the camera by dragging with the right mouse button,\n        or hold down the Ctrl key and drag.\n"
    s += "    To zoom, drag with the left+right mouse buttons,\n         or hold down the Alt/Option key and drag,\n         or use the mouse wheel.\n"
    s += "Touch screen: pinch/extend to zoom, swipe or two-finger rotate."
    scene.caption = s

# Display text below the 3D graphics:
display_instructions()

g = 9.8
M1 = 2.0
M2 = 1.0
d = 0.05 # thickness of each bar
gap = 2*d # distance between two parts of upper, U-shaped assembly
L1 = 0.5 # physical length of upper assembly; distance between axles
L1display = L1+d # show upper assembly a bit longer than physical, to overlap axle
L2 = 1 # physical length of lower bar
L2display = L2+d/2 # show lower bar a bit longer than physical, to overlap axle
# Coefficients used in Lagrangian calculation
A = (1/4)*M1*L1**2+(1/12)*M1*L1**2+M2*L1**2
B = (1/2)*M2*L1*L2
C = g*L1*(M1/2+M2)
D = M2*L1*L2/2
E = (1/12)*M2*L2**2+(1/4)*M2*L2**2
F = g*L2*M2/2

hpedestal = 1.3*(L1+L2) # height of pedestal
wpedestal = 0.1 # width of pedestal
tbase = 0.05 # thickness of base
wbase = 8*gap # width of base
offset = 2*gap # from center of pedestal to center of U-shaped upper assembly
pedestal_top = vec(0,hpedestal/2,0) # top of inner bar of U-shaped upper assembly

theta1 = 1.3*pi/2 # initial upper angle (from vertical)
theta1dot = 0 # initial rate of change of theta1
theta2 = 0 # initial lower angle (from vertical)
theta2dot = 0 # initial rate of change of theta2

pedestal = box( pos=pedestal_top-vec(0,hpedestal/2,offset),
                size=vec(wpedestal,1.1*hpedestal,wpedestal),
                color=vec(0.4,0.4,0.5) )
base = box( pos=pedestal_top-vec(0,hpedestal+tbase/2,offset),
                 size=vec(wbase,tbase,wbase),
                 color=pedestal.color )
axle1 = cylinder( pos=pedestal_top-vec(0,0,gap/2-d/4), axis=vec(0,0,-1),
                 size=vec(offset,d/4,d/4), color=color.yellow )

bar1 = box( pos=pedestal_top+vec(L1display/2-d/2,0,-(gap+d)/2), 
                 size=vec(L1display,d,d), color=color.red )
bar1.rotate( angle=-pi/2, axis=vec(0,0,1), origin=vec(axle1.pos.x, axle1.pos.y, bar1.pos.z) )
bar1.rotate( angle=theta1, axis=vec(0,0,1), origin=vec(axle1.pos.x, axle1.pos.y, bar1.pos.z) )

bar1b = box( pos=pedestal_top+vec(L1display/2-d/2,0,(gap+d)/2), 
                 size=vec(L1display,d,d), color=bar1.color )
bar1b.rotate( angle=-pi/2, axis=vec(0,0,1), origin=vec(axle1.pos.x, axle1.pos.y, bar1b.pos.z) )
bar1b.rotate( angle=theta1, axis=vec(0,0,1), origin=vec(axle1.pos.x, axle1.pos.y, bar1b.pos.z) )

pivot1 = vec(axle1.pos.x, axle1.pos.y, 0)

axle2 = cylinder( pos=pedestal_top+vec(L1,0,-(gap+d)/2), axis=vec(0,0,1), 
                size=vec(gap+d,axle1.size.y/2,axle1.size.y/2), color=axle1.color )
axle2.rotate( angle=-pi/2, axis=vec(0,0,1), origin=vec(axle1.pos.x, axle1.pos.y, axle2.pos.z) )
axle2.rotate( angle=theta1, axis=vec(0,0,1), origin=vec(axle1.pos.x, axle1.pos.y, axle2.pos.z) )

bar2 = box( pos=axle2.pos+vec(L2display/2-d/2,0,(gap+d)/2), 
        size=vec(L2display,d,d), color=color.green )

bar2.rotate( angle=-pi/2,  axis=vec(0,0,1), origin=vec(axle2.pos.x, axle2.pos.y, bar2.pos.z) )
bar2.rotate( angle=theta2,  axis=vec(0,0,1), origin=vec(axle2.pos.x, axle2.pos.y, bar2.pos.z) )

dt = 0.001
t = 0

while True:
    rate(1/dt) 
    # Calculate accelerations of the Lagrangian coordinates=
    atheta1 = ((E*C/B)*sin(theta1)-F*sin(theta2))/(D-E*A/B)
    atheta2 = -(A*atheta1+C*sin(theta1))/B
    # Update velocities of the Lagrangian coordinates=
    theta1dot = theta1dot+atheta1*dt
    theta2dot = theta2dot+atheta2*dt
    # Update Lagrangian coordinates=
    dtheta1 = theta1dot*dt
    dtheta2 = theta2dot*dt
    theta1 = theta1+dtheta1
    theta2 = theta2+dtheta2
    
    bar1.rotate( angle=dtheta1, axis=vec(0,0,1), origin=pivot1 )
    bar1b.rotate( angle=dtheta1, axis=vec(0,0,1), origin=pivot1 )
    pivot2 = vec(axle2.pos.x, axle2.pos.y, pivot1.z)
    axle2.rotate( angle=dtheta1, axis=vec(0,0,1), origin=pivot1 )
    bar2.rotate( angle=dtheta2, axis=vec(0,0,1), origin=pivot2 )
    pivot2 = vec(axle2.pos.x, axle2.pos.y, pivot1.z)
    bar2.pos = pivot2 + bar2.axis/2
    
    t = t+dt
