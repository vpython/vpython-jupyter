from vpython import *
scene.width = 600
scene.height = 600
show = 'box'
last_show = show
 
D = 0.7 # size of box
R = .4 # radius of sphere

names = ['flower', 'granite', 'gravel', 'metal', 'rock', 'rough', 'rug', 'stones', 'stucco', 'wood', 'wood_old', 'earth']
Ts = [textures.flower, textures.granite, textures.gravel, textures.metal, textures.rock, textures.rough,
      textures.rug, textures.stones, textures.stucco, textures.wood, textures.wood_old, textures.earth]
bumps = [ None, None, 'gravel', None, 'rock', None, None, 'stones', 'stucco', None, 'wood_old']

def erase():
    for obj in scene.objects:
        obj.visible = False

def show_object(index, x, y):
    T = Ts[index]
    B = None
    # Bump maps aren't very salient unless one moves the light or rotates the object,
    # so don't bother with bump maps unless there's an option to move the light or object.
    #if (bumps[index] !== None) B = bumpmaps[bumps[index]]
    if show == 'box':
        c = box(pos=vec(x,y,0), size=D*vec(1,1,1))
    elif show == 'sphere':
        c = sphere(pos=vec(x,y,0), size=D*vec(1,1,1))
    elif show == 'cylinder': 
        c = cylinder(pos=vec(x-D/2,y,0), size=D*vec(1,1,1))
    elif show == 'cone': 
        c = cone(pos=vec(x-D/2,y,0), size=D*vec(1,1,1))
    elif show == 'pyramid': 
        c = pyramid(pos=vec(x-D/2,y,0), size=D*vec(1,1,1))
    c.index = index
    c.shininess = 0
    c.texture = {'file':T, 'bumpmap':B}
    label(pos=vec(x,y-.5,0), box=0, text='textures.'+names[index])

def setup():
    scene.range = 2.2
    scene.fov = 0.2
    scene.center = vec(1.5,2,0)
    scene.forward = vec(0,0,-1)
    erase()
    scene.visible = False
    index = 0
    y = 3.3
    while y > 0:
        for x in range(4):
            if index >= len(names): break; 
            show_object(index, x, y)
            index += 1
        y -= 1.3
    scene.visible = True

setup()
scene.visible = False
scene.caption = "Loading textures..."
scene.waitfor("textures")
scene.caption = "Choose the type of object:  "
scene.visible = True

def choose(c):
    global show
    show = c.selected
    
menu(choices=['box', 'sphere', 'cylinder', 'cone', 'pyramid'], selected='box', bind=choose)

scene.append_to_caption('\n\nClick an object to enlarge it; then click anywhere to show all objects again.')

hit = None
clicked = False
def handle_click(ev):
    global hit, clicked
    hit = scene.mouse.pick
    clicked = True
scene.bind('click', handle_click)

def single_object(index):
    scene.center = vec(0,-.1*R,0)
    scene.range = 1.5*R
    erase()
    show_object(index, 0, 0)

picked = None
    
while True:
    rate(30)
    if show != last_show:
        last_show = show
        if picked != None:
            single_object(picked.index)
        else:
            setup()
    if clicked:
        clicked = False
        if picked != None:
            picked = None
            setup()
        elif picked == None and hit != None:
            picked = hit
            hit = None
            single_object(picked.index)
