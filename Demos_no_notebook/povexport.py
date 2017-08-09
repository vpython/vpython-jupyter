from __future__ import division, print_function
"""
This module exports a VPython scene as POV-Ray scene description code.
Lights and camera location from the current scene are included.
Optionally, you may specify a list of include files,
   and pov textures for objects.
For an example of its use, see 'povexample.py'.
Objects not urrently exported:
    compound, 3D text, extrusion, points, triangle, quad
Further documentation is found at the start of the file.
"""

# This module exports a description of a VPython scene as a .pov file that can be
# read by the multiplatform free program POV-Ray, which produces a high-quality
# ray-traced image, with shadows (by default). The output is a png file (.png)
# which can be further processed by many programs, including Photoshop.

# To use, import the export routine from this file ("from povexport import export").
# When you have the VPython scene you want, execute "export()", then read the resulting
# .pov file into POV-ray.

# Here are the export routine's default options:
# export(canvas=None, filename=None, include_list=None, custom_text='', shadowless=0)
# If no canvas is specified, the current display is used.
# If no filename is specified, the title of your display will be used for the .pov file name.
# include_list lets you add your own POV-ray include statements to the .pov file.
# custom_text lets you add any kind of POV-Ray statements to the .pov file.
# shadowless=True makes POV-Ray not produce any shadows.
# You can give an individual object the attribute no_shadow,
#    which if True means it casts no shadow.
# You can give an individual object the attribute no_reflection,
#    which if True means it is not reflected by anything.

#--------------------------------------------------------------------------

# Ruth Chabay created the first version in 2000-12-17
# Contributors include Markus Gritsch, Bruce Sherwood, Scott David Daniels, Guy Kloss, and John Denker
# For details of their contributions, see the version of povexport for Classic VPython

# A version for VPython 7 created by Bruce Sherwood 2017-08-08

## NOTE: when changing this module please change the following string:
POVEXPORT_VERSION = "povexport 2017"

from vpython import *
from numpy import arange
import os

# Not handled: clone, compound, extrusion, 3D text

legal = {sphere:'sphere', box:'box', cylinder:'cylinder', helix:'helix',
         curve:'curve', ring:'ring', arrow:'arrow', label:'label',
         cone:'cone', ellipsoid:'ellipsoid', pyramid:'pyramid',
         distant_light:'distant_light', local_light:'local_light'}

ihat = vec(1, 0, 0)
jhat = vec(0, 1, 0)
khat = vec(0, 0, 1)
displayscale = 1.0 # global scale factor to adjust display.range to 100

def version():
    return POVEXPORT_VERSION

def getpolar(a):
    # a is a vec
    # find rotation angles (standard polar coord)
    xy = sqrt(a.x**2 + a.y**2)
    theta = atan2(xy, a.z)
    phi = atan2(a.y, a.x)
    return [theta, phi]

def find_rotations(a):
    # find rotations
    theta, phi = getpolar(a.axis)
    # find rotation around x-axis (if a.up <> jhat)
    # "undo" theta & phi rotations so can find alpha
    aup = vec(a.up)
    aup = aup.rotate(axis=khat, angle=-phi)
    aup = aup.rotate(axis=jhat, angle=pi/2-theta)
    a_sin = dot(cross(jhat, norm(aup)), ihat)
    a_cos = dot(norm(aup), jhat)
    alpha = atan2(a_sin, a_cos)
    return (alpha, theta, phi)

'''
def process_frame(a, code):
    # add in frame rotations & translations (may be nested)
    frame_code = ''
    fr = a.frame
    while fr:
        alpha, theta, phi = find_rotations(fr)
        frx=alpha*180./pi
        fry=-90+theta*180./pi
        frz=phi*180./pi
        rrot = '    rotate <%f, %f, %f>\n'
        ttrn = '    translate <%f, %f, %f>\n'
        frame_code += rrot % (frx, fry, frz)
        frame_code += ttrn % (displayscale*fr.x, displayscale*fr.y, displayscale*fr.z)
        fr = fr.frame

    # insert frame_code at end (these rot's must be done last)
    end = code.rfind('}')
    code = code[:end] + frame_code + code[end:]
    return code
'''

