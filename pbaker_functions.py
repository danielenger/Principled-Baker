import bpy
import os
import numpy
import time

NODE_TAG = 'p_baker_node'
MATERIAL_TAG = 'p_baker_material'
MATERIAL_TAG_VERTEX = 'p_baker_material_vertex'

NODE_INPUTS = [
    'Color',
    'Subsurface',
    # 'Subsurface Radius', # TODO
    'Subsurface Color',
    'Metallic',
    'Specular',
    'Specular Tint',
    'Roughness',
    'Anisotropic',
    'Anisotropic Rotation',
    'Sheen',
    'Sheen Tint',
    'Clearcoat',
    'Clearcoat Roughness',
    'IOR',
    'Transmission',
    'Transmission Roughness',
    'Normal',
    'Clearcoat Normal',
    'Tangent'
]

NORMAL_INPUTS = ['Normal', 'Clearcoat Normal', 'Tangent']

SRGB_INPUTS = ['Color', 'Base Color']

ALPHA_NODES = {
    "Alpha":'BSDF_TRANSPARENT',
    "Translucent_Alpha":'BSDF_TRANSLUCENT',
    "Glass_Alpha":'BSDF_GLASS'
}

BSDF_NODES = [
    'BSDF_PRINCIPLED',
    'BSDF_DIFFUSE',
    'BSDF_TOON',
    'BSDF_VELVET',
    'BSDF_GLOSSY',
    'BSDF_TRANSPARENT',
    'BSDF_TRANSLUCENT',
    'BSDF_GLASS'
    ]

IMAGE_FILE_FORMAT_ENDINGS = {
    "BMP": "bmp",
    "PNG": "png",
    "JPEG": "jpg",
    "TIFF": "tif",
    "TARGA": "tga",
    "OPEN_EXR": "exr",
}

NODE_OFFSET_X = 300
NODE_OFFSET_Y = 200

IMAGE_NODE_OFFSET_X = -900
IMAGE_NODE_OFFSET_Y = -260
IMAGE_NODE_WIDTH = 300

PRINCIPLED_BAKER_TEMP_MATERIAL_NAME = "PRINCIPLED_BAKER_TEMP_MATERIAL_{}".format(time.time())



def fill_image(image, color):
    image.pixels[:] = color * image.size[0] * image.size[1]


def is_list_equal(list):
    list = iter(list)
    try:
        first = next(list)
    except StopIteration:
        return True
    return all(first == rest for rest in list)


def get_active_output(mat):
    for node in mat.node_tree.nodes:
        if node.type == "OUTPUT_MATERIAL" and node.is_active_output:
            return node


def get_all_outputs(mat):
    outputs = []
    for node in mat.node_tree.nodes:
        if node.type == "OUTPUT_MATERIAL":
            outputs.append(node)
    return outputs


def get_selected_outputs(mat):
    outputs = []
    for node in mat.node_tree.nodes:
        if node.type == "OUTPUT_MATERIAL" and node.select:
            outputs.append(node)
    return outputs


def find_node_by_type(mat, node_type):
    for node in mat.node_tree.nodes:
        if node.type == node_type:
            return node


def new_rgb_node(mat, color=[0, 0, 0, 1]):
    node = mat.node_tree.nodes.new(type="ShaderNodeRGB")
    node[NODE_TAG] = 1
    node.outputs['Color'].default_value = color
    node.color = (0.8, 0.8, 0.8)
    node.use_custom_color = True
    return node


def new_mixrgb_node(mat, fac=0.5, color1=[0, 0, 0, 1], color2=[0, 0, 0, 1]):
    node = mat.node_tree.nodes.new(type="ShaderNodeMixRGB")
    node[NODE_TAG] = 1
    node.inputs[0].default_value = fac
    node.inputs[1].default_value = color1
    node.inputs[2].default_value = color2
    node.color = (0.8, 0.8, 0.8)
    node.use_custom_color = True
    return node


def new_image_node(material):
    image_node = material.node_tree.nodes.new(type="ShaderNodeTexImage")
    return image_node


def get_combined_images(img1, img2, from_channel, to_channel):
    n = 4
    size = img1.size[0] * img1.size[1]
    a = numpy.array(img1.pixels).reshape(size, n)
    b = numpy.array(img2.pixels).reshape(size, n)
    a[:, to_channel] = b[:, from_channel] # numpy magic happens here
    return a.reshape(size * n)


def get_invert_image(img):
    n = 4
    size = img.size[0] * img.size[1]
    a = numpy.array(img.pixels).reshape(size, n)
    a[:,0:3] = 1 - a[:,0:3]
    return a.reshape(size * n)


