import bpy
import os
import numpy

PRINCIPLED_NODE_TAG = 'p_baker_node'


def fill_image(image, color):
    image.pixels[:] = color * image.size[0] * image.size[1]


def is_list_equal(list):
    list = iter(list)
    try:
        first = next(list)
    except StopIteration:
        return True
    return all(first == rest for rest in list)


def find_active_output(mat):
    for node in mat.node_tree.nodes:
        if node.type == "OUTPUT_MATERIAL" and node.is_active_output:
            return node


def find_node_by_type(mat, node_type):
    for node in mat.node_tree.nodes:
        if node.type == node_type:
            return node


def new_rgb_node(mat, color=[0, 0, 0, 1]):
    node = mat.node_tree.nodes.new(type="ShaderNodeRGB")
    node[PRINCIPLED_NODE_TAG] = 1
    node.outputs['Color'].default_value = color
    node.color = (0.8, 0.8, 0.8)
    node.use_custom_color = True
    return node


def new_mixrgb_node(mat, fac=0.5, color1=[0, 0, 0, 1], color2=[0, 0, 0, 1]):
    node = mat.node_tree.nodes.new(type="ShaderNodeMixRGB")
    node[PRINCIPLED_NODE_TAG] = 1
    node.inputs[0].default_value = fac
    node.inputs[1].default_value = color1
    node.inputs[2].default_value = color2
    node.color = (0.8, 0.8, 0.8)
    node.use_custom_color = True
    return node


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



def prepare_for_bake_color(mat, o, n):

    node = o.node

    if not is_node_type_in_node_tree(node, 'AMBIENT_OCCLUSION'):
        mat.node_tree.links.new(o, n)
    
    else:
        if node.type == 'MIX_RGB':
            color1 = node.inputs['Color1'].default_value
            color2 = node.inputs['Color2'].default_value
            fac = node.inputs['Fac'].default_value
            new_node = new_mixrgb_node(mat, fac, color1, color2)
            new_node.inputs['Fac'].default_value = node.inputs['Fac'].default_value            
            mat.node_tree.links.new(new_node.outputs[0], n)

            if node.blend_type == 'MIX':
     
                if node.inputs['Fac'].is_linked:
                    o = node.inputs['Fac'].links[0].from_socket
                    n = new_node.inputs['Fac']
                    mat.node_tree.links.new(o, n)

                if node.inputs['Color1'].is_linked:
                    from_node = node.inputs['Color1'].links[0].from_node
                    if from_node.type == 'AMBIENT_OCCLUSION':
                        new_node.inputs['Color1'].default_value = from_node.inputs['Color'].default_value
                    o = node.inputs['Color1'].links[0].from_socket
                    n = new_node.inputs['Color1']
                    prepare_for_bake_color(mat, o, n)

                if node.inputs['Color2'].is_linked:
                    from_node = node.inputs['Color2'].links[0].from_node
                    if from_node.type == 'AMBIENT_OCCLUSION':
                        new_node.inputs['Color2'].default_value = from_node.inputs['Color'].default_value
                    o = node.inputs['Color2'].links[0].from_socket
                    n = new_node.inputs['Color2']
                    prepare_for_bake_color(mat, o, n)

            else:
               
                if node.inputs['Color1'].is_linked:
                    from_node = node.inputs['Color1'].links[0].from_node
                    if from_node.type == 'AMBIENT_OCCLUSION':
                        new_node.inputs['Fac'].default_value = 1
                        new_node.inputs['Color1'].default_value = from_node.inputs['Color'].default_value
                        o = node.inputs['Color2'].links[0].from_socket
                        n = new_node.inputs['Color2']
                        prepare_for_bake_color(mat, o, n)

                if node.inputs['Color2'].is_linked:
                    from_node = node.inputs['Color2'].links[0].from_node
                    if from_node.type == 'AMBIENT_OCCLUSION':
                        new_node.inputs['Fac'].default_value = 0
                        new_node.inputs['Color2'].default_value = from_node.inputs['Color'].default_value
                        o = node.inputs['Color1'].links[0].from_socket
                        n = new_node.inputs['Color1']
                        prepare_for_bake_color(mat, o, n)

        # skip over AO, if linked
        elif node.type == 'AMBIENT_OCCLUSION':
            color = node.inputs['Color'].default_value
            if node.inputs['Color'].is_linked:
                o = node.inputs['Color'].links[0].from_socket
                prepare_for_bake_color(mat, o, n)
        else:
            mat.node_tree.links.new(o, n)


def remove_empty_material_slots(obj):
    for mat_slot in obj.material_slots:
        if not mat_slot.material:
            index = obj.material_slots.find('')
            bpy.context.object.active_material_index = index
            bpy.ops.object.material_slot_remove({'object': obj})
