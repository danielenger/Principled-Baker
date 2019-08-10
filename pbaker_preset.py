import bpy
from bl_operators.presets import AddPresetBase
from bpy.types import Menu, Operator

PRESET_BAKELIST_SUBDIR = "principled_baker/bake_list"
PRESET_SUFFIXLIST_SUBDIR = "principled_baker/suffix_list"


class PBAKER_MT_display_presets(Menu):
    bl_label = "Bake List Presets"
    preset_subdir = PRESET_BAKELIST_SUBDIR
    preset_operator = "script.execute_preset"
    draw = Menu.draw_preset


class PBAKER_AddPresetObjectDisplay(AddPresetBase, Operator):
    bl_idname = "principled_baker.preset_add"
    bl_label = "Add Bake List Preset"
    preset_menu = "PBAKER_MT_display_presets"

    preset_defines = ["scene = bpy.context.scene"]
    preset_values = ["scene.principled_baker_bakelist"]
    preset_subdir = PRESET_BAKELIST_SUBDIR


class PBAKER_MT_display_suffix_presets(Menu):
    bl_label = "Bake List Presets"
    preset_subdir = PRESET_SUFFIXLIST_SUBDIR
    preset_operator = "script.execute_preset"
    draw = Menu.draw_preset


class PBAKER_AddSuffixPresetObjectDisplay(AddPresetBase, Operator):
    bl_idname = "principled_baker.suffix_preset_add"
    bl_label = "Add Suffix List Preset"
    preset_menu = "PBAKER_MT_display_suffix_presets"

    preset_defines = ["scene = bpy.context.scene"]
    preset_values = ["scene.principled_baker_suffixlist"]
    preset_subdir = PRESET_SUFFIXLIST_SUBDIR
