import bpy
from bpy.props import BoolProperty, StringProperty
from bpy.types import Operator, PropertyGroup, UIList

from .pbaker_functions import *


# 2.79 - OrderedDict
# TODO throw out with future 2.8+ only verion
if is_2_79:
    from collections import OrderedDict

    JOBLIST = OrderedDict([
        ("Color", "_color"),
        ("Metallic", "_metallic"),
        ("Roughness", "_roughness"),

        ("Normal", "_normal"),
        #("Bump", "_bump"),
        ("Displacement", "_disp"),

        ("Alpha", "_alpha"),
        ("Emission", "_emission"),
        # ('Ambient Occlusion', "_ao"),  # not in 2.79

        ("Subsurface", "_subsurface"),
        ("Subsurface Radius", "_subsurface_radius"),
        ("Subsurface Color", "_subsurface_color"),
        ("Specular", "_specular"),
        ("Specular Tint", "_specular_tint"),
        ("Anisotropic", "_anisotropic"),
        ("Anisotropic Rotation", "_anisotropic_rotation"),
        ("Sheen", "_sheen"),
        ("Sheen Tint", "_sheen_tint"),
        ("Clearcoat", "_clearcoat"),
        ("Clearcoat Roughness", "_clearcoat_roughness"),
        ("IOR", "_ior"),
        ("Transmission", "_transmission"),
        ("Transmission Roughness", "_transmission_roughness"),
        ("Clearcoat Normal", "_clearcoat_normal"),
        ("Tangent", "_tangent")
    ])
else:
    JOBLIST = {
        "Color": "_color",
        "Metallic": "_metallic",
        "Roughness": "_roughness",

        "Normal": "_normal",
        # "Bump": "_bump",
        "Displacement": "_disp",

        "Alpha": "_alpha",
        "Emission": "_emission",
        'Ambient Occlusion': "_ao",

        "Subsurface": "_subsurface",
        "Subsurface Radius": "_subsurface_radius",
        "Subsurface Color": "_subsurface_color",
        "Specular": "_specular",
        "Specular Tint": "_specular_tint",
        "Anisotropic": "_anisotropic",
        "Anisotropic Rotation": "_anisotropic_rotation",
        "Sheen": "_sheen",
        "Sheen Tint": "_sheen_tint",
        "Clearcoat": "_clearcoat",
        "Clearcoat Roughness": "_clearcoat_roughness",
        "IOR": "_ior",
        "Transmission": "_transmission",
        "Transmission Roughness": "_transmission_roughness",
        "Clearcoat Normal": "_clearcoat_normal",
        "Tangent": "_tangent",
    }

# JOBLIST_SHORT = {  # TODO

#     "Color": "_color",
#     "Metallic": "_metallic",
#     "Roughness": "_roughness",

#     "Normal": "_normal",
#     "Bump": "_bump",
#     "Displacement": "_disp",

#     "Alpha": "_alpha",
#     "Emission": "_emission",
#     'Ambient Occlusion': "_ao",
# }


class PBAKER_ListItem(PropertyGroup):
    suffix: StringProperty(name="Suffix")
    do_bake: BoolProperty(
        name="",
        default=False)


class PBAKER_UL_List(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "do_bake")
            layout.label(text=item.name)
            layout.prop(item, "suffix", text="")


class PBAKER_BAKELIST_OT_Init(Operator):
    bl_idname = "principled_baker_bakelist.init"
    bl_label = "Init Bakelist"

    def execute(self, context):
        bake_list = context.scene.principled_baker_bakelist

        for job_name, suffix in JOBLIST.items():
            item = bake_list.add()
            item.name = job_name
            item.suffix = suffix

        return{'FINISHED'}


class PBAKER_BAKELIST_OT_Delete(Operator):
    bl_idname = "principled_baker_bakelist.delete"
    bl_label = "Delete Bakelist"

    @classmethod
    def poll(cls, context):
        return context.scene.principled_baker_bakelist

    def execute(self, context):
        principled_baker_bakelist = context.scene.principled_baker_bakelist.clear()
        return{'FINISHED'}


class PBAKER_BAKELIST_OT_Update(Operator):
    """Detect Bake Types from Selected Objects"""

    bl_idname = "principled_baker_bakelist.update"
    bl_label = "Update Bakelist"

    def execute(self, context):
        if not context.scene.principled_baker_bakelist:
            bpy.ops.principled_baker_bakelist.init()

        bakelist = context.scene.principled_baker_bakelist

        temp_joblist = get_joblist_from_objects(context.selected_objects)

        for item_name, item in bakelist.items():
            if item_name in temp_joblist:
                item.do_bake = True
            else:
                item.do_bake = False

        return{'FINISHED'}


class PBAKER_BAKELIST_OT_Reset(Operator):
    """Reset list including suffixes"""

    bl_idname = "principled_baker_bakelist.reset"
    bl_label = "Update Bakelist"

    def execute(self, context):
        if context.scene.principled_baker_bakelist:
            bpy.ops.principled_baker_bakelist.delete()
            bpy.ops.principled_baker_bakelist.init()

        return{'FINISHED'}


class PBAKER_BAKELIST_OT_Disable_All(Operator):
    """Disable all"""

    bl_idname = "principled_baker_bakelist.disable_all"
    bl_label = "Disable All"

    def execute(self, context):
        bakelist = context.scene.principled_baker_bakelist

        for item_name, item in bakelist.items():
            item.do_bake = False

        return{'FINISHED'}


class PBAKER_BAKELIST_OT_MoveItem_Up(Operator):
    bl_idname = "principled_baker_bakelist.move_up"
    bl_label = "Up"

    @classmethod
    def poll(cls, context):
        return context.scene.principled_baker_bakelist

    def execute(self, context):
        principled_baker_bakelist = context.scene.principled_baker_bakelist
        index = bpy.context.scene.principled_baker_bakelist_index
        prev_index = index - 1
        principled_baker_bakelist.move(prev_index, index)
        new_index = index - 1
        list_len = len(principled_baker_bakelist)
        bpy.context.scene.principled_baker_bakelist_index = max(
            0, min(new_index, list_len - 1))

        return{'FINISHED'}


class PBAKER_BAKELIST_OT_MoveItem_Down(Operator):
    bl_idname = "principled_baker_bakelist.move_down"
    bl_label = "Down"

    @classmethod
    def poll(cls, context):
        return context.scene.principled_baker_bakelist

    def execute(self, context):
        principled_baker_bakelist = context.scene.principled_baker_bakelist
        index = bpy.context.scene.principled_baker_bakelist_index
        next_index = index + 1
        principled_baker_bakelist.move(next_index, index)
        new_index = index + 1
        list_len = len(principled_baker_bakelist)
        bpy.context.scene.principled_baker_bakelist_index = max(
            0, min(new_index, list_len - 1))

        return{'FINISHED'}
