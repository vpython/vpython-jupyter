## vectors and associated methods
from math import cos, sin, acos, sqrt, pi
from random import random

# List of names imported from this module with import *
__all__ = ['adjust_axis', 'adjust_up', 'comp', 'cross', 'diff_angle', 'dot',
           'hat', 'mag', 'mag2', 'norm', 'object_rotate', 'proj', 'rotate',
           'vector']


class vector(object):
    'vector class'

    @staticmethod
    def random():
        return vector(-1.0 + 2.0*random(), -1.0 + 2.0*random(), -1.0 + 2.0*random())

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

    @property
    def value(self):
        return [self._x, self._y, self._z]
    @value.setter
    def value(self,other):  ## ensures a copy; other is a vector
        self._x = other._x
        self._y = other._y
        self._z = other._z

    def __neg__(self):
        return vector(-self._x, -self._y, -self._z)

    def __pos__(self):
        return self

    def __str__(self):
        return '<{:.6g}, {:.6g}, {:.6g}>'.format(self._x, self._y, self._z)

    def __repr__(self):
        return '<{:.6g}, {:.6g}, {:.6g}>'.format(self._x, self._y, self._z)

    def __add__(self, other):
        if type(other) is vector:
            return vector(self._x + other._x, self._y + other._y, self._z + other._z)
        return NotImplemented

    def __sub__(self, other):
        if type(other) is vector:
            return vector(self._x - other._x, self._y - other._y, self._z - other._z)
        return NotImplemented

    def __truediv__(self, other): # used by Python 3, and by Python 2 in the presence of __future__ division
        if isinstance(other, (float, int)):
            return vector(self._x / other, self._y / other, self._z / other)
        return NotImplemented

    def __mul__(self, other):
        if isinstance(other, (float, int)):
            return vector(self._x * other, self._y * other, self._z * other)
        return NotImplemented

    def __rmul__(self, other):
        if isinstance(other, (float, int)):
            return vector(self._x * other, self._y * other, self._z * other)
        return NotImplemented

    def __eq__(self,other):
        if type(self) is vector and type(other) is vector:
            return self.equals(other)
        return False

    def __ne__(self,other):
        if type(self) is vector and type(other) is vector:
            return not self.equals(other)
        return True

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
        return sqrt(self._x**2+self._y**2+self._z**2)
    @mag.setter
    def mag(self,value):
        normA = self.hat
        self._x = value * normA._x
        self._y = value * normA._y
        self._z = value * normA._z
        self.on_change()

    @property
    def mag2(self):
        return self._x**2+self._y**2+self._z**2
    @mag2.setter
    def mag2(self,value):
        normA = self.hat
        v = sqrt(value)
        self._x = v * normA._x
        self._y = v * normA._y
        self._z = v * normA._z
        self.on_change()

    @property
    def hat(self):
        smag = self.mag
        if ( smag > 0. ):
            return self / smag
        else:
            return vector(0., 0., 0.)
    @hat.setter
    def hat(self, value):
        smg = self.mag
        normA = value.hat
        self._x = smg * normA._x
        self._y = smg * normA._y
        self._z = smg * normA._z
        self.on_change()

    def norm(self):
        return self.hat

    def dot(self,other):
        return ( self._x*other._x + self._y*other._y + self._z*other._z )

    def cross(self,other):
        return vector( self._y*other._z-self._z*other._y,
                       self._z*other._x-self._x*other._z,
                       self._x*other._y-self._y*other._x )

    def proj(self,other):
        normB = other.hat
        return self.dot(normB) * normB

    def equals(self,other):
        return self._x == other._x and self._y == other._y and self._z == other._z

    def comp(self,other):  ## result is a scalar
        normB = other.hat
        return self.dot(normB)

    def diff_angle(self, other):
        a = self.hat.dot(other.hat)
        if a > 1:  # avoid roundoff problems
            return 0
        if a < -1:
            return pi
        return acos(a)

    def rotate(self, angle=0., axis=None):
        if axis is None:
            u = vector(0,0,1)
        else:
            u = axis.hat
        c = cos(angle)
        s = sin(angle)
        t = 1.0 - c
        x = u._x
        y = u._y
        z = u._z
        m11 = t*x*x+c
        m12 = t*x*y-z*s
        m13 = t*x*z+y*s
        m21 = t*x*y+z*s
        m22 = t*y*y+c
        m23 = t*y*z-x*s
        m31 = t*x*z-y*s
        m32 = t*y*z+x*s
        m33 = t*z*z+c
        sx = self._x
        sy = self._y
        sz = self._z
        return vector( (m11*sx + m12*sy + m13*sz),
                    (m21*sx + m22*sy + m23*sz),
                    (m31*sx + m32*sy + m33*sz) )

    def rotate_in_place(self, angle=0., axis=None):
        if axis is None:
            u = vector(0,0,1)
        else:
            u = axis.hat
        c = cos(angle)
        s = sin(angle)
        t = 1.0 - c
        x = u._x
        y = u._y
        z = u._z
        m11 = t*x*x+c
        m12 = t*x*y-z*s
        m13 = t*x*z+y*s
        m21 = t*x*y+z*s
        m22 = t*y*y+c
        m23 = t*y*z-x*s
        m31 = t*x*z-y*s
        m32 = t*y*z+x*s
        m33 = t*z*z+c
        sx = self._x
        sy = self._y
        sz = self._z
        self._x = m11*sx + m12*sy + m13*sz
        self._y = m21*sx + m22*sy + m23*sz
        self._z = m31*sx + m32*sy + m33*sz

