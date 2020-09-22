import os
import time

import bpy
import numpy

is_2_79 = True if bpy.app.version < ( 2, 80, 0) else False
is_2_80 = True if bpy.app.version >= ( 2, 80, 0) else False

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
# 2.80
if is_2_80:
    NODE_INPUTS.extend(['Emission', 'Alpha'])

NORMAL_INPUTS = ['Normal', 'Clearcoat Normal', 'Tangent']

SRGB_INPUTS = ['Color', 'Base Color']

ALPHA_NODES = {  # TODO 'BSDF_TRANSPARENT' in alpha nodes?
    # "Alpha":'BSDF_TRANSPARENT',
    "Translucent_Alpha": 'BSDF_TRANSLUCENT',
    "Glass_Alpha": 'BSDF_GLASS'
}
# 2.79
if is_2_79:
    ALPHA_NODES["Alpha"] = 'BSDF_TRANSPARENT'


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

PRINCIPLED_BAKER_TEMP_MATERIAL_NAME = "PRINCIPLED_BAKER_TEMP_MATERIAL_{}".format(
    time.time())

# signs not allowed in file names or paths
NOT_ALLOWED_SIGNS = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']


def fill_image(image, color):
    image.pixels[:] = color * image.size[0] * image.size[1]


def is_list_equal(list):
    """return True, if all items in list are equal"""
    if not list:
        return False  # False, if list is empty
    first = list[0]
    return all(first == item for item in list[1:])


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


def new_rgb_node(mat, color=(0, 0, 0, 1)):
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


def new_pb_emission_node(material, color=[0, 0, 0, 1]):
    node = material.node_tree.nodes.new(type='ShaderNodeEmission')
    node.inputs['Color'].default_value = color  # [0, 0, 0, 1]
    node[NODE_TAG] = 1
    return node


def new_pb_output_node(material):
    node = material.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
    node.is_active_output = True
    node[NODE_TAG] = 1
    return node


def get_combined_images(img1, img2, from_channel, to_channel):
    n = 4
    size = img1.size[0] * img1.size[1]
    a = numpy.array(img1.pixels).reshape(size, n)
    b = numpy.array(img2.pixels).reshape(size, n)
    a[:, to_channel] = b[:, from_channel]  # numpy magic happens here
    return a.reshape(size * n)


def combine_channels_to_image(target_image, R=None, G=None, B=None, A=None, channel_r=0, channel_g=0, channel_b=0, channel_a=0):
    """combine image channels into RGBA-channels of target image"""

    n = 4
    t = numpy.array(target_image.pixels)
    if R:
        t[0::n] = numpy.array(R.pixels)[channel_r::n]
    if G:
        t[1::n] = numpy.array(G.pixels)[channel_g::n]
    if B:
        t[2::n] = numpy.array(B.pixels)[channel_b::n]
    if A:
        t[3::n] = numpy.array(A.pixels)[channel_a::n]
    target_image.pixels = t


def get_invert_image(img):
    n = 4
    size = img.size[0] * img.size[1]
    a = numpy.array(img.pixels).reshape(size, n)
    a[:, 0:3] = 1 - a[:, 0:3]
    return a.reshape(size * n)


def get_sibling_node(node):
    if node.outputs[0].is_linked:
        parent_node = node.outputs[0].links[0].to_node
        for input_socket in parent_node.inputs:
            if input_socket.is_linked:
                child_node = input_socket.links[0].from_node
                if not child_node == node:
                    if input_socket.type == node.outputs[0].links[0].to_socket.type:
                        return child_node


def are_nodes_connected(node, to_node):
    if node == to_node:
        return True
    for output_socket in node.outputs:
        if output_socket.is_linked:
            to_node_tmp = output_socket.links[0].to_node
            return are_nodes_connected(to_node_tmp, to_node)


def is_node_type_in_node_tree(material, node, node_type):
    for n in material.node_tree.nodes:
        if n.type == node_type:
            if are_nodes_connected(n, node):
                return True


def are_node_types_in_node_tree(material, node, node_types):
    for n_type in node_types:
        return is_node_type_in_node_tree(material, node, n_type)


def select_set(obj, s):
    # 2.79
    if is_2_79:
        obj.select = s
    # 2.80
    else:
        obj.select_set(s)


