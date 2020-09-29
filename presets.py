from bpy.types import Menu, Operator

from bl_operators.presets import AddPresetBase

PRESET_BAKELIST_SUBDIR = "principled_baker/bake_list"
PRESET_SUFFIXLIST_SUBDIR = "principled_baker/suffix_list"
PRESET_COMBINELIST_SUBDIR = "principled_baker/combine_list"


# --------------------------------------------------------
# Bake List Presets
# --------------------------------------------------------
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


# --------------------------------------------------------
# Suffix Presets
# --------------------------------------------------------
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


# --------------------------------------------------------
# Combine Presets
# --------------------------------------------------------
class PBAKER_MT_display_combine_presets(Menu):
    bl_label = "Combine List Presets"
    preset_subdir = PRESET_COMBINELIST_SUBDIR
    preset_operator = "script.execute_preset"
    draw = Menu.draw_preset


class PBAKER_AddCombinePresetObjectDisplay(AddPresetBase, Operator):
    bl_idname = "principled_baker.combine_preset_add"
    bl_label = "Add Combine List Preset"
    preset_menu = "PBAKER_MT_display_combine_presets"

    preset_defines = ["scene = bpy.context.scene"]
    preset_values = ["scene.principled_baker_combinelist"]
    preset_subdir = PRESET_COMBINELIST_SUBDIR