def add_texture(a, code):
    # add in user-specified POV-ray texture (replaces color)
    tex = None
    if hasattr(a, 'pov_texture'):
        tex = a.pov_texture
    if tex:
        start = code.rfind('pigment {')
        end = start + code[start:].find('}') + 1
        code = code[:start] + tex + code[end:] 
    return code

def no_shadow(a):
    if hasattr(a,"no_shadow") and a.no_shadow:
        return "no_shadow"
    else:
        return ""

def no_reflection(a):
    if hasattr(a,"no_reflection") and a.no_reflection:
        return "no_reflection"
    else:
        return ""

def transparency(a):
    if hasattr(a,"opacity"):
        return 1-a.opacity
    else:
        return 0

def export_sphere(a):
    sphere_template = """
sphere {
    <%(posx)f, %(posy)f, %(posz)f>, %(radius)f
    texture {
        pigment {color rgbt <%(red)f, %(green)f, %(blue)f, %(transparency)f>}
        finish { phong %(shininess)f }
    }
    %(no_shadow)s
    %(no_reflection)s
}
"""
    object_code = sphere_template % { 'posx':displayscale*a.pos.x, 'posy':displayscale*a.pos.y, 'posz':displayscale*a.pos.z,
                                      'radius':displayscale*a.radius, 'shininess':0.6, 
                                      'red':a.red, 'green':a.green, 'blue':a.blue, 'transparency':transparency(a),
                                      'no_shadow':no_shadow(a), 'no_reflection':no_reflection(a)}
    object_code = add_texture(a, object_code)
    return object_code

def export_ellipsoid(a):
    ellipsoid_template = """
sphere {
    <0, 0, 0>, %(radius)f
    texture {
        pigment {color rgbt <%(red)f, %(green)f, %(blue)f, %(transparency)f>}
        finish { phong %(shininess)f }
    }
    scale <%(sizex)f, %(sizey)f, %(sizez)f>
    rotate <%(rotx)f, %(roty)f, %(rotz)f>
    translate <%(posx)f, %(posy)f, %(posz)f>
    %(no_shadow)s
    %(no_reflection)s
}
"""
    alpha, theta, phi = find_rotations(a)
    object_code = ellipsoid_template % { 'posx':displayscale*a.pos.x, 'posy':displayscale*a.pos.y, 'posz':displayscale*a.pos.z,
                    'radius':displayscale*a.size.x/2, 'shininess':0.6,
                    'sizex':1, 'sizey':a.size.y/a.size.x, 'sizez':a.size.z/a.size.x,
                    'rotx':alpha*180/pi, 'roty':-90+theta*180/pi, 'rotz':phi*180/pi,
                    'red':a.red, 'green':a.green, 'blue':a.blue, 'transparency':transparency(a),
                    'no_shadow':no_shadow(a), 'no_reflection':no_reflection(a) }
    object_code = add_texture(a, object_code)
    return object_code

def export_box(a):
    # create box at origin along x-axis
    # then rotate around x,y,z axes
    # then translate to final location
    box_template = """
box {
    <%(posx)f, %(posy)f, %(posz)f>, <%(pos2x)f, %(pos2y)f, %(pos2z)f>
    texture {
        pigment {color rgbt <%(red)f, %(green)f, %(blue)f, %(transparency)f>}
        finish { phong %(shininess)f }
    }
    rotate <%(rotx)f, %(roty)f, %(rotz)f>
    translate <%(transx)f, %(transy)f, %(transz)f>
    %(no_shadow)s
    %(no_reflection)s
}
"""
    alpha, theta, phi = find_rotations(a)
    # pos of box is at center
    # generate two opposite corners for POV-ray
    pos1 = displayscale*(-a.size/2)
    pos2 = displayscale*( a.size/2)

    object_code = box_template % { 'posx':pos1.x, 'posy':pos1.y, 'posz':pos1.z,
                                   'pos2x':pos2.x, 'pos2y':pos2.y, 'pos2z':pos2.z,
                                   'rotx':alpha*180/pi, 'roty':-90+theta*180/pi, 'rotz':phi*180/pi,
                                   'transx':displayscale*a.pos.x, 'transy':displayscale*a.pos.y, 'transz':displayscale*a.pos.z,
                                   'red':a.red, 'green':a.green, 'blue':a.blue, 'transparency':transparency(a),
                                   'shininess':0.6,
                                   'no_shadow':no_shadow(a), 'no_reflection':no_reflection(a) }
    object_code = add_texture(a, object_code)
    return object_code

