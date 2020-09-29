import bpy

from principled_baker.const import MATERIAL_TAG, MATERIAL_TAG_VERTEX
from principled_baker.nodes.find import find_node_by_type
from principled_baker.nodes.outputs import get_active_output


def delete_tagged_materials(obj, tag):
    for i, mat_slot in enumerate(obj.material_slots):
        if mat_slot.material:
            if tag in mat_slot.material.keys():
                bpy.context.object.active_material_index = i
                bpy.ops.object.material_slot_remove({'object': obj})
