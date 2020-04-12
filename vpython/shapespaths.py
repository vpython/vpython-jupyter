from math import sqrt, sin, cos, tan, asin, acos, atan, floor, pi

from ._vector_import_helper import vec, vector, mag, norm

# List of names that are imported from this module with import *
__all__ = ['RackOutline', 'ToothOutline', 'addpos', 'convert', 'path_object',
           'paths', 'rotatecp', 'roundc', 'scalecp', 'shape_object', 'shapes']

 # The path and shape objects were designed and implemented by Kadir Haldenbilen
 # for Classic VPython 5. Modified by Bruce Sherwood for GlowScript/Jupyter VPython,
 # eliminating dependency on Polygon library.

 # GlowScript API:
 # shape = [2Ds], hole = [2Ds] or shape = [ [shape 2Ds], [hole 2Ds] ]
 # Another option for hole is [ [hole1], [hole2], ..... ]
 # If hole represents multiple holes, len([hole[0]]) > 1

   ##################################
   ## ----------- shapes ------------
   ##################################

npdefault = 64 # default number of points for a circle. ellipse, and arc

def roundc(cps, roundness=0.1, invert=False, nseg=16):
    cp = []
    for i in range(len(cps)): cp.append(vec(cps[i][0], cps[i][1], 0)) # convert [x,y] => vec(x,y,0), so can use vector functions

    # If points are ordered counterclockwise, vord will be > 0
    vord = 0
    cp.pop() # remove the final point, which is equal to the initial point
    lcp = len(cp)
    for i in range(lcp):
        i1 = (i + 1) % lcp
        i2 = (i + 2) % lcp
        v1 = cp[i1] - cp[i]
        v2 = cp[i2] - cp[i1]
        dv = v1.cross(v2).z
        vord += dv

    if vord < 0: cp.reverse() # force points to be in counterclockwise order

    # Determine shortest side
    L = 1e200
    for i in range(lcp):
        p1 = cp[i]
        p2 = cp[(i + 1) % lcp]
        lm = mag(p2 - p1)
        if (lm < L):
            L = lm

    r = L * roundness # radius of rounded curve connecting adjacent sides

    ncp = [[0,0]] # starting point will be modified later
    for i in range(lcp):
        v1 = cp[(i+1) % lcp] - cp[i % lcp]   # first side
        v2 = cp[(i+2) % lcp] - cp[(i+1) % lcp] # next side
        theta = v1.diff_angle(v2)   # angle of change of direction from first side to next side
        d = r*tan(theta/2)         # how much to shorten the end of a side and the start of the next
        p1 = cp[i] + v1 - d*norm(v1)   # end of first side, start of bend
        p2 = cp[(i+1) % lcp] + d*norm(v2) # start of next side, end of bend
        ncp.append([p1.x, p1.y])
        N = norm(v1).cross(norm(v2))
        center = p1 + r*norm(N.cross(v1)) # center of circular arc
        v = p1 - center
        dtheta = theta/(nseg+1)
        if N.z < 0: dtheta = -dtheta
        if invert:
            c = 0.5*(p1 + p2) # midpoint along line connecting p1 and p2
            center = c + (c-center)    # move center to other side of corner
            v = p1 - center
            dtheta = -dtheta

        for j in range(1,nseg): # don't repeat the starting point of this arc
            v1 = center + v.rotate(j*dtheta)
            ncp.append([v1.x, v1.y])

        ncp.append([p2.x, p2.y])

    v1 = cp[1] - cp[0]
    v1 = cp[0] + d*norm(v1) # start of first side, at end of preceding bend
    ncp[0] = [v1.x, v1.y]
    return ncp

def rotatecp(cp, pos=[0,0], rotate=0):
    sinr = sin(rotate)
    cosr = cos(rotate)
    xRel = pos[0]
    yRel = pos[1]
    cpr = []
    for i in range(len(cp)):
        p = cp[i]
        x = p[0]
        y = p[1]
        newx = x * cosr - y * sinr - xRel * cosr + yRel * sinr + xRel
        newy = x * sinr + y * cosr - xRel * sinr - yRel * cosr + yRel
        cpr.append([ newx, newy ])
    return cpr

def scalecp(cp, xscale=1, yscale=1):
    cpr = []
    for i in range(len(cp)):
        p = cp[i]
        cpr.append([ xscale * p[0], yscale * p[1] ])
    return cpr

def addpos(cp, pos=[0,0]):
    for i in range(len(cp)):
        p = cp[i]
        p[0] += pos[0]
        p[1] += pos[1]
    return cp

##The following script has been developed and based on the
##Blender 235 script "Blender Mechanical Gears"
##developed in 2004 by Stefano <S68> Selleri,
##released under the Blender Artistic License (BAL).
##See www.blender.org.

