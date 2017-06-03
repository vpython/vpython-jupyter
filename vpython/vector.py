## vectors and associated methods
from __future__ import division, print_function, absolute_import
import math
from random import random

class vector(object):
    'vector class'
    
    @staticmethod 
    def random():
        return vector(-1 + 2*random(), -1 + 2*random(), -1 + 2*random())

    def __init__(self, *args):
        if len(args) == 3:
            self._x = float(args[0]) # make sure it's a float; could be numpy.float64
            self._y = float(args[1])
            self._z = float(args[2])
        elif len(args) == 1 and isinstance(args[0], vector): # make a copy of a vector
            other = args[0]
            self._x = other._x
            self._y = other._y
            self._z = other._z
        else:
            raise TypeError('A vector needs 3 components.')
        self.on_change = self.ignore
    
    def ignore(self):
        pass
        
    def __str__(self):
        return '<%f, %f, %f>' % (self._x, self._y, self._z)
   
    def __repr__(self):
        return '<%f, %f, %f>' % (self._x, self._y, self._z)
   
    def __add__(self,other):
        return vector(self._x + other._x, self._y + other._y, self._z + other._z)
    
    def __sub__(self,other):
        return vector(self._x - other._x, self._y - other._y, self._z - other._z)
    
    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return vector(self._x * other, self._y * other, self._z * other)
        raise TypeError('a vector can only be multiplied by a scalar')
    
    def __rmul__(self, other):
        if isinstance(other, (int, float)):
            return vector(self._x * other, self._y * other, self._z * other)
        raise TypeError('a vector can only be multiplied by a scalar')

    def __div__(self, other): # used by Python 2 in the absence of __future__ division
        if isinstance(other, (int, float)):
            return vector(self._x / other, self._y / other, self._z / other)
        raise TypeError('a vector can only be divided by a scalar')
    
    def __truediv__(self, other): # used by Python 3, and by Python 2 in the presence of __future__ division
        if isinstance(other, (int, float)):
            return vector(self._x / other, self._y / other, self._z / other)
        raise TypeError('a vector can only be divided by a scalar')

    def __neg__(self):
        return vector(-1.*self._x, -1.*self._y, -1.*self._z)
        
    def norm(self):
        smag = self.mag
        if (smag > 0.):
            return self / smag
        else:
            return vector(0.,0.,0.)

    def dot(self,other):
        return ( self._x*other._x + self._y*other._y + self._z*other._z )

    def cross(self,other):
        return vector( self._y*other._z-self._z*other._y, 
                       self._z*other._x-self._x*other._z,
                       self._x*other._y-self._y*other._x )

    def proj(self,other):
        normB = other.norm()
        return self.dot(normB) * normB
        
    def equals(self,other):
        return self._x == other._x and self._y == other._y and self._z == other._z

    def comp(self,other):  ## result is a scalar
        normB = other.norm()
        return self.dot(normB)

    def diff_angle(self, other):
        a = self.norm().dot(other.norm())
        if a > 1:  # avoid roundoff problems
            return 0
        if a < -1:
            return math.pi
        return math.acos(a)
        
    def rotate(self,angle = 0., axis = None):
        if axis == None:
            u = vector(0,0,1)
        else:
            u = norm(axis)
        c = math.cos(angle)
        s = math.sin(angle)
        t = 1.0 - c
        x = u.x
        y = u.y
        z = u.z
        sx = self.x
        sy = self.y
        sz = self.z
        m11 = t*x*x+c
        m12 = t*x*y-z*s
        m13 = t*x*z+y*s
        m21 = t*x*y+z*s
        m22 = t*y*y+c
        m23 = t*y*z-x*s
        m31 = t*x*z-y*s
        m32 = t*y*z+x*s
        m33 = t*z*z+c
        return vector( (m11*sx + m12*sy + m13*sz),
                    (m21*sx + m22*sy + m23*sz),
                    (m31*sx + m32*sy + m33*sz) )

    @property
    def value(self):  ## attribute vectors
        return [self._x, self._y, self._z]
    @value.setter
    def value(self,other):  ## ensures a copy; other is a vector
        self._x = other._x
        self._y = other._y
        self._z = other._z
    
    @property
    def x(self):
        return self._x
    @x.setter
    def x(self,value):
        self._x = value
        self.on_change()
    
    @property
    def y(self):
        return self._y
    @y.setter
    def y(self,value):
        self._y = value
        self.on_change()
    
    @property
    def z(self):
        return self._z
    @z.setter
    def z(self,value):
        self._z = value
        self.on_change()

    @property
    def mag(self):
        return math.sqrt(self._x**2+self._y**2+self._z**2)
    @mag.setter
    def mag(self,value):
        normA = self.norm()
        self._x = value * normA._x
        self._y = value * normA._y
        self._z = value * normA._z
        self.on_change()

    @property
    def mag2(self):
        return self._x**2+self._y**2+self._z**2
    @mag2.setter
    def mag2(self,value):
        normA = self.norm()
        v = math.sqrt(value)
        self._x = v * normA._x
        self._y = v * normA._y
        self._z = v * normA._z
        self.on_change()
        
    @property
    def hat(self):
        return self.norm()
    @hat.setter
    def hat(self, value):
        mg = self.mag
        normA = value.norm()
        self._x = mg * normA._x
        self._y = mg * normA._y
        self._z = mg * normA._z
        self.on_change()

def mag(A):
    return A.mag

def mag2(A):
    return A.mag2

def norm(A):
    return A.norm()

def hat(A):
    return A.norm()

def dot(A,B):
    return A.dot(B)

def cross(A,B):
    return A.cross(B)

def proj(A,B):
    return A.proj(B)

def comp(A,B):
    return A.comp(B)

def diff_angle(A,B):
    return A.diff_angle(B)
                            
def rotate(A,angle = 0., axis = None):
    return A.rotate(angle,axis)
