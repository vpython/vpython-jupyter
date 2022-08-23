from vpython import *
scene.width = 350
scene.height = 300
scene.range = 1.3
scene.title = "Widgets (buttons, etc.)\n"

running = True

def Run(b):
    global running
    running = not running
    if running: b.text = "Pause"
    else: b.text = "Run"
    
button(text="Pause", pos=scene.title_anchor, bind=Run)

box_object = box(visible=True)
cone_object = cone(visible=False, radius=0.5)
pyramid_object = pyramid(visible=False)
cylinder_object = cylinder(visible=False, radius=0.5)

col = color.cyan
currentobject = box_object
currentobject.color = col

def Color(c):
    global col
    if col.equals(color.cyan): # change to red
        currentobject.color = col = color.red
        c.text = "<b>Cyan</b>"
        c.color = color.cyan
        c.background = color.red
        if c.name is None: # this is the top button
            r1.checked = False
            r2.checked = True
    else:                      # change to cyan
        currentobject.color = col = color.cyan
        c.text = "<b>Red</b>"
        c.color = color.red
        c.background = color.cyan
        if c.name is None: # this is the top button
            r1.checked = True
            r2.checked = False
        
def cc(c):
    global col
    if col.equals(color.cyan): # change to red:
        currentobject.color = col = color.red
        cbutton.text = "<b>Cyan</b>"
        cbutton.color = color.cyan
        cbutton.background = color.red
    else:                      # change to cyan
        currentobject.color = col = color.cyan
        cbutton.text = "<b>Red</b>"
        cbutton.color = color.red
        cbutton.background = color.cyan
        
cbutton = button(text='<b>Red</b>', color=color.red, background=color.cyan, 
            pos=scene.title_anchor, bind=Color, name=None)

scene.caption = "Vary the rotation speed: \n\n"

def setspeed(s):
    wt.text = '{:1.2f}'.format(s.value)
    
sl = slider(min=0.3, max=3, value=1.5, length=220, bind=setspeed, right=15)

wt = wtext(text='{:1.2f}'.format(sl.value))

scene.append_to_caption(' radians/s\n')

r1 = radio(bind=cc, checked=True, text='Cyan', name='rads')

scene.append_to_caption('       ')

def M(m):
    global col, currentobject
    op = currentobject.opacity
    currentaxis = currentobject.axis
    currentobject.visible = False
    val = m.selected
    if val == "box": 
        currentobject = box_object
    elif val == "cone": 
        currentobject = cone_object
    elif val == "pyramid": 
        currentobject = pyramid_object
    elif val == "cylinder": 
        currentobject = cylinder_object
    currentobject.color = col
    currentobject.axis = currentaxis
    currentobject.visible = True
    currentobject.opacity = op

menu(choices=['Choose an object', 'box', 'cone', 'pyramid', 'cylinder'], index=0, bind=M)

scene.append_to_caption('\n')

r2 = radio(bind=cc, text='Red', name='rads')

scene.append_to_caption('         ')

def transparency(b):
    if b.checked:
        currentobject.opacity = 0.5
    else:
        currentobject.opacity = 1

checkbox(bind=transparency, text='Transparent')

dt = 0.01
while True:
    rate(1/dt)
    if running:
        currentobject.rotate(angle=sl.value*dt, axis=vector(0,1,0))