def save_image_as(image, file_path, file_format, color_mode='RGB', color_depth='8', compression=15, quality=90, tiff_codec='DEFLATE', exr_codec='ZIP'):
    s = bpy.context.scene.render.image_settings
    fm = s.file_format
    cm = s.color_mode
    cd = s.color_depth
    c = s.compression
    q = s.quality
    tc = s.tiff_codec
    ec = s.exr_codec
    vt = bpy.context.scene.view_settings.view_transform

    s.file_format = file_format
    s.color_mode = color_mode
    s.color_depth = color_depth
    s.compression = compression
    s.quality = quality
    s.tiff_codec = tiff_codec
    s.exr_codec = exr_codec
    defalut_vt = 'Standard' if is_2_80 else 'Default'
    bpy.context.scene.view_settings.view_transform = defalut_vt

    image.use_view_as_render = False

    abs_path = bpy.path.abspath(file_path)

    image.save_render(abs_path)

    s.file_format = fm
    s.color_mode = cm
    s.color_depth = cd
    s.compression = c
    s.quality = q
    s.tiff_codec = tc
    s.exr_codec = ec
    bpy.context.scene.view_settings.view_transform = vt


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
                prepare_bake_factor(
                    mat, from_socket, new_socket, node_type, factor_name)


def is_mixnode_in_node_tree(node):
    """return True only if mix node is higher in tree"""
    node_type = 'MIX_RGB'
    if node.type == node_type:
        return True
    elif node.type == 'AMBIENT_OCCLUSION':
        return False
    else:
        for input_socket in node.inputs:
            if input_socket.is_linked:
                from_node = input_socket.links[0].from_node
                if is_mixnode_in_node_tree(from_node):
                    return True
        return False


def prepare_bake_ao(mat, socket, new_socket):

    node = socket.node

    if node.type == 'MIX_RGB':
        if node.inputs[1].is_linked and node.inputs[2].is_linked:
            from_node_1 = node.inputs[1].links[0].from_node
            from_node_2 = node.inputs[2].links[0].from_node
            is_ao_in_1 = is_node_type_in_node_tree(mat,
                                                   from_node_1, 'AMBIENT_OCCLUSION')
            is_ao_in_2 = is_node_type_in_node_tree(mat,
                                                   from_node_2, 'AMBIENT_OCCLUSION')
            if is_ao_in_1 and is_ao_in_2:
                from_socket = socket
                mat.node_tree.links.new(from_socket, new_socket)
                return

    if is_node_type_in_node_tree(mat, node, 'AMBIENT_OCCLUSION'):
        if not is_mixnode_in_node_tree(node):
            if not socket.type == 'SHADER':
                from_socket = socket
                mat.node_tree.links.new(from_socket, new_socket)
            else:
                for input_socket in node.inputs:
                    if input_socket.is_linked:
                        from_socket = input_socket.links[0].from_socket
                        prepare_bake_ao(mat, from_socket, new_socket)
        else:
            for input_socket in node.inputs:
                if input_socket.is_linked:
                    from_socket = input_socket.links[0].from_socket
                    prepare_bake_ao(mat, from_socket, new_socket)
    else:
        for input_socket in node.inputs:
            if input_socket.is_linked:
                from_socket = input_socket.links[0].from_socket
                prepare_bake_ao(mat, from_socket, new_socket)


def prepare_bake_color(mat, from_socket, new_socket):
    node = from_socket.node

    # find and unlink AO trees in tagged nodes
    for node in mat.node_tree.nodes:
        if node.type == 'MIX_RGB' and NODE_TAG in node.keys():
            for i, node_input in enumerate(node.inputs[1:]):
                if node_input.is_linked:
                    from_node = node_input.links[0].from_node
                    if not is_mixnode_in_node_tree(from_node):
                        if is_node_type_in_node_tree(mat, from_node, 'AMBIENT_OCCLUSION'):
                            mat.node_tree.links.remove(node_input.links[0])

                            # if 'Fac' not linked, set to 0 or 1
                            fac_in = node.inputs[0]
                            if not fac_in.is_linked:
                                fac_in.default_value = 0 if i == 1 else 1

    mat.node_tree.links.new(from_socket, new_socket)


