import bpy
from bl_operators.presets import AddPresetBase
from bpy.types import Menu, Operator

PRESET_SUBDIR = "principled_baker/bake_list"


class PBAKER_MT_display_presets(Menu):
    bl_label = "Bake List Presets"
    preset_subdir = PRESET_SUBDIR
    preset_operator = "script.execute_preset"
    draw = Menu.draw_preset


class PBAKER_AddPresetObjectDisplay(AddPresetBase, Operator):
    bl_idname = "principled_baker.preset_add"
    bl_label = "Add Bake List Preset"
    preset_menu = "PBAKER_MT_display_presets"

    # variable used for all preset values
    preset_defines = ["scene = bpy.context.scene"]

    # properties to store in the preset
    preset_values = ["scene.principled_baker_bakelist"]

    # where to store the preset
    preset_subdir = PRESET_SUBDIR
