import bpy
import mathutils
from os.path import dirname, join
from . import Utilities as ut

if "ut" in locals():
    import importlib
    importlib.reload(ut)

verts: list[mathutils.Vector] = []
edges: list = []
faces: list = []


def create_alpha_material(name, image_path) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.blend_method = 'CLIP'
    mat.use_nodes = True
    node_tree = mat.node_tree
    node_tree.nodes.clear()
    node_output = node_tree.nodes.new(type="ShaderNodeOutputMaterial")
    node_principal = node_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    # print("image path: " + image_path)

    node_texture = node_tree.nodes.new(type="ShaderNodeTexImage")
    node_texture.interpolation = 'Closest'
    try:
        node_texture.image = bpy.data.images.load(image_path)
        node_tree.links.new(node_texture.outputs['Color'],
                            node_principal.inputs['Base Color'])
        node_tree.links.new(node_texture.outputs['Alpha'],
                            node_principal.inputs['Alpha'])
    except Exception:
        mat.node_tree.nodes.remove(node_texture)
        node_value = node_tree.nodes.new(type="ShaderNodeValue")
        node_value.name = image_path
        node_value.outputs['Value'].default_value = 0.0

    node_tree.links.new(node_principal.outputs['BSDF'],
                        node_output.inputs['Surface'])

    return mat


def main(context,
         filepath,
         *,
         relpath=None,
         ):
    # print()
    # print("Started importing : ", filepath)
    # print()

    file = open(filepath, "rb")
    _ = ut.readS32(file)
    _ = ut.readS32(file)

    NAME = ut.readmax(file, ut.MAX_QPATH)
    # print(NAME)

    FLAGS = ut.readS32(file)
    # print("FLAGS : ", FLAGS)
    NUM_FRAMES = ut.readS32(file)
    # print("num frames : ", NUM_FRAMES)

    NUM_TAGS = ut.readS32(file)
    # print("num tags : ", NUM_TAGS)

    NUM_SURFACES = ut.readS32(file)
    # print("num surfaces :", NUM_SURFACES)

    _ = ut.readS32(file)
    OFS_FRAMES = ut.readS32(file)
    OFS_TAGS = ut.readS32(file)
    OFS_SURFACES = ut.readS32(file)
    OFS_EOF = ut.readS32(file)

    # print("ofs frames : ", OFS_FRAMES)
    # print("ofs tags : ", OFS_TAGS)
    # print("ofs surfaces : ", OFS_SURFACES)
    # print("ofs eof : ", OFS_EOF)

    file.seek(OFS_FRAMES)
    Frames: list[ut.Frame] = []
    for _ in range(min(NUM_FRAMES, ut.MD3_MAX_FRAMES)):
        Frames.append(ut.Frame.read(file))

    file.seek(OFS_TAGS)
    Tags: list[ut.Tag] = []
    for _ in range(min(NUM_TAGS, ut.MD3_MAX_TAGS)):
        Tags.append(ut.Tag.read(file))
        # print("ut.Tag name :", Tags[-1].NAME)

    file.seek(OFS_SURFACES)
    surface: list[ut.Surface] = []
    for _ in range(min(NUM_SURFACES, ut.MD3_MAX_SURFACES)):
        surface.append(ut.Surface.read(file, OFS_SURFACES))
        OFS_SURFACES += surface[-1].OFS_END

    # create the starting model data
    ofs: int = 0
    for sur in surface:

        for xy in sur.xyzs[0]:
            verts.append(mathutils
                         .Vector((float(xy.x*ut.MD3_XYZ_SCALE),
                                  float(xy.y*ut.MD3_XYZ_SCALE),
                                  float(xy.z*ut.MD3_XYZ_SCALE))))

        for tri in sur.triangles:
            edges.append([tri.indexes[0]+ofs, tri.indexes[1]+ofs])
            edges.append([tri.indexes[1]+ofs, tri.indexes[2]+ofs])
            edges.append([tri.indexes[2]+ofs, tri.indexes[0]+ofs])

            faces.append([tri.indexes[0]+ofs, tri.indexes[1]+ofs,
                          tri.indexes[2]+ofs])

        ofs = ofs + sur.NUM_VERTS

    # Initialize the blender object

    obj_name = NAME.rsplit('.', 1)[0]
    mesh_data: bpy.types.Mesh = bpy.data.meshes.new(obj_name + "_data")
    obj: bpy.types.Object = bpy.data.objects.new(obj_name, mesh_data)
    bpy.context.scene.collection.objects.link(obj)
    mesh_data.from_pydata(verts, edges, faces)

    # create the shapekeys

    sk_basis = obj.shape_key_add(name=Frames[0].NAME)
    sk_basis.interpolation = 'KEY_LINEAR'
    obj.data.shape_keys.use_relative = False
    for f in range(1, len(Frames)):
        sk = obj.shape_key_add(name=Frames[f].NAME)
        sk.interpolation = 'KEY_LINEAR'

        i = 0

        for sur in surface:
            for xy in sur.xyzs[f]:
                sk.data[i].co = mathutils.Vector((
                    float(xy.x*ut.MD3_XYZ_SCALE),
                    float(xy.y*ut.MD3_XYZ_SCALE),
                    float(xy.z*ut.MD3_XYZ_SCALE)))
                i += 1

    # Map UV and materials to the mesh

    uv = obj.data.uv_layers.new()

    i = 0
    ofs = 0
    for idx, sur in enumerate(surface):

        # UV mapping

        for tri in sur.triangles:
            uv.data[i].uv = sur.st[tri.indexes[0]].st
            uv.data[i+1].uv = sur.st[tri.indexes[1]].st
            uv.data[i+2].uv = sur.st[tri.indexes[2]].st
            i += 3

        # Create materials

        path = join(dirname(filepath), sur.shaders[0].name)
        mat = create_alpha_material(sur.NAME, path)
        obj.data.materials.append(mat)
        for sh in sur.shaders[1:]:
            node = mat.node_tree.nodes.new(type='ShaderNodeValue')
            node.outputs[0].default_value = sh.VALUE
            node.name = sh.name

        # Assign materials to vertex
        for t in range(sur.NUM_TRIANGLES):
            obj.data.polygons[t+ofs].material_index = idx

        ofs += sur.NUM_TRIANGLES

    normals = []
    vertexes = [sur.xyzs[0] for sur in surface]
    for v1 in vertexes:
        for v2 in v1:
            normals.append(v2.normal)

    obj.data.normals_split_custom_set_from_vertices(normals)

    print("Importing done")
    print()
    return {'FINISHED'}