def prepare_bake(mat, socket, new_socket, input_socket_name):
    settings = bpy.context.scene.principled_baker_settings

    if input_socket_name in NORMAL_INPUTS:
        color = (0.5, 0.5, 1.0, 1.0)
    else:
        color = (0.0, 0.0, 0.0, 0.0)

    # 2.79
    if is_2_79:
        if input_socket_name == 'Displacement':
            if socket.is_linked:
                from_socket = socket.links[0].from_socket
                mat.node_tree.links.new(from_socket, new_socket)

    node = socket.node

    if node.type == 'OUTPUT_MATERIAL':
        from_socket = socket.links[0].from_socket
        prepare_bake(mat, from_socket, new_socket, input_socket_name)

    elif node.type == 'MIX_SHADER':
        color2 = [1, 1, 1, 0] if input_socket_name == 'Fac' else color
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
                if settings.use_exclude_transparent_colors:
                    if next_node.type in ALPHA_NODES.values() or next_node.type == 'BSDF_TRANSPARENT':
                        other_i = i % 2 + 1
                        mix_node.inputs[i].default_value = (0, 0, 0, 0)
                        mix_node.inputs[other_i].default_value = (1, 1, 1, 0)
                        if node.inputs[other_i].is_linked:
                            from_socket = node.inputs[other_i].links[0].from_socket
                            new_socket = mix_node.inputs[i]
                    else:
                        from_socket = node.inputs[i].links[0].from_socket
                        new_socket = mix_node.inputs[i]
                    prepare_bake(mat, from_socket, new_socket,
                                 input_socket_name)

    elif node.type == 'ADD_SHADER' and not input_socket_name == 'Fac':
        mix_node = new_mixrgb_node(mat, 1, color, color)
        mix_node.blend_type = 'ADD'
        mat.node_tree.links.new(mix_node.outputs[0], new_socket)
        mix_node.label = input_socket_name

        for i, input in enumerate(node.inputs):
            if input.is_linked:
                from_socket = input.links[0].from_socket
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

        if input_socket_name == 'Ambient Occlusion':
            # AO: remove all non-ao branches
            for tmp_node in mat.node_tree.nodes:
                if tmp_node.type == 'MIX_RGB' and NODE_TAG in tmp_node.keys():
                    for i, node_input in enumerate(tmp_node.inputs[1:]):
                        if node_input.is_linked:
                            from_node = node_input.links[0].from_node
                            if not is_node_type_in_node_tree(mat, from_node, 'AMBIENT_OCCLUSION'):
                                mat.node_tree.links.remove(node_input.links[0])

                                # if 'Fac' not linked, set to 0 or 1
                                fac_in = tmp_node.inputs[0]
                                if not fac_in.is_linked:
                                    fac_in.default_value = 0 if i == 1 else 1

            # AO: link ao branch
            for input_socket in node.inputs:
                if input_socket.type == 'RGBA':
                    if input_socket.is_linked:
                        from_node = input_socket.links[0].from_node
                        if is_node_type_in_node_tree(mat, from_node, 'AMBIENT_OCCLUSION'):
                            from_socket = input_socket.links[0].from_socket
                            mat.node_tree.links.new(from_socket, new_socket)

        elif input_socket_name in node.inputs.keys():
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
                        node = mat.node_tree.nodes.new(
                            type="ShaderNodeRGBToBW")
                        node[NODE_TAG] = 1
                        mat.node_tree.links.new(from_socket, node.inputs[0])
                        mat.node_tree.links.new(node.outputs[0], new_socket)
                else:
                    value_node = mat.node_tree.nodes.new(
                        type="ShaderNodeValue")
                    value_node[NODE_TAG] = 1
                    value_node.outputs[0].default_value = node.inputs[input_socket_name].default_value
                    mat.node_tree.links.new(value_node.outputs[0], new_socket)

            elif input_socket.type == 'VECTOR':
                if input_socket.name == input_socket_name:
                    # 2.79
                    if is_2_79:
                        if input_socket.is_linked:
                            from_socket = input_socket.links[0].from_socket
                            if from_socket.node.type == 'NORMAL_MAP':
                                prepare_bake(mat, from_socket,
                                             new_socket, 'Color')
                            if from_socket.node.type == 'BUMP':
                                prepare_bake(mat, from_socket,
                                             new_socket, 'Height')
                    # 2.80
                    else:
                        if input_socket.is_linked:
                            from_socket = input_socket.links[0].from_socket
                            mat.node_tree.links.new(from_socket, new_socket)

        else:
            for input_socket in node.inputs:
                if input_socket.is_linked:
                    from_socket = input_socket.links[0].from_socket
                    prepare_bake(mat, from_socket, new_socket,
                                 input_socket_name)