def get_sibling_node(node):
    if node.outputs[0].is_linked:
        parent_node = node.outputs[0].links[0].to_node
        for input_socket in parent_node.inputs:
            child_node = input_socket.links[0].from_node
            if not child_node == node:
                if input_socket.type == node.outputs[0].links[0].to_socket.type:
                    return child_node


def is_node_type_in_node_tree(node, node_type):
    if node.type == node_type:
        return True
    else:
        for input_socket in node.inputs:
            if input_socket.is_linked:
                from_node = input_socket.links[0].from_node
                if is_node_type_in_node_tree(from_node, node_type):
                    return True
        return False


def are_node_types_in_node_tree(node, node_types):
    for n_type in node_types:
        if is_node_type_in_node_tree(node, n_type):
            return True
    return False


def select_set(obj, s):
    # 2.79
    if bpy.app.version_string.startswith('2.7'):
        obj.select = s
    # 2.80
    else:
        obj.select_set(s)


def save_image_as(image, file_path, file_format, color_mode='RGB', color_depth='8', compression=15, quality=90, tiff_codec='DEFLATE', exr_codec='ZIP'):
    if color_depth == '8':
        image.save()
    else:
        # temp scene
        tmp_scene = bpy.data.scenes.new('scene name')

        # set new render.image_settings
        s = tmp_scene.render.image_settings
        s.file_format = file_format
        s.color_mode = color_mode
        s.color_depth = color_depth
        s.compression = compression
        s.quality = quality
        s.tiff_codec = tiff_codec
        s.exr_codec = exr_codec
        
        # save
        file_path = os.path.normpath(image.filepath.lstrip("//"))
        image.save_render(file_path)

        # remove temp scene
        bpy.data.scenes.remove(tmp_scene)

        image.source = 'FILE'
        # image.update()


def prepare_bake_ao(mat, socket, new_socket):
    node = socket.node
    if node.type == 'AMBIENT_OCCLUSION':
        mat.node_tree.links.new(node.outputs['AO'], new_socket)
    else:
        for input_socket in node.inputs:
            if input_socket.is_linked:
                from_socket = input_socket.links[0].from_socket
                prepare_bake_ao(mat, from_socket, new_socket)


def prepare_bake_factor(mat, socket, new_socket, node_type, factor_name='Fac'):
    node = socket.node
    if node.type == node_type:
        to_node = node.outputs[0].links[0].to_node
        if factor_name in to_node.inputs.keys():
            socket = to_node.inputs[factor_name]
            prepare_bake(mat, socket, new_socket, factor_name)
    else:
        for input_socket in node.inputs:
            if input_socket.is_linked:
                from_socket = input_socket.links[0].from_socket
                prepare_bake_factor(mat, from_socket, new_socket, node_type, factor_name)


def prepare_bake_color(mat, from_socket, new_socket):

    node = from_socket.node

    if not is_node_type_in_node_tree(node, 'AMBIENT_OCCLUSION'):
        mat.node_tree.links.new(from_socket, new_socket)
    
    else:
        if node.type == 'MIX_RGB':
            color1 = node.inputs['Color1'].default_value
            color2 = node.inputs['Color2'].default_value
            fac = node.inputs['Fac'].default_value
            new_node = new_mixrgb_node(mat, fac, color1, color2)
            new_node.inputs['Fac'].default_value = node.inputs['Fac'].default_value            
            mat.node_tree.links.new(new_node.outputs[0], new_socket)

            if node.blend_type == 'MIX':
     
                if node.inputs['Fac'].is_linked:
                    from_socket = node.inputs['Fac'].links[0].from_socket
                    new_socket = new_node.inputs['Fac']
                    mat.node_tree.links.new(from_socket, new_socket)

                if node.inputs['Color1'].is_linked:
                    from_node = node.inputs['Color1'].links[0].from_node
                    if from_node.type == 'AMBIENT_OCCLUSION':
                        new_node.inputs['Color1'].default_value = from_node.inputs['Color'].default_value
                    from_socket = node.inputs['Color1'].links[0].from_socket
                    new_socket = new_node.inputs['Color1']
                    prepare_bake_color(mat, from_socket, new_socket)

                if node.inputs['Color2'].is_linked:
                    from_node = node.inputs['Color2'].links[0].from_node
                    if from_node.type == 'AMBIENT_OCCLUSION':
                        new_node.inputs['Color2'].default_value = from_node.inputs['Color'].default_value
                    from_socket = node.inputs['Color2'].links[0].from_socket
                    new_socket = new_node.inputs['Color2']
                    prepare_bake_color(mat, from_socket, new_socket)

            else:
               
                if node.inputs['Color1'].is_linked:
                    from_node = node.inputs['Color1'].links[0].from_node
                    if from_node.type == 'AMBIENT_OCCLUSION':
                        new_node.inputs['Fac'].default_value = 1
                        new_node.inputs['Color1'].default_value = from_node.inputs['Color'].default_value
                        if node.inputs['Color2'].is_linked:
                            from_socket = node.inputs['Color2'].links[0].from_socket
                            new_socket = new_node.inputs['Color2']
                            prepare_bake_color(mat, from_socket, new_socket)

                if node.inputs['Color2'].is_linked:
                    from_node = node.inputs['Color2'].links[0].from_node
                    if from_node.type == 'AMBIENT_OCCLUSION':
                        new_node.inputs['Fac'].default_value = 0
                        new_node.inputs['Color2'].default_value = from_node.inputs['Color'].default_value
                        if node.inputs['Color1'].is_linked:
                            from_socket = node.inputs['Color1'].links[0].from_socket
                            new_socket = new_node.inputs['Color1']
                            prepare_bake_color(mat, from_socket, new_socket)

        # skip over Afrom_socket, if linked
        elif node.type == 'AMBIENT_OCCLUSION':
            color = node.inputs['Color'].default_value
            if node.inputs['Color'].is_linked:
                from_socket = node.inputs['Color'].links[0].from_socket
                prepare_bake_color(mat, from_socket, new_socket)
        else:
            mat.node_tree.links.new(from_socket, new_socket)