####################################################################
#CREATES THE BASE INVOLUTE PROFILE
####################################################################
def ToothOutline(n=30, res=1, phi=20, radius=50, addendum=0.4, dedendum=0.5, fradius=0.1, bevel=0.05):
    TOOTHGEO = {
        'PitchRadius' : radius,
        'TeethN'      : n,
        'PressureAng' : phi,
        'Addendum'    : addendum,
        'Dedendum'    : dedendum,
        'Fillet'      : fradius,
        'Bevel'       : bevel,
        'Resolution'  : res,
        }
    ####################################################################
    #Basic Math computations: Radii
    #
    R = {
        'Bottom'  : TOOTHGEO['PitchRadius'] - TOOTHGEO['Dedendum'] - TOOTHGEO['Fillet'],
        'Ded'     : TOOTHGEO['PitchRadius'] - TOOTHGEO['Dedendum'],
        'Base'    : TOOTHGEO['PitchRadius'] * cos(TOOTHGEO['PressureAng']*pi/180.0),
        'Bevel'   : TOOTHGEO['PitchRadius'] + TOOTHGEO['Addendum'] - TOOTHGEO['Bevel'],
        'Add'     : TOOTHGEO['PitchRadius'] + TOOTHGEO['Addendum']
    }

    ####################################################################
    #Basic Math computations: Angles
    #
    DiametralPitch = TOOTHGEO['TeethN']/(2*TOOTHGEO['PitchRadius'])
    ToothThickness = 1.5708/DiametralPitch
    CircularPitch  = pi / DiametralPitch

    U1 = sqrt((1-cos(TOOTHGEO['PressureAng']*pi/180.0))/
                   cos(TOOTHGEO['PressureAng']*pi/180.0))
    U2 = sqrt(R['Bevel']*R['Bevel']/(R['Ded']*R['Ded'])-1)

    ThetaA1 = atan((sin(U1)-U1*cos(U1))/(cos(U1)+U1*sin(U1)))
    ThetaA2 = atan((sin(U2)-U2*cos(U2))/(cos(U2)+U2*sin(U2)))
    ThetaA3 = ThetaA1 + ToothThickness/(TOOTHGEO['PitchRadius']*2.0)

    A = {
        'Theta0' : CircularPitch/(TOOTHGEO['PitchRadius']*2.0),
        'Theta1' : ThetaA3 + TOOTHGEO['Fillet']/R['Ded'],
        'Theta2' : ThetaA3,
        'Theta3' : ThetaA3 - ThetaA2,
        'Theta4' : ThetaA3 - ThetaA2 - TOOTHGEO['Bevel']/R['Add']
    }

    ####################################################################
    # Profiling
    #
    N = TOOTHGEO['Resolution']
    points  = []
    normals = []
    # Top half bottom of tooth
    for i in range(2*N):
        th = (A['Theta1'] - A['Theta0'])*i/(2*N-1) + A['Theta0']
        points.append ([R['Bottom']*cos(th),
                        R['Bottom']*sin(th)])
        normals.append([-cos(th),
                        -sin(th)])

    # Bottom Fillet
    xc = R['Ded']*cos(A['Theta1'])
    yc = R['Ded']*sin(A['Theta1'])
    Aw = pi/2.0 + A['Theta2'] - A['Theta1']
    for i in range(N):
        th = (Aw)*(i+1)/(N) + pi + A['Theta1']
        points.append ([xc + TOOTHGEO['Fillet']*cos(th),
                        yc + TOOTHGEO['Fillet']*sin(th)])
        normals.append([cos(th),
                        sin(th)])

    # Straight part
    for i in range(N):
        r = (R['Base']-R['Ded'])*(i+1)/(N) + R['Ded']
        points.append ([r*cos(A['Theta2']),
                        r*sin(A['Theta2'])])
        normals.append([cos(A['Theta2']-pi/2.0),
                        sin(A['Theta2']-pi/2.0)])

    # Tooth Involute
    for i in range(3*N):
        r = (R['Bevel'] - R['Base'])*(i+1)/(3*N) + R['Base']
        u = sqrt(r*r/(R['Base']*R['Base'])-1)
        xp = R['Base']*(cos(u)+u*sin(u))
        yp = - R['Base']*(sin(u)-u*cos(u))
        points.append ([xp*cos(A['Theta2'])-yp*sin(A['Theta2']),
                        +xp*sin(A['Theta2'])+yp*cos(A['Theta2'])])
        normals.append([-sin(u),
                        -cos(u)])

    # Tooth Bevel
    auxth = -u
    auxth = auxth + ThetaA3 + pi/2.0
    m     = tan(auxth)
    P0    = points[len(points)-1]
    rA    = TOOTHGEO['Bevel']/(1-cos(auxth-A['Theta4']))
    xc    = P0[0] - rA*cos(auxth)
    yc    = P0[1] - rA*sin(auxth)
    for i in range(N):
        th = (A['Theta4'] - auxth)*(i+1)/(N) + auxth
        points.append ([xc + rA*cos(th),
                        yc +rA*sin(th)])
        normals.append([-cos(th),
                        -sin(th)])

    # Tooth Top
    P0    = points[len(points)-1]
    A['Theta4'] = atan (P0[1]/P0[0])
    Ra = sqrt(P0[0]*P0[0]+P0[1]*P0[1])
    for i in range(N):
        th = (-A['Theta4'])*(i+1)/(N) + A['Theta4']
        points.append ([Ra*cos(th),
                        Ra*sin(th)])
        normals.append([-cos(th),
                        -sin(th)])

    # Mirrors this!
    N = len(points)
    for i in range(N-1):
        P = points[N-2-i]
        points.append([P[0],-P[1]])
        V = normals[N-2-i]
        normals.append([V[0],-V[1]])

    return points               # ,normals

####################################################################
#CREATES THE BASE RACK PROFILE
####################################################################
def RackOutline(n=30, res=1, phi=20, radius=5, addendum=0.4, dedendum=0.5, fradius=0.1, bevel=0.05):
    TOOTHGEO = {
        'PitchRadius' : radius,
        'TeethN'      : n,
        'PressureAng' : phi,
        'Addendum'    : addendum,
        'Dedendum'    : dedendum,
        'Fillet'      : fradius,
        'Bevel'       : bevel,
        'Resolution'  : res,
        }
    ####################################################################
    #Basic Math computations: QUotes
    #
    X = {
        'Bottom'  :  - TOOTHGEO['Dedendum'] - TOOTHGEO['Fillet'],
        'Ded'     :  - TOOTHGEO['Dedendum'],
        'Bevel'   : TOOTHGEO['Addendum'] - TOOTHGEO['Bevel'],
        'Add'     : TOOTHGEO['Addendum']
    }

    ####################################################################
    #Basic Math computations: Angles
    #
    DiametralPitch = TOOTHGEO['TeethN']/(2*TOOTHGEO['PitchRadius'])
    ToothThickness = 1.5708/DiametralPitch
    CircularPitch  = pi / DiametralPitch

    Pa = TOOTHGEO['PressureAng']*pi/180.0

    yA1 = ToothThickness/2.0
    yA2 = (-X['Ded']+TOOTHGEO['Fillet']*sin(Pa))*tan(Pa)
    yA3 = TOOTHGEO['Fillet']*cos(Pa)

    A = {
        'y0' : CircularPitch/2.0,
        'y1' : yA1+yA2+yA3,
        'y2' : yA1+yA2,
        'y3' : yA1 -(X['Add']-TOOTHGEO['Bevel'])*tan(Pa),
        'y4' : yA1 -(X['Add']-TOOTHGEO['Bevel'])*tan(Pa)
                - cos(Pa)/(1-sin(Pa))*TOOTHGEO['Bevel']
    }

    ####################################################################
    # Profiling
    #
    N = TOOTHGEO['Resolution']
    points  = []
    normals = []
    ist = 0
    if fradius: ist = 1
    # Top half bottom of tooth
    for i in range(ist, 2*N):
        y = (A['y1'] - A['y0'])*i/(2*N-1) + A['y0']
        points.append ([X['Bottom'],
                        y])
        normals.append([-1.0,
                        -0.0])

    # Bottom Fillet
    xc = X['Ded']
    yc = A['y1']
    Aw = pi/2.0 - Pa

    for i in range(N):
        th = (Aw)*(i+1)/(N) + pi
        points.append ([xc + TOOTHGEO['Fillet']*cos(th),
                        yc + TOOTHGEO['Fillet']*sin(th)])
        normals.append([cos(th),
                        sin(th)])

    # Straight part
    Xded = X['Ded'] - TOOTHGEO['Fillet']*sin(Pa)
    for i in range(4*N):
        x = (X['Bevel']-Xded)*(i+1)/(4*N) + Xded
        points.append ([x,
                        yA1-tan(Pa)*x])
        normals.append([-sin(Pa),
                        -cos(Pa)])

    # Tooth Bevel
    rA    = TOOTHGEO['Bevel']/(1-sin(Pa))
    xc    =  X['Add'] - rA
    yc    =  A['y4']
    for i in range(N):
        th = (-pi/2.0+Pa)*(i+1)/(N) + pi/2.0-Pa
        points.append ([xc + rA*cos(th),
                        yc + rA*sin(th)])
        normals.append([-cos(th),
                        -sin(th)])

    # Tooth Top
    for i in range(N):
        y = -A['y4']*(i+1)/(N) + A['y4']
        points.append ([X['Add'],
                        y])
        normals.append([-1.0,
                        0.0])

    # Mirrors this!
    N = len(points)
    for i in range(N-1):
        P = points[N-2-i]
        points.append([P[0],-P[1]])
        V = normals[N-2-i]
        normals.append([V[0],-V[1]])

    return points               # ,normals

