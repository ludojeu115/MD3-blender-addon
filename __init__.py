# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
import bpy
from bpy.props import (
    StringProperty,
)
from bpy_extras.io_utils import (
    ImportHelper,
    ExportHelper,
)

bl_info = {
    "name": "DOOM MD3 format",
    "author": "ludojeu115",
    "description": "Import/export MD3, Import Mesh, UV's, Materials and animations as ShapeData",
    "blender": (3, 0, 0),
    "location": "File > Import-Export",
    "version": (0, 0, 1),
    "warning": "In development",
    "category": "Import-Export"
}

if "bpy" in locals():
    import importlib
    if "import_md3" in locals():
        importlib.reload(import_md3)  # noqa: F821
    if "export_md3" in locals():
        importlib.reload(export_md3)  # noqa: F821


class ImportMD3(bpy.types.Operator, ImportHelper):
    """Load a DOOM md3 File"""
    bl_idname = "import_scene.md3"
    bl_label = "Import MD3"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".md3"
    filter_glob: StringProperty(
        default="*.md3",
        options={'HIDDEN'},
    )

    def execute(self, context):
        # print("Selected: " + context.active_object.name)
        from . import import_md3

        keywords = self.as_keywords(
            ignore=(
                "filter_glob",
            ),
        )

        if bpy.data.is_saved and context.preferences.filepaths.use_relative_paths:
            import os
            keywords["relpath"] = os.path.dirname(bpy.data.filepath)

        return import_md3.main(context, **keywords)

    def draw(self, context):
        pass


class ExportMD3(bpy.types.Operator, ExportHelper):
    """Save a DOOM md3 File"""

    bl_idname = "export_scene.md3"
    bl_label = 'Export md3'
    bl_options = {'PRESET'}

    filename_ext = ".md3"
    filter_glob: StringProperty(
        default="*.md3;",
        options={'HIDDEN'},
    )

    check_extension = True

    def execute(self, context):
        from . import export_md3

        keywords = self.as_keywords(
            ignore=(
                "check_existing",
                "filter_glob",
            ),
        )

        return export_md3.main(context, **keywords)

    def draw(self, context):
        pass


def menu_func_import(self, context):
    self.layout.operator(ImportMD3.bl_idname, text="DOOM MODEL (.md3)")


def menu_func_export(self, context):
    self.layout.operator(ExportMD3.bl_idname, text="DOOM MODEL (.md3)")


classes = (
    ImportMD3,
    ExportMD3,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