def prepare_bake(mat, socket, new_socket, input_socket_name):

    settings = bpy.context.scene.principled_baker_settings

    if input_socket_name in NORMAL_INPUTS:
        color = (0.5, 0.5, 1.0, 1.0)
    else:
        color = (0.0, 0.0, 0.0, 0.0)
    
    # 2.79
    if bpy.app.version_string.startswith('2.7'):
        if input_socket_name == 'Displacement':
            if socket.is_linked:
                from_socket = socket.links[0].from_socket
                mat.node_tree.links.new(from_socket, new_socket)

    node = socket.node

    if node.type == 'OUTPUT_MATERIAL':
        from_socket = socket.links[0].from_socket
        prepare_bake(mat, from_socket, new_socket, input_socket_name)

    elif node.type == 'MIX_SHADER':
        color2 = [1,1,1,0] if input_socket_name == 'Fac' else color
        fac = node.inputs['Fac'].default_value
        mix_node = new_mixrgb_node(mat, fac, color, color2)
        mat.node_tree.links.new(mix_node.outputs[0], new_socket)
        mix_node.label = input_socket_name

        if node.inputs['Fac'].is_linked:
            from_socket = node.inputs[0].links[0].from_socket
            new_socket = mix_node.inputs[0]
            mat.node_tree.links.new(from_socket, new_socket)

        for i in range(1, 3):
            if node.inputs[i].is_linked:
                next_node = node.inputs[i].links[0].from_node
                if next_node.type in ALPHA_NODES.values() and settings.use_exclude_transparent_colors:
                    other_i = i % 2 + 1
                    if node.inputs[other_i].is_linked:
                        from_socket = node.inputs[other_i].links[0].from_socket
                        new_socket = mix_node.inputs[i]
                else:
                    from_socket = node.inputs[i].links[0].from_socket
                    new_socket = mix_node.inputs[i]
                prepare_bake(mat, from_socket, new_socket, input_socket_name)

    elif node.type == 'ADD_SHADER' and not input_socket_name == 'Fac':
        mix_node = new_mixrgb_node(mat, 1, color, color)
        mix_node.blend_type = 'ADD'
        mat.node_tree.links.new(mix_node.outputs[0], new_socket)
        mix_node.label = input_socket_name

        for i in range(0, 2):
            if node.inputs[i].is_linked:
                from_socket = node.inputs[i].links[0].from_socket
                new_socket = mix_node.inputs[i + 1]
                prepare_bake(mat, from_socket, new_socket, input_socket_name)

    # exclude some colors from color
    elif node.type in ['EMISSION']:
        return

    # 2.79
    elif node.type == 'NORMAL_MAP' and bpy.app.version_string.startswith('2.7'):
        if node.inputs['Color'].is_linked:
            from_socket = node.inputs['Color'].links[0].from_socket
            mat.node_tree.links.new(from_socket, new_socket)

    # 2.79
    elif node.type == 'BUMP' and bpy.app.version_string.startswith('2.7'):
        if node.inputs['Height'].is_linked:
            from_socket = node.inputs['Height'].links[0].from_socket
            mat.node_tree.links.new(from_socket, new_socket)

    else:
        if node.type == 'BSDF_PRINCIPLED' and input_socket_name == 'Color':
            input_socket_name = 'Base Color'

        if input_socket_name in node.inputs.keys():
            input_socket = node.inputs[input_socket_name]
            
            if input_socket.type == 'RGBA':
                if input_socket.is_linked:
                    o = input_socket.links[0].from_socket
                    prepare_bake_color(mat, o, new_socket)
                else:
                    color = node.inputs[input_socket_name].default_value
                    rgb_node = new_rgb_node(mat, color)
                    mat.node_tree.links.new(rgb_node.outputs[0], new_socket)

            elif input_socket.type == 'VALUE':
                if input_socket.is_linked:
                    from_socket = input_socket.links[0].from_socket
                    if from_socket.type == 'VALUE':
                        mat.node_tree.links.new(from_socket, new_socket)
                    else:  # RGB to BW
                        node = mat.node_tree.nodes.new(type="ShaderNodeRGBToBW")
                        node[NODE_TAG] = 1
                        mat.node_tree.links.new(from_socket, node.inputs[0])
                        mat.node_tree.links.new(node.outputs[0], new_socket)
                else:
                    value_node = mat.node_tree.nodes.new(type="ShaderNodeValue")
                    value_node[NODE_TAG] = 1
                    value_node.outputs[0].default_value = node.inputs[input_socket_name].default_value
                    mat.node_tree.links.new(value_node.outputs[0], new_socket)

            elif input_socket.type == 'VECTOR':
                if input_socket.name == input_socket_name:
                    # 2.79
                    if bpy.app.version_string.startswith('2.7'):
                        if input_socket.is_linked:
                            from_socket = input_socket.links[0].from_socket
                            if from_socket.node.type == 'NORMAL_MAP':
                                prepare_bake(mat, from_socket, new_socket, 'Color')
                            if from_socket.node.type == 'BUMP':
                                prepare_bake(mat, from_socket, new_socket, 'Height')
                    # 2.80
                    else:
                        if input_socket.is_linked:
                            from_socket = input_socket.links[0].from_socket
                            mat.node_tree.links.new(from_socket, new_socket)

        else:
            for input_socket in node.inputs:
                if input_socket.is_linked:
                    from_socket = input_socket.links[0].from_socket
                    prepare_bake(mat, from_socket, new_socket, input_socket_name)


