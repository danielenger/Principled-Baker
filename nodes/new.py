from ..const import NODE_TAG


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


def create_bake_image_node(mat, image):
    bake_image_node = new_image_node(mat)
    bake_image_node.image = image  # add image to node
    bake_image_node[NODE_TAG] = 1  # tag for clean up
    bake_image_node.label = "TEMP BAKE NODE (If you see this, something went wrong!)"
    bake_image_node.use_custom_color = True
    bake_image_node.color = (1, 0, 0)

    # make only bake_image_node active
    bake_image_node.select = True
    mat.node_tree.nodes.active = bake_image_node


def create_bake_image_nodes(objects, image):
    for obj in objects:
        for mat_slot in obj.material_slots:
            if mat_slot.material:
                create_bake_image_node(mat_slot.material, image)