####################################################################
## CREATES THE BASE CROWN INVOLUTE -- NOT CURRENTLY IMPLEMENTED IN GLOWSCRIPT -- GAVE ERRORS
####################################################################
# def CrownOutline(n=30, res=1, phi=20., radius=5.0, addendum=0.4, dedendum=0.5, fradius=0.1, bevel=0.05):
    # TOOTHGEO = {
        # 'PitchRadius' : radius,
        # 'TeethN'      : n,
        # 'PressureAng' : phi,
        # 'Addendum'    : addendum,
        # 'Dedendum'    : dedendum,
        # 'Fillet'      : fradius,
        # 'Bevel'       : bevel,
        # 'Resolution'  : res,
        # }
    ###################################################################
    ## Basic Math computations: Radii

    # R = {
        # 'Bottom'  : TOOTHGEO['PitchRadius'] * cos(TOOTHGEO['PressureAng']*pi/180.0) ,
        # 'Base'    : TOOTHGEO['PitchRadius'] * cos(TOOTHGEO['PressureAng']*pi/180.0) + TOOTHGEO['Fillet'],
        # 'Ded'     : TOOTHGEO['PitchRadius'] + TOOTHGEO['Dedendum']
    # }

    ###################################################################
    ## Basic Math computations: Angles

    # DiametralPitch = TOOTHGEO['TeethN']/(2*TOOTHGEO['PitchRadius'])
    # ToothThickness = 1.5708/DiametralPitch
    # CircularPitch  = pi / DiametralPitch

    # U1 = sqrt((1-cos(TOOTHGEO['PressureAng']*pi/180.0))/
                   # cos(TOOTHGEO['PressureAng']*pi/180.0))
    # U2 = sqrt(R['Ded']*R['Ded']/(R['Base']*R['Base'])-1)

    # ThetaA1 = atan((sin(U1)-U1*cos(U1))/(cos(U1)+U1*sin(U1)))
    # ThetaA2 = atan((sin(U2)-U2*cos(U2))/(cos(U2)+U2*sin(U2)))
    # ThetaA3 = ThetaA1 + ToothThickness/(TOOTHGEO['PitchRadius']*2.0)

    # A = {
        # 'Theta0' : CircularPitch/(TOOTHGEO['PitchRadius']*2.0),
        # 'Theta1' : (ThetaA3 + TOOTHGEO['Fillet']/R['Base']),
        # 'Theta2' : ThetaA3,
        # 'Theta3' : ThetaA3 - ThetaA2,
        # 'Theta4' : ThetaA3 - ThetaA2 - TOOTHGEO['Bevel']/R['Ded']
    # }

    # M = A['Theta0']
    # A['Theta0'] = 0
    # A['Theta1'] = A['Theta1']-M
    # A['Theta2'] = A['Theta2']-M
    # A['Theta3'] = A['Theta3']-M
    # A['Theta4'] = A['Theta4']-M

    ###################################################################
    ## Profiling

    # N = TOOTHGEO['Resolution']
    # apoints  = []
    # anormals = []

    ## Top half top of tooth
    # for i in range(2*N):
        # th = (A['Theta1'] - A['Theta0'])*i/(2*N-1) + A['Theta0']
        # apoints.append ([R['Bottom']*cos(th),
                        # R['Bottom']*sin(th)])
        # anormals.append([cos(th),
                        # sin(th)])

    ## Bottom Bevel
    # xc = R['Base']*cos(A['Theta1'])
    # yc = R['Base']*sin(A['Theta1'])
    # Aw = pi/2.0 + A['Theta2'] - A['Theta1']
    # for i in range(N):
        # th = (Aw)*(i+1)/(N) + pi + A['Theta1']
        # apoints.append ([xc + TOOTHGEO['Fillet']*cos(th),
                        # yc + TOOTHGEO['Fillet']*sin(th)])
        # anormals.append([-cos(th),
                        # -sin(th)])

    ## Tooth Involute
    # for i in range(4*N):
        # r = (R['Ded'] - R['Base'])*(i+1)/(4*N) + R['Base']
        # u = sqrt(r*r/(R['Base']*R['Base'])-1)
        # xp = R['Base']*(cos(u)+u*sin(u))
        # yp = - R['Base']*(sin(u)-u*cos(u))
        # apoints.append ([xp*cos(A['Theta2'])-yp*sin(A['Theta2']),
                        # +xp*sin(A['Theta2'])+yp*cos(A['Theta2'])])
        # anormals.append([sin(u),
                        # cos(u)])

    ## Tooth Bevel
    # auxth = -u
    # auxth = auxth + ThetaA3 + pi/2.0
    # m     = tan(auxth)
    # P0    = apoints[len(apoints)-1]
    # rA    = TOOTHGEO['Bevel']/(1-cos(auxth-A['Theta4']))
    # xc    = P0[0] - rA*cos(auxth)
    # yc    = P0[1] - rA*sin(auxth)
    # for i in range(N):
        # th = (A['Theta4'] - auxth)*(i+1)/(N) + auxth
        # apoints.append ([xc + rA*cos(th),
                        # yc +rA*sin(th)])
        # anormals.append([cos(th),
                        # sin(th)])

    ## Tooth Top
    # P0    = apoints[len(apoints)-1]
    # A['Theta4'] = atan (P0[1]/P0[0])
    # Ra = sqrt(P0[0]*P0[0]+P0[1]*P0[1])
    # for i in range(N):
        # th = (-M - A['Theta4'])*(i+1)/(N) + A['Theta4']
        # apoints.append ([Ra*cos(th),
                        # Ra*sin(th)])
        # anormals.append([cos(th),
                        # sin(th)])
    # points = []
    # normals = []
    # N = len(apoints)
    # for i in range(N):
        # points.append(apoints[N-1-i])
        # normals.append(anormals[N-1-i])

    ## Mirrors this!
    # N = len(points)
    # for i in range(N-1):
        # P = points[N-2-i]
        # points.append([P[0],-P[1]])
        # V = normals[N-2-i]
        # normals.append([V[0],-V[1]])

    # return points           #,normals       process nromals later

