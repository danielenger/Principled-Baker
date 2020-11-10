import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import Operator, PropertyGroup, UIList


def channel_items(scene, context):
    items = [
        ('None', "None", ""),
        ('Color', "Color", ""),
        ('Metallic', "Metallic", ""),
        ('Specular', "Specular", ""),
        ('Roughness', "Roughness", ""),
        ('Glossiness', "Glossiness", ""),
        ('Ambient Occlusion', "Ambient Occlusion", ""),
        ('Alpha', "Alpha", ""),
        ('Bump', "Bump", ""),
        ('Displacement', "Displacement", ""),
        ('Normal', "Normal", ""),
        ('Emission', "Emission", ""),
        ('Subsurface', "Subsurface", ""),
        ('Subsurface Radius', "Subsurface Radius", ""),
        ('Subsurface Color', "Subsurface Color", ""),
        ('Specular Tint', "Specular Tint", ""),
        ('Anisotropic', "Anisotropic", ""),
        ('Anisotropic Rotation', "Anisotropic Rotation", ""),
        ('Sheen', "Sheen", ""),
        ('Sheen Tint', "Sheen Tint", ""),
        ('Clearcoat', "Clearcoat", ""),
        ('Clearcoat Roughness', "Clearcoat Roughness", ""),
        ('IOR', "IOR", ""),
        ('Transmission', "Transmission", ""),
        ('Transmission Roughness', "Transmission Roughness", ""),
        ('Clearcoat Normal', "Clearcoat Normal", ""),
        ('Tangent', "Tangent", ""),
    ]
    return items


def from_channel_items(scene, context):
    return [
        ('0', "R", ""),
        ('1', "G", ""),
        ('2', "B", ""),
        ('3', "A", ""),
    ]


class PBAKER_CombineListItem(PropertyGroup):
    suffix: StringProperty(name="Suffix", default="_combined")

    do_combine: BoolProperty(name="", default=True)

    channel_r: EnumProperty(name="R", items=channel_items,
                            description="Red Channel")
    channel_g: EnumProperty(name="G", items=channel_items,
                            description="Green Channel")
    channel_b: EnumProperty(name="B", items=channel_items,
                            description="Blue Channel")
    channel_a: EnumProperty(name="A", items=channel_items,
                            description="Alpha Channel")

    channel_r_from_channel: EnumProperty(
        name="channel", items=from_channel_items, description="from channel")
    channel_g_from_channel: EnumProperty(
        name="channel", items=from_channel_items, description="from channel")
    channel_b_from_channel: EnumProperty(
        name="channel", items=from_channel_items, description="from channel")
    channel_a_from_channel: EnumProperty(
        name="channel", items=from_channel_items, description="from channel")

    channel_r_invert: BoolProperty(name="R invert", description="Red invert")
    channel_g_invert: BoolProperty(name="G invert", description="Green invert")
    channel_b_invert: BoolProperty(name="B invert", description="Blue invert")
    channel_a_invert: BoolProperty(name="A invert", description="Alpha invert")


class PBAKER_UL_CombineList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):

        if self.layout_type == 'DEFAULT':
            layout.prop(item, 'do_combine', text='')
            layout.prop(item, 'name', text='', emboss=False, translate=False)
            layout.prop(item, 'suffix', text='')
        elif self.layout_type == 'COMPACT':
            col = layout.column()
            col.label(text=item.name)
            col2 = col.column()
            col2.prop(item, "suffix", text="Suffix")
            row = col2.row()
            row.prop(item, "channel_r")
            row.prop(item, "channel_r_from_channel", text='')
            row.prop(item, "channel_r_invert", text='invert')
            row = col2.row()
            row.prop(item, "channel_g")
            row.prop(item, "channel_g_from_channel", text='')
            row.prop(item, "channel_g_invert", text='invert')
            row = col2.row()
            row.prop(item, "channel_b")
            row.prop(item, "channel_b_from_channel", text='')
            row.prop(item, "channel_b_invert", text='invert')
            row = col2.row()
            row.prop(item, "channel_a")
            row.prop(item, "channel_a_from_channel", text='')
            row.prop(item, "channel_a_invert", text='invert')
            row = col2.row()


class PBAKER_COMBINELIST_OT_Add(Operator):
    """Create Combine List to customize combinees"""

    bl_idname = "principled_baker_combinelist.add"
    bl_label = "Init Combinelist"

    def execute(self, context):
        combinelist = bpy.context.scene.principled_baker_combinelist
        item = combinelist.add()
        item.name = "Combine"

        return{'FINISHED'}


class PBAKER_COMBINELIST_OT_Delete(Operator):
    bl_idname = "principled_baker_combinelist.delete"
    bl_label = "Delete Combinelist"

    @classmethod
    def poll(cls, context):
        return context.scene.principled_baker_combinelist

    def execute(self, context):
        combinelist = context.scene.principled_baker_combinelist
        index = context.scene.principled_baker_combinelist_index
        combinelist.remove(index)
        context.scene.principled_baker_combinelist_index = min(
            max(0, index - 1), len(combinelist) - 1)

        return{'FINISHED'}


class PBAKER_COMBINELIST_OT_MoveItem_Up(Operator):
    bl_idname = "principled_baker_combinelist.move_up"
    bl_label = "Up"

    @classmethod
    def poll(cls, context):
        return context.scene.principled_baker_combinelist

    def execute(self, context):
        combinelist = context.scene.principled_baker_combinelist
        index = bpy.context.scene.principled_baker_combinelist_index
        prev_index = index - 1
        combinelist.move(prev_index, index)
        new_index = index - 1
        list_len = len(combinelist)
        context.scene.principled_baker_combinelist_index = max(
            0, min(new_index, list_len - 1))

        return{'FINISHED'}


class PBAKER_COMBINELIST_OT_MoveItem_Down(Operator):
    bl_idname = "principled_baker_combinelist.move_down"
    bl_label = "Down"

    @classmethod
    def poll(cls, context):
        return context.scene.principled_baker_combinelist

    def execute(self, context):
        combinelist = context.scene.principled_baker_combinelist
        index = bpy.context.scene.principled_baker_combinelist_index
        next_index = index + 1
        combinelist.move(next_index, index)
        new_index = index + 1
        list_len = len(combinelist)
        context.scene.principled_baker_combinelist_index = max(
            0, min(new_index, list_len - 1))

        return{'FINISHED'}
