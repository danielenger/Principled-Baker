import bpy

from ..const import MATERIAL_TAG, NODE_INPUTS
from ..functions import is_list_equal
from ..nodes.outputs import get_active_output
from ..nodes.value_list import get_value_from_node_by_name


def get_value_list(node, value_name, node_type):
    """
    :returns: List of all values by value name in a node tree starting from node.
    Values from Normal Map are exclued.
    """

    value_list = []

    def find_values(node, value_name):
        if node.type == node_type:
            val = get_value_from_node_by_name(node, value_name)
            if val is not None:
                value_list.append(val)

        for socket in node.inputs:
            if socket.is_linked:
                from_node = socket.links[0].from_node
                find_values(from_node, value_name)

    find_values(node, value_name)
    return value_list


def get_principled_node_values(objs):
    # TODO bug: ignores nodes in groups
    """:returns: Dictionary with equal node values in all materials in all objects, eg. metal, roughness, etc."""

    settings = bpy.context.scene.principled_baker_settings

    pri_node_values = {}
    for obj in objs:
        for value_name in NODE_INPUTS + ["Base Color"]:

            if value_name not in {'Subsurface Radius', 'Normal', 'Clearcoat Normal', 'Tangent'}:
                value_list = []
                for mat_slot in obj.material_slots:
                    if mat_slot.material:
                        mat = mat_slot.material
                        if MATERIAL_TAG not in mat.keys():
                            material_output = get_active_output(mat)
                            tmp_val_list = get_value_list(
                                material_output, value_name, 'BSDF_PRINCIPLED')
                            value_list.extend(tmp_val_list)

                if value_list:
                    if is_list_equal(value_list):
                        if settings.make_new_material or settings.bake_mode == 'SELECTED_TO_ACTIVE' or settings.duplicate_objects:
                            pri_node_values[value_name] = value_list[0]

    return pri_node_values
