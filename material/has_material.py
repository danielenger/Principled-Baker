from ..const import MATERIAL_TAG
from ..nodes.outputs import get_active_output


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
