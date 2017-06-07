from vpython import *
scene.caption = """In GlowScript programs:
Right button drag or Ctrl-drag to rotate "camera" to view scene.
To zoom, drag with middle button or Alt/Option depressed, or use scroll wheel.
  On a two-button mouse, middle is left + right.
Touch screen: pinch/extend to zoom, swipe or two-finger rotate."""
scene.forward = vector(0,-.3,-1)

G = 6.7e-11 # Newton gravitational constant

giant = sphere(pos=vector(-1e11,0,0), radius=2e10, color=color.red, 
                make_trail=True, trail_type='points', interval=10, retain=50)
giant.mass = 2e30
giant.p = vector(0, 0, -1e4) * giant.mass

dwarf = sphere(pos=vector(1.5e11,0,0), radius=1e10, color=color.yellow,
                make_trail=True, interval=10, retain=50)
dwarf.mass = 1e30
dwarf.p = -giant.p

dt = 1e5
while True:
    rate(200)
    r = dwarf.pos - giant.pos
    F = G * giant.mass * dwarf.mass * norm(r) / mag2(r)
    giant.p = giant.p + F*dt
    dwarf.p = dwarf.p - F*dt
    giant.pos = giant.pos + (giant.p/giant.mass) * dt
    dwarf.pos = dwarf.pos + (dwarf.p/dwarf.mass) * dt
