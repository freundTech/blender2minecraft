class ImportBlockModel(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "import_mc.blockmodel"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import a Minecraft Blockmodel in Scene"

    def execute(self, context):

        # import file
        readfile = open(self.filepath,'r', encoding='utf-8')
        data = json.load(readfile)
        readfile.close()

        # Make scene
        scene = bpy.data.scenes["Scene"]
        scene.render.resolution_x = 1000
        scene.render.resolution_y = 1000
        if scene.objects.active :
            bpy.ops.object.mode_set(mode='OBJECT')

        ## Light
        bpy.ops.object.lamp_add(type='SUN', view_align=False, location=(-0.0402176, 1.2157, 1.36071), layers=(True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False))
        light = context.object
        light.data.shadow_method = 'NOSHADOW'
        light.data.energy = 1.5
        light.location[0] = 4
        light.location[1] = -4
        light.location[2] = 12
        light.rotation_euler[0] = 0.035
        light.rotation_euler[1] = 0.192
        light.rotation_euler[2] = -0.838

        ## camera
        bpy.ops.object.camera_add(location=(1.38, -1.38, 1.86), rotation=(0.959931, 0, 0.785398))
        cam = context.object
        cam.data.type = 'ORTHO'
        cam.data.ortho_scale = 1.96
        cam.name = "MinecraftView"
        scene.camera = cam

        ## grid
        for area in bpy.context.screen.areas :
            for space in area.spaces :
                if space.type == 'VIEW_3D' :
                    space.grid_scale = 0.03125
                    space.grid_subdivisions = 2
                    space.grid_lines = 32

        ## Ambiant Occlusion
        if 'ambientocclusion' in data :
            print("ambientocclusion - " + str(data['ambientocclusion']))
        else :
            data['ambientocclusion'] = True
            print("ambientocclusion force - " + str(data['ambientocclusion']))

        scene.world.light_settings.use_ambient_occlusion = data['ambientocclusion']

        ## texture
        if 'textures' in data : void = 0
        else : data['textures'] = []

        for texture in data['textures'] :
            self.loadTextures(context, data['textures'][texture], texture)

        ## import element
        if 'elements' in data : void = 0
        else : data['elements'] = []

        nbMake = 0
        nbTotal = len(data['elements'])
        for element in data['elements'] :
            if self.makeElement(context, element, nbMake) == True :
                nbMake += 1

        print( str(nbMake) + " elements make on " + str(nbTotal) )

        return {'FINISHED'}

    def makeElement(self, context, data, id):

        if 'from' in data and 'to' in data :

            # cube
            print("cube" + str(id))
            name = "Elem_%i" % id
            if '__comment' in data :
                name = data['__comment']

            #mat = bpy.data.materials.new(name)
            #mat.diffuse_color = random.random(), random.random(), random.random()

            fromBL = MC2BL(data['from'])
            toBL   = MC2BL(data['to'])

            size = [(toBL[x]-fromBL[x])/2,
                    (toBL[y]-fromBL[y])/2,
                    (toBL[z]-fromBL[z])/2]

            loca = [size[x]+fromBL[x],
                    size[y]+fromBL[y],
                    size[z]+fromBL[z]]

            bpy.ops.mesh.primitive_cube_add( radius=1, location=(loca[x], loca[y], loca[z]))

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
            bpy.ops.object.mode_set(mode='OBJECT')

            elem = context.object
            elem.scale = size
            #elem.data.materials.append(mat)
            elem.name = name

            # rotation

            if 'rotation' in data :
                if 'origin' in data['rotation'] and 'axis' in data['rotation'] and  'angle' in data['rotation'] :
                    originBL = MC2BL(data['rotation']['origin'])
                    context.scene.cursor_location = originBL
                    bpy.types.SpaceView3D.pivot_point = 'CURSOR'

                    if data['rotation']['axis'] == 'x' :
                        axis = (1, 0, 0);
                        rad = math.radians(data['rotation']['angle'])
                    elif data['rotation']['axis'] == 'y' :
                        axis = (0, 0, 1);
                        rad = -math.radians(data['rotation']['angle'])
                    else :
                        axis = (0, 1, 0);
                        rad = math.radians(data['rotation']['angle'])

                    bpy.ops.transform.rotate(value=rad, axis=axis)

            # faces
            if 'faces' in data : void = 0
            else : data['faces'] = []

            faceRef = {"down":4, "up":5, "north":3, "south":1, "west":0, "east":2}

            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(type="FACE")
            bpy.ops.mesh.select_all(action='TOGGLE')
            bpy.ops.object.mode_set(mode='OBJECT')

            nbMake = 0
            nbTotal = len(data['faces'])
            for face in faceRef :
                print(face)
                if face in data['faces'] :
                    if self.makeFace(context, elem, data['faces'][face], faceRef[face]) == True :
                        nbMake += 1
                else :
                    poly = elem.data.polygons[faceRef[face]]
                    poly.select = True   # won't show in viewport

            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.delete(type='FACE') # will be acted on.
            bpy.ops.object.mode_set(mode='OBJECT')


            print( str(nbMake) + " faces make on " + str(nbTotal) )

            return True
        else :
            return False

    def makeFace(self, context, elem, data, id):

        if 'uv' in data and 'texture' in data :

            uv_layer = elem.data.uv_layers.active.data
            poly = elem.data.polygons[id]

            uvBL = uvMC2BL(data['uv'])
            uvref = collections.deque([[2,1],[0,1],[0,3],[2,3]])
            if id == 4 : uvref.rotate(-1) #down 4
            if id == 5 : uvref.rotate(1)  #up 5

            if 'rotation' in data :
                uvref.rotate(int(-data['rotation']/90))

            index = -1
            for loop_index in range(poly.loop_start, poly.loop_start + poly.loop_total) :
                index += 1
                uv_layer[loop_index].uv[0] = uvBL[ uvref[index][0] ]
                uv_layer[loop_index].uv[1] = uvBL[ uvref[index][1] ]

            # Assign materials to faces
            if dataMat[data['texture']].name in elem.data.materials : void = 0
            else : elem.data.materials.append(dataMat[data['texture']])

            index = -1
            for slot in elem.material_slots :
                index += 1
                if slot.material == dataMat[data['texture']] :
                    break

            poly.material_index = index

            return True
        else :
            return False

    def loadTextures(self, context, data, id) :

        spl = data.split('/')
        name = spl[len(spl)-1]

        # if material existe
        if name in bpy.data.materials :
            dataMat['#'+id] = bpy.data.materials[name]
        else :

            # if texture existe
            if name in bpy.data.textures :
                cTex = bpy.data.textures[name]
            else :

                # if image existe
                if name + '.png' in bpy.data.images :
                    img = bpy.data.images[name + '.png']
                else :
                    # Load image file. Change here if the snippet folder is
                    realpath  = self.filepath.split('/minecraft/')[0]
                    realpath += '/minecraft/textures/'
                    realpath += data + '.png'

                    cTex = bpy.data.textures.new(name, type = 'IMAGE')

                    try:
                        cTex.image = bpy.data.images.load(realpath)
                    except:
                        bpy.ops.info.message('INVOKE_DEFAULT',
                            title = "Loading image Error",
                            type = "Message",
                            message = "Cannot load image %s" % realpath)

                        #raise NameError("Cannot load image %s" % realpath)

            dataMat['#'+id] = bpy.data.materials.new(name)
            dataMat['#'+id].use_transparency = True
            dataMat['#'+id].alpha = 0
            dataMat['#'+id].preview_render_type = 'CUBE'
            dataMat['#'+id].use_raytrace = False

            # Add texture slot for color texture
            mtex = dataMat['#'+id].texture_slots.add()
            mtex.texture = cTex
            mtex.texture_coords = 'UV'
            mtex.use_map_alpha = True

            cTex.use_interpolation = False
            cTex.filter_type = 'BOX'

        return True

def MC2BL(mc):
    bl = [mc[x]*0.0625-0.5, -mc[z]*0.0625+0.5, mc[y]*0.0625]
    return bl

def uvMC2BL(mc):
    bl = [mc[0]*0.0625, (16-mc[1])*0.0625, mc[2]*0.0625, (16-mc[3])*0.0625]
    return bl

