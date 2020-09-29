import bpy
from bpy.props import BoolProperty, EnumProperty, IntProperty
from bpy.types import Operator, PropertyGroup, UIList

from .joblist import get_joblist_by_autodetection_from_objects

DEFAULT_SAMPLES = 128

JOBLIST = [
    "Color",
    "Metallic",
    "Roughness",

    "Normal",
    # "Bump",
    "Displacement",

    "Alpha",
    "Emission",
    'Ambient Occlusion',

    "Subsurface",
    "Subsurface Radius",
    "Subsurface Color",
    "Specular",
    "Specular Tint",
    "Anisotropic",
    "Anisotropic Rotation",
    "Sheen",
    "Sheen Tint",
    "Clearcoat",
    "Clearcoat Roughness",
    "IOR",
    "Transmission",
    "Transmission Roughness",
    "Clearcoat Normal",
    "Tangent",
]

JOBLIST_SHORT = [
    "Color",
    "Metallic",
    "Roughness",
    "Normal",
    "Displacement",
    "Alpha",
    "Emission",
    'Ambient Occlusion',
]

# temp store for values in bake list to toggle short/long bake list
temp_bakelist = {}


def color_mode_items(item, context):
    if bpy.context.scene.principled_baker_settings.file_format in ['PNG', 'TARGA', 'TIFF', 'OPEN_EXR']:
        items = [
            ('RGB', "RGB", ""),
            ('RGBA', "RGBA", ""),
        ]
    else:
        items = [
            ('RGB', "RGB", ""),
            ('BW', "BW", ""),
        ]
    return items


def color_depth_items(scene, context):
    if bpy.context.scene.principled_baker_settings.file_format == 'OPEN_EXR':
        items = [
            ('16', "Float (Half)", ""),
            ('32', "Float (Full)", "")
        ]
    else:
        items = [
            ('8', "8", ""),
            ('16', "16", ""),
        ]
    return items


class PBAKER_ListItem(PropertyGroup):
    do_bake: BoolProperty(
        name="",
        default=False
    )
    # color_mode: EnumProperty(
    #     name="Color Mode",
    #     description="Color Mode",
    #     items=color_mode_items
    # )
    color_depth: EnumProperty(
        name="Color Depth",
        description="Color Depth",
        items=color_depth_items
    )
    samples: IntProperty(
        name="Samples",
        default=128,
        min=1
    )


class PBAKER_UL_List(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "do_bake")
            layout.label(text=item.name)

            settings = bpy.context.scene.principled_baker_settings

            if settings.individual_samples:
                layout.prop(item, "samples", text="")

            if settings.color_depth == 'INDIVIDUAL':
                layout.prop(item, "color_depth", expand=True)

            # TODO expand bake list
            # layout.prop(item, "color_mode", expand=True)  # is this useful?


class PBAKER_BAKELIST_OT_Init(Operator):
    bl_idname = "principled_baker_bakelist.init"
    bl_label = "Init Bakelist"

    def execute(self, context):
        bake_list = context.scene.principled_baker_bakelist

        if not len(bake_list):
            for jobname in JOBLIST:
                if bpy.context.scene.principled_baker_settings.use_shortlist:
                    if jobname in JOBLIST_SHORT:
                        item = bake_list.add()
                        item.name = jobname
                else:
                    item = bake_list.add()
                    item.name = jobname
                    item.samples = DEFAULT_SAMPLES

        return{'FINISHED'}


class PBAKER_BAKELIST_OT_Delete(Operator):
    bl_idname = "principled_baker_bakelist.delete"
    bl_label = "Delete Bakelist"

    @classmethod
    def poll(cls, context):
        return context.scene.principled_baker_bakelist

    def execute(self, context):
        context.scene.principled_baker_bakelist.clear()
        return{'FINISHED'}


class PBAKER_BAKELIST_OT_Update(Operator):
    bl_idname = "principled_baker_bakelist.update"
    bl_label = "Update Bakelist"

    def execute(self, context):

        bakelist = context.scene.principled_baker_bakelist

        for item_name, item in bakelist.items():
            temp_bakelist[item_name] = (item.do_bake, item.samples)

        bpy.ops.principled_baker_bakelist.reset()

        for item_name, item in bakelist.items():
            item.do_bake = temp_bakelist[item_name][0]
            item.samples = temp_bakelist[item_name][1]

        return{'FINISHED'}


class PBAKER_BAKELIST_OT_Detect(Operator):
    """Detect Bake Types from Selected Objects"""

    bl_idname = "principled_baker_bakelist.detect"
    bl_label = "Update Bakelist"

    def execute(self, context):
        settings = bpy.context.scene.principled_baker_settings

        if not settings.use_value_differ and not settings.use_connected_inputs:
            self.report({'INFO'}, "Select at least one Detection Option!")
            return {'CANCELLED'}

        if not context.scene.principled_baker_bakelist:
            bpy.ops.principled_baker_bakelist.init()

        bakelist = context.scene.principled_baker_bakelist

        temp_joblist = get_joblist_by_autodetection_from_objects(
            context.selected_objects)

        for item_name, item in bakelist.items():
            if item_name in temp_joblist:
                item.do_bake = True
            else:
                item.do_bake = False

        return {'FINISHED'}


class PBAKER_BAKELIST_OT_Reset(Operator):
    bl_idname = "principled_baker_bakelist.reset"
    bl_label = "Update Bakelist"

    def execute(self, context):
        if context.scene.principled_baker_bakelist:
            bpy.ops.principled_baker_bakelist.delete()
            bpy.ops.principled_baker_bakelist.init()

        return{'FINISHED'}


class PBAKER_BAKELIST_OT_Disable_All(Operator):
    bl_idname = "principled_baker_bakelist.disable_all"
    bl_label = "Disable All"

    def execute(self, context):
        bakelist = context.scene.principled_baker_bakelist

        for _, item in bakelist.items():
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
