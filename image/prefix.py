import bpy

from ..functions import remove_not_allowed_signs
from ..material.has_material import has_material


def get_image_prefix(object_name):
    """:returns: Image prefix by object name and altered by user settings."""

    settings = bpy.context.scene.principled_baker_settings
    prefix = settings.image_prefix
    object_name = remove_not_allowed_signs(object_name)

    if settings.use_first_material_name:
        if has_material(bpy.data.objects[object_name]):
            prefix += bpy.data.objects[object_name].material_slots[0].material.name
    return prefix
