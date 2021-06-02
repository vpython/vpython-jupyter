# UINT8[80]    – Header                 -     80 bytes                           
# UINT32       – Number of triangles    -      4 bytes
# foreach triangle                      - 50 bytes:
    # REAL32[3] – Normal vector             - 12 bytes
    # REAL32[3] – Vertex 1                  - 12 bytes
    # REAL32[3] – Vertex 2                  - 12 bytes
    # REAL32[3] – Vertex 3                  - 12 bytes
    # UINT16    – Attribute byte count      -  2 bytes
# end

from vpython import *
import struct
from collections import namedtuple
import numpy as np

Ctypes = namedtuple('Ctype', ['fmt', 'size'])

Ctype_names = ['char', 'signed char', 'unsigned char', '_Bool', 'short', \
               'unsigned short', 'int', 'unsigned int', 'long', 'unsigned long',\
                   'long long', 'unsigned long long', 'float', 'double', 'char[]']
Ctype_sizes = [1, 1, 1, 1, 2,\
              2, 4, 4, 4, 4,\
                  8, 8, 4, 8, -1]
Ctype_formats = ['c', 'b', 'B', '?', 'h',\
                'H', 'i', 'I', 'l', 'L',\
                    'q', 'Q', 'f', 'd', 's']

Ctype_dict = {}
for i, name in enumerate(Ctype_names):
    Ctype_dict[name] = Ctypes(Ctype_formats[i], Ctype_sizes[i])    
   
def binary_reader(fid, Ctype, **opts):
    assert Ctype in Ctype_dict, "Ctype not found in Ctype_dict"
    if Ctype == 'char[]':  
        string = []       
        for ch in range(opts['size']):
            char = struct.unpack(Ctype_dict['char'].fmt, fid.read(Ctype_dict['char'].size))[0]            
            if chr(0).encode('utf-8') not in char:
                string.append(char.decode('utf-8'))
            else:
                string.append(' ')                 
        return ''.join(string)
   
    if Ctype == 'char':
        return ord(struct.unpack(Ctype_dict[Ctype].fmt, fid.read(Ctype_dict[Ctype].size))[0].decode('utf-8'))   
    return struct.unpack(Ctype_dict[Ctype].fmt, fid.read(Ctype_dict[Ctype].size))[0]
    
def stl_to_triangles(filename):
    with open(filename, "rb") as f:
        header = binary_reader(f,'char[]', size = 80)    
        numOfTri = binary_reader(f,'unsigned int')
        
        print(header)
        print(numOfTri)
        
        tris = []
        
        for i in range(numOfTri):
            vs = []
            x1, x2, x3 = binary_reader(f,'float'), binary_reader(f,'float'), binary_reader(f,'float')
            N = vec(x1, x2, x3)
            
            x1, x2, x3 = binary_reader(f,'float'), binary_reader(f,'float'), binary_reader(f,'float')
            p1 = vertex(pos = vec(x1, x2, x3), normal=N, color=color.white)
            vs.append(p1)
            
            x1, x2, x3 = binary_reader(f,'float'), binary_reader(f,'float'), binary_reader(f,'float')
            p2 = vertex(pos = vec(x1, x2, x3), normal=N, color=color.white)
            vs.append(p2)
            
            x1, x2, x3 = binary_reader(f,'float'), binary_reader(f,'float'), binary_reader(f,'float')
            p3 = vertex(pos = vec(x1, x2, x3), normal=N, color=color.white)
            vs.append(p3)
                    
            attr = binary_reader(f,'unsigned short')    
            tris.append(triangle(vs=vs))   
        
        return compound(tris)
    
if __name__ == '__main__':
    filename = r"\convert_stl\Part1_bin.stl" # update this file
    man = stl_to_triangles(filename)
    man.color = color.orange
    
    
    