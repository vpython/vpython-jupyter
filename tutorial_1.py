import vpython as vp
from vpython import vector
vp.scene.background = vp.color.white
L = 2
H = 7
W = 1
'''
main_body = vp.box(pos = vp.vector(0,0,0),
                   length = L, height = H, width = W)

cone_pos = vp.vector(0, H/2, 0)
top_cone = vp.cone(pos = cone_pos,
                   axis = vp.vector(0,5,0), radius = main_body.width,
                   color = vp.color.red)

rocket = vp.compound([main_body, top_cone])
'''

wall_opacity = 1
ball = vp.sphere(pop = vector(-5, 0, 0), radius = 0.5, color = vp.color.cyan, make_trail = True, retain = 3)
wallR = vp.box(pos = vector(6,0,0), size = vector(0.2, 12, 12), color = vp.color.green, opacity = wall_opacity)
wallL = vp.box(pos = vector(-6,0,0), size = vector(0.2, 12, 12), color = vp.color.green, opacity = wall_opacity)
wall_up = vp.box(pos = vector(0,6,0), size = vector(12, 0.2, 12), color = vp.color.green, opacity = wall_opacity)
wall_down = vp.box(pos = vector(0,-6,0), size = vector(12, 0.2, 12), color = vp.color.green, opacity = wall_opacity)
wall_back = vp.box(pos = vector(0,0,-6), size = vector(12, 12, 0.2), color = vp.color.white, opacity = wall_opacity)
wall_front = vp.box(pos = vector(0,0,6), size = vector(12, 12, 0.2), color = vp.color.white, opacity = 0.4)

ball.velocity = vector(25, 5, 10)
d_t = 0.005
t = 0
t_max = 100
vscale = 0.1
varr = vp.arrow(pos = ball.pos ,axis = vscale*ball.velocity, color = vp.color.yellow)
vp.scene.autoscale = False
while t < t_max:
    vp.rate(200)
    ball.pos = ball.pos + ball.velocity*d_t
    if ball.pos.x + ball.radius > wallR.pos.x or ball.pos.x - ball.radius < wallL.pos.x:
        ball.velocity.x = -ball.velocity.x
    if ball.pos.y + ball.radius > wall_up.pos.y or ball.pos.y - ball.radius < wall_down.pos.y:
        ball.velocity.y = -ball.velocity.y
    if ball.pos.z + ball.radius > wall_front.pos.z or ball.pos.z - ball.radius < wall_back.pos.z:
        ball.velocity.z = -ball.velocity.z
    varr.pos = ball.pos
    varr.axis = vscale*ball.velocity
    t += d_t

