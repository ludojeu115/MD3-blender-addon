from math import sin, atan2, cos, acos
import math
import struct
from typing import List

MAX_QPATH: int = 64
MD3_MAX_FRAMES: int = 1024
MD3_MAX_TAGS: int = 16
MD3_MAX_SURFACES: int = 32
MD3_XYZ_SCALE: float = (1.0/64.0)

# Functions Start Here

# READING FUNCTIONS


def readS16(f) -> int:
    return struct.unpack('<h', f.read(2))[0]


def readS32(f) -> int:
    return struct.unpack('<i', f.read(4))[0]


def readF32(f) -> float:
    return struct.unpack('f', f.read(4))[0]


def readmax(f, n) -> str:
    str = b''
    for _ in range(n):
        tmp = f.read(1)
        if tmp != '\x00':
            str = str+tmp  # .decode('ascii')
    return str.decode("utf-8")

# WRITING FUNCTIONS


def writeS32(f, x):
    f.write(struct.pack('<i', x))


def writeF32(f, x):
    f.write(struct.pack('f', x))


def writeS16(f, x):
    f.write(struct.pack('<h', x))


def writemax(f, str, n):
    # print("writing max string:", str)
    for _ in range(n):
        if len(str) == 0:
            f.write(b'\x00')
        else:
            f.write(str[0:1])
            str = str[1:]


class Vec3:
    def __init__(self, x, y, z) -> None:
        self.x: int = x
        self.y: int = y
        self.z: int = z

    def read(f):
        return Vec3(readS32(f), readS32(f), readS32(f))

    def write(self, f):
        writeS32(f, self.x)
        writeS32(f, self.y)
        writeS32(f, self.z)


class Shader:
    def __init__(self, name, shader_index) -> None:
        self.name: str = name
        self.shader_index: int = shader_index
        # print("    shader index : ", shader_index)
        # print("    shader name : ", name)

    def read(f):
        return Shader(readmax(f, MAX_QPATH), readS32(f))

    def write(self, f):
        # print("position write: ", f.tell())
        writemax(f, self.name.encode("utf-8"), MAX_QPATH)
        writeS32(f, self.shader_index)


class Triangle:
    def __init__(self, indexes) -> None:
        self.indexes: list[int] = indexes

    def read(f):
        return Triangle([readS32(f), readS32(f), readS32(f)])

    def write(self, f):
        writeS32(f, self.indexes[0])
        writeS32(f, self.indexes[1])
        writeS32(f, self.indexes[2])


class TexCoord:
    def __init__(self, st) -> None:
        self.st: list[float] = st

    def read(f):
        return TexCoord([readF32(f), 1.0-readF32(f)])

    def write(self, f):
        writeF32(f, self.st[0])
        writeF32(f, 1-self.st[1])


class Vertex:
    def __init__(self, x, y, z, normal) -> None:
        # print(x, y, z, normal)
        self.x: int = x
        self.y: int = y
        self.z: int = z
        self.normal: list[float] = normal
        # print("normal: ", self.normal)

    def read(f):
        x = readS16(f)
        y = readS16(f)
        z = readS16(f)
        oldNorm = readS16(f)
        long = (oldNorm % 256)*(2*math.pi)/255.0
        lat = (oldNorm/256)*(2*math.pi)/255.0
        norm = [-cos(lat)*sin(long), -sin(lat)*sin(long), -cos(long)]

        return Vertex(x, y, z, norm)

    def write(self, f):
        writeS16(f, self.x)
        writeS16(f, self.y)
        writeS16(f, self.z)
        oldNorm = int(round(255.0*(atan2(-self.normal[1],
                                         -self.normal[0])/(2*math.pi))))
        oldNorm += int(round(255.0*(acos(-self.normal[2])/(2*math.pi))))*256
        writeS16(f, oldNorm)


