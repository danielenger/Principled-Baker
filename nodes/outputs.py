import bpy

from ..const import MATERIAL_TAG


def deactivate_material_outputs(material):
    for node in material.node_tree.nodes:
        if node.type == "OUTPUT_MATERIAL":
            node.is_active_output = False


def get_active_output(mat) -> bpy.types.Node:
    for node in mat.node_tree.nodes:
        if node.type == "OUTPUT_MATERIAL" and node.is_active_output:
            return node


def get_active_outputs(objects) -> list:
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


def get_all_material_outputs(objects) -> dict:
    if not isinstance(objects, list):
        objects = [objects]

    outputs = {}
    for obj in objects:
        for mat_slot in obj.material_slots:
            if mat_slot.material:
                for node in mat_slot.material.node_tree.nodes:
                    if node.type == "OUTPUT_MATERIAL":
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
