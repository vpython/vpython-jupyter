from vpython import *

# Convert 3D .stl file ("stereo lithography") to VPython 7 object.

# Limitations:
#    Code for binary files needs to be updated to VPython 7.
#    Does not deal with color.
#    Does not assign texpos values to vertex objects,
#      so cannot add a meaningful texture to the final compound object.

# Original converter and STLbot by Derek Lura 10/06/09
# Be sure to look at the bottom of the STLbot figure!
# Part1.stl found at 3Dcontentcentral.com; also see 3dvia.com

# Factory function and handling of binary files by Bruce Sherwood 1/26/10
# Conversion to VPython 7 by Bruce Sherwood 2018 May 8

# Give this factory function an .stl file and it returns a compound object,
# to permit moving and rotating.

# Specify the file as a file name.

# See http://en.wikipedia.org/wiki/STL_(file_format)
# Text .stl file starts with a header that begins with the word "solid".
# Binary .stl file starts with a header that should NOT begin with the word "solid",
# but this rule seems not always to be obeyed.
# Currently the 16-bit unsigned integer found after each triangle in a binary
# file is ignored; some versions of .stl files put color information in this value.

def stl_to_triangles(fileinfo): # specify file
    # Accept a file name or a file descriptor; make sure mode is 'rb' (read binary)
    fd = open(fileinfo, mode='rb')
    text = fd.read()
    tris = [] # list of triangles to compound
    keywords = [b'outer', b'endloop', b'endfacet', b'solid', b'endsolid']
    if False: # prevent executing code for binary file
        pass
    # The following code for binary files must be updated:
#    if chr(0) in text: # if binary file
#        text = text[84:]
#        L = len(text)
#        N = 2*(L//25) # 25/2 floats per point: 4*3 float32's + 1 uint16
#        triPos = []
#        triNor = []
#        n = i = 0
#        while n < L:
#            triNor[i] = fromstring(text[n:n+12], float32)
#            triPos[i] = fromstring(text[n+12:n+24], float32)
#            triPos[i+1] = fromstring(text[n+24:n+36], float32)
#            triPos[i+2] = fromstring(text[n+36:n+48], float32)
#            colors = fromstring(text[n+48:n+50], uint16)
#            if colors != 0:
#                print '%x' % colors
#            if triNor[i].any():
#                triNor[i] = triNor[i+1] = triNor[i+2] = norm(vector(triNor[i]))
#            else:
#                triNor[i] = triNor[i+1] = triNor[i+2] = \
#                    norm(cross(triPos[i+1]-triPos[i],triPos[i+2]-triPos[i]))
#            n += 50
#            i += 3
    else:
        fd.seek(0)
        fList = fd.readlines()
        print('Number of lines =', len(fList))
    
        # Decompose list into vertex positions and normals
        ret = [] # will return a list of compounds if necessary
        vs = []
        vertices = 0
        for line in fList:
            FileLine = line.split( )
            first = FileLine[0]
            if first == b'facet':
                N = vec(float(FileLine[2]), float(FileLine[3]), float(FileLine[4]))
            elif first == b'vertex':
                vertices += 1
                vs.append( vertex(pos=vec(float(FileLine[1]), float(FileLine[2]), float(FileLine[3])), normal=N, color=color.white) )
                if len(vs) == 3:
                    tris.append(triangle(vs=vs))
                    vs = []
                    if vertices > 64000:
                        print(vertices)
                        ret.append(compound(tris))
                        tris = []
                        vertices = 0
            elif first in keywords:
                pass
            else:
                print(line) # for debugging
    if len(tris) > 0: ret.append(compound(tris))
    if len(ret) == 1: return ret[0]               
    else: return ret

if __name__ == '__main__':
    man = stl_to_triangles('STLbot.stl')
    man.pos = vec(-200,0,0)
    man.color = color.cyan
    part = stl_to_triangles('Part1.stl')
    part.size *= 200
    part.pos = vec(250,0,0)
    part.color = color.orange
    print('Done')
