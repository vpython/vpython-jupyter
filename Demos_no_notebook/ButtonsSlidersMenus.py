from vpython import *
# This version uses VPython widgets: button, radio button, checkbox, slider, menu
# See ButtonsSlidersMenus1 for a version that uses Jupyter notebook widgets: button, slider, menu
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
sphere(radius=0.3)

col = color.cyan
currentobject = box_object
currentobject.color = col

def Color(c):
    global col
    if col.equals(color.cyan): # change to red
        currentobject.color = col = color.red
        cbutton.text = "<b>Cyan</b>"
        cbutton.textcolor = color.cyan
        cbutton.background = color.red
        r1.checked = False
        r2.checked = True
    else:                      # change to cyan
        currentobject.color = col = color.cyan
        cbutton.text = "<b>Red</b>"
        cbutton.textcolor = color.red
        cbutton.background = color.cyan
        r1.checked = True
        r2.checked = False
        
cbutton = button(text='<b>Red</b>', textcolor=color.red, background=color.cyan, pos=scene.title_anchor, bind=Color)

scene.caption = "Vary the rotation speed:\n"
speed = 150
def setspeed(s):
    global speed
    speed = s.value
    wt.text = '{:1.0f}'.format(s.value)
    
sl = slider(min=20, max=500, value=250, length=280, bind=setspeed, right=15)

wt = wtext(text='{:1.0f}'.format(sl.value))

scene.append_to_caption('\n')

r1 = radio(bind=Color, checked=True, text='Cyan')

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

r2 = radio(bind=Color, text='Red')

scene.append_to_caption('         ')

def transparency(b):
    if b.checked:
        currentobject.opacity = 0.5
    else:
        currentobject.opacity = 1

checkbox(bind=transparency, text='Transparent')

while True:
    rate(100)
    if running:
        currentobject.rotate(angle=speed*1e-4, axis=vector(0,1,0))

