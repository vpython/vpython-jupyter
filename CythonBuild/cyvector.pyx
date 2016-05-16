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
        return vector(-1 + 2*random(), -1 + 2*random(), -1 + 2*random())

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

    #cpdef void on_change(self):
    #    pass
        
    def __neg__(self):  ## seems like this must come before properties (???)
        return vector(-1.*self.x, -1.*self.y, -1.*self.z)
    
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

    def __repr__(self):
        return '<%f, %f, %f>' % (self._x, self._y, self._z)
    
    def __str__(self):
        return '<%f, %f, %f>' % (self._x, self._y, self._z)

    def __add__(self,other):
        return vector(self.x + other.x, self.y + other.y, self.z + other.z)

    def __truediv__(self, other): # Python 3, or Python 2 + future division
        if isinstance(other, (int, float)):
            return vector(self.x / other, self.y / other, self.z / other)
        raise TypeError('a vector can only be divided by a scalar')

    def __div__(self, other): # Python 2 without future division
        if isinstance(other, (int, float)):
            return vector(self.x / other, self.y / other, self.z / other)
        raise TypeError('a vector can only be divided by a scalar')

    def __sub__(self,other):
        return vector(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __mul__(self, other):  ## in cython order of arguments is arbitrary, rmul doesn't exist
        if isinstance(other, (int, float)):
            return vector(self.x * other, self.y * other, self. z * other)
        elif isinstance(self, (int, float)):
            return vector(self * other.x, self * other.y, self * other.z)
        else:
            raise TypeError('a vector can only be multiplied by a scalar', self, other)
        
    property mag:
        def __get__(self):
            return sqrt(self.x**2 + self.y**2 + self.z**2)
        def __set__(self, value):
            cdef vector normA
            normA = self.norm()
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
            
    property value:
        def __get__(self):
            return [self.x, self.y, self.z]
        def __set__(self, other):
            self._x = other.x
            self._y = other.y
            self._z = other.z
            

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
                            
cpdef vector rotate(A, angle = 0., axis = None):
    cdef double ang
    cdef vector ax
    if axis is None:
        ax = vector(0,0,1)
    else:
        ax = axis
    ang = angle
    return A.rotate(ang, ax)
