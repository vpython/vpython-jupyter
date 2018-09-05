from vpython import *

# Bruce Sherwood

N = 4 # N by N by N array of atoms
# Surrounding the N**3 atoms is another layer of invisible fixed-position atoms
# that provide stability to the lattice.
k = 1
m = 1
spacing = 1
atom_radius = 0.3*spacing
L0 = spacing-1.8*atom_radius
V0 = pi*(0.5*atom_radius)**2*L0 # initial volume of spring
scene.center = 0.5*(N-1)*vector(1,1,1)
dt = 0.04*(2*pi*sqrt(m/k))
axes = [vector(1,0,0), vector(0,1,0), vector(0,0,1)]

scene.caption= """A model of a solid represented as atoms connected by interatomic bonds.

Right button drag or Ctrl-drag to rotate "camera" to view scene.
To zoom, drag with middle button or Alt/Option depressed, or use scroll wheel.
  On a two-button mouse, middle is left + right.
Touch screen: pinch/extend to zoom, swipe or two-finger rotate."""

class crystal:
        
    def __init__(self,  N, atom_radius, spacing, momentumRange ):
        self.atoms = []
        self.springs = []
        
        # Create (N+2)^3 atoms in a grid; the outermost atoms are fixed and invisible
        for z in range(-1,N+1,1):
            for y in range(-1,N+1,1):
                for x in range(-1,N+1,1):
                    atom = sphere()
                    atom.pos = vector(x,y,z)*spacing
                    atom.radius = atom_radius
                    atom.color = vector(0,0.58,0.69)
                    if 0 <= x < N and 0 <= y < N and 0 <= z < N:
                        p = vec.random()
                        atom.momentum = momentumRange*p
                    else:
                        atom.visible = False
                        atom.momentum = vec(0,0,0)
                    atom.index = len(self.atoms)
                    self.atoms.append( atom )
        for atom in self.atoms:
            if atom.visible:
                if atom.pos.x == 0:
                    self.make_spring(self.atoms[atom.index-1], atom, False)
                    self.make_spring(atom, self.atoms[atom.index+1], True)
                elif atom.pos.x == N-1:
                    self.make_spring(atom, self.atoms[atom.index+1], False)
                else:
                    self.make_spring(atom, self.atoms[atom.index+1], True)

                if atom.pos.y == 0:
                    self.make_spring(self.atoms[atom.index-(N+2)], atom, False)
                    self.make_spring(atom, self.atoms[atom.index+(N+2)], True)
                elif atom.pos.y == N-1:
                    self.make_spring(atom, self.atoms[atom.index+(N+2)], False)
                else:
                    self.make_spring(atom, self.atoms[atom.index+(N+2)], True)
                    
                if atom.pos.z == 0:
                    self.make_spring(self.atoms[atom.index-(N+2)**2], atom, False)
                    self.make_spring(atom, self.atoms[atom.index+(N+2)**2], True)
                elif atom.pos.z == N-1:
                    self.make_spring(atom, self.atoms[atom.index+(N+2)**2], False)
                else:
                    self.make_spring(atom, self.atoms[atom.index+(N+2)**2], True)
    
    # Create a grid of springs linking each atom to the adjacent atoms
    # in each dimension, or to invisible motionless atoms
    def make_spring(self, start, end, visible):
        spring = helix()
        spring.pos = start.pos
        spring.axis = end.pos-start.pos
        spring.visible = visible
        spring.thickness = 0.05
        spring.radius = 0.5*atom_radius
        spring.length = spacing
        spring.start = start
        spring.end = end
        spring.color = color.orange
        self.springs.append(spring)

c = crystal(N, atom_radius, spacing, 0.1*spacing*sqrt(k/m))

while True:
    rate(60)
    for atom in c.atoms:
        if atom.visible:
            atom.pos = atom.pos + atom.momentum/m*dt
    for spring in c.springs:
        spring.axis = spring.end.pos - spring.start.pos
        L = mag(spring.axis)
        spring.axis = spring.axis.norm()
        spring.pos = spring.start.pos+0.5*atom_radius*spring.axis
        Ls = L-atom_radius
        spring.length = Ls
        Fdt = spring.axis * (k*dt * (1-spacing/L))
        if spring.start.visible:
            spring.start.momentum = spring.start.momentum + Fdt
        if spring.end.visible:
            spring.end.momentum = spring.end.momentum - Fdt
