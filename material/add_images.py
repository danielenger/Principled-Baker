import bpy

from ..const import (ALPHA_NODES, NODE_INPUTS_SORTED,
                                    NORMAL_INPUTS)
from ..nodes.find import find_node_by_type
from ..nodes.new import new_image_node, new_mixrgb_node
from ..nodes.node import get_sibling_node


def add_images_to_material(new_images, new_mat):
    """Add new images to new material. Nodes will be linked and arranged."""

    settings = bpy.context.scene.principled_baker_settings

    def new_link(from_socket, to_socket):
        new_mat.node_tree.links.new(from_socket, to_socket)

    NOT_TO_LINK_NODES = {"Glossiness", "Ambient Occlusion",
                         "Vertex Color", "Material ID", "Diffuse", "Wireframe"}

    NEW_NODE_COLORS = {
        "Alpha": [1.0, 1.0, 1.0, 1.0],
        "Translucent_Alpha": [0.8, 0.8, 0.8, 1.0],
        "Glass_Alpha": [1.0, 1.0, 1.0, 1.0],
        'Emission': [1.0, 1.0, 1.0, 1.0],
    }

    NODE_OFFSET_X = 300
    NODE_OFFSET_Y = 200

    IMAGE_NODE_OFFSET_X = -900
    IMAGE_NODE_OFFSET_Y = -260
    IMAGE_NODE_WIDTH = 300

    principled_node = find_node_by_type(new_mat, 'BSDF_PRINCIPLED')
    material_output = find_node_by_type(new_mat, 'OUTPUT_MATERIAL')

    nodes = new_mat.node_tree.nodes

    if new_images:
        tex_coord_node = nodes.new(type="ShaderNodeTexCoord")
        mapping_node = nodes.new(type="ShaderNodeMapping")
        new_link(tex_coord_node.outputs["UV"],
                 mapping_node.inputs["Vector"])
        mapping_node.location.x = principled_node.location.x + \
            IMAGE_NODE_OFFSET_X - mapping_node.width - 100
        tex_coord_node.location.x = mapping_node.location.x - tex_coord_node.width - 100

    # sort images nicely for new material
    images_sorted = {}
    images_rest = {}  # for Vertex Colors
    for jobname in NODE_INPUTS_SORTED:
        if (jobname in new_images.keys()):
            images_sorted[jobname] = new_images[jobname]
    for jobname in set(new_images) - set(images_sorted):
        images_rest[jobname] = new_images[jobname]
    images_sorted.update(images_rest)

    image_nodes = {}
    node_offset_index = 0
    for name, image in images_sorted.items():
        image_node = new_image_node(new_mat)
        image_node.label = name

        image_nodes[name] = image_node
        image_node.image = image

        # link to mapping node
        new_link(mapping_node.outputs["Vector"],
                 image_node.inputs["Vector"])

        # rearrange nodes
        image_node.width = IMAGE_NODE_WIDTH
        image_node.location.x = principled_node.location.x + IMAGE_NODE_OFFSET_X
        image_node.location.y = principled_node.location.y + \
            IMAGE_NODE_OFFSET_Y * node_offset_index
        node_offset_index += 1

    # link nodes
    for name, image_node in image_nodes.items():
        if name in NORMAL_INPUTS:
            normal_node = nodes.new(type="ShaderNodeNormalMap")
            normal_node.location.x = IMAGE_NODE_OFFSET_X + 1.5 * IMAGE_NODE_WIDTH
            normal_node.location.y = image_nodes[name].location.y
            new_link(image_node.outputs['Color'],
                     normal_node.inputs['Color'])
            new_link(normal_node.outputs[name],
                     principled_node.inputs[name])

        elif name == 'Bump':
            bump_node = nodes.new(type="ShaderNodeBump")
            bump_node.location.x = IMAGE_NODE_OFFSET_X + 1.5 * IMAGE_NODE_WIDTH
            bump_node.location.y = image_nodes[name].location.y
            new_link(image_node.outputs['Color'],
                     bump_node.inputs['Height'])
            new_link(bump_node.outputs['Normal'],
                     principled_node.inputs['Normal'])

        elif name == "Displacement":
            disp_node = nodes.new(type='ShaderNodeDisplacement')
            new_link(image_node.outputs['Color'],
                     disp_node.inputs["Height"])
            new_link(disp_node.outputs["Displacement"],
                     material_output.inputs["Displacement"])
            disp_node.location.x = NODE_OFFSET_X

        elif name in ALPHA_NODES.keys():
            if name == "Translucent_Alpha":
                alpha_node = nodes.new(type='ShaderNodeBsdfTranslucent')
            elif name == "Glass_Alpha":
                alpha_node = nodes.new(type='ShaderNodeBsdfGlass')

            # color
            alpha_node.inputs['Color'].default_value = NEW_NODE_COLORS[name]

            mixshader_node = nodes.new(type='ShaderNodeMixShader')

            # links
            new_link(material_output.inputs[0].links[0].from_socket,
                     mixshader_node.inputs[2])
            new_link(mixshader_node.outputs['Shader'],
                     material_output.inputs[0])
            new_link(alpha_node.outputs['BSDF'],
                     mixshader_node.inputs[1])
            if not settings.use_alpha_to_color:
                new_link(image_node.outputs['Color'],
                         mixshader_node.inputs['Fac'])

            # node locations
            sib = get_sibling_node(alpha_node)
            alpha_node.location = (
                sib.location.x, sib.location.y + NODE_OFFSET_Y)
            mid_offset_y = alpha_node.location.y
            mixshader_node.location = (
                sib.location.x + NODE_OFFSET_X, mid_offset_y)

        elif name == "Alpha":
            new_link(image_node.outputs['Color'],
                     principled_node.inputs['Alpha'])

        elif name == 'Emission':
            new_link(image_node.outputs['Color'],
                     principled_node.inputs['Emission'])

        elif name == 'Color':
            name = 'Base Color'
            new_link(image_node.outputs['Color'],
                     principled_node.inputs[name])

            if settings.use_alpha_to_color and "Alpha" in new_images.keys():
                new_link(image_node.outputs['Alpha'],
                         principled_node.inputs['Alpha'])

            # mix AO with color
            if 'Ambient Occlusion' in image_nodes.keys():
                ao_image_node = image_nodes['Ambient Occlusion']

                # mix
                mix_node = new_mixrgb_node(new_mat, fac=1.0)
                mix_node.blend_type = 'MULTIPLY'
                mix_node.location.x = image_node.location.x - IMAGE_NODE_OFFSET_X / 2
                mix_node.location.y = image_node.location.y

                # links
                new_link(mix_node.outputs["Color"],
                         principled_node.inputs['Base Color'])
                new_link(image_node.outputs["Color"],
                         mix_node.inputs['Color1'])
                new_link(ao_image_node.outputs["Color"],
                         mix_node.inputs['Color2'])

        elif name in NOT_TO_LINK_NODES or name.startswith("Vertex Color"):
            pass  # skip some

            # TODO link single baked images as option
            if len(image_nodes) == 1:
                new_link(image_node.outputs['Color'],
                         principled_node.inputs["Base Color"])

        else:
            new_link(image_node.outputs['Color'],
                     principled_node.inputs[name])
