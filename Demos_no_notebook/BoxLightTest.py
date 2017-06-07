from vpython import *

# Mikhail Temkine, University of Toronto, April 2007

scene.forward = vector(-0.4,-0.3,-1)
r = 3
a1 = a2 = a3 = 0.0

arrow(pos=vector(0, 4, 0), axis=vector(0, 1, 0), color=color.red)
boxy = box(size=vector(3,3,3), color=vector(0.5, 0.5, 0.5), texture=textures.rough)
b1 = sphere(radius=0.3, pos=vector(r, 0, 0), color=color.magenta, emissive=True)
b2 = sphere(radius=0.3, pos=vector(0, 0, r), color=color.yellow, emissive=True)
b3 = arrow(radius=0.3, pos=vector(0, 0, r), color=color.green, emissive=True)
l1 = local_light(pos=b1.pos, color=b1.color)
l2 = local_light(pos=b2.pos, color=b2.color)
l3 = distant_light(direction=b3.pos, color=b3.color)

while True:
    rate(100)
    l1.pos = b1.pos = r*vector(cos(a1), sin(a1), b1.pos.z)
    a1 += 0.02
    l2.pos = b2.pos = (r+0.4)*vector(b2.pos.x, sin(a2), cos(a2))
    a2 += 0.055
    l3.direction = b3.pos = (r+3)*vector(sin(a3), b3.pos.y, cos(a3))
    b3.axis = b3.pos * -0.3
    a3 += 0.033