class Frame:
    def __init__(self, min_bounds, max_bounds,
                 local_origin, radius, name) -> None:
        self.MIN_BOUNDS: Vec3 = min_bounds
        self.MAX_BOUNDS: Vec3 = max_bounds
        self.LOCAL_ORIGIN: Vec3 = local_origin
        self.RADIUS: float = radius
        self.NAME: str = name
        # print("    frame name : ", name)

    def read(f):
        return Frame(Vec3.read(f), Vec3.read(f), Vec3.read(f), readF32(f),
                     readmax(f, 16))

    def write(self, f):
        self.MIN_BOUNDS.write(f)
        self.MAX_BOUNDS.write(f)
        self.LOCAL_ORIGIN.write(f)
        writeF32(f, self.RADIUS)

        writemax(f, self.NAME.encode("utf-8"), 16)


class Tag:
    def __init__(self, origin, axis_rotation, name) -> None:
        self.NAME = name
        self.ORIGIN = origin
        self.AXIS_ROTATION = axis_rotation

    def read(f):
        return Tag(readmax(f, MAX_QPATH), Vec3.read(f),
                   [Vec3.read(f), Vec3.read(f), Vec3.read(f)])

    def write(self, f):
        writemax(f, self.NAME.encode("utf-8"), MAX_QPATH)
        self.ORIGIN.write(f)
        for i in range(3):
            self.AXIS_ROTATION[i].write(f)