class shape_object(object):

    def rframe(self, pos=[0,0], width=1, height=None, rotate=0, thickness=None,
                    roundness=0, invert=False, scale=1, xscale=1, yscale=1):
        if height is None:
            height = width
        if thickness is None: thickness = min(height, width) * .2
        else: thickness = min(height, width) * thickness * 2
        outer = self.rectangle(pos=pos, width=width, height=height)
        inner = self.rectangle(pos=pos, width=width - thickness, height=height - thickness)
        if rotate != 0:
            outer = rotatecp(outer, pos=pos, rotate=rotate)
            inner = rotatecp(inner, pos=pos, rotate=rotate)
        if xscale != 1 or yscale != 1:
            outer = scalecp(outer, xscale=xscale, yscale=yscale)
            inner = scalecp(inner, xscale=xscale, yscale=yscale)
        if roundness > 0:
            outer = roundc(outer, roundness=roundness, invert=invert)
            inner = roundc(inner, roundness=roundness, invert=invert)
        return [ outer, inner ]

    def rectangle(self, pos=[0,0], width=1, height=None, rotate=0, thickness=0,
                    roundness=0, invert=False, scale=1, xscale=1, yscale=1):
        if height is None:
            height = width
        if thickness == 0:
            cp = []
            w2 = width / 2
            h2 = height / 2
            cp = [ [ w2, -h2 ], [ w2, h2 ], [ -w2, h2 ], [ -w2, -h2 ], [ w2, -h2 ] ]
            cp = addpos(cp, pos=pos)
            if rotate != 0: cp = rotatecp(cp, pos, rotate)
            if scale != 1: xscale = yscale = scale
            if xscale != 1 or yscale != 1: cp = scalecp(cp, xscale, yscale)
            if roundness > 0: cp = roundc(cp, roundness=roundness, invert=invert)
        else:
            cp = self.rframe(pos=pos, width=width, height=height, rotate=rotate, thickness=thickness,
                    roundness=roundness, invert=invert, scale=scale, xscale=xscale, yscale=yscale)
        return cp

    def cross(self, pos=[0,0], width=1, rotate=0, thickness=0.2,
                    roundness=0, invert=False, scale=1, xscale=1, yscale=1):
        wtp = (width + thickness) / 2
        w2 = width / 2
        t2 = thickness / 2
        cp = [ [ w2, -t2 ], [ w2, t2 ], [ t2, t2 ], [ t2, w2 ], [ -t2, w2 ], [ -t2, t2 ], [ -w2, t2 ],
               [ -w2, -t2 ], [ -t2, -t2 ], [ -t2, -w2 ], [ t2, -w2 ], [ t2, -t2 ], [ w2, -t2 ] ]
        cp = addpos(cp, pos=pos)
        if rotate != 0: cp = rotatecp(cp, pos=pos, rotate=rotate)
        if scale != 1: xscale = yscale = scale
        if xscale != 1 or yscale != 1: cp = scalecp(cp, xscale=xscale, yscale=yscale)
        if roundness > 0: cp = roundc(cp, roundness=roundness, invert=invert)
        return cp

    def trframe(self, pos=[0,0], width=2, height=1, top=None, rotate=0, thickness=None,
                    roundness=0, invert=False, scale=1, xscale=1, yscale=1):
        if top is None: top = width / 2
        if thickness is None:
            thickness = min(height, top) * .2
        else:
            thickness = min(height, top) * thickness * 2

        outer = self.trapezoid(pos=pos, width=width, height=height, top=top)
        angle = atan((width - top) / 2 / height)
        db = thickness / cos(angle)
        inner = self.trapezoid(pos=pos, width=width - db - thickness * tan(angle),
                                height=height - thickness, top=top - (db - thickness * tan(angle)))
        outer = addpos(outer, pos=pos)
        inner = addpos(inner, pos=pos)
        if rotate != 0:
            outer = rotatecp(outer, pos=pos, rotate=rotate)
            inner = rotatecp(inner, pos=pos, rotate=rotate)

        if scale != 1: xscale = yscale = scale
        if xscale != 1 or yscale != 1:
            outer = scalecp(outer, xscale=xscale, yscale=yscale)
            inner = scalecp(inner, xscale=xscale, yscale=yscale)

        if roundness > 0:
            outer = roundc(outer, roundness=roundness, invert=invert)
            inner = roundc(inner, roundness=roundness, invert=invert)

        return [ outer, inner ]

    def trapezoid(self, pos=[0,0], width=2, height=1, top=None, rotate=0, thickness=0,
                    roundness=0, invert=False, scale=1, xscale=1, yscale=1):
        w2 = width / 2
        h2 = height / 2
        if top is None: top = w2
        t2 = top / 2
        if thickness == 0:
            cp = [ [ w2, -h2 ], [ t2, h2 ], [ -t2, h2 ], [ -w2, -h2 ], [ w2, -h2 ] ]
            cp = addpos(cp, pos=pos)
            if rotate != 0: cp = rotatecp(cp, pos=pos, rotate=rotate)
            if scale != 1: xscale = yscale = scale
            if xscale != 1 or yscale != 1: cp = scalecp(cp, xscale=xscale, yscale=yscale)
            if roundness > 0: cp = roundc(cp, roundness=roundness, invert=invert)
        else:
            cp = self.trframe(pos=pos, width=width, height=height, top=top, rotate=rotate, thickness=thickness,
                    roundness=roundness, invert=invert, scale=scale, xscale=xscale, yscale=yscale)
        return cp

    def circframe(self, pos=[0,0], radius=0.5, np=npdefault, rotate=0, iradius=None,
                    angle1=0, angle2=2*pi, scale=1, xscale=1, yscale=1):
        thickness = 0
        if iradius is None: iradius = radius * .8
        outer = self.circle(pos=pos, radius=radius, np=np, rotate=rotate, iradius=iradius,
                       angle1=angle1, angle2=angle2, scale=scale, xscale=xscale, yscale=yscale)
        if angle1 == 0 and angle2 == 2*pi:
            radius = iradius
            inner = self.circle(pos=pos, radius=radius, np=np, rotate=rotate, thickness=thickness,
                       angle1=angle1, angle2=angle2, scale=scale, xscale=xscale, yscale=yscale)
        else:
            t = radius - iradius
            angle = (angle1 + angle2)/2 # pos and center lie on this line
            offset = t/sin((angle2-angle1)/2)
            corner = [pos[0]+offset*cos(angle), pos[1]+offset*sin(angle)]
            dangle = asin(t/iradius)
            angle1 = angle1 + dangle
            angle2 = angle2 - dangle
            radius = iradius
            inner = self.circle(pos=pos, radius=radius, np=np, rotate=rotate, thickness=thickness, corner=corner,
                       angle1=angle1, angle2=angle2, scale=scale, xscale=xscale, yscale=yscale)
        if rotate != 0:
            outer = rotatecp(outer, pos=pos, rotate=rotate)
            inner = rotatecp(inner, pos=pos, rotate=rotate)
        if scale != 1: xscale = yscale = scale
        if xscale != 1 or yscale != 1:
            outer = scalecp(outer, xscale=xscale, yscale=yscale)
            inner = scale(inner, xscale=xscale, yscale=yscale)
        return [ outer, inner ]

    def circle(self, pos=[0,0], radius=0.5, np=npdefault, rotate=0, thickness=0, corner=None, iradius=None,
                    angle1=0, angle2=2*pi, scale=1, xscale=1, yscale=1):
        if corner is None: corner = pos # where the two straight edges meet
        cp = []
        if thickness > 0:
            iradius = radius - radius*thickness
            cp = self.circframe(pos=pos, radius=radius, np=np, rotate=rotate, iradius=iradius,
                    angle1=angle1, angle2=angle2, scale=scale, xscale=xscale, yscale=yscale)
        else:
            if angle1 != 0 or angle2 != 2 *pi:
                cp.append([ corner[0], corner[1] ])
            seg = 2 * pi / np
            nseg = int(floor(abs((angle2 - angle1) / seg + .5)))
            seg = (angle2 - angle1) / nseg
            if angle1 != 0 or angle2 != 2 * pi: nseg += 1
            c = radius * cos(angle1)
            s = radius * sin(angle1)
            dc = cos(seg)
            ds = sin(seg)
            x0 = pos[0]
            y0 = pos[1]
            cp.append([ x0 + c, y0 + s ])
            for i in range(nseg-1):
                c2 = c * dc - s * ds
                s2 = s * dc + c * ds
                cp.append([ x0 + c2, y0 + s2 ])
                c = c2
                s = s2
            cp.append(cp[0])
            if rotate != 0: cp = rotatecp(cp, pos=pos, rotate=rotate)
            if scale != 1: xscale = yscale = scale
            if xscale != 1 or yscale != 1: cp = scalecp(cp, xscale=xscale, yscale=yscale)
        return cp

    def arc(self, pos=[0,0], radius=0.5, np=npdefault, rotate=0, thickness=None,
                    angle1=0, angle2=2*pi, scale=1, xscale=1, yscale=1, path=False):
        if thickness is None: thickness = .01 * radius
        cp = []  # outer arc
        cpi = [] # inner arc
        seg = 2 * pi / np
        nseg = int(floor(abs(angle2 - angle1) / seg) + 1)
        seg = (angle2 - angle1) / nseg
        for i in range(nseg+1):
            x = cos(angle1 + i * seg)
            y = sin(angle1 + i * seg)
            cp.append([radius * x + pos[0], radius * y + pos[1]])
            if not path: cpi.append([(radius - thickness) * x + pos[0],
                                      (radius - thickness) * y + pos[1]])
        if not path:
            cpi.reverse()
            for i in range(len(cpi)): cp.append(cpi[i])
            cp.append(cp[0])
        if rotate != 0: cp = rotatecp(cp, pos, rotate)
        if scale != 1: xscale = yscale = scale
        if xscale != 1 or yscale != 1: scalecp(cp, xscale, yscale)
        return cp

    def ellipse(self, pos=[0,0], width=1, height=None, np=npdefault, rotate=0, thickness=0,
                    angle1=0, angle2=2*pi, scale=1, xscale=1, yscale=1):
        if height is None: height = .5 * width
        yscale *= height/width
        radius = width
        return self.circle(pos=pos, radius=radius, np=np, rotate=rotate,
                    angle1=angle1, angle2=angle2, scale=scale, xscale=xscale, yscale=yscale)

    # line is not called by paths.line()
    def line(self, pos=[0,0], width=1, height=None, np=2, rotate=0, thickness=None,
                    start=[0,0], end=[0,1], scale=1, xscale=1, yscale=1):
        v = vec(end[0] - start[0], end[1] - start[1], 0)
        if thickness is None: thickness = .01 * mag(v)
        dv = thickness * norm(vec(0, 0, 1).cross(v))
        dx = dv.x
        dy = dv.y
        cp = []   # outer line
        cpi = []  # inner line
        vstart = vec(start[0], start[1], 0)
        v = vec(end[0]-start[0], end[1]-start[1], 0)
        vline = v/(floor(np-1))
        for i in range(np):
            v = i*vline
            x = start[0] + v.x
            y = start[1] + v.y
            cp.append([x + pos[0], y + pos[1]])
            cpi.append([x + pos[0] + dx, y + pos[1] + dy])

        cpi.reverse()
        for i in range(len(cpi)): cp.append(cpi[i])
        cp.append(cp[0])
        if rotate != 0: cp = rotatecp(cp, pos, rotate)
        if scale != 1: xscale = yscale = scale
        if xscale != 1 or yscale != 1: scalecp(cp, xscale, yscale)
        return cp

    def nframe(self, pos=[0,0], length=1, rotate=0, thickness=None, np=3,
                    roundness=0, invert=False, scale=1, xscale=1, yscale=1):
        if thickness is None:
            thickness = length * .1
        else:
            thickness = length * thickness

        outer = self.ngon(pos=pos, np=np, length=length)
        angle = pi * (.5 - 1 / np)
        length2 = length - 2 * thickness / tan(angle)
        inner = self.ngon(pos=pos, np=np, length=length2)
        if rotate != 0:
            outer = rotatecp(outer, pos, rotate)
            inner = rotatecp(inner, pos, rotate)

        if scale != 1: xscale = yscale = scale
        if xscale != 1 or yscale != 1:
            outer = scale(outer, xscale, yscale)
            inner = scale(inner, xscale, yscale)

        if roundness > 0:
            outer = roundc(outer, roundness=roundness, invert=invert)
            inner = roundc(inner, roundness=roundness, invert=invert)

        return [ outer, inner ]

    def ngon(self, pos=[0,0], length=1, rotate=0, thickness=0, np=None,
                    roundness=0, invert=False, scale=1, xscale=1, yscale=1):
        cp = []
        if np is None:  raise AttributeError("must specify np for ngon shape")
        if np < 3: raise AttributeError("number of sides can not be less than 3")
        angle = 2 * pi / np
        radius = length / 2 / sin(angle / 2)
        if thickness == 0:
            seg = 2 * pi / np
            angle = 0
            for i in range(np):
                x = radius * cos(angle) + pos[0]
                y = radius * sin(angle) + pos[1]
                cp.append([ x, y ])
                angle += seg
            cp.append(cp[0])
            if rotate != 0: cp = rotatecp(cp, pos, rotate)
            if scale != 1: xscale = yscale = scale
            if xscale != 1 or yscale != 1: scalecp(cp, xscale, yscale)
            if roundness > 0: cp = roundc(cp, roundness=roundness, invert=invert)
        else:
            cp = self.nframe(pos=pos, length=length, rotate=rotate, thickness=thickness, np=np,
                    roundness=roundness, invert=invert, scale=scale, xscale=xscale, yscale=yscale)
        return cp

    def triangle(self, pos=[0,0], length=1, rotate=0, thickness=0,
                    roundness=0, invert=False, scale=1, xscale=1, yscale=1):
        return self.ngon(pos=pos, np=3, length=length, rotate=rotate-pi/6,
                   roundness=roundness, invert=invert, scale=scale,
                   xscale=xscale, yscale=yscale, thickness=thickness)

    def pentagon(self, pos=[0,0], length=1, rotate=0, thickness=0,
                    roundness=0, invert=False, scale=1, xscale=1, yscale=1):
        return self.ngon(pos=pos, np=5, length=length, rotate=rotate-pi/10,
                   roundness=roundness, invert=invert, scale=scale,
                   xscale=xscale, yscale=yscale, thickness=thickness)

    def hexagon(self, pos=[0,0], length=1, rotate=0, thickness=0,
                    roundness=0, invert=False, scale=1, xscale=1, yscale=1):
        return self.ngon(pos=pos, np=6, length=length, rotate=rotate,
                   roundness=roundness, invert=invert, scale=scale,
                   xscale=xscale, yscale=yscale, thickness=thickness)

    def octagon(self, pos=[0,0], length=1, rotate=0, thickness=0,
                    roundness=0, invert=False, scale=1, xscale=1, yscale=1):
        return self.ngon(pos=pos, np=8, length=length, rotate=rotate+pi/8,
                   roundness=roundness, invert=invert, scale=scale,
                   xscale=xscale, yscale=yscale, thickness=thickness)

    def sframe(self, pos=[0,0], rotate=0, thickness=None, radius=1, n=5, iradius=None,
                    roundness=0, invert=False, scale=1, xscale=1, yscale=1):
        if iradius is None:
            iradius = .5 * radius
        if thickness is None:
            thickness = .2 * radius
        else:
            thickness = thickness * 2 * iradius

        outer = self.star(pos=pos, n=n, radius=radius, iradius=iradius)
        inner = self.star(pos=pos, n=n, radius=radius - thickness, iradius=(radius - thickness) * iradius / radius)
        if rotate != 0:
            outer = rotatecp(outer, pos, rotate)
            inner = rotatecp(inner, pos, rotate)

        if scale != 1: xscale = yscale = scale
        if xscale != 1 or yscale != 1:
            outer = scale(outer, xscale, yscale)
            inner = scale(inner, xscale, yscale)

        if roundness > 0:
            outer = roundc(outer, roundness=roundness, invert=invert)
            inner = roundc(inner, roundness=roundness, invert=invert)

        return [ outer, inner ]

    def star(self, pos=[0,0], rotate=0, thickness=0, radius=1, n=5, iradius=None,
                    roundness=0, invert=False, scale=1, xscale=1, yscale=1):
        ## radius is from center to outer point of the star
        ## iradius is from center to inner corners of the star
        if iradius is None: iradius = radius * .5
        if thickness == 0:
            cp = []
            dtheta = pi / n
            theta = 0
            for i in range(2*n+1):
                if i % 2 == 0:
                    cp.append([ -radius * sin(theta), radius * cos(theta) ])
                else:
                    cp.append([ -iradius * sin(theta), iradius * cos(theta) ])
                theta += dtheta
            cp = addpos(cp, pos)
            cp[-1] = cp[0] # take care of possible rounding errors
            if rotate != 0: cp = rotatecp(cp, pos, rotate)
            if scale != 1: xscale = yscale = scale
            if xscale != 1 or yscale != 1: scalecp(cp, xscale, yscale)
            if roundness > 0: cp = roundc(cp, roundness=roundness, invert=invert)
        else:
            cp = self.sframe(pos=pos, rotate=rotate, thickness=thickness, radius=radius, iradius=iradius,
                    n=n, roundness=roundness, invert=invert, scale=scale, xscale=xscale, yscale=yscale)
        return cp

    def points(self, pos=[], rotate=0, path=False, roundness=0, invert=False, scale=1, xscale=1, yscale=1):
        cp = pos
        closed = cp[-1][0] == cp[0][0] and cp[-1][1] == cp[0][1]
        if not closed and not path: cp.append(cp[0])
        if len(cp) > 0 and rotate != 0: cp = rotatecp(cp, [0,0], rotate)
        if scale != 1: xscale = yscale = scale
        if xscale != 1 or yscale != 1: scalecp(cp, xscale, yscale)
        if roundness > 0: cp = roundc(cp, roundness=roundness, invert=invert)
        return cp

    def gear(self, pos=[0,0], n=20, radius=1, phi=20, addendum=None, dedendum=None,
                fradius=None, rotate=0, scale=1, res=1, bevel=0):
            if addendum is None: addendum = 0.08*radius
            if dedendum is None: dedendum = 0.1*radius
            if fradius is None: fradius = 0.02*radius
            tooth = ToothOutline(n=n, res=res, phi=phi, radius=radius,
                        addendum=addendum, dedendum=dedendum, fradius=fradius, bevel=0)
            g = []
            for i in range(n):
                rotan = -i * 2 * pi / n
                rtooth = []
                for j in range(len(tooth)):
                    p = tooth[j]
                    x = p[0]
                    y = p[1]
                    rx = x * cos(rotan) - y * sin(rotan) +  pos[0]
                    ry = x * sin(rotan) + y * cos(rotan) +  pos[1]
                    rtooth.append([rx, ry])
                g.extend(rtooth)
            if scale != 1: g = scalecp(g, scale, scale)
            if rotate != 0: g = rotatecp(g, pos, rotate)
            pts = []
            i = 0
            while i < len(g):
                ### must eliminate neighboring repeated points and collinear points; poly2tri.js chokes on them
                g1 = g[i]
                pts.append(g1)
                if i == len(g)-1: break
                g2 = g[i+1]
                if i < len(g)-2:
                    g3 = g[i+2]
                    # check for a-b-a instance of collinear points
                    if abs(g3[0]-g1[0]) < .001*radius and abs(g3[1]-g1[1]) < .001*radius: i += 2
                    g2 = g[i]
                    if abs(g1[0] - g2[0]) < .001*radius and abs(g1[1] - g2[1]) < .001*radius:
                        i += 1
                if abs(g1[0] - g2[0]) < .001*radius and abs(g1[1] - g2[1]) < .001*radius:
                    i += 1
                i += 1
            g1 = pts[0]
            g2 = pts[-1]
            if not (g1[0] == g2[0] and g1[1] == g2[1]): pts.append(g1)
            return pts

    def rackgear(self, pos=(0,0), n=30, radius=5., phi=20., addendum=0.4, dedendum=0.5,
             fradius=0.1, rotate=0, scale=1.0, length=10*pi, res=1, bevel=0.05, depth=(0.4+0.6+0.1)):
            if addendum is None: addendum = 0.08*radius
            if dedendum is None: dedendum = 0.1*radius
            if fradius is None: fradius = 0.02*radius
            tooth = RackOutline(n=n, res=res, phi=phi, radius=radius,
                        addendum=addendum, dedendum=dedendum, fradius=fradius, bevel=bevel)
            toothl = tooth[0][1] - tooth[-1][1]
            nt = int(floor(length / toothl))
            flength = nt * toothl
            g = []
            lastx = lasty = 1e9
            for i in range(nt):
                ntooth = []
                for j in range(len(tooth)):
                    p = tooth[j]
                    x = p[0]
                    y = p[1]
                    if x == lastx or y == lasty: continue
                    nx = x + pos[0]
                    ny = -i * toothl + y + pos[1]
                    ntooth.append([nx, ny])
                    lastx = x
                    lasty = y
                g.extend(ntooth)

            g.append([g[-1][0] - depth, g[-1][1]])
            g.append([g[0][0] - depth, g[0][1]])
            g.append(g[0])
            left = 1e9
            right = -1e9
            bottom = 1e9
            top = -1e9
            for i in range(len(g)):
                g1 = g[i]
                x = g1[0]
                y = g1[1]
                if x < left: left = x
                if x > right: right = x
                if y < bottom: bottom = y
                if y > top: top = y

            center = [ (left + right) / 2, (bottom + top) / 2 ]
            dx = pos[0] - center[0]
            dy = pos[1] - center[1]
            g2 = []
            for i in range(len(g)):
                temp = g[i]
                g2.append([ temp[0] + dx, temp[1] + dy ])
            if scale != 1: g2 = scalecp(g2, scale, scale)
            if rotate != 0: g2 = rotatecp(g2, pos, rotate)
            a1 = g2[0]
            a2 = g2[-1]
            if not a1[0] == a2[0] and a1[1] == a2[1]: g2.append(a1)
            return g2

