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


def new_mixrgb_node(mat, color1=[0, 0, 0, 1], color2=[0, 0, 0, 1]):
    node = mat.node_tree.nodes.new(type="ShaderNodeMixRGB")
    node[PRINCIPLED_NODE_TAG] = 1
    node.inputs[1].default_value = color1
    node.inputs[2].default_value = color2
    node.color = (0.8, 0.8, 0.8)
    node.use_custom_color = True
    return node


def combine_images(img1, img2, from_channel, to_channel):
    n = 4
    size = img1.size[0] * img1.size[1]
    a = numpy.array(img1.pixels).reshape(size, n)
    b = numpy.array(img2.pixels).reshape(size, n)
    a[:, to_channel] = b[:, from_channel]  # numpy magic happens here
    img1.pixels = a.reshape(size * n)
    img1.save()


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
