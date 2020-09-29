import bpy

from ..const import MATERIAL_TAG_VERTEX
from ..nodes.find import find_node_by_type


def add_temp_material(obj):
    import time
    name = f"PRINCIPLED_BAKER_TEMP_MATERIAL_{time.time()}"
    mat = bpy.data.materials.new(name)
    mat[MATERIAL_TAG_VERTEX] = 1
    mat.use_nodes = True
    principled_node = find_node_by_type(mat, 'BSDF_PRINCIPLED')
    principled_node.inputs["Base Color"].default_value = [0, 0, 0, 1]
    obj.data.materials.append(mat)
