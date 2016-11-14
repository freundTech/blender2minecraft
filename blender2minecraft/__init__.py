bl_info = {
    "name": "Blender2Minecraft",
    "author": "freundTech",
    "version": (0, 3),
    "blender": (2, 6, 9),
    "location": "File > Export > Export to Minecraft",
    "description": "Export Scene as Minecraft Blockmodel",
    "wiki_url": "https://github.com/freundTech/blender2minecraft/wiki",
    "tracker_url": "https://github.com/freundTech/blender2minecraft/issues",
    "support": "COMMUNITY",
    "category": "Import-Export"
}

if "bpy" in locals():
    import imp
    imp.reload(export)
    print("Reloaded multifiles")
else:
    from . import export
    print("Imported multifiles")

import bpy
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, FloatProperty
from bpy.types import Operator


class ExportBlockModel(Operator, ExportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "export_mc.blockmodel"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export Scene as Minecraft Blockmodel"

    filename_ext = ".json"

    filter_glob = StringProperty(
            default="*.json",
            options={'HIDDEN'},
            )
    include_textures = BoolProperty(
            name="Include Textures",
            description="Includes the texturepaths into the models",
            default=True,
            )
    ambientocclusion = BoolProperty(
            name="Use Ambient Occlusion",
            description="Turns the Ambient Occlusion option on or off",
            default=True,
            )
    minify = BoolProperty(
            name="Minify Json",
            description="Reduces size of exported .json by omitting redundant whitespaces",
            default=True,
            )

    fplTransform = bpy.props.FloatVectorProperty(
        name = "First Person Left Hand Transform",
        description = "Translation, Rotation and Scale of first person (in left hand) rendering",
        size = 9,
        default=[0.0, 0.0, 0.0,
                 0.0, 45.0, 0.0,
                 0.4, 0.4, 0.4
                ]
    )
    fprTransform = bpy.props.FloatVectorProperty(
        name = "First Person Right Hand Transform",
        description = "Translation, Rotation and Scale of first person (in right hand) rendering",
        size = 9,
        default=[0.0, 0.0, 0.0,
                 0.0, 45.0, 0.0,
                 0.4, 0.4, 0.4
                ]
    )
    tplTransform = bpy.props.FloatVectorProperty(
        name = "Third Person Left Hand Transform",
        description = "Translation, Rotation and Scale of third person (in left hand) rendering",
        size = 9,
        default=[0.0, 2.5, 0.0,
                 75.0, 45.0, 0.0,
                 0.375, 0.375, 0.375
                ]
    )
    tprTransform = bpy.props.FloatVectorProperty(
        name = "Third Person Right Hand Transform",
        description = "Translation, Rotation and Scale of third person (in right hand) rendering",
        size = 9,
        default=[0.0, 2.5, 0.0,
                 75.0, 45.0, 0.0,
                 0.375, 0.375, 0.375
                ]
    )
    guiTransform = bpy.props.FloatVectorProperty(
        name = "GUI Transform",
        description = "Translation, Rotation and Scale in the GUI (Inventory)",
        size = 9,
        default=[0.0, 0.0, 0.0,
                 30.0, 225.0, 0.0,
                 0.35, 0.35, 0.35
                ]
    )
    headTransform = bpy.props.FloatVectorProperty(
        name = "Head Transform",
        description = "Translation, Rotation and Scale when equipped as helmet",
        size = 9,
        default=[0.0, 0.0, 0.0,
                 0.0, 0.0, 0.0,
                 1.0, 1.0, 1.0])
    groundTransform = bpy.props.FloatVectorProperty(
        name = "Ground Transform",
        description = "Translation, Rotation and Scale on the ground",
        size = 9,
        default=[0.0, 3.0, 0.0,
                 0.0, 0.0, 0.0,
                 0.25, 0.25, 0.25
                ]
    )
    fixedTransform = bpy.props.FloatVectorProperty(
        name = "Item Frame Transform",
        description = "Translation, Rotation and Scale in Item Frames",
        size = 9,
        default=[0.0, 0.0, 0.0,
                 0.0, 0.0, 0.0,
                 0.5, 0.5, 0.5
                ]
    )

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        # Create a simple row.
        layout.label(text="Textures:")
        row = layout.row()
        row.prop(self, "include_textures")

        layout.label(text="Ambient Occlusion:")
        row = layout.row()
        row.prop(self, "ambientocclusion")

        layout.label(text="Minify Json:")
        row = layout.row()
        row.prop(self, "minify")

        def createTransform(name, value):
            layout.label()
            layout.label(text=name)
            split = layout.split()
            col = split.column(align=True)
            col.label(text="Translate:")
            col.prop(self, value, index=0, text="X")
            col.prop(self, value, index=1, text="Y")
            col.prop(self, value, index=2, text="Z")

            col = split.column(align=True)
            col.label(text="Rotate:")
            col.prop(self, value, index=3, text="X")
            col.prop(self, value, index=4, text="Y")
            col.prop(self, value, index=5, text="Z")

            col = split.column(align=True)
            col.label(text="Scale:")
            col.prop(self, value, index=6, text="X")
            col.prop(self, value, index=7, text="Y")
            col.prop(self, value, index=8, text="Z")

        createTransform("First Person - Left hand :", "fplTransform")
        createTransform("First Person - Right hand :", "fprTransform")
        createTransform("Third Person - Left hand:", "tplTransform")
        createTransform("Third Person - Right hand:", "tprTransform")
        createTransform("Inventory:", "guiTransform")
        createTransform("Head:", "headTransform")
        createTransform("Ground:", "groundTransform")
        createTransform("Item Frame:", "fixedTransform")

    def execute(self, context):
        print(dir(export))

        #do the export
        #TODO: What was I thinking when writing that function signature
        return export.write_to_file(context, self.filepath, self.include_textures, self.ambientocclusion, self.minify,
                self.fplTransform[0:3],
                self.fplTransform[6:9],
                self.fplTransform[3:6],
                self.fprTransform[0:3],
                self.fprTransform[6:9],
                self.fprTransform[3:6],
                self.tplTransform[0:3],
                self.tplTransform[6:9],
                self.tplTransform[3:6],
                self.tprTransform[0:3],
                self.tprTransform[6:9],
                self.tprTransform[3:6],
                self.guiTransform[0:3],
                self.guiTransform[6:9],
                self.guiTransform[3:6],
                self.headTransform[0:3],
                self.headTransform[6:9],
                self.headTransform[3:6],
                self.groundTransform[0:3],
                self.groundTransform[6:9],
                self.groundTransform[3:6],
                self.fixedTransform[0:3],
                self.fixedTransform[6:9],
                self.fixedTransform[3:6])


def menu_func_export(self, context):
    self.layout.operator(ExportBlockModel.bl_idname, text="Minecraft model (.json)")

def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()

    # test call
    bpy.ops.export_mc.blockmodel('INVOKE_DEFAULT')
