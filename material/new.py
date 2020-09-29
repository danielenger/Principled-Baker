import bpy

from ..const import MATERIAL_TAG


def new_material(name, principled_node_values=None):
    """:returns: Object reference to new material."""

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat[MATERIAL_TAG] = 1

    mat_output = mat.node_tree.nodes['Material Output']
    mat_output.location = (300.0, 300.0)

    principled_node = mat.node_tree.nodes['Principled BSDF']

    principled_node.location = (10.0, 300.0)

    # copy settings to new principled_node
    if not principled_node_values == None:
        for name, val in principled_node_values.items():
            if name == 'Color':
                name = 'Base Color'
            if val is not None:
                principled_node.inputs[name].default_value = val

    mat.node_tree.links.new(
        principled_node.outputs['BSDF'], mat_output.inputs['Surface'])
    return mat