def add_temp_material(obj):
    name = "PRINCIPLED_BAKER_TEMP_MATERIAL_{}".format(time.time())
    mat = bpy.data.materials.new(name)
    mat[MATERIAL_TAG_VERTEX] = 1
    mat.use_nodes = True
    principled_node = find_node_by_type(mat, 'BSDF_PRINCIPLED')
    principled_node.inputs["Base Color"].default_value = [0, 0, 0, 1]
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
                if MATERIAL_TAG not in mat_slot.material.keys():
                    material_output = get_active_output(mat_slot.material)
                    if material_output is None:
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
    list = []
    for o in objects:
        if o.type == 'MESH':
            list.append(o)
    return list


def get_active_outputs(objects):
    if not isinstance(objects, list):
        objects = [objects]

    active_outputs = []
    for obj in objects:
        for mat_slot in obj.material_slots:
            if mat_slot.material:
                if MATERIAL_TAG not in mat_slot.material.keys():
                    node = get_active_output(mat_slot.material)
                    if node:
                        active_outputs.append(node)
    return active_outputs


def get_all_material_outputs(objects):
    if not isinstance(objects, list):
        objects = [objects]

    outputs = {}
    for obj in objects:
        for mat_slot in obj.material_slots:
            if mat_slot.material:
                for node in mat_slot.material.node_tree.nodes:
                    if node.type == "OUTPUT_MATERIAL":
                        # 2.79
                        if is_2_79:
                            outputs[node] = None
                        # 2.80
                        else:
                            outputs[node] = node.target
    return outputs


def set_material_outputs_target_to_all(objects):
    if not isinstance(objects, list):
        objects = [objects]

    for obj in objects:
        for mat_slot in obj.material_slots:
            if mat_slot.material:
                for node in mat_slot.material.node_tree.nodes:
                    if node.type == "OUTPUT_MATERIAL":
                        node.target = 'ALL'


def prepare_material_for_bake(material, do_ungroup_values=True):
    mat = material

    # TODO location too far off on large node trees
    # location_list = []
    # for node in mat.node_tree.nodes:
    #     location_list.append(node.location.x)
    # loc_most_left = min(location_list)
    # loc_most_right = max(location_list)

    # Duplicate node tree from active output
    active_output = get_active_output(mat)
    selected_nodes = get_all_nodes_linked_from(active_output)
    selected_nodes = duplicate_nodes(mat, selected_nodes, keep_inputs=True)

    # TAG all selected nodes for clean up
    for node in selected_nodes:
        node[NODE_TAG] = 1

    # Ungroup all groups in selected nodes
    group_nodes = [n for n in selected_nodes if n.type == 'GROUP']
    selected_nodes = ungroup_nodes(
        mat, group_nodes, do_ungroup_values=do_ungroup_values)

    # TAG all selected nodes for clean up
    for node in selected_nodes:
        node[NODE_TAG] = 1

    # move temp nodes in location and put in frame
    # TODO
    # for node in mat.node_tree.nodes:
    #     if NODE_TAG in node.keys():
    #         node.location.x += abs(loc_most_left - loc_most_right) + 500
    p_baker_frame = mat.node_tree.nodes.new(type="NodeFrame")
    for node in mat.node_tree.nodes:
        if NODE_TAG in node.keys():
            node.parent = p_baker_frame
    p_baker_frame.name = "p_baker_temp_frame"
    p_baker_frame.label = "PRINCIPLED BAKER NODES (If you see this, something went wrong!)"
    p_baker_frame.use_custom_color = True
    p_baker_frame.color = (1, 0, 0)
    p_baker_frame[NODE_TAG] = 1
    p_baker_frame.label_size = 64

    for node in mat.node_tree.nodes:
        if NODE_TAG in node.keys() and node.type == "OUTPUT_MATERIAL":
            new_output = node
            new_output.is_active_output = True
    return new_output


