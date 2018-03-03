from vpython import *
scene.background = color.gray(0.8)
scene.forward = vec(0,-0.2,-1)
scene.fov = 0.2
scene.range = 3.8
scene.caption = """Right button drag or Ctrl-drag to rotate "camera" to view scene.
To zoom, drag with middle button or Alt/Option depressed, or use scroll wheel.
     On a two-button mouse, middle is left + right.
Touch screen: pinch/extend to zoom, swipe or two-finger rotate.\n"""

E1 = extrusion(path=[vec(0,0,0), vec(0,0,-0.7)], texture=textures.wood_old,
    shape=[ shapes.circle(radius=1.5),
            shapes.triangle(pos=[0,-0.6], length=1.2),
            shapes.trapezoid(pos=[0,0.6], width=1.6,
              height=1, top=0.6) ], pos=vec(-4,1.5,0))

copper = vec(0.722,0.451,0.200)
E2 = extrusion(path=paths.arc(radius=1.7, angle2=pi), texture=textures.metal, 
    shape=[ [shapes.triangle(length=2), shapes.circle(pos=[0,.5], radius=0.2),
    shapes.trapezoid(pos=[0,-0.2], width=0.6, height=0.4)],
    [shapes.rectangle(pos=[0,1.8], width=1,height=0.3)] ],
    start_face_color=copper, end_face_color=copper)
E2center = E2.pos    # initial pos of center of extrusion
E2.pos = vec(3,2,0)  # new pos of center of extrsion
E2rot = E2.pos+vec(0,0,-E2center.z) # a location at the front of the extrusion

halo = ring(pos=vec(0,0,1), radius=0.8, thickness=0.2, color=color.cyan )

rect = extrusion(path=paths.rectangle(width=5, height=2), 
            shape=shapes.hexagon(length=0.3), color=color.red)

bottom = extrusion(path=paths.cross(width=4, thickness=1),
            shape=shapes.circle(radius=0.2), color=color.green)

tube = extrusion(path=[vec(0,0,0), vec(2,0,0)], shape=shapes.circle(radius=0.6, thickness=0.2),
                    pos=vec(-1,1.7,0), axis=vec(0,0,2), color=color.yellow, end_face_color=color.blue)
text(pos=tube.pos+vec(0,0,1), text='tube', align='center',
        height=0.25, depth=0, color=color.blue)

run = True

def runner(r):
    global run
    run = r.checked
    
checkbox(bind=runner, text='Run', checked=True)

scene.waitfor('textures')

t = 0
dt = 0.01
dtheta = 0.01
while True:
    rate(100)
    if run:
        halo.pos.x = -1+sin(2*t)
        bottom.pos.y = -2+0.5*cos(3*t)
        E1.rotate(angle=dtheta, axis=vec(0,1,0))
        E2.rotate(angle=-dtheta, axis=vec(0,1,0), origin=E2rot)
        t += dt

