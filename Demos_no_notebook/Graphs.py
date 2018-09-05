from vpython import *
s = '    Test of <b><i>graphing</i></b>. Move the mouse over the graph to display data.'
test = graph(title=s, xtitle='time', ytitle='value', fast=False)
funct1 = gcurve(color=color.blue, width=4, dot=True, 
        dot_color=color.green, dot_radius=15, radius=5, markers=True, marker_color=color.cyan)
funct2 = gvbars(delta=0.4, color=color.red, label='bars')
funct3 = gdots(color=color.orange)

for t in range(-30, 74):
    rate(500)
    funct1.plot( t, 5.0+5.0*cos(-0.2*t)*exp(0.015*t) )
    funct2.plot( t, 2.0+5.0*cos(-0.1*t)*exp(0.015*t) )
    funct3.plot( t, 5.0*cos(-0.03*t)*exp(0.015*t) )

scene.width = scene.height = 100
box()
scene.pause()
test.title = 'New title'
test.xtitle = "New xtitle"
test.ytitle = 'New ytitle'
scene.pause()
funct2.data = [(-20,8), (-30,4)]
funct2.color = color.green
scene.pause()
funct2.label = 'new bars'
funct3.label = 'dots'
scene.pause()
funct2.legend = False
scene.pause()
funct2.delta = 10
funct1.width = 1
funct3.radius = 2*funct3.radius
scene.pause()
#funct3.size = 20
#funct2.horizontal = True
#funct2.orientation = 'h'
funct1.dot_radius = 40
funct1.dot_color = color.cyan
funct1.marker_color = color.black
scene.pause()
funct1.markers = False
scene.pause()
funct1.delete()
scene.pause()
test.delete()
print('done')