def add_temp_material(obj):
    name = "PRINCIPLED_BAKER_TEMP_MATERIAL_FOR_VERTEX_COLOR_{}".format(time.time())
    mat = bpy.data.materials.new(name)
    mat[MATERIAL_TAG_VERTEX] = 1
    mat.use_nodes = True
    principled_node = find_node_by_type(mat, 'BSDF_PRINCIPLED')
    principled_node.inputs["Base Color"].default_value = [0,0,0,1]
    obj.data.materials.append(mat)


def is_socket_linked_in_node_tree(node, input_socket_name):
    if input_socket_name == 'Color':
        if node.type == 'NORMAL_MAP':
            return False  # exclude 'Color' from Normal Map input!
        if node.type == 'BSDF_PRINCIPLED':
            input_socket_name = 'Base Color'
    for input_socket in node.inputs:
        if input_socket.is_linked:
            if input_socket_name == input_socket.name:
                return True
            else:
                from_node = input_socket.links[0].from_node
                if is_socket_linked_in_node_tree(from_node, input_socket_name):
                    return True
    return False



def has_material(obj):
    if len(obj.material_slots) >= 1:
        for mat_slot in obj.material_slots:
            if mat_slot.material:
                if not MATERIAL_TAG in mat_slot.material.keys():
                    material_output = get_active_output(mat_slot.material)
                    if material_output == None:
                        return False
                    else:
                        if not material_output.inputs['Surface'].is_linked:
                            return False
                        else:
                            return True                    
    else:
        return False


def get_bake_type(job_name):
    if job_name in NORMAL_INPUTS:
        return 'NORMAL'
    if job_name in ['Diffuse']:
        return 'DIFFUSE'
    else:
        return 'EMIT'


def get_only_meshes(objects):
    l = []
    for o in objects:
        if o.type == 'MESH':
            l.append(o)
    return l


def get_active_outputs(objects):
    active_outputs = []
    for obj in objects:
        for mat_slot in obj.material_slots:
            if mat_slot.material:
                if not MATERIAL_TAG in mat_slot.material.keys():
                    node = get_active_output(mat_slot.material)
                    if node:
                        active_outputs.append(node)
    return active_outputs


def get_all_material_outputs(objects):
    outputs = {}
    for obj in objects:
        for mat_slot in obj.material_slots:
            if mat_slot.material:
                for node in mat_slot.material.node_tree.nodes:
                    if node.type == "OUTPUT_MATERIAL":
                        # 2.79
                        if bpy.app.version_string.startswith('2.7'):
                            outputs[node] = None
                        # 2.80
                        else:
                            outputs[node] = node.target
    return outputs


def set_material_outputs_target_to_all(objects):
    for obj in objects:
        for mat_slot in obj.material_slots:
            if mat_slot.material:
                for node in mat_slot.material.node_tree.nodes:
                    if node.type == "OUTPUT_MATERIAL":
                        node.target = 'ALL'