def convert(pos=(0,0,0), up=(0,1,0), points=None, closed=True):
        pos = vector(pos)
        up = norm(vector(up))
        up0 = vector(0,1,0)
        angle = acos(up.dot(up0))
        reorient = (angle > 0.0)
        axis = up0.cross(up)
        pts = []
        for pt in points:
            newpt = vector(pt[0],0,-pt[1])
            if reorient: newpt = newpt.rotate(angle=angle, axis=axis)
            pts.append(pos+newpt)
        if closed and not pts[-1].equals(pts[0]): pts.append(pts[0])
        return pts

class path_object(object):

    def rectangle(self, pos=vec(0,0,0), width=6, height=None, rotate=0.0, thickness=None,
                      roundness=0.0, invert=False, scale=1.0, xscale=1.0, yscale=1.0, up=vec(0,1,0)):
            if height == None: height = width
            if thickness is not None:
                raise AttributeError("Thickness is not allowed in a rectangular path")
            c = shapes.rectangle(width=width, height=height, rotate=rotate, thickness=0,
                      roundness=roundness, invert=invert, scale=scale, xscale=xscale, yscale=yscale)
            return convert(pos=pos, up=up, points=c)

    def cross(self, pos=vec(0,0,0), width=5, thickness=2, rotate=0.0,
                      roundness=0.0, invert=False, scale=1.0, xscale=1.0, yscale=1.0, up=vec(0,1,0)):
            c = shapes.cross(width=width, rotate=rotate, thickness=thickness,
                      roundness=roundness, invert=invert, scale=scale, xscale=xscale, yscale=yscale)
            return convert(pos=pos, up=up, points=c)

    def trapezoid(self, pos=vec(0,0,0), width=6, height=3, top=None, rotate=0.0, thickness=None,
                      roundness=0.0, invert=False, scale=1.0, xscale=1.0, yscale=1.0, up=vec(0,1,0)):
            if height == None: height = width
            if thickness is not None:
                raise AttributeError("Thickness is not allowed in a trapezoidal path")
            c = shapes.trapezoid(width=width, height=height, top=top, rotate=rotate, thickness=0,
                      roundness=roundness, invert=invert, scale=scale, xscale=xscale, yscale=yscale)
            return convert(pos=pos, up=up, points=c)

    def circle(self, pos=vec(0,0,0), radius=3, np=32, thickness=None,
                      scale=1.0, xscale=1.0, yscale=1.0, up=vec(0,1,0)):
            if thickness is not None:
                raise AttributeError("Thickness is not allowed in a circular path")
            c = shapes.circle(radius=radius, np=np, scale=scale, xscale=xscale, yscale=yscale)
            return convert(pos=pos, up=up, points=c)

    def line(self, start=vec(0,0,0), end=vec(0,0,-1), np=2):
            if np < 2:
                raise AttributeError("The minimum value of np is 2 (one segment)")
            start = vector(start)
            end = vector(end)
            vline = (end-start)/(np-1)
            pos = []
            for i in range(np):
                pos.append(start + i*vline)
            return pos

    def arc(self, pos=vec(0,0,0), radius=3, np=32, rotate=0.0, angle1=0, angle2=pi, thickness=None,
                      scale=1.0, xscale=1.0, yscale=1.0, up=vec(0,1,0)):
            if thickness is not None:
                raise AttributeError("Thickness is not allowed in a circular path")
            c = shapes.arc(radius=radius, angle1=angle1, angle2=angle2, rotate=rotate, np=np,
                       scale=scale, xscale=xscale, yscale=yscale, path=True)
            return convert(pos=pos, up=up, points=c, closed=False)

    def ellipse(self, pos=vec(0,0,0), width=6, height=None, np=32, thickness=None,
                      scale=1.0, xscale=1.0, yscale=1.0, up=vec(0,1,0)):
            if thickness is not None:
                raise AttributeError("Thickness is not allowed in an elliptical path")
            c = shapes.ellipse(width=width, height=height, np=np, scale=scale, xscale=xscale, yscale=yscale)
            return convert(pos=pos, up=up, points=c)

    def ngon(self, pos=vec(0,0,0), np=3, length=6, radius=3.0, rotate=0.0, thickness=None,
                      roundness=0.0, invert=False, scale=1.0, xscale=1.0, yscale=1.0, up=vec(0,1,0)):
            if thickness is not None:
                raise AttributeError("Thickness is not allowed in an ngon path")
            c = shapes.ngon(np=np, length=length, radius=radius, rotate=rotate, thickness=0,
                      roundness=roundness, invert=invert, scale=scale, xscale=xscale, yscale=yscale)
            return convert(pos=pos, up=up, points=c)

    def triangle(self, pos=vec(0,0,0), np=3, length=6, rotate=0.0, thickness=None,
                      roundness=0.0, invert=False, scale=1.0, xscale=1.0, yscale=1.0, up=vec(0,1,0)):
            if thickness is not None:
                raise AttributeError("Thickness is not allowed in a triangular path")
            c = shapes.ngon(np=np, length=length, rotate=rotate-pi/6.0, thickness=0,
                      roundness=roundness, invert=invert, scale=scale, xscale=xscale, yscale=yscale)
            return convert(pos=pos, up=up, points=c)

    def pentagon(self, pos=vec(0,0,0), np=5, length=6, rotate=0.0, thickness=None,
                      roundness=0.0, invert=False, scale=1.0, xscale=1.0, yscale=1.0, up=vec(0,1,0)):
            if thickness is not None:
                raise AttributeError("Thickness is not allowed in a pentagonal path")
            c = shapes.ngon(np=np, length=length, rotate=rotate+pi/10, thickness=0,
                      roundness=roundness, invert=invert, scale=scale, xscale=xscale, yscale=yscale)
            return convert(pos=pos, up=up, points=c)

    def hexagon(self, pos=vec(0,0,0), np=6, length=6, rotate=0.0, thickness=None,
                      roundness=0.0, invert=False, scale=1.0, xscale=1.0, yscale=1.0, up=vec(0,1,0)):
            if thickness is not None:
                raise AttributeError("Thickness is not allowed in a hexagonal path")
            c = shapes.ngon(np=np, length=length, rotate=rotate, thickness=0,
                      roundness=roundness, invert=invert, scale=scale, xscale=xscale, yscale=yscale)
            return convert(pos=pos, up=up, points=c)

    def star(self, pos=vec(0,0,0), radius=3, n=5, iradius=None, rotate=0.0, thickness=None,
                      roundness=0.0, invert=False, scale=1.0, xscale=1.0, yscale=1.0, up=vec(0,1,0)):
            if thickness is not None:
                raise AttributeError("Thickness is not allowed in a star path")
            c = shapes.star(n=n, radius=radius, iradius=iradius, rotate=rotate,
                      roundness=roundness, invert=invert, scale=scale, xscale=xscale, yscale=yscale)
            return convert(pos=pos, up=up, points=c)

    def pointlist(self, pos=[], rotate=0.0, thickness=None,
                      roundness=0.0, invert=False, scale=1.0, xscale=1.0, yscale=1.0, up=vec(0,1,0)):
            if thickness is not None:
                raise AttributeError("Thickness is not allowed in a pointlist path")
            # pos may be either a list of points or a Polygon object
            try:
                points = pos.contour(0)
                if len(pos) > 1:
                    raise AttributeError("pointlist can deal with only a single contour.")
            except:
                points = pos[:]
            closed = (points[-1] == points[0])
            if not closed:
                points.append(points[0])
            c = shapes.pointlist(pos=points, rotate=rotate, roundness=roundness, invert=invert,
                             scale=scale, xscale=xscale, yscale=yscale, path=True)
            return convert(pos=(0,0,0), up=up, points=c, closed=closed)

shapes = shape_object()
paths = path_object()
