import math
import bpy
from numpy import amin, amax
from . import Utilities as ut

if "ut" in locals():
    import importlib
    importlib.reload(ut)


def bounding_box(data):
    new_arrangement = [[key.co.x, key.co.y, key.co.z] for key in data]
    min = amin(new_arrangement, axis=0)
    max = amax(new_arrangement, axis=0)
    return min, max

    # return [(min, min, min), (min, min, max), (min, max, min),
    #         (min, max, max), (max, min, min), (max, min, max),
    #         (max, max, min), (max, max, max)]
    # rien à voir avec cette fonction


def export(obj, filepath):
    Frames = []
    Tags = []
    current_position = 0
    IDENT = 860898377

    VERSION = 15
    exportFile = open(filepath,
                      "w+b")

    # print("MD3 export")
    # print("Started exporting : ", obj.name)
    # print()
    # print("Exporting simple values ...")
    # print()

    ut.writeS32(exportFile, IDENT)
    ut.writeS32(exportFile, VERSION)
    # use object name as file name
    ut.writemax(exportFile, (obj.name.rsplit('.', 1)[0]+".md3")
                .encode("utf-8"), ut.MAX_QPATH)

    FLAGS = 0  # DONT KNOW HOW TO IMPLEMENT THIS YET
    # AND DON'T KNOW HOW IT IS USED
    ut.writeS32(exportFile, FLAGS)
    NUM_FRAMES = len(obj.data.shape_keys.key_blocks)
    ut.writeS32(exportFile, NUM_FRAMES)
    NUM_TAGS = 0  # LIKE FOR FLAGS, DONT KNOW HOW TO IMPLEMENT THIS YET
    ut.writeS32(exportFile, NUM_TAGS)
    NUM_SURFACES = len(obj.data.materials)
    ut.writeS32(exportFile, NUM_SURFACES)
    NUM_SKINS = 0  # DOCUMENTATION SAYS THIS IS NOT USED
    ut.writeS32(exportFile, NUM_SKINS)
    OFS_OFS_FRAMES = exportFile.tell()  # REMEMBER THE POSITION FOR FUTURE EDIT
    OFS_FRAMES = 0  # THIS IS A PLACEHOLDER
    ut.writeS32(exportFile, OFS_FRAMES)
    OFS_OFS_TAGS = exportFile.tell()  # REMEMBER THE POSITION FOR FUTURE EDIT
    OFS_TAGS = 0  # THIS IS A PLACEHOLDER
    ut.writeS32(exportFile, OFS_TAGS)
    OFS_OFS_SURFACES = exportFile.tell()  # REMEMBER THE POSITION FOR FUTURE
    OFS_SURFACES = 0  # THIS IS A PLACEHOLDER
    ut.writeS32(exportFile, OFS_SURFACES)
    OFS_OFS_EOF = exportFile.tell()  # REMEMBER THE POSITION FOR FUTURE EDIT
    OFS_EOF = 0  # THIS IS A PLACEHOLDER
    ut.writeS32(exportFile, OFS_EOF)

    # go replace the placeholder with the real value

    current_position = exportFile.tell()
    exportFile.seek(OFS_OFS_FRAMES)
    # print("OFS_FRAMES : ", current_position)
    ut.writeS32(exportFile, current_position)
    exportFile.seek(current_position)

    # print()
    # print("Exporting complex values")
    # print()

    # create the frames for writting

    for shape in obj.data.shape_keys.key_blocks:
        minim, maxim = bounding_box(shape.data)
        # print(minim, maxim)
        center = (minim + maxim) / 2.0
        radius = math.dist(minim, maxim)/2.0

        minim = [int(math.floor(a/ut.MD3_XYZ_SCALE)) for a in minim]
        maxim = [int(math.floor(a/ut.MD3_XYZ_SCALE)) for a in maxim]
        center = [int(math.floor(a/ut.MD3_XYZ_SCALE)) for a in center]
        # print(minim, maxim, center)
        min_bound = ut.Vec3(*minim)
        max_bound = ut.Vec3(*maxim)
        local_origin = ut.Vec3(*center)

        Frames.append(ut.Frame(min_bound, max_bound,
                               local_origin, radius, shape.name))

    for f in Frames:
        f.write(exportFile)

    # go replace the placeholder with the real value

    current_position = exportFile.tell()
    exportFile.seek(OFS_OFS_TAGS)
    # print("OFS_TAGS : ", current_position)
    ut.writeS32(exportFile, current_position)
    exportFile.seek(current_position)

    for t in Tags:  # like flags, dont know how to implement this yet
        t.write(exportFile)

    current_position = exportFile.tell()
    exportFile.seek(OFS_OFS_SURFACES)
    # print("OFS_SURFACES", current_position)
    ut.writeS32(exportFile, current_position)
    exportFile.seek(current_position)

    # write all surface into exportFile

    # Create an empty list named indexes and add an empty list for every
    # object material
    # then Loop through all polygons of obj, store each
    # vertices index in the list
    # corresponding to the polygon material_index

    indexes = []
    for i in range(len(obj.data.materials)):
        indexes.append([])
    for poly in obj.data.polygons:
        indexes[poly.material_index].extend(poly.vertices)

    # make sure every list dosen't contain duplicates and sort it
    for i in range(len(indexes)):
        indexes[i] = list(dict.fromkeys(indexes[i]))
        indexes[i].sort()
    num_mat = 0

    mat: bpy.types.Material

    uv = obj.data.uv_layers.active

    for id, mat in enumerate(obj.data.materials):
        # store number of node in num_shaders

        num_frames = len(obj.data.shape_keys.key_blocks)
        num_shaders = len(mat.node_tree.nodes)-2
        num_verts = len(indexes[num_mat])

        mat_triangles = [(idx, tri.vertices)
                         for idx, tri in enumerate(obj.data.polygons)
                         if tri.material_index == num_mat]
        sur_triangles = [ut.Triangle([indexes[num_mat].index(vtx)
                                      for vtx in tri])
                         for _, tri in mat_triangles]
        num_triangles = len(mat_triangles)

        shaders: list[ut.Shader] = []

        if num_shaders > 0:
            if mat.node_tree.nodes.get("Image Texture") is not None:
                shaders.append(ut.Shader(
                    mat.node_tree.nodes["Image Texture"].
                    image.filepath.rsplit("\\", 1)[-1], 0))

            nodes = [ut.Shader(node.name, node.outputs[0].default_value)
                     for node in mat.node_tree.nodes
                     if node.bl_idname == 'ShaderNodeValue']
            shaders.extend(nodes)
        sts = [None]*num_verts
        for i, tri in mat_triangles:
            sts[indexes[id].
                index(tri[0])] = ut.TexCoord(uv.data[i*3].uv)
            sts[indexes[id].
                index(tri[1])] = ut.TexCoord(uv.data[i*3+1].uv)

            sts[indexes[id].
                index(tri[2])] = ut.TexCoord(uv.data[i*3+2].uv)

        xyzs = []
        for idx, shape in enumerate(obj.data.shape_keys.key_blocks):
            shapedata = [None]*num_verts
            for i in range(len(shape.data)):
                if i in indexes[num_mat]:
                    vec = shape.data[i].co
                    shapedata[indexes[num_mat].index(i)] = ut.Vertex(
                        int(vec.x/ut.MD3_XYZ_SCALE),
                        int(vec.y/ut.MD3_XYZ_SCALE),
                        int(vec.z/ut.MD3_XYZ_SCALE),
                        obj.data.vertices[i].normal
                        )
            xyzs.append(shapedata)

        sur = ut.Surface(IDENT, mat.name.rsplit(".", 1)[0], 0,
                         num_frames,
                         num_shaders,
                         num_verts,
                         num_triangles,  # num_triangles TODO
                         0, 0, 0,
                         0, 0,
                         shaders,
                         sur_triangles,  # sur_triangles TODO
                         sts,
                         xyzs)  # TODO
        sur.writeWithoutOFS(exportFile)
        num_mat += 1

    current_position = exportFile.tell()
    exportFile.seek(OFS_OFS_EOF)
    # print("OFS_EOF:", current_position)
    ut.writeS32(exportFile, current_position)
    exportFile.seek(current_position)

    # print()
    # print("Exporting finished")
    # print()


def main(context,
         filepath,
         *,
         relpath=True,):
    obj = context.object
    if obj is not None and obj.type == 'MESH':
        export(obj, filepath)
        return {'FINISHED'}
