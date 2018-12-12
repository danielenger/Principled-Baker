import bpy
from bpy.types import Panel

from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
    # FloatProperty,
    # FloatVectorProperty,
                       EnumProperty,
                       PointerProperty,
                       )

from bpy.types import (Panel,
                       Operator,
                       PropertyGroup,
                       )

class PBAKER_PT_panel(Panel):
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_label = "Principled Baker"
    bl_context = "objectmode"
    bl_category = "Principled Baker"

    def draw(self, context):
        settings = context.scene.principled_baker_settings

        layout = self.layout
        col = layout.column()

        col.operator('object.pbaker_bake', text='Bake', icon='RENDER_STILL')

        col.prop(settings, "resolution")
        col.prop(settings, "margin")
        col.prop(settings, "use_selected_to_active")
        col.prop(settings, "file_path")
        col.prop(settings, "image_prefix")
        col.prop(settings, "file_format", text="")
        col.prop(settings, "use_overwrite")
        col.prop(settings, "use_alpha")

        # col.label("Suffixes:")
        col.prop(settings, "suffix_color")
        col.prop(settings, "suffix_metallic")
        col.prop(settings, "suffix_roughness")
        col.prop(settings, "suffix_normal")
        col.prop(settings, "suffix_bump")
        col.prop(settings, "use_bump_to_normal")
        col.prop(settings, "suffix_bump_to_normal")
        col.prop(settings, "suffix_displacement")

        # col.label("Settings:")
        col.prop(settings, "use_alpha_to_color")
        col.prop(settings, "use_normal_strength")
        col.prop(settings, "use_bump_strength")
        col.prop(settings, "use_new_material")
        col.prop(settings, "new_material_prefix")

        # col.label("Bake:")
        col.prop(settings, "use_autodetect", toggle=True)

        # col.label("OR:")
        col.prop(settings, "use_Alpha", toggle=True)
        col.prop(settings, "use_Base_Color", toggle=True)
        col.prop(settings, "use_Metallic", toggle=True)
        col.prop(settings, "use_Roughness", toggle=True)
        col.prop(settings, "use_Specular", toggle=True)

        col.prop(settings, "use_Normal", toggle=True)
        col.prop(settings, "use_Bump", toggle=True)
        col.prop(settings, "use_Displacement", toggle=True)

        # col.label("")
        col.prop(settings, "use_Subsurface", toggle=True)
        # TODO Subsurface Radius        col.prop(settings, "use_Subsurface_Radius", toggle=True)
        col.prop(settings, "use_Subsurface_Color", toggle=True)
        col.prop(settings, "use_Specular_Tint", toggle=True)
        col.prop(settings, "use_Anisotropic", toggle=True)
        col.prop(settings, "use_Anisotropic_Rotation", toggle=True)
        col.prop(settings, "use_Sheen", toggle=True)
        col.prop(settings, "use_Sheen_Tint", toggle=True)
        col.prop(settings, "use_Clearcoat", toggle=True)
        col.prop(settings, "use_Clearcoat_Roughness", toggle=True)
        col.prop(settings, "use_IOR", toggle=True)
        col.prop(settings, "use_Transmission", toggle=True)
        col.prop(settings, "use_Transmission_Roughness", toggle=True)
        col.prop(settings, "use_Clearcoat_Normal", toggle=True)
        col.prop(settings, "use_Tangent", toggle=True)