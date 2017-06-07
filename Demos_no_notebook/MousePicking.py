from vpython import *
scene.width = scene.height = 500
scene.background = color.gray(0.8)
scene.range = 2.2
scene.caption = "Click to pick an object and make it red."
scene.append_to_caption("\nNote picking of individual curve segments.")
box(pos=vector(-1,0,0), color=color.cyan, opacity=1)
box(pos=vector(1,-1,0), color=color.green)
arrow(pos=vector(-1,-1.3,0), color=color.orange)
cone(pos=vector(2,0,0), axis=vector(0,1,-.3), color=color.blue, size=vector(2,1,1))
sphere(pos=vector(-1.5,1.5,0), color=color.white, size=.4*vector(3,2,1))
square = curve(color=color.yellow, radius=.05)
square.append(vector(0,0,0))
square.append(pos=vector(0,1,0), color=color.cyan, radius=.1)
square.append(vector(1,1,0))
square.append(pos=vector(1,0,0), radius=.1)
square.append(vector(0.3,-.3,0))
v0 = vertex(pos=vector(-.5,1.2,0), color=color.green)
v1 = vertex(pos=vector(1,1.2,0), color=color.red)
v2 = vertex(pos=vector(1,2,0), color=color.blue)
v3 = vertex(pos=vector(-.5,2,0), color=color.yellow)
quad(vs=[v0, v1, v2, v3])
extrusion(path=[vector(-1.8,-1.3,0), vector(-1.4,-1.3,0)],
            shape=shapes.circle(radius=.5, thickness=0.4), color=color.yellow)
ring(pos=vector(-0.6,-1.3,0), size=vector(0.2,1,1), color=color.green)
lasthit = None
lastpick = None
lastcolor = None

def getevent(evt):
    global lasthit, lastpick, lastcolor
    if lasthit != None:
        if lastpick != None: lasthit.modify(lastpick, color=lastcolor)
        else: lasthit.color = vector(lastcolor)
        lasthit = lastpick = None

    hit = scene.mouse.pick
    if hit != None:
        lasthit = hit
        lastpick = None
        if isinstance(hit, curve):  # pick individual point of curve
            lastpick = hit.segment
            lastcolor = hit.point(lastpick)['color']
            hit.modify(lastpick, color=color.red)
        elif isinstance(hit, quad):
            lasthit = hit.v0
            lastcolor = vector(lasthit.color) # make a copy
            lasthit.color = color.red
        else:
            lastcolor = vector(hit.color) # make a copy
            hit.color = color.red

scene.bind("mousedown", getevent)