def export_cylinder(a):
    cylinder_template = """
cylinder {
    <%(posx)f, %(posy)f, %(posz)f>,<%(pos2x)f, %(pos2y)f, %(pos2z)f>, %(radius)f
    texture {
        pigment {color rgbt <%(red)f, %(green)f, %(blue)f, %(transparency)f>}
        finish { phong %(shininess)f }
    }
    %(no_shadow)s
    %(no_reflection)s
}
"""
    endpt1=displayscale*a.pos
    endpt2=displayscale*(a.pos+a.axis)
    object_code = cylinder_template % { 'posx':endpt1.x, 'posy':endpt1.y, 'posz':endpt1.z,
                                        'pos2x':endpt2.x, 'pos2y':endpt2.y, 'pos2z':endpt2.z,
                                        'red':a.red, 'green':a.green, 'blue':a.blue, 'transparency':transparency(a),
                                        'radius':displayscale*a.radius, 'shininess':0.6,
                                        'no_shadow':no_shadow(a), 'no_reflection':no_reflection(a) }
    object_code = add_texture(a, object_code)
    return object_code

def export_helix(a):
    thickness = a.thickness
    pts = []
    N = 40 # number of curve segments in one coil
    L = a.length
    R = a.radius
    dx = L/(N*a.coils)
    for x in arange(0,L+dx/2,dx):
        pts.append(vec(x, R*sin(2*pi*(x/(N*dx))), R*cos(2*pi*(x/(N*dx)))))
    # Create a curve whose size is LxRxR:
    c = curve(pos=pts, color=a.color, radius=thickness/2, visible=False)
    c.origin = a.pos
    c.axis = a.axis
    c.up = a.up
    return export_curve(c)

def export_curve(a):
    object_code = ''
    ccyl = cylinder(visible=False) # create cylinder and sphere that can be deleted
    csph = sphere(visible=False)
    curve_no_shadow = no_shadow(a)
    curve_no_reflection = no_reflection(a)
    rotaxis = vec(1,0,0).cross(a.axis)
    rotangle = diff_angle(vec(1,0,0),a.axis)
    if a.npoints > 1:
        ii = 0
        while ii < a.npoints-1:
            endpt1 = a.point(ii)
            endpt2 = a.point(ii+1)
            if endpt1['radius'] == 0:
                rr = a.radius
            else:
                rr = endpt1['radius']
            curve_color = endpt1['color']
            if ii == 0:
                csph = sphere(pos=a.origin+endpt1['pos'], radius=rr, color=curve_color,
                          no_shadow=curve_no_shadow,
                          no_reflection=curve_no_reflection, visible=False)
                object_code += export_sphere(csph)
            if endpt2 == endpt1:
                ii += 1
                continue
            p1 = vec(endpt1['pos']) # make copies of these position vectors
            p2 = vec(endpt2['pos'])
            if rotangle > 0.001:
                if abs(rotangle-pi) < 0.001:
                    p1 = - p1
                    p2 = - p2
                else:
                    p1 = p1.rotate(angle=rotangle, axis=rotaxis)
                    p2 = p2.rotate(angle=rotangle, axis=rotaxis)
            ccyl = cylinder(pos=a.origin+p1, axis=(p2-p1),
                            radius=rr, color=curve_color,
                            no_shadow=curve_no_shadow,
                            no_reflection=curve_no_reflection, visible=False)
            csph = sphere(pos=a.origin+p2, radius=rr, color=curve_color,
                          no_shadow=curve_no_shadow,
                          no_reflection=curve_no_reflection, visible=False)
            if hasattr(a, 'pov_texture'):
                ccyl.pov_texture = a.pov_texture
                csph.pov_texture = a.pov_texture
            object_code += export_cylinder(ccyl) + export_sphere(csph)
            ii += 1
        if hasattr(a, 'pov_texture'):
            csph.pov_texture = a.pov_texture
    return object_code

