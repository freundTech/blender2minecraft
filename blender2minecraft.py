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

import bpy
from bpy import context
import bmesh
import os
import math
import json
from collections import OrderedDict

x = 0
y = 1
z = 2

toRound = 2

# ExportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
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
        return self.write_to_file(context, self.filepath, self.include_textures, self.ambientocclusion, self.minify,
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


    def getMaxMin(self, values, axis):
        max = [None]*len(axis)
        min = [None]*len(axis)
        for u in range(0, len(axis)):
            max[u] = float('-inf')
            min[u] = float('inf')

        for value in values:
            for u in range(0, len(axis)):
                if value[axis[u]] > max[u]:
                    max[u] = value[axis[u]]
                if value[axis[u]] < min[u]:
                    min[u] = value[axis[u]]

        for u in range(0, len(axis)):
            max[u] = round(max[u], toRound)
            min[u] = round(min[u], toRound)
        return max, min

    def getIndex(self, values, mask, axis):
        for value in values:
            if round(value[axis[0]], toRound) == mask[0] and round(value[axis[1]], toRound) == mask[1]:
                return values.index(value)
        raise Exception("Value not found")

    def roundValue(self, num):
        return round(num, toRound)

    def getDir(self, face):
        normals = []
        for i in range(0, len(face.loops)):
            normals.append(list(face.loops[i].vert.normal))

        top = 0
        bottom = 0
        north = 0
        south = 0
        east = 0
        west = 0

        for i in range(0, len(normals)):
            if normals[i][x] >= 0:
                east += 1
            else:
                west += 1
            if normals[i][y] >= 0:
                 north += 1
            else:
                south += 1
            if normals[i][z] >= 0:
                top += 1
            else:
                bottom += 1

        if top == 4:
            return ["up", [x, y]]
        if bottom == 4:
            return ["down", [x, y]]
        if north == 4:
            return ["north", [x, z]]
        if south == 4:
            return ["south", [x, z]]
        if east == 4:
            return ["east", [y, z]]
        if west == 4:
            return ["west", [y, z]]
        raise Exception("This should never happen")

    class attrdict(dict):
        def __init__(self, *args, **kwargs):
            dict.__init__(self, *args, **kwargs)
            self.__dict__ = self

    def write_to_file(self, context, filepath, include_textures, ambientocclusion, minify,
                    first_left_trans, first_left_scale, first_left_rot,
                    first_right_trans, first_right_scale, first_right_rot,
                    third_left_trans, third_left_scale, third_left_rot,
                    third_right_trans, third_right_scale, third_right_rot,
                    invtrans, invscale, invrot,
                    headtrans, headscale, headrot,
                    groundtrans, groundscale, groundrot,
                    fixedtrans, fixedscale, fixedrot):
        textures = []
        particle = ""
        scene = context.scene
        objects = scene.objects

        file = open(filepath,'w', encoding='utf-8')

        fileContent = OrderedDict()

        fileContent["__comment"] = "This model was created with freundTech's Blender2Minecraft converter (BETA)"
        fileContent["ambientocclusion"] = ambientocclusion
        fileContent["elements"] = []

        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')

        for obj in objects:
            if obj.type == 'MESH':

                data = obj.data
                bm = bmesh.new()
                bm.from_mesh(data)
                uv_layer = bm.loops.layers.uv.active

                if len(bm.faces) == 6:
                    box = []
                    for i in range(0, len(obj.bound_box)):
                        box.append([])
                        for j in range(0, len(obj.bound_box[i])):
                            box[i].append(obj.bound_box[i][j])
                    pos = obj.location
                    scale = obj.scale

                    for co in box:
                        for i in range(0, 3):
                            co[i] *= scale[i]
                            co[i] += pos[i]
                            co[i] *= 16
                        co[x] += 8
                        co[y] = (co[y]) * -1 + 8

                    toCoord, fromCoord = self.getMaxMin(box, [x, y, z])
                    print(toCoord)
                    print(fromCoord)

                    objname = [""]
                    for c in obj.name:
                        if c != '.':
                            objname[len(objname)-1] += c
                        else:
                            objname.append("")

                    item = {}

                    item["__comment"] = objname[0]
                    item["from"] = [self.roundValue(fromCoord[x]), self.roundValue(fromCoord[z]), self.roundValue(fromCoord[y])]
                    item["to"] = [self.roundValue(toCoord[x]), self.roundValue(toCoord[z]), self.roundValue(toCoord[y])]

                    rotation = [round(math.degrees(a), 1) for a in obj.rotation_euler]
                    notnull = 0
                    for i in range(0, len(rotation)):
                        while rotation[i] >= 360:
                            rotation[i] -= 360
                    for r in rotation:
                        if r != 0:
                            notnull += 1
                            axis = rotation.index(r)
                    if notnull > 1:
                        raise Exception("Only one Axis can be rotated at a time!")
                    elif notnull == 1:
                        if rotation[axis] == -22.5 or rotation[axis] == 22.5 or rotation[axis] == -45 or rotation[axis] == 45:
                            item["rotation"] = { "origin": [self.roundValue(pos[x]*16+8), self.roundValue(pos[z]*16), self.roundValue(pos[y]*-16+8)] }

                            axisStr = "none"
                            if axis == 0:
                                axisStr = "x"
                            elif axis == 1:
                                axisStr = "z"
                                rotation[axis] *= -1
                            elif axis == 2:
                                axisStr = "y"
                            item["rotation"]["axis"] = axisStr
                            item["rotation"]["angle"] = rotation[axis]

                            for n in objname:
                                if n[0:8] == "rescale:":
                                    item["rotation"]["rescale"] = n[8:].lower() == "true"
                        else:
                            raise Exception("You can only rotate by 22.5, -22.5, 45 or -45 degrees!")

                    item["faces"] = {}

                    for face in bm.faces:
                        if len(face.loops) == 4:
                            direction, toUse = self.getDir(face)

                            try:
                                uvs = []
                                for i in range(0, len(face.loops)):
                                    uvs.append([face.loops[i][uv_layer].uv[x] * 16, face.loops[i][uv_layer].uv[y] * 16])
                            except AttributeError:
                                uvs = [[16, 16], [0, 16], [0, 0], [16, 0]]

                            max, min = self.getMaxMin(uvs, [x, y])

                            if min[x] != max[x] and min[y] != max[y]:

                                verts = []
                                for i in range(0, len(face.loops)):
                                    verts.append([face.loops[i].vert.co[x] * 16, face.loops[i].vert.co[y] * 16, face.loops[i].vert.co[z] * 16])
                                maxr, minr = self.getMaxMin(verts, toUse)

                                if direction == "south":
                                    bottom = minr
                                elif direction == "east":
                                    bottom = minr
                                elif direction == "up":
                                    bottom = minr
                                elif direction == "down":
                                    bottom = [minr[0], maxr[1]]
                                elif direction == "north":
                                    bottom = [maxr[0], minr[1]]
                                elif direction == "west":
                                    bottom = [maxr[0], minr[1]]

                                minI = self.getIndex(verts, bottom, toUse)

                                minUv = list(uvs[minI])
                                for i in range(0, len(minUv)):
                                    minUv[i] = round(minUv[i], toRound)

                                nextI = minI + 1
                                while nextI >= 4:
                                    nextI -= 4

                                nextUv = list(uvs[nextI])
                                for i in range(0, len(nextUv)):
                                    nextUv[i] = round(nextUv[i], toRound)

                                if minUv == min and nextUv == [max[x], min[y]]:
                                    rot = 0
                                    mirror = False
                                elif minUv == [max[x], min[y]] and nextUv == max:
                                    rot = 90
                                    mirror = False
                                elif minUv == max and nextUv == [min[x], max[y]]:
                                    rot = 180
                                    mirror = False
                                elif minUv == [min[x], max[y]] and nextUv == min:
                                    rot = 270
                                    mirror = False
                                elif minUv == [max[x], min[y]] and nextUv == min:
                                    rot = 0
                                    mirror = True
                                elif minUv == max and nextUv == [max[x], min[y]]:
                                    rot = 270
                                    mirror = True
                                elif minUv == [min[x], max[y]] and nextUv == max:
                                    rot = 180
                                    mirror = True
                                elif minUv == min and nextUv == [min[x], max[y]]:
                                    rot = 90
                                    mirror = True
                                else:
                                    raise Exception("Your UV is messed up")

                                try:
                                    image = data.uv_textures.active.data[face.index].image
                                except AttributeError:
                                    image = attrdict(name=["texture"], filepath="")

                                name = [""]
                                for c in image.name:
                                    if c != '.':
                                        name[len(name)-1] += c
                                    else:
                                        name.append("")

                                path = [""]
                                filepath = ""
                                imagepath = bpy.path.abspath(image.filepath)
                                imagepath = os.path.abspath(imagepath)

                                path = imagepath.split(os.sep)

                                for dir in path:
                                    index = path.index(dir)
                                    if dir == "assets" and path[index+1] == "minecraft" and path[index+2] == "textures":
                                        for i in range(index+3, len(path)-1):
                                            filepath += path[i]
                                            filepath += "/"

                                        for c in path[len(path)-1]:
                                            if c != '.':
                                                filepath += c
                                            else:
                                                break

                                if not [name[0], filepath] in textures:
                                    textures.append([name[0], filepath])

                                s = max[y]

                                max[y] = (min[y]- 8)*-1+8
                                min[y] = (s- 8)*-1+8

                                item["faces"][direction] = {}

                                if not mirror:
                                    item["faces"][direction]["uv"] = [min[x], min[y], max[x], max[y]]
                                    item["faces"][direction]["texture"] = "#" + name[0]
                                    item["faces"][direction]["rotation"] = rot
                                else:
                                    item["faces"][direction]["uv"] = [max[x], min[y], min[x], max[y]]
                                    item["faces"][direction]["texture"] = "#" + name[0]
                                    item["faces"][direction]["rotation"] = rot

                                for n in name:
                                    if n[0:9] == "cullface:":
                                        item["faces"][direction]["cullface"] = n[9:]
                                    elif n[0:8] == "cullface":
                                        item["faces"][direction]["cullface"] = direction
                                    elif n[0:10] == "tintindex:":
                                        item["faces"][direction]["tintindex"] = int(n[10:])
                                    elif n[0:9] == "tintindex":
                                        item["faces"][direction]["tintindex"] = 1
                                    elif n[0:8] == "particle":
                                        particle = filepath

                        else:
                            print("Object \"" + data.name + "\" is not a cube!!!")

                    fileContent["elements"].append(item)

                else:
                    print("Object \"" + data.name + "\" is not a cube!")

        if include_textures:
            fileContent["textures"] = {}

            for texture in textures:
                fileContent["textures"][texture[0]] = 'blocks/' + texture[0]

            if particle != "":
                fileContent["textures"]["particle"] = particle

        fileContent["display"] = {
            "firstperson_lefthand": {
                "rotation": [self.roundValue(first_left_rot[x]), self.roundValue(first_left_rot[y]), self.roundValue(first_left_rot[z])],
                "translation": [self.roundValue(first_left_trans[x]), self.roundValue(first_left_trans[y]), self.roundValue(first_left_trans[z])],
                "scale": [self.roundValue(first_left_scale[x]), self.roundValue(first_left_scale[y]), self.roundValue(first_left_scale[z])]
            },
            "firstperson_righthand": {
                "rotation": [self.roundValue(first_right_rot[x]), self.roundValue(first_right_rot[y]), self.roundValue(first_right_rot[z])],
                "translation": [self.roundValue(first_right_trans[x]), self.roundValue(first_right_trans[y]), self.roundValue(first_right_trans[z])],
                "scale": [self.roundValue(first_right_scale[x]), self.roundValue(first_right_scale[y]), self.roundValue(first_right_scale[z])]
            },
            "thirdperson_righthand": {
                "rotation": [self.roundValue(third_right_rot[x]), self.roundValue(third_right_rot[y]), self.roundValue(third_right_rot[z])],
                "translation": [self.roundValue(third_right_trans[x]), self.roundValue(third_right_trans[y]), self.roundValue(third_right_trans[z])],
                "scale": [self.roundValue(third_right_scale[x]), self.roundValue(third_right_scale[y]), self.roundValue(third_right_scale[z])]
            },
            "thirdperson_lefthand": {
                "rotation": [self.roundValue(third_left_rot[x]), self.roundValue(third_left_rot[y]), self.roundValue(third_left_rot[z])],
                "translation": [self.roundValue(third_left_trans[x]), self.roundValue(third_left_trans[y]), self.roundValue(third_left_trans[z])],
                "scale": [self.roundValue(third_left_scale[x]), self.roundValue(third_left_scale[y]), self.roundValue(third_left_scale[z])]
            },
            "gui": {
                "rotation": [self.roundValue(invrot[x]), self.roundValue(invrot[y]), self.roundValue(invrot[z])],
                "translation": [self.roundValue(invtrans[x]), self.roundValue(invtrans[y]), self.roundValue(invtrans[z])],
                "scale": [self.roundValue(invscale[x]), self.roundValue(invscale[y]), self.roundValue(invscale[z])]
            },
            "head": {
                "rotation": [self.roundValue(headrot[x]), self.roundValue(headrot[y]), self.roundValue(headrot[z])],
                "translation": [self.roundValue(headtrans[x]), self.roundValue(headtrans[y]), self.roundValue(headtrans[z])],
                "scale": [self.roundValue(headscale[x]), self.roundValue(headscale[y]), self.roundValue(headscale[z])]
            },
            "ground": {
                "rotation": [self.roundValue(groundrot[x]), self.roundValue(groundrot[y]), self.roundValue(groundrot[z])],
                "translation": [self.roundValue(groundtrans[x]), self.roundValue(groundtrans[y]), self.roundValue(groundtrans[z])],
                "scale": [self.roundValue(groundscale[x]), self.roundValue(groundscale[y]), self.roundValue(groundscale[z])]
            },
            "fixed": {
                "rotation": [self.roundValue(fixedrot[x]), self.roundValue(fixedrot[y]), self.roundValue(fixedrot[z])],
                "translation": [self.roundValue(fixedtrans[x]), self.roundValue(fixedtrans[y]), self.roundValue(fixedtrans[z])],
                "scale": [self.roundValue(fixedscale[x]), self.roundValue(fixedscale[y]), self.roundValue(fixedscale[z])]
            }
        }

        if(minify):
            file.write(json.dumps(fileContent, separators=(',', ':'), sort_keys=False))
        else:
            file.write(json.dumps(fileContent, indent=4, sort_keys=False))

        file.close()

        return {'FINISHED'}

def menu_func_export(self, context):
    self.layout.operator(ExportBlockModel.bl_idname, text="Minecraft model (.json)")

def register():
    bpy.utils.register_class(ExportBlockModel)
    bpy.types.INFO_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_class(ExportBlockModel)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()

    # test call
    bpy.ops.export_mc.blockmodel('INVOKE_DEFAULT')