def get_joblist_from_object(obj, by_value_differ=True, by_connected_inputs=True):
    joblist = dict()
    settings = bpy.context.scene.principled_baker_settings

    for mat_slot in obj.material_slots:
        if mat_slot.material:
            mat = mat_slot.material
            prepare_material_for_bake(mat, do_ungroup_values=False)

    # add to joblist if values differ
    if by_value_differ:
        if settings.bake_mode == 'BATCH':
            value_list = []

            for value_name in NODE_INPUTS:
                value_list.clear()
                if value_name not in joblist and value_name not in ['Subsurface Radius', 'Normal', 'Clearcoat Normal', 'Tangent']:

                    for mat_slot in obj.material_slots:
                        if mat_slot.material:
                            mat = mat_slot.material

                            material_output = None
                            for node in mat.node_tree.nodes:
                                if node.type == "OUTPUT_MATERIAL" and NODE_TAG in node.keys():
                                    material_output = node

                            if material_output:
                                value_list.extend(get_value_list_from_bsdf_nodes_in_material(
                                    mat, material_output, value_name))
                    if value_list:
                        if not is_list_equal(value_list):
                            joblist[value_name] = True

    # search material for jobs by connected node types
    if by_connected_inputs:
        for mat_slot in obj.material_slots:
            if mat_slot.material:
                mat = mat_slot.material
                if MATERIAL_TAG not in mat_slot.material.keys():
                    material_output = None
                    for node in mat.node_tree.nodes:
                        if node.type == "OUTPUT_MATERIAL" and NODE_TAG in node.keys():
                            material_output = node
                    if material_output:
                        # add special cases:
                        # Alpha node: Transparent
                        if is_node_type_in_node_tree(mat, material_output, 'BSDF_TRANSPARENT'):
                            # if not 'Alpha' in joblist:
                            joblist['Alpha'] = True

                        # Alpha for nodes: Translucent, Glass
                        for alpha_name, n_type in ALPHA_NODES.items():
                            if is_node_type_in_node_tree(mat, material_output, n_type):
                                # if not alpha_name in joblist:
                                joblist[alpha_name] = True

                        # Emission
                        if is_node_type_in_node_tree(mat, material_output, 'EMISSION'):
                            # if not 'Emission' in joblist:
                            joblist['Emission'] = True

                        # AO - 2.80 only
                        if is_2_80:
                            if is_node_type_in_node_tree(mat, material_output, 'AMBIENT_OCCLUSION'):
                                # if not 'Ambient Occlusion' in joblist:
                                joblist['Ambient Occlusion'] = True

                        # Displacement
                        socket_name = 'Displacement'
                        if material_output.inputs[socket_name].is_linked:
                            joblist[socket_name] = True

                        # Bump
                        socket_name = 'Bump'
                        if settings.use_Bump and is_node_type_in_node_tree(mat, material_output, 'BUMP'):
                            if socket_name not in joblist:
                                joblist[socket_name] = True

                        # BSDF nodes
                        for node in mat.node_tree.nodes:
                            if NODE_TAG in node.keys():
                                if node.type in BSDF_NODES:
                                    for socket in node.inputs:
                                        socket_name = socket.name
                                        if socket_name in NODE_INPUTS + ['Base Color']:
                                            if socket.is_linked:
                                                if are_nodes_connected(node, material_output):
                                                    socket_name = 'Color' if socket_name == 'Base Color' else socket_name
                                                    # if not socket_name in joblist:
                                                    joblist[socket_name] = True

    # force bake of Color, if user wants alpha in color
    if settings.use_alpha_to_color and settings.color_mode == 'RGBA':
        # if not 'Color' in joblist:
        joblist['Color'] = True

    # Clean up! - delete temp nodes
    for mat_slot in obj.material_slots:
        if mat_slot.material:
            delete_tagged_nodes(mat_slot.material, NODE_TAG)

    return joblist