def export_ring(a):
    torus_template = """
torus {
    %(radius)f, %(minorradius)f
    texture {
        pigment {color rgbt <%(red)f, %(green)f, %(blue)f, %(transparency)f>}
        finish { phong %(shininess)f }
    }
    rotate <0.0, 0.0, -90.0> // align with x-axis
    rotate <%(rotx)f, %(roty)f, %(rotz)f>
    translate <%(transx)f, %(transy)f, %(transz)f>
    %(no_shadow)s
    %(no_reflection)s
}
"""
    ang = getpolar(a.axis)
    theta = ang[0]
    phi = ang[1]
    object_code = torus_template % { 'radius':displayscale*a.radius, 'minorradius':displayscale*a.thickness,
                                     'transx':displayscale*a.pos.x, 'transy':displayscale*a.pos.y, 'transz':displayscale*a.pos.z,
                                     'rotx':0, 'roty':-90+theta*180/pi, 'rotz':phi*180/pi, 'shininess':0.6,
                                     'red':a.red, 'green':a.green, 'blue':a.blue, 'transparency':transparency(a),
                                     'no_shadow':no_shadow(a), 'no_reflection':no_reflection(a) }
    object_code = add_texture(a, object_code)
    return object_code

def export_pyramid(a):
    pyramid_template = """
object {Pyramid
    texture {
        pigment {color rgbt <%(red)f, %(green)f, %(blue)f, %(transparency)f>}
        finish { phong %(shininess)f }
    }
    scale <%(scalex)f, %(scaley)f, %(scalez)f>
    rotate <%(rotx)f, %(roty)f, %(rotz)f>
    translate <%(transx)f, %(transy)f, %(transz)f>
    %(no_shadow)s
    %(no_reflection)s
}
"""
    alpha, theta, phi = find_rotations(a)
    object_code = pyramid_template % { 'scalex':displayscale*a.size.x,
                                       'scaley':displayscale*a.size.y,
                                       'scalez':displayscale*a.size.z,
                              'rotx':0, 'roty':-90+theta*180/pi, 'rotz':phi*180/pi, 'shininess':0.6,
                              'red':a.red, 'green':a.green, 'blue':a.blue, 'transparency':transparency(a),
                              'transx':displayscale*a.pos.x, 'transy':displayscale*a.pos.y, 'transz':displayscale*a.pos.z,
                              'no_shadow':no_shadow(a), 'no_reflection':no_reflection(a) }
    object_code = add_texture(a, object_code)
    return object_code

