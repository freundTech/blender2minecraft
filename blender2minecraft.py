bl_info = {
    "name": "Blender2Minecraft",
    "author": "freundTech",
    "version": (0, 1),
    "blender": (2, 7, 9),
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

x = 0
y = 1
z = 2

toRound = 2

def getMaxMin(values, use):
    max = [None]*len(use)
    min = [None]*len(use)
    for u in range(0, len(use)):
        max[u] = float('-inf')
        min[u] = float('inf')

    for value in values:
        for u in range(0, len(use)):
            if value[use[u]] > max[u]:
                max[u] = value[use[u]]
            if value[use[u]] < min[u]:
                min[u] = value[use[u]]

    for u in range(0, len(use)):
        max[u] = round(max[u], toRound)
        min[u] = round(min[u], toRound)
    return [max, min]

def getIndex(values, mask, toUse):
    for value in values:
        if round(value[toUse[0]], toRound) == mask[0] and round(value[toUse[1]], toRound) == mask[1]:
            return values.index(value)
    raise Exception("Value not found")

def rval(num):
    return round(num, toRound)

def getDir(face):
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

def write_to_file(context, filepath, include_textures, ambientocclusion, minify,
                firsttrans, firstscale, firstrot,
                thirdtrans, thirdscale, thirdrot,
                invtrans, invscale, invrot,
                headtrans, headscale, headrot,
                groundtrans, groundscale, groundrot,
                fixedtrans, fixedscale, fixedrot):
    textures = []
    particle = ""
    scene = context.scene
    objects = scene.objects

    file = open(filepath,'w', encoding='utf-8')

    fileContent = {}

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
                #print(str(obj.bound_box[0][:]) + " " + str(obj.bound_box[1][:]) + " " + str(obj.bound_box[2][:]) + str(obj.bound_box[3][:]) + " " + str(obj.bound_box[4][:]) + " " + str(obj.bound_box[5][:]) + " " + str(obj.bound_box[6][:]) + " " + str(obj.bound_box[7][:]) + " ")

                for co in box:
                    for i in range(0, 3):
                        co[i] *= scale[i]
                        co[i] += pos[i]
                        co[i] *= 16
                    co[x] += 8
                    co[y] = (co[y]) * -1 + 8

                #print(nl + nl)
                #print(box[:][:])
                toCoord, fromCoord = getMaxMin(box, [x, y, z])
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
                item["from"] = [rval(fromCoord[x]), rval(fromCoord[z]), rval(fromCoord[y])]
                item["to"] = [rval(toCoord[x]), rval(toCoord[z]), rval(toCoord[y])]

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
                        item["rotation"] = { "origin": [rval(pos[x]*16+8), rval(pos[z]*16), rval(pos[y]*16+8)] }

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
                        direction, toUse = getDir(face)

                        try:
                            uvs = []
                            for i in range(0, len(face.loops)):
                                uvs.append([face.loops[i][uv_layer].uv[x] * 16, face.loops[i][uv_layer].uv[y] * 16])
                        except AttributeError:
                            uvs = [[16, 16], [0, 16], [0, 0], [16, 0]]

                        max, min = getMaxMin(uvs, [x, y])

                        if min[x] != max[x] and min[y] != max[y]:

                            verts = []
                            for i in range(0, len(face.loops)):
                                verts.append([face.loops[i].vert.co[x] * 16, face.loops[i].vert.co[y] * 16, face.loops[i].vert.co[z] * 16])
                                print(face.loops[i].vert.co)
                            maxr, minr = getMaxMin(verts, toUse)

                            print(maxr)
                            print(minr)

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

                            print(bottom)
                            print(verts)
                            minI = getIndex(verts, bottom, toUse)

                            print(minI)
                            print(uvs)
                            print(verts)
                            print(toUse)
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
                                print(minUv)
                                print(min)
                                print(nextUv)
                                print(max)
                                raise Exception("Your UV is messed up")

                            print(rot)
                            print(mirror)

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

                            print(name)

                            print(direction)
                            print(minUv)
                            print(nextUv)
                            print(max)
                            print(min)

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
                #TODO
                fileContent["elements"].append(item)

            else:
                print("Object \"" + data.name + "\" is not a cube!")

    if include_textures:
        fileContent["textures"] = {}

        for texture in textures:
            fileContent["textures"][texture[0]] = texture[1]

        if particle != "":
            fileContent["textures"]["particle"] = particle

    fileContent["display"] = {
        "firstperson": {
            "rotation": [rval(firstrot[x]), rval(firstrot[y]), rval(firstrot[z])],
            "translation": [rval(firsttrans[x]), rval(firsttrans[y]), rval(firsttrans[z])],
            "scale": [rval(firstscale[x]), rval(firstscale[y]), rval(firstscale[z])]
        },
        "thirdperson": {
            "rotation": [rval(thirdrot[x]), rval(thirdrot[y]), rval(thirdrot[z])],
            "translation": [rval(thirdtrans[x]), rval(thirdtrans[y]), rval(thirdtrans[z])],
            "scale": [rval(thirdscale[x]), rval(thirdscale[y]), rval(thirdscale[z])]
        },
        "gui": {
            "rotation": [rval(invrot[x]), rval(invrot[y]), rval(invrot[z])],
            "translation": [rval(invtrans[x]), rval(invtrans[y]), rval(invtrans[z])],
            "scale": [rval(invscale[x]), rval(invscale[y]), rval(invscale[z])]
        },
        "head": {
            "rotation": [rval(headrot[x]), rval(headrot[y]), rval(headrot[z])],
            "translation": [rval(headtrans[x]), rval(headtrans[y]), rval(headtrans[z])],
            "scale": [rval(headscale[x]), rval(headscale[y]), rval(headscale[z])]
        },
        "ground": {
            "rotation": [rval(groundrot[x]), rval(groundrot[y]), rval(groundrot[z])],
            "translation": [rval(groundtrans[x]), rval(groundtrans[y]), rval(groundtrans[z])],
            "scale": [rval(groundscale[x]), rval(groundscale[y]), rval(groundscale[z])]
        },
        "fixed": {
            "rotation": [rval(fixedrot[x]), rval(fixedrot[y]), rval(fixedrot[z])],
            "translation": [rval(fixedtrans[x]), rval(fixedtrans[y]), rval(fixedtrans[z])],
            "scale": [rval(fixedscale[x]), rval(fixedscale[y]), rval(fixedscale[z])]
        }
    }

    if(minify):
        file.write(json.dumps(fileContent, separators=(',', ':'), sort_keys=False))
    else:
        file.write(json.dumps(fileContent, indent=4, sort_keys=False))

    file.close()

    return {'FINISHED'}

# ExportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, FloatProperty
from bpy.types import Operator

class ExportBlockModel(Operator, ExportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "export_mc.blockmodel"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export Scene as Minecraft Blockmodel"

    # ExportHelper mixin class uses this
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

    fpTransform = bpy.props.FloatVectorProperty(name = "First Person Transform", description = "Translation, Rotation and Scale of first person (in hand) rendering", size = 9, default=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0])
    tpTransform = bpy.props.FloatVectorProperty(name = "Third Person Transform", description = "Translation, Rotation and Scale of third person rendering", size = 9, default=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0])
    guiTransform = bpy.props.FloatVectorProperty(name = "GUI Transform", description = "Translation, Rotation and Scale in the GUI (Inventory)", size = 9, default=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0])
    headTransform = bpy.props.FloatVectorProperty(name = "Head Transform", description = "Translation, Rotation and Scale when equipped as helmet", size = 9, default=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0])
    groundTransform = bpy.props.FloatVectorProperty(name = "Ground Transform", description = "Translation, Rotation and Scale on the ground", size = 9, default=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0])
    fixedTransform = bpy.props.FloatVectorProperty(name = "Item Frame Transform", description = "Translation, Rotation and Scale in Item Frames", size = 9, default=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0])

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

        createTransform("First Person:", "fpTransform")
        createTransform("Third Person:", "tpTransform")
        createTransform("Inventory:", "guiTransform")
        createTransform("Head:", "headTransform")
        createTransform("Ground:", "groundTransform")
        createTransform("Item Frame:", "fixedTransform")

#        layout.label(text="NOTE: The following options don't work in 14w26b")
#        layout.label(text="They used to work in 14w21b. Hopefully they get readded.")
#        row = layout.row()
#        layout.label(text="Random Offset:")
#        row = layout.row()
#        row.prop(self, "randomoffset_x")
#        row.prop(self, "randomoffset_y")
#        row.prop(self, "randomoffset_z")
#
#        layout.label(text="Inventory Rendering:")
#        row = layout.row()
#        row.prop(self, "inverntory3drender")

    def execute(self, context):
        return write_to_file(context, self.filepath, self.include_textures, self.ambientocclusion, self.minify,
                self.fpTransform[0:3],
                self.fpTransform[6:9],
                self.fpTransform[3:6],
                self.tpTransform[0:3],
                self.tpTransform[6:9],
                self.tpTransform[3:6],
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

# Only needed if you want to add into a dynamic menu
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