def get_joblist_from_objects(objs, by_value_differ=True, by_connected_inputs=True):
    joblist = dict()
    settings = bpy.context.scene.principled_baker_settings

    if settings.bake_mode == 'SELECTED_TO_ACTIVE':
        # exclude active object from selected objects
        if bpy.context.active_object in objs:
            objs.remove(bpy.context.active_object)
        # return "Normal" only, if one object has no material
        for obj in objs:
            if not has_material(obj):
                return ["Normal"]

    # add to joblist if values differ
    if by_value_differ:
        if not settings.bake_mode == 'BATCH':
            for obj in objs:
                for mat_slot in obj.material_slots:
                    if mat_slot.material:
                        mat = mat_slot.material
                        prepare_material_for_bake(mat, do_ungroup_values=False)

            value_list = []
            for value_name in NODE_INPUTS:
                value_list.clear()
                if value_name not in joblist and value_name not in ['Subsurface Radius', 'Normal', 'Clearcoat Normal', 'Tangent']:
                    for obj in objs:
                        for mat_slot in obj.material_slots:
                            if mat_slot.material:
                                mat = mat_slot.material

                            material_output = None
                            for node in mat.node_tree.nodes:
                                if node.type == "OUTPUT_MATERIAL" and NODE_TAG in node.keys():
                                    material_output = node

                            if material_output:
                                value_list.extend(get_value_list_from_bsdf_nodes_in_material(
                                    mat, material_output, value_name))
                    if value_list:
                        if not is_list_equal(value_list):
                            joblist[value_name] = True

            # Clean up! - delete temp nodes
            for obj in objs:
                for mat_slot in obj.material_slots:
                    if mat_slot.material:
                        delete_tagged_nodes(mat_slot.material, NODE_TAG)

    for obj in objs:
        for job in get_joblist_from_object(obj, by_value_differ=by_value_differ, by_connected_inputs=by_connected_inputs):
            # if job not in joblist:
            joblist[job] = True
    return joblist


def get_joblist_manual():
    joblist = dict()
    settings = bpy.context.scene.principled_baker_settings
    bakelist = bpy.context.scene.principled_baker_bakelist

    for job_name, data in bakelist.items():
        if data.do_bake:
            joblist[job_name] = True

    # force bake of Color, if user wants alpha in color
    if settings.use_alpha_to_color and settings.color_mode == 'RGBA':
        if 'Color' not in joblist:
            joblist['Color'] = True
        if 'Alpha' not in joblist:
            joblist['Alpha'] = True

    return joblist


def check_permission(path):
    if not path.endswith("\\"):
        path += "\\"
    return os.access(path, os.W_OK)


def get_all_nodes_linked_from(node):
    nodes = []

    def linked_from(node):
        if node:
            nodes.append(node)
            for input_socket in node.inputs:
                if input_socket.is_linked:
                    from_node = input_socket.links[0].from_node
                    linked_from(from_node)
    linked_from(node)
    return nodes


def socket_index(socket):
    node = socket.node
    sockets = node.outputs if socket.is_output else node.inputs
    for i, s in enumerate(sockets):
        if s.is_linked:
            if socket == s:
                return i
                break


def duplicate_node(mat, node):

    node_type = str(type(node)).split('.')[-1][:-2]
    new_node = mat.node_tree.nodes.new(type=node_type)

    # copy attributes
    for attr in dir(node):
        try:
            a = getattr(node, attr)
            setattr(new_node, attr, a)
        except AttributeError:
            pass

    # Color Ramp
    if node.type == 'VALTORGB':
        for attr in dir(node.color_ramp):
            try:
                a = getattr(node.color_ramp, attr)
                setattr(new_node.color_ramp, attr, a)
            except AttributeError:
                pass

        for i, col_ramp_elem in enumerate(node.color_ramp.elements):
            try:
                new_node.color_ramp.elements[i].color = col_ramp_elem.color
                new_node.color_ramp.elements[i].position = col_ramp_elem.position
            except IndexError:
                pos = col_ramp_elem.position
                new_elem = new_node.color_ramp.elements.new(pos)
                new_elem.color = col_ramp_elem.color

    # Curve
    if node.type == 'CURVE_RGB':
        for attr in dir(node.mapping):
            try:
                a = getattr(node.mapping, attr)
                setattr(new_node.mapping, attr, a)
            except AttributeError:
                pass

        # copy every point in every curve
        for i, curve in enumerate(node.mapping.curves):
            for j, point in enumerate(curve.points):
                try:
                    new_node.mapping.curves[i].points[j].location = point.location
                    new_node.mapping.curves[i].points[j].handle_type = point.handle_type
                except IndexError:
                    pos = point.location[0]
                    val = point.location[1]
                    new_node.mapping.curves[i].points.new(pos, val)

    # copy values inputs
    for i, input in enumerate(node.inputs):
        try:
            new_node.inputs[i].default_value = input.default_value
        except:
            pass

    # copy values outputs
    for i, output in enumerate(node.outputs):
        try:
            new_node.outputs[i].default_value = output.default_value
        except:
            pass

    return new_node