def export_arrow(a):
    al = a.length
    if al == 0:       ## omit zero-length arrows
        return
    sw = a.shaftwidth
    if sw == 0:
        sw = 0.1*al
    hw = a.headwidth
    if hw == 0:
        hw = 2*sw
    hl = a.headlength
    if hl == 0:
        hl = 3*sw
    if a.shaftwidth != 0:
        if hl > .5*al:
            hl = .5*al
    else:
        if sw < .02*al:
            swtemp = .02*al
            hw *= swtemp/sw
            hl *= swtemp/sw
            sw = swtemp
        if hl > .5*al:
            hltemp = .5*al
            hw *= hltemp/hl
            sw *= hltemp/hl
            hl = hltemp
    sl = al-hl # length of shaft
    arrow_no_shadow = no_shadow(a)
    arrow_no_reflection = no_reflection(a)

    # head is a pyramid; need to create a dummy pyramid
    apyramid = pyramid(pos=a.pos+a.axis.norm()*sl, up=a.up,
               size=vec(hl,hw,hw), color=a.color, no_shadow=arrow_no_shadow,
               shininess=a.shininess,
               no_reflection=arrow_no_reflection, opacity=a.opacity, visible=False)
    apyramid.axis = hl*a.axis.norm() 
    m1 = export_pyramid(apyramid)
    m1 = add_texture(a, m1)

    # shaft is a box; need to create a dummy box
    abox = box(pos=(a.pos+a.axis*(sl/al)/2), axis=(a.axis*(sl/al)),
               up=a.up, width=sw, height=sw,
               color=a.color, opacity=a.opacity, shininess=a.shininess,
               no_shadow=arrow_no_shadow, no_reflection=arrow_no_reflection, visible=False)
    m2 = export_box(abox)
    m2 = add_texture(a, m2)
    # concatenate pyramid & box
    object_code = m1 + m2
    return object_code

def export_cone(a):
    cone_template = """
cone {
    <%(posx)f, %(posy)f, %(posz)f>, %(radius)f
    <%(pos2x)f, %(pos2y)f, %(pos2z)f>, %(minorradius)f
    texture {
        pigment {color rgbt <%(red)f, %(green)f, %(blue)f, %(transparency)f>}
        finish { phong %(shininess)f }
    }
    %(no_shadow)s
    %(no_reflection)s
}
"""
    pos2 = displayscale*(a.pos+a.axis)
    object_code = cone_template % { 'radius':displayscale*a.radius, 'minorradius':0,
                                    'posx':displayscale*a.pos.x, 'posy':displayscale*a.pos.y, 'posz':displayscale*a.pos.z,
                                    'pos2x':pos2.x, 'pos2y':pos2.y, 'pos2z':pos2.z, 'shininess':0.6,
                                    'red':a.red, 'green':a.green, 'blue':a.blue, 'transparency':transparency(a),
                                    'no_shadow':no_shadow(a), 'no_reflection':no_reflection(a) }
    object_code = add_texture(a, object_code)
    return object_code

def export_label(a):
    label_template = """
text {
    ttf "cyrvetic.ttf" "%(text)s" 0.1, 0
    pigment {color rgbt <%(red)f, %(green)f, %(blue)f, %(transparency)f>}
    translate <%(transx)f, %(transy)f, %(transz)f>
    %(no_shadow)s
    %(no_reflection)s
}
"""
    object_code = label_template % {'transx': displayscale * a.pos.x,
                                    'transy': displayscale * a.pos.y,
                                    'transz': displayscale * a.pos.z,
                                    'red': a.color.x, 'green': a.color.y, 'blue': a.color.z, 'transparency': transparency(a),
                                    'text': a.text,
                                    'no_shadow': no_shadow(a), 'no_reflection': no_reflection(a)}
    object_code = add_texture(a, object_code)
    return object_code