def object_rotate(objaxis, objup, angle, axis):
    u = axis.hat
    c = cos(angle)
    s = sin(angle)
    t = 1.0 - c
    x = u._x
    y = u._y
    z = u._z
    m11 = t*x*x+c
    m12 = t*x*y-z*s
    m13 = t*x*z+y*s
    m21 = t*x*y+z*s
    m22 = t*y*y+c
    m23 = t*y*z-x*s
    m31 = t*x*z-y*s
    m32 = t*y*z+x*s
    m33 = t*z*z+c
    sx = objaxis._x
    sy = objaxis._y
    sz = objaxis._z
    objaxis._x = m11*sx + m12*sy + m13*sz # avoid creating a new vector object
    objaxis._y = m21*sx + m22*sy + m23*sz
    objaxis._z = m31*sx + m32*sy + m33*sz
    sx = objup._x
    sy = objup._y
    sz = objup._z
    objup._x = m11*sx + m12*sy + m13*sz
    objup._y = m21*sx + m22*sy + m23*sz
    objup._z = m31*sx + m32*sy + m33*sz

def mag(A):
    return A.mag

def mag2(A):
    return A.mag2

def norm(A):
    return A.hat

def hat(A):
    return A.hat

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

def rotate(A, angle=0., axis = None):
    return A.rotate(angle,axis)

def adjust_up(oldaxis, newaxis, up, save_oldaxis): # adjust up when axis is changed
    if abs(newaxis._x) + abs(newaxis._y) + abs(newaxis._z) == 0:
        # If axis has changed to <0,0,0>, must save the old axis to restore later
        if save_oldaxis is None: save_oldaxis = oldaxis
        return save_oldaxis
    if save_oldaxis is not None:
        # Restore saved oldaxis now that newaxis is nonzero
        oldaxis._x = save_oldaxis._x # avoid creating a new vector
        oldaxis._y = save_oldaxis._y
        oldaxis._z = save_oldaxis._z
        save_oldaxis = None
    if newaxis.dot(up) != 0: # axis and up not orthogonal
        angle = oldaxis.diff_angle(newaxis)
        if angle > 1e-6: # smaller angles lead to catastrophes
            # If axis is flipped 180 degrees, cross(oldaxis,newaxis) is <0,0,0>:
            if abs(angle-pi) < 1e-6:
                up._x = -up._x
                up._y = -up._y
                up._z = -up._z
            else:
                rotaxis = oldaxis.cross(newaxis)
                up.rotate_in_place(angle=angle, axis=rotaxis) # avoid creating a new vector
    oldaxis._x = newaxis._x # avoid creating a new vector
    oldaxis._y = newaxis._y
    oldaxis._z = newaxis._z

def adjust_axis(oldup, newup, axis, save_oldup): # adjust axis when up is changed
    if abs(newup._x) + abs(newup._y) + abs(newup._z) == 0:
        # If up will be set to <0,0,0>, must save the old up to restore later
        if save_oldup is None: save_oldup = oldup
        return save_oldup
    if save_oldup is not None:
        # Restore saved oldup now that newup is nonzero
        oldup = save_oldup
        save_oldup = None
    if newup.dot(axis) != 0: # axis and up not orthogonal
        angle = oldup.diff_angle(newup)
        if angle > 1e-6: # smaller angles lead to catastrophes
            # If up is flipped 180 degrees, cross(oldup,newup) is <0,0,0>:
            if abs(angle-pi) < 1e-6:
                axis._x = -axis._x
                axis._y = -axis._y
                axis._z = -axis._z
            else:
                rotaxis = oldup.cross(newup)
                axis.rotate_in_place(angle=angle, axis=rotaxis) # avoid creating a new vector
    oldup._x = newup._x # avoid creating a new vector
    oldup._y = newup._y
    oldup._z = newup._z
    return save_oldup
