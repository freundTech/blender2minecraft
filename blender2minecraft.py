bl_info = {
    "name": "Blender2Minecraft",
    "author": "freundTech",
    "version": (0, 1),
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


x = 0
y = 1
z = 2
nl = os.linesep
tab = "    "

particle = ""
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

def rstr(num):
    return str(round(num, toRound))

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
    

def write_to_file(context, filepath, include_textures, ambientocclusion, firsttrans, firstscale, firstrot, thirdtrans, thirdscale, thirdrot, invtrans, invscale, invrot):
    textures = []
    scene = context.scene
    objects = scene.objects
    file = open(filepath,'w', encoding='utf-8')
    file.write("{" + nl)
    file.write(tab + "\"__comment\": \"This model was created with freundTech's Blender2Minecraft converter (BETA)\"," + nl)
    
    file.write(tab + "\"ambientocclusion\": " + str(ambientocclusion).lower() + "," + nl)
    
    file.write(tab + "\"elements\": [" + nl)
    
    firstObj = True
    
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
                                    
                if firstObj:
                    firstObj = False
                else:
                    file.write("," + nl)
                    
                objname = [""]
                for c in obj.name:
                    if c != '.':
                        objname[len(objname)-1] += c
                    else:
                        objname.append("")
                    
                file.write(tab + tab + "{   \"__comment\": \"" + objname[0] + "\"," + nl)
                file.write(tab + tab + tab + "\"from\": [ " + rstr(fromCoord[x]) + ", " + rstr(fromCoord[z]) + ", " + rstr(fromCoord[y]) + " ]," + nl)
                file.write(tab + tab + tab + "\"to\": [ " + rstr(toCoord[x]) + ", " + rstr(toCoord[z]) + ", " + rstr(toCoord[y]) + " ]," + nl)
                
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
                        file.write(tab + tab + tab + "\"rotation\": { \"origin\": [ " + rstr(pos[x]*16+8) + ", " + rstr(pos[z]*16) + ", " + rstr(pos[y]*16+8) + " ], \"axis\": \"")
                    
                        if axis == 0:
                            file.write("x")
                        elif axis == 1:
                             file.write("z")
                             rotation[axis] *= -1
                        elif axis == 2:
                             file.write("y")
                        file.write("\", \"angle\": " + str(rotation[axis]))
                        for n in objname:
                            if n[0:8] == "rescale:":
                                file.write(", \"rescale\": " + n[8:])
                        file.write(" }," + nl)
                    else:
                        raise Exception("You can only rotate by 22.5, -22.5, 45 or -45 degrees!")
                
                
                file.write(tab + tab + tab + "\"faces\": {" + nl)
                
                firstUv = True                                                                                                                                                                                                      
                
                for face in bm.faces:
                    if len(face.loops) == 4:
                        direction, toUse = getDir(face)
                        
                        uvs = []
                        for i in range(0, len(face.loops)):
                            uvs.append([face.loops[i][uv_layer].uv[x] * 16, face.loops[i][uv_layer].uv[y] * 16])
                        
                        
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
                            
                            image = data.uv_textures.active.data[face.index].image
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
                            if firstUv:
                                firstUv = False
                            else:
                                file.write("," + nl)
                            
                            print(direction)
                            print(minUv)
                            print(nextUv)
                            print(max)
                            print(min)
                            file.write(tab + tab + tab + tab + "\"" + direction + "\": { ")
                            
                            s = max[y]
                            
                            max[y] = (min[y]- 8)*-1+8
                            min[y] = (s- 8)*-1+8
                            
                       
                            if not mirror:
                                file.write("\"uv\": [ "+str(min[x])+", "+str(min[y])+", "+str(max[x])+", "+str(max[y])+" ], \"texture\": \"#" + name[0] + "\", \"rotation\": " + str(rot))
                            else:
                                file.write("\"uv\": [ "+str(max[x])+", "+str(min[y])+", "+str(min[x])+", "+str(max[y])+" ], \"texture\": \"#" + name[0] + "\", \"rotation\": " + str(rot))
                            
                            for n in name:
                                if n[0:9] == "cullface:":
                                    file.write(", \"cullface\": \""+n[9:]+"\"")
                                elif n[0:8] == "cullface":
                                    file.write(", \"cullface\": \""+direction+"\"")
                                elif n[0:10] == "tintindex:":
                                    file.write(", \"tintindex\": "+n[10:])
                                elif n[0:9] == "tintindex":
                                    file.write(", \"tintindex\": 1")
                                elif n[0:8] == "particle":
                                    particle = filepath

                            file.write(" }") 
                        print(rstr(max[x]) + nl)
                        print(rstr(min[x]) + nl)
                        print(rstr(max[y]) + nl)
                        print(rstr(min[y]) + nl + nl)
                        
                        
                    else:
                        print("Object \"" + data.name + "\" is not a cube!!!")
                #TODO
                file.write(nl)
                file.write(tab + tab + tab + "}" + nl)
                file.write(tab + tab + "}")
                
            else:
                print("Object \"" + data.name + "\" is not a cube!")
            
    file.write(nl + tab + "]," + nl)
    if include_textures:
        file.write(tab + "\"textures\": {" + nl)
    
        
        for texture in textures:
            file.write(tab + tab + "\"" + texture[0] + "\": " + "\"" + texture[1] + "\"," + nl)
    
        if particle != "":
            file.write(tab + tab + "\"particle\": \"" + particle + "\"" + nl)
    
        file.write(tab + "}," + nl)
    
    file.write(tab + "\"display\": {" + nl)
    file.write(tab + tab + "\"firstperson\": {" + nl)
    file.write(tab + tab + tab + "\"rotation\": [ " + rstr(firstrot[x]) + ", " + rstr(firstrot[y]) + ", " + rstr(firstrot[z]) + " ]," + nl)
    file.write(tab + tab + tab + "\"translation\": [ " + rstr(firsttrans[x]) + ", " + rstr(firsttrans[y]) + ", " + rstr(firsttrans[z]) + " ]," + nl)
    file.write(tab + tab + tab + "\"scale\": [ " + rstr(firstscale[x]) + ", " + rstr(firstscale[y]) + ", " + rstr(firstscale[z]) + " ]" + nl)
    file.write(tab + tab + "}," + nl)

    file.write(tab + tab + "\"thirdperson\": {" + nl)
    file.write(tab + tab + tab + "\"rotation\": [ " + rstr(thirdrot[x]) + ", " + rstr(thirdrot[y]) + ", " + rstr(thirdrot[z]) + " ]," + nl)
    file.write(tab + tab + tab + "\"translation\": [ " + rstr(thirdtrans[x]) + ", " + rstr(thirdtrans[y]) + ", " + rstr(thirdtrans[z]) + " ]," + nl)
    file.write(tab + tab + tab + "\"scale\": [ " + rstr(thirdscale[x]) + ", " + rstr(thirdscale[y]) + ", " + rstr(thirdscale[z]) + " ]" + nl)
    file.write(tab + tab + "}," + nl)
    
    file.write(tab + tab + "\"gui\": {" + nl)
    file.write(tab + tab + tab + "\"rotation\": [ " + rstr(invrot[x]) + ", " + rstr(invrot[y]) + ", " + rstr(invrot[z]) + " ]," + nl)
    file.write(tab + tab + tab + "\"translation\": [ " + rstr(invtrans[x]) + ", " + rstr(invtrans[y]) + ", " + rstr(invtrans[z]) + " ]," + nl)
    file.write(tab + tab + tab + "\"scale\": [ " + rstr(invscale[x]) + ", " + rstr(invscale[y]) + ", " + rstr(invscale[z]) + " ]" + nl)
    file.write(tab + tab + "}" + nl)
    
    file.write(tab + "}" + nl)
         
    file.write("}")   

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
    firsttransx = FloatProperty(
            name="X",
            description="Moves the Object in firstperson on the X axis",
            default=0.0,
            )
    firsttransy = FloatProperty(
            name="Y",
            description="Moves the Object in firstperson on the Y axis",
            default=0.0,
            )
    firsttransz = FloatProperty(
            name="Z",
            description="Moves the Object in firstperson on the Z axis",
            default=0.0,
            )
    firstrotx = FloatProperty(
            name="X",
            description="Rotates the Object in firstperson on the X axis",
            default=0.0,
            )
    firstroty = FloatProperty(
            name="Y",
            description="Rotates the Object in firstperson on the Y axis",
            default=0.0,
            )
    firstrotz = FloatProperty(
            name="Z",
            description="Rotates the Object in firstperson on the Z axis",
            default=0.0,
            )
    firstscalex = FloatProperty(
            name="X",
            description="Scales the Object in firstperson on the X axis",
            default=1.0,
            )
    firstscaley = FloatProperty(
            name="Y",
            description="Scales the Object in firstperson on the Y axis",
            default=1.0,
            )
    firstscalez = FloatProperty(
            name="Z",
            description="Scales the Object in firstperson on the Z axis",
            default=1.0,
            )
    thirdtransx = FloatProperty(
            name="X",
            description="Moves the Object in thirdperson on the X axis",
            default=0.0,
            )
    thirdtransy = FloatProperty(
            name="Y",
            description="Moves the Object in thirdperson on the Y axis",
            default=0.0,
            )
    thirdtransz = FloatProperty(
            name="Z",
            description="Moves the Object in thirdperson on the Z axis",
            default=0.0,
            )
    thirdrotx = FloatProperty(
            name="X",
            description="Rotates the Object in thirdperson on the X axis",
            default=0.0,
            )
    thirdroty = FloatProperty(
            name="Y",
            description="Rotates the Object in thirdperson on the Y axis",
            default=0.0,
            )
    thirdrotz = FloatProperty(
            name="Z",
            description="Rotates the Object in thirdperson on the Z axis",
            default=0.0,
            )
    thirdscalex = FloatProperty(
            name="X",
            description="Scales the Object in thirdperson on the X axis",
            default=1.0,
            )
    thirdscaley = FloatProperty(
            name="Y",
            description="Scales the Object in thirdperson on the Y axis",
            default=1.0,
            )
    thirdscalez = FloatProperty(
            name="Z",
            description="Scales the Object in thirdperson on the Z axis",
            default=1.0,
            )
            
    invtransx = FloatProperty(
            name="X",
            description="Moves the Object in the Inventory on the X axis",
            default=0.0,
            )
    invtransy = FloatProperty(
            name="Y",
            description="Moves the Object in the Inventory on the Y axis",
            default=0.0,
            )
    invtransz = FloatProperty(
            name="Z",
            description="Moves the Object in the Inventory on the Z axis",
            default=0.0,
            )
    invrotx = FloatProperty(
            name="X",
            description="Rotates the Object in the Inventory on the X axis",
            default=0.0,
            )
    invroty = FloatProperty(
            name="Y",
            description="Rotates the Object in the Inventory on the Y axis",
            default=0.0,
            )
    invrotz = FloatProperty(
            name="Z",
            description="Rotates the Object in the Inventory on the Z axis",
            default=0.0,
            )
    invscalex = FloatProperty(
            name="X",
            description="Scales the Object in the Inventory on the X axis",
            default=1.0,
            )
    invscaley = FloatProperty(
            name="Y",
            description="Scales the Object in the Inventory on the Y axis",
            default=1.0,
            )
    invscalez = FloatProperty(
            name="Z",
            description="Scales the Object in the Inventory on the Z axis",
            default=1.0,
            )
#    randomoffset_x = BoolProperty(
#            name="X",
#            description="Use Random Offset on the X Axis",
#            default=False,
#            )
#    randomoffset_y = BoolProperty(
#            name="Y",
#            description="Use Random Offset on the X Axis",
#            default=False,
#            )
#    randomoffset_z = BoolProperty(
#            name="Z",
#            description="Use Random Offset on the X Axis",
#            default=False,
#            )
#    inverntory3drender = BoolProperty(
#            name="Inventory 3D Rendering",
#            description="Renders the Block 3D inside an inventory",
#            default=True,
#            )
    
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
        
        
        layout.label()
        layout.label(text="First Person:")
        split = layout.split()
        col = split.column(align=True)
        col.label(text="Translate:")
        col.prop(self, "firsttransx")
        col.prop(self, "firsttransy")
        col.prop(self, "firsttransz")
        
        col = split.column(align=True)
        col.label(text="Rotate:")
        col.prop(self, "firstrotx")
        col.prop(self, "firstroty")
        col.prop(self, "firstrotz")
        
        col = split.column(align=True)
        col.label(text="Scale:")
        col.prop(self, "firstscalex")
        col.prop(self, "firstscaley")
        col.prop(self, "firstscalez")
        
        layout.label()
        layout.label(text="Third Person:")
        split = layout.split()
        col = split.column(align=True)
        col.label(text="Translate:")
        col.prop(self, "thirdtransx")
        col.prop(self, "thirdtransy")
        col.prop(self, "thirdtransz")
        
        col = split.column(align=True)
        col.label(text="Rotate:")
        col.prop(self, "thirdrotx")
        col.prop(self, "thirdroty")
        col.prop(self, "thirdrotz")
        
        col = split.column(align=True)
        col.label(text="Scale:")
        col.prop(self, "thirdscalex")
        col.prop(self, "thirdscaley")
        col.prop(self, "thirdscalez")
        
        
        layout.label()
        layout.label(text="Inventory:")
        split = layout.split()
        col = split.column(align=True)
        col.label(text="Translate:")
        col.prop(self, "invtransx")
        col.prop(self, "invtransy")
        col.prop(self, "invtransz")
        
        col = split.column(align=True)
        col.label(text="Rotate:")
        col.prop(self, "invrotx")
        col.prop(self, "invroty")
        col.prop(self, "invrotz")
        
        col = split.column(align=True)
        col.label(text="Scale:")
        col.prop(self, "invscalex")
        col.prop(self, "invscaley")
        col.prop(self, "invscalez")
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
        return write_to_file(context, self.filepath, self.include_textures, self.ambientocclusion, 
                [self.firsttransx, self.firsttransy, self.firsttransz],
                [self.firstscalex, self.firstscaley, self.firstscalez],
                [self.firstrotx, self.firstroty, self.firstrotz],
                [self.thirdtransx, self.thirdtransy, self.thirdtransz],
                [self.thirdscalex, self.thirdscaley, self.thirdscalez],
                [self.thirdrotx, self.thirdroty, self.thirdrotz],
                [self.invtransx, self.invtransy, self.invtransz],
                [self.invscalex, self.invscaley, self.invscalez],
                [self.invrotx, self.invroty, self.invrotz])


# Only needed if you want to add into a dynamic menu
def menu_func_export(self, context):
    self.layout.operator(ExportBlockModel.bl_idname, text="Export to Minecraft")


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
