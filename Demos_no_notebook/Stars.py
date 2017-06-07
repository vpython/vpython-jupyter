from vpython import *

# Stars interacting gravitationally

# Bruce Sherwood

scene.width = scene.height = 600

# Display text below the 3D graphics:
scene.title = "Stars interacting gravitationally"

scene.caption = """Right button drag or Ctrl-drag to rotate "camera" to view scene.
To zoom, drag with middle button or Alt/Option depressed, or use scroll wheel.
  On a two-button mouse, middle is left + right.
Touch screen: pinch/extend to zoom, swipe or two-finger rotate."""

Nstars = 20  # change this to have more or fewer stars

G = 6.7e-11 # Universal gravitational constant

# Typical values
Msun = 2E30
Rsun = 2E9
L = 4e10
vsun = 0.8*sqrt(G*Msun/Rsun)

scene.range = 2*L
scene.forward = vec(-1,-1,-1)

xaxis = curve(color=color.gray(0.5), radius=3e8)
xaxis.append(vec(0,0,0))
xaxis.append(vec(L,0,0))
yaxis = curve(color=color.gray(0.5), radius=3e8)
yaxis.append(vec(0,0,0))
yaxis.append(vec(0,L,0))
zaxis = curve(color=color.gray(0.5), radius=3e8)
zaxis.append(vec(0,0,0))
zaxis.append(vec(0,0,L))

Stars = []
star_colors = [color.red, color.green, color.blue,
              color.yellow, color.cyan, color.magenta]

psum = vec(0,0,0)
for i in range(Nstars):
    star = sphere(pos=L*vec.random(), make_trail=True, retain=150, trail_radius=3e8)
    R = Rsun/2+Rsun*random()
    star.radius = R
    star.mass = Msun*(R/Rsun)**3
    star.momentum = vec.random()*vsun*star.mass
    star.color = star.trail_color = star_colors[i % 6]
    Stars.append( star )
    psum = psum + star.momentum

#make total initial momentum equal zero
for i in range(Nstars):
    Stars[i].momentum = Stars[i].momentum - psum/Nstars

dt = 1000
hitlist = []

def computeForces():
    global hitlist, Stars
    hitlist = []
    N = len(Stars)
    for i in range(N):
        si = Stars[i]
        if si is None: continue
        F = vec(0,0,0)
        pos1 = si.pos
        m1 = si.mass
        radius = si.radius
        for j in range(N):
            if i == j: continue
            sj = Stars[j]
            if sj is None: continue
            r = sj.pos - pos1
            rmag2 = mag2(r)
            if rmag2 <= (radius+sj.radius)**2: hitlist.append([i,j])
            F = F + (G*m1*sj.mass/(rmag2**1.5))*r
        si.momentum = si.momentum + F*dt

while True:
    rate(100)
    
    # Compute all forces on all stars
    computeForces()

    # Having updated all momenta, now update all positions
    for star in Stars:
        if star is None: continue
        star.pos = star.pos + star.momentum*(dt/star.mass)

    # If any collisions took place, merge those stars
    hit = len(hitlist)-1
    while hit > 0:
        s1 = Stars[hitlist[hit][0]]
        s2 = Stars[hitlist[hit][1]]
        if (s1 is None) or (s2 is None): continue
    
        mass = s1.mass + s2.mass
        momentum = s1.momentum + s2.momentum
        pos = (s1.mass*s1.pos + s2.mass*s2.pos) / mass
        s1.color = s1.trail_color = (s1.mass*s1.color + s2.mass*s2.color) / mass
        R = Rsun*(mass / Msun)**(1/3)
        
        s1.clear_trail()
        s2.clear_trail()
        s2.visible = False
        
        s1.mass = mass
        s1.momentum = momentum
        s1.pos = pos
        s1.radius = R
        Stars[hitlist[hit][1]] = None
        hit -= 1