def duplicate_nodes(mat, nodes, keep_inputs=False):

    new_nodes = {}

    for node in set(nodes):
        new_node = duplicate_node(mat, node)
        new_nodes[node] = new_node

    if keep_inputs:
        for node, new_node in new_nodes.items():
            len_inputs = len(node.inputs)
            if len_inputs > 0:
                for i, input in enumerate(node.inputs):
                    if input.is_linked:
                        link = input.links[0]
                        from_node = link.from_node
                        to_socket = new_node.inputs[i]
                        if from_node in new_nodes.keys():
                            from_socket_index = socket_index(link.from_socket)
                            from_socket = new_nodes[from_node].outputs[from_socket_index]
                        else:
                            from_socket = link.from_socket
                        mat.node_tree.links.new(from_socket, to_socket)

    return list(new_nodes.values())


def ungroup_nodes(mat, group_nodes, do_ungroup_values=True):

    new_nodes = {}
    val_nodes = []

    def duplicate_from_input_socket(mat, input_socket, link_to_socket):
        if not input_socket:
            return
        old_node = input_socket.links[0].from_node
        old_from_socket = input_socket.links[0].from_socket
        if old_node.type == 'GROUP_INPUT':

            # link
            index_in = socket_index(old_from_socket)
            if group_node.inputs[index_in].is_linked:
                from_socket = group_node.inputs[index_in].links[0].from_socket
                to_socket = link_to_socket
                mat.node_tree.links.new(from_socket, to_socket)
            return

        # create new node or take existing
        index_out = socket_index(old_from_socket)
        if old_node in new_nodes.keys():
            new_node = new_nodes[old_node]
            # link
            from_socket = new_node.outputs[index_out]
            to_socket = link_to_socket
            mat.node_tree.links.new(from_socket, to_socket)
            return
        else:
            new_node = duplicate_node(mat, old_node)
            new_nodes[old_node] = new_node
            # link
            from_socket = new_node.outputs[index_out]
            to_socket = link_to_socket
            mat.node_tree.links.new(from_socket, to_socket)

            for input_socket in old_node.inputs:
                if input_socket.is_linked:
                    index_in = socket_index(input_socket)
                    link_to_socket = new_node.inputs[index_in]
                    duplicate_from_input_socket(
                        mat, input_socket, link_to_socket)

    for group_node in group_nodes:

        if group_node.type == 'GROUP':

            # group_input_outputs
            group_input_nodes = [
                n for n in group_node.node_tree.nodes if n.type == 'GROUP_INPUT']
            output_count = len(group_input_nodes[0].outputs)
            group_input_outputs = [None] * output_count
            for node in group_input_nodes:
                for i, output in enumerate(node.outputs):
                    if output.is_linked:
                        group_input_outputs[i] = output

            # group_output_inputs
            group_output_nodes = [
                n for n in group_node.node_tree.nodes if n.type == 'GROUP_OUTPUT']
            input_count = len(group_output_nodes[0].inputs)
            group_output_inputs = [None] * input_count
            for node in group_output_nodes:
                for i, input in enumerate(node.inputs):
                    if input.is_linked:
                        group_output_inputs[i] = input

            # new value nodes
            if do_ungroup_values:
                for index, input in enumerate(group_node.inputs):
                    if group_input_outputs[index]:
                        if not input.is_linked:
                            val = input.default_value
                            tmp_node = None
                            if input.type == 'VALUE':
                                tmp_node = mat.node_tree.nodes.new(
                                    type="ShaderNodeValue")
                                tmp_node.outputs[0].default_value = val
                            elif input.type == 'RGBA':
                                tmp_node = mat.node_tree.nodes.new(
                                    type="ShaderNodeRGB")
                                tmp_node.outputs[0].default_value = val
                            if tmp_node:
                                val_nodes.append(tmp_node)
                                from_socket = tmp_node.outputs[0]
                                to_socket = input
                                mat.node_tree.links.new(from_socket, to_socket)

            for output in group_node.outputs:
                if output.is_linked:
                    index = socket_index(output)
                    input_socket = group_output_inputs[index]
                    to_sockets = [
                        link.to_socket for link in group_node.outputs[index].links]
                    for link_to_socket in to_sockets:
                        duplicate_from_input_socket(
                            mat, input_socket, link_to_socket)

            # delete group node
            mat.node_tree.nodes.remove(group_node)

    # remove non linked value nodes
    for node in val_nodes:
        if not node.outputs[0].is_linked:
            mat.node_tree.nodes.remove(node)
            val_nodes.remove(node)

    return list(new_nodes.values()) + val_nodes


