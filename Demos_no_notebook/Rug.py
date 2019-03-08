from vpython import *
scene.width = scene.height = 600
scene.range = 0.6

# A pulse ripples along a rug, demonstrating dynamic changea of shape
# Bruce Sherwood, May 2012

def display_instructions():
    s = "In GlowScript programs:\n\n"
    s += "    Rotate the camera by dragging with the right mouse button,\n        or hold down the Ctrl key and drag.\n\n"
    s += "    To zoom, drag with the left+right mouse buttons,\n         or hold down the Alt/Option key and drag,\n         or use the mouse wheel.\n"
    s += "\nTouch screen: pinch/extend to zoom, swipe or two-finger rotate."
    scene.caption = s
    
display_instructions()

# Construct a square WxH divided into little squares
# There are (w+1)x(h+1) vertices
# Center of rug is at 0,0,0

H = W = 1
w = 1
h = 50
dx = W/w
dy = H/h

# Create a grid of vertex objects covering the rug
verts = []
for y in range(h+1): # from 0 to h inclusive, to include both bottom and top edges
    verts.append([])
    for x in range(w+1): # from 0 to w inclusive, to include both left and right edges
        verts[y].append(vertex(pos=vector(-0.5+x*dx,-0.5+y*dy,0), normal=vector(0,0,1), texpos=vector(x/w,y/h,0), shininess= 0))

# Create quads (equivalent to two triangles) based on the vertex objects just created.
# Note that a particular vertex may be shared by as many as 4 neighboring quads, and
# changing one vertex affects all of the quads that use that vertex.
for y in range(h): # from 0 to h, not including h
    for x in range(w): # from 0 to w, not including w
        quad(vs=[verts[y][x], verts[y][x+1], verts[y+1][x+1], verts[y+1][x]], texture=textures.rug)

scene.waitfor('textures') # wait until the rug texture has been loaded

Lpulse = 0.4 # length of half sine wave
dy_pulse = Lpulse/50
k = pi/(0.6*Lpulse)
A = 0.05

def pulse(z): # return the pulse height and normal
    if z < 0.2*Lpulse: return 0
    if z > 0.8*Lpulse: return 0
    z -= 0.2*Lpulse
    return A*sin(k*z)

run = True

def down(ev):
    global run
    run = not run

scene.bind("mousedown", down)

y = -0.5-Lpulse-dy_pulse # bottom of pulse (starts below rug)
while True:
    rate(50)
    while not run:
        scene.waitfor('redraw')
    y += dy_pulse
    if y+Lpulse <= -0.5:
        continue
    if y >= 0.5:
        y = -0.5-Lpulse
        continue
        
    # Note: floor and ceil are floats in Python 2 but ints in Python 3
    start = int(floor((y+0.5)/dy))     # lowest row of vertices in pulse
    end = int(ceil((y+0.5+Lpulse)/dy)) # highest row of vertices in pulse
    if start < 0:
        if end <= 0: continue
        start = 0
    if end > h:
        end = h
    
    yp = -0.5+start*dy
    for s in range(start,end):
        z0 = pulse(yp-y-dy_pulse)
        z1 = pulse(yp-y)
        z2 = pulse(yp+dy_pulse-y)
        yp += dy # advance to next row
        
        # If slope of a line is dy/dz, normal to the line is in direction < -dz, +dy >
        n1y0 = -(z1-z0)
        n2y0 = -(z2-z1)
        n1y = .5*(n1y0+n2y0) # average adjacent normals to smooth the lighting
        n1z = dy
        
        vy = verts[s]
        for vx in range(w+1):
            vy[vx].pos.z = z1
            vy[vx].normal = vector(0,n1y,n1z) 
