# Visual check for PR #290 (issue #287): constructor size= must be honoured.
# BEFORE the fix: both curves render at the default thickness and both dot
# sets at the default radius — size= silently ignored.
# AFTER the fix: the second of each pair is visibly fatter.
from vpython import *
from math import sin

g = graph(title='#287 check: thin = default, FAT = size argument honoured', fast=False)

thin_curve = gcurve(color=color.blue, label='gcurve default')
fat_curve  = gcurve(color=color.red,  size=10, label='gcurve size=10')
thin_dots  = gdots(color=color.green, label='gdots default')
fat_dots   = gdots(color=color.orange, size=14, label='gdots size=14')

for i in range(60):
    x = i / 10
    thin_curve.plot(x, sin(x) + 2.5)
    fat_curve.plot(x, sin(x) + 1.2)
    thin_dots.plot(x, sin(x) - 1.2)
    fat_dots.plot(x, sin(x) - 2.5)

while True:
    rate(10)
