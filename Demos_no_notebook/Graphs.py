from vpython import *

s = '    Test of <b><i>graphing</i></b>. Move the mouse over the graph to display data.'
oscillation = graph(title=s, xtitle='time', ytitle='value')
funct1 = gcurve(color=color.blue, width=4)
funct2 = gvbars(delta=0.4, color=color.red)
funct3 = gdots(color=color.orange, size=3)

for t in range(-30, 74, 1):
    rate(100)
    funct1.plot( t, 5.0+5.0*cos(-0.2*t)*exp(0.015*t) )
    funct2.plot( t, 2.0+5.0*cos(-0.1*t)*exp(0.015*t) )
    funct3.plot( t, 5.0*cos(-0.03*t)*exp(0.015*t) )

box()
scene.pause()
funct2.delete()
scene.pause()
oscillation.delete()
scene.pause()
scene.delete()
