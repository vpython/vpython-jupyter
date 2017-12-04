from random import random

cdef extern from "math.h":
    double cos(double theta)
    double sin(double theta)
    double acos(double theta)
    double sqrt(double x)
cdef double pi = 3.14159265358979323846

cdef class vector(object):

    cdef public double _x
    cdef public double _y
    cdef public double _z
    cdef public object on_change
    
    @staticmethod 
    def random():
        return vector(-1.0 + 2.0*random(), -1.0 + 2.0*random(), -1.0 + 2.0*random())

    def __init__(self, *args):
        if len(args) == 3:
            self._x = args[0] # make sure it's a float; could be numpy.float64?
            self._y = args[1]
            self._z = args[2]
        elif len(args) == 1 and isinstance(args[0], vector): # make a copy of a vector
            other = args[0]
            self._x = other.x
            self._y = other.y
            self._z = other.z
        else:
            raise TypeError('A vector needs 3 components.')
        self.on_change = self.ignore
        
    cpdef ignore(self):
        pass
            
    property value:
        def __get__(self):
            return [self.x, self.y, self.z]
        def __set__(self, other):
            self._x = other.x
            self._y = other.y
            self._z = other.z

    def __repr__(self):
        return '<{:.6g}, {:.6g}, {:.6g}>'.format(self._x, self._y, self._z)
    
    def __str__(self):
        return '<{:.6g}, {:.6g}, {:.6g}>'.format(self._x, self._y, self._z)

    def __add__(self,other):
        return vector(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __truediv__(self, other): # used by Python 3, and by Python 2 in the presence of __future__ division
        try:
            return vector(self._x / other, self._y / other, self._z / other)
        except:
            raise TypeError('a vector can only be divided by a scalar', self, other)

    def __div__(self, other): # used by Python 2 in the absence of __future__ division
        try:
            return vector(self._x / other, self._y / other, self._z / other)
        except:
            raise TypeError('a vector can only be divided by a scalar', self, other)

    def __sub__(self,other):
        return vector(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __mul__(self, other):  ## in cython order of arguments is arbitrary, rmul doesn't exist
        try:
            return vector(self.x * other, self.y * other, self. z * other)
        except:
            pass
        try:
            return vector(self * other.x, self * other.y, self * other.z)
        except:
            raise TypeError('a vector can only be multiplied by a scalar', self, other)
        
    def __neg__(self):  ## seems like this must come before properties (???)
        return vector(-self.x, -self.y, -self.z)
    
    def __pos__(self):
        return self
                  
    property x:
        def __get__(self):
            return self._x
        def __set__(self,value):
            self._x = value
            self.on_change()
    
    property y:
        def __get__(self):
            return self._y
        def __set__(self,value):
            self._y = value
            self.on_change()
    
    property z:
        def __get__(self):
            return self._z
        def __set__(self,value):
            self._z = value
            self.on_change()
        
    property mag:
        def __get__(self):
            return sqrt(self.x**2 + self.y**2 + self.z**2)
        def __set__(self, value):
            cdef vector normA
            normA = self.hat
            self.x = value * normA.x
            self.y = value * normA.y
            self.z = value * normA.z
            self.on_change()
            
    property mag2:
        def __get__(self):
            return (self.x**2 + self.y**2 + self.z**2)
        def __set__(self, value):
            cdef double v
            v = sqrt(value)
            self.mag = v
        
    property hat:
        def __get__(self):
            cdef double smag
            smag = self.mag
            if ( smag > 0. ):
                return self / smag
            else:
                return vector(0., 0., 0.)
        def __set__(self, value):
            cdef double smag
            smag = self.mag
            cdef vector normA
            normA = value.hat
            self.x = smag * normA.x
            self.y = smag * normA.y
            self.z = smag * normA.z
            
    cpdef vector norm(self):
        return self.hat

    cpdef double dot(self,other):
        return ( self.x*other.x + self.y*other.y + self.z*other.z )

    cpdef vector cross(self,other):
        return vector( self.y*other.z-self.z*other.y, 
                       self.z*other.x-self.x*other.z,
                       self.x*other.y-self.y*other.x )

    cpdef vector proj(self,other):
        cdef vector normB
        normB = other.hat
        return self.dot(normB) * normB
        
    cpdef bint equals(self,other):
        return ( self.x == other.x and self.y == other.y and self.z == other.z )

    cpdef double comp(self,other):  ## result is a scalar
        cdef vector normB
        normB = other.hat
        return self.dot(normB)

    cpdef double diff_angle(self, other):
        cdef double a
        a = self.hat.dot(other.hat)
        if a > 1:  # avoid roundoff problems
            return 0
        if a < -1:
            return pi
        return acos(a)

    cpdef vector rotate(self, angle = 0., axis = None):
        if axis == None:
            u = vector(0,0,1)
        else:
            u = axis.hat
            
        cdef double cangle
        cangle = angle
        cdef double c = cos(cangle)
        cdef double s = sin(cangle)
        cdef double t = 1.0 - c
        cdef double x = u.x
        cdef double y = u.y
        cdef double z = u.z
        cdef double sx = self.x
        cdef double sy = self.y
        cdef double sz = self.z
        cdef double m11 = t*x*x+c
        cdef double m12 = t*x*y-z*s
        cdef double m13 = t*x*z+y*s
        cdef double m21 = t*x*y+z*s
        cdef double m22 = t*y*y+c
        cdef double m23 = t*y*z-x*s
        cdef double m31 = t*x*z-y*s
        cdef double m32 = t*y*z+x*s
        cdef double m33 = t*z*z+c
        return vector( (m11*sx + m12*sy + m13*sz),
                    (m21*sx + m22*sy + m23*sz),
                    (m31*sx + m32*sy + m33*sz) )

cpdef double mag(A):
    return A.mag

cpdef double mag2(A):
    return A.mag2

cpdef vector norm(A):
    return A.hat

cpdef vector hat(A):
    return A.hat

cpdef double dot(A,B):
    return A.dot(B)

cpdef vector cross(A,B):
    return A.cross(B)

cpdef vector proj(A,B):
    return A.proj(B)

cpdef double comp(A,B):
    return A.comp(B)

cpdef double diff_angle(A,B):
    return A.diff_angle(B)
                            
cpdef vector rotate(A, angle=0., axis = None):
    return A.rotate(angle, axis)
        
cpdef adjust_up(oldaxis, newaxis, up, save_oldaxis): # adjust up when axis is changed
    if abs(newaxis.x) + abs(newaxis.y) + abs(newaxis.z) == 0:
        # If axis has changed to <0,0,0>, must save the old axis to restore later
        if save_oldaxis is None: save_oldaxis = oldaxis
        return [up, save_oldaxis]
    if save_oldaxis is not None:
        # Restore saved oldaxis now that newaxis is nonzero
        oldaxis = save_oldaxis
        save_oldaxis = None
    if newaxis.dot(up) == 0: return [up, save_oldaxis] # axis and up already orthogonal
    cdef double angle = oldaxis.diff_angle(newaxis)
    cdef vector newup
    cdef vector rotaxis
    if angle > 1e-6: # smaller angles lead to catastrophes
        # If axis is flipped 180 degrees, cross(oldaxis,newaxis) is <0,0,0>:
        if abs(angle-pi) < 1e-6:
            newup = -up
        else:
            rotaxis = oldaxis.cross(newaxis)
            newup = up.rotate(angle=angle, axis=rotaxis)
        return [newup, save_oldaxis]
    else:
        return [up, save_oldaxis]

cpdef adjust_axis(oldup, newup, axis, save_oldup): # adjust axis when up is changed
    if abs(newup.x) + abs(newup.y) + abs(newup.z) == 0:
        # If up will be set to <0,0,0>, must save the old up to restore later
        if save_oldup is None: save_oldup = oldup
        return [axis, save_oldup]
    if save_oldup is not None:
        # Restore saved oldup now that newup is nonzero
        oldup = save_oldup
        save_oldup = None
    if newup.dot(axis) == 0: return [axis, save_oldup] # axis and up already orthogonal
    cdef double angle = oldup.diff_angle(newup)
    cdef vector newaxis
    cdef vector rotaxis
    if angle > 1e-6: # smaller angles lead to catastrophes
        # If up is flipped 180 degrees, cross(oldup,newup) is <0,0,0>:
        if abs(angle-pi) < 1e-6:
            newaxis = -axis
        else:
            rotaxis = oldup.cross(newup)
            newaxis = axis.rotate(angle=angle, axis=rotaxis)
        return [newaxis, save_oldup]
    else:
        return [axis, save_oldup]