def delete_tagged_nodes(material, tag):
    for node in material.node_tree.nodes:
        if tag in node.keys():
            material.node_tree.nodes.remove(node)


def delete_tagged_nodes_in_object(obj):
    for mat_slot in obj.material_slots:
        if mat_slot.material:
            delete_tagged_nodes(mat_slot.material, NODE_TAG)


def deactivate_material_outputs(material):
    for node in material.node_tree.nodes:
        if node.type == "OUTPUT_MATERIAL":
            node.is_active_output = False


def remove_not_allowed_signs(string):
    """retuns string (eg. from object name) without all signs not allowed in file names or paths"""
    for s in NOT_ALLOWED_SIGNS:
        string = string.replace(s, "")
    return string


def delete_tagged_materials(obj, tag):
    for i, mat_slot in enumerate(obj.material_slots):
        if mat_slot.material:
            if tag in mat_slot.material.keys():
                bpy.context.object.active_material_index = i
                bpy.ops.object.material_slot_remove({'object': obj})


def disable_material_outputs(obj):
    for mat_slot in obj.material_slots:
        if mat_slot.material:
            for node in mat_slot.material.node_tree.nodes:
                if node.type == "OUTPUT_MATERIAL":
                    node.is_active_output = False


def get_value_from_node_by_name(node, value_name):
    tmp_value_name = value_name
    if value_name == 'Color' and node.type == 'BSDF_PRINCIPLED':
        tmp_value_name = "Base Color"

    if tmp_value_name in node.inputs.keys():
        if node.inputs[tmp_value_name].type == 'RGBA':
            r, g, b, a = node.inputs[tmp_value_name].default_value
            return [r, g, b, a]
        else:
            return node.inputs[value_name].default_value


def get_value_list_from_bsdf_nodes_in_material(material, node, value_name):
    value_list = []
    for n in material.node_tree.nodes:
        if n.type in BSDF_NODES:
            if are_nodes_connected(n, node):
                val = get_value_from_node_by_name(n, value_name)
                if val is not None:
                    value_list.append(val)
    return value_list


def get_value_list(node, value_name):
    """Return a list of all values by value name in a node tree starting from node.
    Values from Normal Map are exclued."""

    value_list = []

    def find_values(node, value_name):
        if not node.type == 'NORMAL_MAP':
            val = get_value_from_node_by_name(node, value_name)
            if val is not None:
                value_list.append(val)

            for socket in node.inputs:
                if socket.is_linked:
                    from_node = socket.links[0].from_node
                    find_values(from_node, value_name)

    find_values(node, value_name)
    return value_list


def get_value_list_from_node_types(node, value_name, node_types):
    """Return a list of all values by value name with node types in a node tree starting from node.
    Values from Normal Map are exclued."""

    value_list = []

    def find_values(node, value_name, node_types):
        if value_name == 'Color' and node.type == 'BSDF_PRINCIPLED':
            tmp_value_name = 'Base Color'
        else:
            tmp_value_name = value_name

        if node.type in node_types and tmp_value_name in node.inputs.keys():
            val = get_value_from_node_by_name(node.inputs[tmp_value_name])
            if val is not None:
                value_list.append(val)

        for socket in node.inputs:
            if socket.is_linked:
                from_node = socket.links[0].from_node
                find_values(from_node, value_name, node_types)

    find_values(node, value_name, node_types)
    return value_list