def export(canvas=None, filename=None, include_list=None, custom_text='', shadowless=0):
    canv = canvas

    global displayscale
    if canv == None:         # no display specified so find active display
        b = box(visible=0)
        canv = b.canvas

    if filename == None:
        if len(canv.title) == 0: filename = 'povray.pov'
        else: filename = canv.title + '.pov'

    if include_list == None:
        include_text = ''
        # Maybe should always include the following definitions?
        #include_text = '#include "colors.inc"\n#include "stones.inc"\n#include "woods.inc"\n#include "metals.inc"\n'
    else:
        include_text = '\n'
        for x in include_list:
            include_text = include_text + '#include "'+ x + '"\n'

    initial_comment = """// POV-ray code generated by povexport.py
"""

    pyramid_def = """
// Four-sided pyramid from shapes2.inc, slightly modified.
// The 1x1 base of the pyramid is at the origin, in the yz plane.
// The tip of the pyramid is at <1,0,0>.
#declare Pyramid = union {
    triangle { <0, -0.5, -0.5>, <0, +0.5, -0.5>, <1, 0, 0> }
    triangle { <0, +0.5, -0.5>, <0, +0.5, +0.5>, <1, 0, 0> }
    triangle { <0, -0.5, +0.5>, <0, +0.5, +0.5>, <1, 0, 0> }
    triangle { <0, -0.5, +0.5>, <0, -0.5, -0.5>, <1, 0, 0> }
    triangle { <0, -0.5, -0.5>, <0, -0.5, +0.5>, <0, 0.5, 0.5> }
    triangle { <0, -0.5, -0.5>, <0, +0.5, -0.5>, <0, 0.5, 0.5> }
}
"""

    ambient_template = """
global_settings { ambient_light rgb <%(red)f, %(green)f, %(blue)f> }
"""

    scalar_ambient_template = """
global_settings { ambient_light rgb <%(amb)f, %(amb)f, %(amb)f> }
"""

    background_template = """
background { color rgb <%(red)f, %(green)f, %(blue)f> }
"""

    light_template = """
light_source { <%(posx)f, %(posy)f, %(posz)f>
    color rgb <%(red)f, %(green)f, %(blue)f>
}
"""

    camera_template = """
camera {
    right <-image_width/image_height, 0, 0>      // vpython uses right-handed coord. system
    location <%(posx)f, %(posy)f, %(posz)f>
    up <%(upx)f, %(upy)f, %(upz)f>
    look_at <%(pos2x)f, %(pos2y)f, %(pos2z)f>
    angle %(fov)f
}
"""

    # begin povray setup
    file = open(filename, 'w')
    print(os.path.realpath(file.name))

    file.write( initial_comment + include_text + custom_text + pyramid_def )
    file.write( ambient_template % { 'red':canv.ambient.x*10 ,
                                         'green':canv.ambient.y*10,
                                         'blue':canv.ambient.z*10 })
    file.write( background_template % { 'red':canv.background.x,
                                        'green':canv.background.y,
                                        'blue':canv.background.z } )

    displayscale = 10/canv.range # deal with very small range values (e.g. atomic sizes)

    for light in canv.lights: # reproduce vpython lighting (not ideal, but good approximation)
        if type(light) is distant_light:
            pos = norm(light.direction) * 1000 # far away to simulate parallel light
        elif type(light) is local_light:
            pos = displayscale*light.pos
        lcolor = light.color
        light_code = light_template % { 'posx':pos.x, 'posy':pos.y, 'posz':pos.z,
                                        'red':lcolor.x, 'green':lcolor.y, 'blue':lcolor.z }
        if shadowless:
            end = light_code.rfind('}')
            light_code = light_code[:end] + '    shadowless\n' + light_code[end:]
        file.write( light_code )

    cpos = 1.5*displayscale*canv.camera.pos # 1.5 is a not understood fudge factor
    ctr = displayscale*canv.center
    cup = canv.up
    file.write( camera_template % { 'posx':cpos.x, 'posy':cpos.y, 'posz':cpos.z,
                                    'upx':cup.x, 'upy':cup.y, 'upz':cup.z,
                                    'pos2x':ctr.x, 'pos2y':ctr.y, 'pos2z':ctr.z,
                                    'fov':canv.fov*180/pi } )

    for obj in canv.objects:
        key = obj.__class__
        if key in legal:
            obj_name = legal[key]
            if obj_name == 'distant_light' or obj_name == 'local_light': continue
            function_name = 'export_' + obj_name
            function = globals().get(function_name)
            object_code = function(obj)
            if object_code is None:
                continue
            file.write( object_code )
        else:
            print('WARNING: export function for ' + str(obj.__class__) + ' not implemented')

    file.close()
    return 'The export() function no longer returns the display as an\n' \
           'endless POV-Ray string, but saves it to a file instead.'
# end defining export()


if __name__ == '__main__':
    print(__doc__)
