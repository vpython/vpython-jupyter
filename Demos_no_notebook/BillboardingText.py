from vpython import *
b = box(pos=vec(-4,2,0), color=color.red)
c1 = cylinder(pos=b.pos, radius=0.1, axis=vec(0,1.5,0), color=color.yellow)
s = sphere(pos=vec(4,-4,0), radius=0.5, color=color.green)
c2 = cylinder(pos=s.pos, radius=0.1, axis=vec(0,1.5,0), color=color.yellow)
t1 = text(text='box', pos=c1.pos+c1.axis, align='center', height=0.5,
          color=color.yellow, billboard=True, emissive=True)
t2 = text(text='sphere', pos=c2.pos+c2.axis, align='center', height=0.5,
          color=color.yellow, billboard=True, emissive=True)
t3 = text(text='Faces forward', pos=vec(-4,0,0),
          color=color.cyan, billboard=True, emissive=True)
box(pos=t3.start, size=0.1*vec(1,1,1), color=color.red)
t4 = text(text='Regular text', pos=vec(-4,-1,0), depth=0.5, color=color.yellow,
        start_face_color=color.red, end_face_color=color.green)
box(pos=t4.start, size=0.1*vec(1,1,1), color=color.red)

scene.caption = """<b>3D text can be "billboard" text -- always facing you.</b>
Note that the "Regular text" has different colors on the front, back and sides.
Right button drag or Ctrl-drag to rotate "camera" to view scene.
To zoom, drag with middle button or Alt/Option depressed, or use scroll wheel.
  On a two-button mouse, middle is left + right.
Touch screen: pinch/extend to zoom, swipe or two-finger rotate."""
