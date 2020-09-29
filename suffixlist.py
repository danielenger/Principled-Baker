import bpy
from bpy.props import StringProperty
from bpy.types import Operator, PropertyGroup, UIList

DEFAULT_SUFFIXLIST = {
    "Color": "_color",
    "Metallic": "_metallic",
    "Roughness": "_roughness",

    "Normal": "_normal",
    # "Bump": "_bump",
    "Displacement": "_disp",

    "Alpha": "_alpha",
    "Emission": "_emission",
    'Ambient Occlusion': "_ao",

    "Diffuse": "_diffuse",
    "Glossiness": "_glossiness",
    "Bump": "_bump",
    "Vertex Color": "_vertex",
    "Material ID": "_MatID",
    "Wireframe": "_wireframe",

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


class PBAKER_SuffixListItem(PropertyGroup):
    suffix: StringProperty(name="Suffix")


class PBAKER_UL_SuffixList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.name)
            layout.prop(item, "suffix", text="")


class PBAKER_SUFFIXLIST_OT_Init(Operator):
    """Create Suffix List to customize suffixes"""

    bl_idname = "principled_baker_suffixlist.init"
    bl_label = "Init Suffixlist"

    def execute(self, context):
        suffix_list = context.scene.principled_baker_suffixlist

        if not len(suffix_list):
            for jobname, suffix in DEFAULT_SUFFIXLIST.items():
                item = suffix_list.add()
                item.name = jobname
                item.suffix = suffix

        return{'FINISHED'}


class PBAKER_SUFFIXLIST_OT_Delete(Operator):
    bl_idname = "principled_baker_suffixlist.delete"
    bl_label = "Delete Suffixlist"

    @classmethod
    def poll(cls, context):
        return context.scene.principled_baker_suffixlist

    def execute(self, context):
        context.scene.principled_baker_suffixlist.clear()
        return{'FINISHED'}


class PBAKER_SUFFIXLIST_OT_Reset(Operator):
    """Reset list to default values"""

    bl_idname = "principled_baker_suffixlist.reset"
    bl_label = "Update Suffixlist"

    def execute(self, context):
        if context.scene.principled_baker_suffixlist:
            bpy.ops.principled_baker_suffixlist.delete()
            bpy.ops.principled_baker_suffixlist.init()

        return{'FINISHED'}
