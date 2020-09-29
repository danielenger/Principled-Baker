import bpy


def duplicate_object(obj, new_mat):
    """Duplicate object and append new material.

    :returns: Object reference to new object.
    """

    settings = bpy.context.scene.principled_baker_settings

    dup_obj = None
    # Duplicate object
    for o in bpy.context.selected_objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.duplicate()
    dup_obj = bpy.context.active_object

    # Rename
    prefix = settings.duplicate_objects_prefix
    suffix = settings.duplicate_objects_suffix
    if prefix or suffix:
        dup_obj.name = prefix + dup_obj.name[:-4] + suffix

    # Relocate duplicat object
    dup_obj.location.x += settings.duplicate_object_loc_offset_x
    dup_obj.location.y += settings.duplicate_object_loc_offset_y
    dup_obj.location.z += settings.duplicate_object_loc_offset_z

    # Remove all but selected UV Map
    uv_layers = dup_obj.data.uv_layers
    active_uv_layer_name = dup_obj.data.uv_layers.active.name

    uv_layers_to_delete = []
    for uv_layer in uv_layers:
        if not uv_layer.name == active_uv_layer_name:
            uv_layers_to_delete.append(uv_layer.name)
    for uv_layer_name in uv_layers_to_delete:
        uv_layers.remove(uv_layers[uv_layer_name])

    # Remove all materials
    for i in range(0, len(dup_obj.material_slots)):
        bpy.context.object.active_material_index = i
        bpy.ops.object.material_slot_remove({'object': dup_obj})

    # Remove all modifiers
    if not settings.copy_modifiers:
        dup_obj.modifiers.clear()

    # Add new material
    dup_obj.data.materials.append(new_mat)

    dup_obj.select_set(False)

    # dup_objects.append(dup_obj)

    return dup_obj


def duplicate_objects(active_object, objs, new_mat):
    """Duplicate a list of objecs and append new material to each.

    :returns: List of Object references to new objects.
    """

    active_dup_obj = duplicate_object(active_object, new_mat)

    objs = objs.copy()
    if active_object in objs:
        objs.remove(active_object)

    dup_objects = []

    for obj in objs:
        dup_obj = duplicate_object(obj, new_mat)
        uv_layers = dup_obj.data.uv_layers

        # Equal UV Map names
        uv_layers[0].name = active_dup_obj.data.uv_layers.active.name

        dup_objects.append(dup_obj)

    return dup_objects