class Surface:
    def __init__(self, ident, name, flags, num_frames, num_shaders, num_verts,
                 num_triangles, ofs_triangles, ofs_shaders, ofs_st,
                 ofs_xyznormal, ofs_end, shaders, triangles, sts,
                 xyzs) -> None:
        # print("creating surface")
        self.IDENT: int = ident
        self.NAME: str = name
        # print("surface name: ", name)
        self.FLAGS: int = flags
        self.NUM_FRAMES: int = num_frames
        # print("num frames: ", num_frames)
        self.NUM_SHADERS: int = num_shaders
        # print("num shaders: ", num_shaders)
        self.NUM_VERTS: int = num_verts
        # print("num verts: ", num_verts)
        self.NUM_TRIANGLES: int = num_triangles
        # print("num triangles: ", num_triangles)
        self.OFS_TRIANGLES: int = ofs_triangles
        self.OFS_SHADERS: int = ofs_shaders
        self.OFS_ST: int = ofs_st
        self.OFS_XYZNORMAL: int = ofs_xyznormal
        self.OFS_END: int = ofs_end
        self.shaders: list[Shader] = shaders
        self.triangles: list[Triangle] = triangles
        self.st: list[TexCoord] = sts
        self.xyzs: List[list[Vertex]] = xyzs

    def read(f, ofs_surface):
        ident = readS32(f)
        name = readmax(f, MAX_QPATH)
        flags = readS32(f)
        # print("surface name:", name)
        # print("Model flags : ", flags)
        num_frames = readS32(f)
        num_shaders = readS32(f)
        num_verts = readS32(f)
        num_triangles = readS32(f)
        ofs_triangles = readS32(f)
        ofs_shaders = readS32(f)
        ofs_st = readS32(f)
        ofs_xyznormal = readS32(f)
        ofs_end = readS32(f)
        # print("     ofs shaders: ", ofs_shaders+ofs_surface)
        f.seek(ofs_shaders+ofs_surface)
        shaders = []
        for _ in range(num_shaders):
            shaders.append(Shader.read(f))
        # print("     ofs triangles", ofs_triangles+ofs_surface)
        f.seek(ofs_triangles+ofs_surface)
        triangles = []
        for _ in range(num_triangles):
            triangles.append(Triangle.read(f))
        # print("     ofs st", ofs_st+ofs_surface)
        f.seek(ofs_st+ofs_surface)
        sts = []
        for _ in range(num_verts):
            sts.append(TexCoord.read(f))
        # print("     ofs xyznormal", ofs_xyznormal+ofs_surface)
        f.seek(ofs_xyznormal+ofs_surface)
        xyzs = []
        for _ in range(num_frames):
            tmp = []
            for _ in range(num_verts):
                tmp.append(Vertex.read(f))
            xyzs.append(tmp)

        # print("     ofs end", ofs_end+ofs_surface)
        return Surface(ident, name, flags, num_frames, num_shaders, num_verts,
                       num_triangles, ofs_triangles, ofs_shaders, ofs_st,
                       ofs_xyznormal, ofs_end, shaders, triangles, sts, xyzs)

    def write(self, f):
        writeS32(f, self.IDENT)
        writemax(f, self.NAME.encode("utf-8"), MAX_QPATH)
        writeS32(f, self.FLAGS)
        writeS32(f, self.NUM_FRAMES)
        writeS32(f, self.NUM_SHADERS)
        writeS32(f, self.NUM_VERTS)
        writeS32(f, self.NUM_TRIANGLES)
        writeS32(f, self.OFS_TRIANGLES)
        writeS32(f, self.OFS_SHADERS)
        writeS32(f, self.OFS_ST)
        writeS32(f, self.OFS_XYZNORMAL)
        writeS32(f, self.OFS_END)

        # print("offset shaders: ", self.OFS_SHADERS)
        # print("offset triangles: ", self.OFS_TRIANGLES)

        for triangle in self.triangles:
            triangle.write(f)

        for shader in self.shaders:
            shader.write(f)

        for st in self.st:
            st.write(f)

        for xyz in self.xyzs:
            for vert in xyz:
                vert.write(f)

    def writeWithoutOFS(self, f):
        start = f.tell()
        current_position = 0
        writeS32(f, self.IDENT)
        writemax(f, self.NAME.encode("utf-8"), MAX_QPATH)
        writeS32(f, self.FLAGS)
        writeS32(f, self.NUM_FRAMES)
        writeS32(f, self.NUM_SHADERS)
        writeS32(f, self.NUM_VERTS)
        writeS32(f, self.NUM_TRIANGLES)

        OFS_OFS_TRIANGLE = f.tell()  # REMEMBER THE POSITION FOR FUTURE EDIT
        writeS32(f, self.OFS_TRIANGLES)

        OFS_OFS_SHADERS = f.tell()  # REMEMBER THE POSITION FOR FUTURE EDIT
        writeS32(f, self.OFS_SHADERS)

        OFS_OFS_ST = f.tell()  # REMEMBER THE POSITION FOR FUTURE EDIT
        writeS32(f, self.OFS_ST)

        OFS_OFS_XYZ = f.tell()  # REMEMBER THE POSITION FOR FUTURE EDIT
        writeS32(f, self.OFS_XYZNORMAL)

        OFS_OFS_END = f.tell()  # REMEMBER THE POSITION FOR FUTURE EDIT
        writeS32(f, self.OFS_END)

        current_position = f.tell()
        f.seek(OFS_OFS_TRIANGLE)
        # print("     offset triangles: ", current_position)
        writeS32(f, current_position-start)
        f.seek(current_position)

        for triangle in self.triangles:
            triangle.write(f)

        current_position = f.tell()
        f.seek(OFS_OFS_SHADERS)
        # print("     offset shaders: ", current_position)
        writeS32(f, current_position-start)
        f.seek(current_position)

        for shader in self.shaders:
            shader.write(f)

        current_position = f.tell()
        f.seek(OFS_OFS_ST)
        # print("     offset st: ", current_position)
        writeS32(f, current_position-start)
        f.seek(current_position)

        for st in self.st:
            if st is not None:
                st.write(f)
            else:
                # print("SBog")
                TexCoord([0.0, 0.0]).write(f)

        current_position = f.tell()
        f.seek(OFS_OFS_XYZ)
        # print("     offset xyz: ", current_position)
        writeS32(f, current_position-start)
        f.seek(current_position)

        for xyz in self.xyzs:
            for vert in xyz:
                if vert is not None:
                    vert.write(f)
                else:
                    # print("VBog")
                    Vertex(0, 0, 0, [0.0, 0.0, 0.0]).write(f)

        current_position = f.tell()
        f.seek(OFS_OFS_END)
        # print("     offset end: ", current_position)
        writeS32(f, current_position-start)
        f.seek(current_position)
