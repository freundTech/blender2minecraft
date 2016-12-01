import bpy
import bmesh
import os
import math
import json
from collections import OrderedDict

#Axis for better readability
x = 0
y = 1
z = 2

#Might contain errors. Not tested yet.
cullfaceDirection = {
    2: "east",
    3: "north",
    4: "up",
    5: "west",
    6: "south",
    7: "bottom"
}

#Maybe make it configurable?
#Number of decimal digits to be rounded to
toRound = 2

#Get Maximum and Minimum values form dict values for axis axis
def getMaxMin(values, axis):
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

def getIndex(values, mask, axis):
    for value in values:
        if round(value[axis[0]], toRound) == mask[0] and round(value[axis[1]], toRound) == mask[1]:
            return values.index(value)
    raise Exception("Value not found")

#Round value to the accuracy defined in toRound
def roundValue(num):
    return round(num, toRound)

#Get direction of a face by checking the normals
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

#TODO: Use acctual image class?
class attrdict(dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        __dict__ = self

#Export the model
#TODO: Fix signature
def write_to_file(context, filepath, include_textures, ambientocclusion, minify,
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

    #TODO: Figure out how to make jsondump respect the OrderedDict order
    fileContent = OrderedDict()

    fileContent["__comment"] = "This model was created with freundTech's Blender2Minecraft converter (BETA)"
    fileContent["ambientocclusion"] = ambientocclusion
    fileContent["elements"] = []

    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')

    for obj in objects:
        #TODO: Maybe assert or inverted if would be better than giant if
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

                toCoord, fromCoord = getMaxMin(box, [x, y, z])

                objname = [""]
                for c in obj.name:
                    if c != '.':
                        objname[len(objname)-1] += c
                    else:
                        objname.append("")

                item = {}

                item["__comment"] = objname[0]
                item["from"] = [roundValue(fromCoord[x]), roundValue(fromCoord[z]), roundValue(fromCoord[y])]
                item["to"] = [roundValue(toCoord[x]), roundValue(toCoord[z]), roundValue(toCoord[y])]

                rotation = [round(math.degrees(a), 1) for a in obj.rotation_euler]
                numaxis = 0
                for i in range(0, len(rotation)):
                    while rotation[i] >= 360:
                        rotation[i] -= 360
                for r in rotation:
                    if r != 0:
                        numaxis += 1
                        axis = rotation.index(r)
                if numaxis > 1:
                    raise Exception("Only one Axis can be rotated at a time!")
                elif numaxis == 1:
                    if rotation[axis] == -22.5 or rotation[axis] == 22.5 or rotation[axis] == -45 or rotation[axis] == 45:
                        item["rotation"] = { "origin": [roundValue(pos[x]*16+8), roundValue(pos[z]*16), roundValue(pos[y]*-16+8)] }

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

                        #TODO: Don't use builtin functions as variables
                        max, min = getMaxMin(uvs, [x, y])

                        if min[x] != max[x] and min[y] != max[y]:

                            verts = []
                            for i in range(0, len(face.loops)):
                                verts.append([face.loops[i].vert.co[x] * 16, face.loops[i].vert.co[y] * 16, face.loops[i].vert.co[z] * 16])
                            maxr, minr = getMaxMin(verts, toUse)

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

                            minI = getIndex(verts, bottom, toUse)

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

                            filepath = ""
                            if image.filepath == "":
                                print("Warning: Image %s not saved to disk. Can't get path!" % image.name)
                            else:
                                filepath = bpy.path.relpath(image.filepath)
                                
                                imagepath = bpy.path.abspath(image.filepath)
                                imagepath = os.path.abspath(imagepath)
                                path = imagepath.split(os.sep)
                                for i, dir in enumerate(path):
                                    if dir == "assets" and path[i+1] == "minecraft" and path[i+2] == "textures":
                                        filepath = os.path.join(*path[i+3:])

                                filepath = os.path.splitext(filepath)[0]

                            if not [image.name, filepath] in textures:
                                textures.append([image.name, filepath])

                            s = max[y]

                            max[y] = (min[y]- 8)*-1+8
                            min[y] = (s- 8)*-1+8

                            item["faces"][direction] = {}

                            if not mirror:
                                item["faces"][direction]["uv"] = [min[x], min[y], max[x], max[y]]
                                item["faces"][direction]["texture"] = "#" + image.name
                                item["faces"][direction]["rotation"] = rot
                            else:
                                item["faces"][direction]["uv"] = [max[x], min[y], min[x], max[y]]
                                item["faces"][direction]["texture"] = "#" + image.name
                                item["faces"][direction]["rotation"] = rot

                            if "MinecraftParticle" in image and image["MinecraftParticle"] == 1:
                                particle = filepath
                            if "MinecraftTintindex" in image and image["MinecraftTintindex"] != 0:
                                item["faces"][direction]["tintindex"] = image["MinecraftTintindex"]
                            if "MinecraftCullface" in image and image["MinecraftCullface"] != 0:
                                if image["MinecraftCullface"] == 1:
                                    item["faces"][direction]["cullface"] = direction
                                else:
                                    item["faces"][direction]["cullface"] = cullfaceDirection[image["MinecraftCullface"]]
                    else:
                        print("Object \"" + data.name + "\" is not a cube!!!")

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
        "firstperson_lefthand": {
            "rotation": [roundValue(first_left_rot[x]), roundValue(first_left_rot[y]), roundValue(first_left_rot[z])],
            "translation": [roundValue(first_left_trans[x]), roundValue(first_left_trans[y]), roundValue(first_left_trans[z])],
            "scale": [roundValue(first_left_scale[x]), roundValue(first_left_scale[y]), roundValue(first_left_scale[z])]
        },
        "firstperson_righthand": {
            "rotation": [roundValue(first_right_rot[x]), roundValue(first_right_rot[y]), roundValue(first_right_rot[z])],
            "translation": [roundValue(first_right_trans[x]), roundValue(first_right_trans[y]), roundValue(first_right_trans[z])],
            "scale": [roundValue(first_right_scale[x]), roundValue(first_right_scale[y]), roundValue(first_right_scale[z])]
        },
        "thirdperson_righthand": {
            "rotation": [roundValue(third_right_rot[x]), roundValue(third_right_rot[y]), roundValue(third_right_rot[z])],
            "translation": [roundValue(third_right_trans[x]), roundValue(third_right_trans[y]), roundValue(third_right_trans[z])],
            "scale": [roundValue(third_right_scale[x]), roundValue(third_right_scale[y]), roundValue(third_right_scale[z])]
        },
        "thirdperson_lefthand": {
            "rotation": [roundValue(third_left_rot[x]), roundValue(third_left_rot[y]), roundValue(third_left_rot[z])],
            "translation": [roundValue(third_left_trans[x]), roundValue(third_left_trans[y]), roundValue(third_left_trans[z])],
            "scale": [roundValue(third_left_scale[x]), roundValue(third_left_scale[y]), roundValue(third_left_scale[z])]
        },
        "gui": {
            "rotation": [roundValue(invrot[x]), roundValue(invrot[y]), roundValue(invrot[z])],
            "translation": [roundValue(invtrans[x]), roundValue(invtrans[y]), roundValue(invtrans[z])],
            "scale": [roundValue(invscale[x]), roundValue(invscale[y]), roundValue(invscale[z])]
        },
        "head": {
            "rotation": [roundValue(headrot[x]), roundValue(headrot[y]), roundValue(headrot[z])],
            "translation": [roundValue(headtrans[x]), roundValue(headtrans[y]), roundValue(headtrans[z])],
            "scale": [roundValue(headscale[x]), roundValue(headscale[y]), roundValue(headscale[z])]
        },
        "ground": {
            "rotation": [roundValue(groundrot[x]), roundValue(groundrot[y]), roundValue(groundrot[z])],
            "translation": [roundValue(groundtrans[x]), roundValue(groundtrans[y]), roundValue(groundtrans[z])],
            "scale": [roundValue(groundscale[x]), roundValue(groundscale[y]), roundValue(groundscale[z])]
        },
        "fixed": {
            "rotation": [roundValue(fixedrot[x]), roundValue(fixedrot[y]), roundValue(fixedrot[z])],
            "translation": [roundValue(fixedtrans[x]), roundValue(fixedtrans[y]), roundValue(fixedtrans[z])],
            "scale": [roundValue(fixedscale[x]), roundValue(fixedscale[y]), roundValue(fixedscale[z])]
        }
    }

    if(minify):
        file.write(json.dumps(fileContent, separators=(',', ':'), sort_keys=False))
    else:
        file.write(json.dumps(fileContent, indent=4, sort_keys=False))

    file.close()

    return {'FINISHED'}
