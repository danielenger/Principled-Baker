import bpy
from bpy.types import Panel

from .pbaker_functions import *
from .pbaker_preset import *


class PBAKER_PT_SubPanel(Panel):
    bl_space_type = "NODE_EDITOR"
    bl_region_type = 'UI'
    bl_context = "objectmode"
    bl_label = "Subpanel"

    def __init__(self):
        self.settings = bpy.context.scene.principled_baker_settings
        self.render_settings = bpy.context.scene.render.bake

    def draw(self, context):
        pass


class PBAKER_PT_BakeList(PBAKER_PT_SubPanel):
    bl_parent_id = "PBAKER_PT_Main"
    bl_label = "Autodetect/Bake List"

    def draw(self, context):
        # Autodetect
        col = self.layout.column(align=True)
        col.prop(self.settings, "use_autodetect", toggle=True)
        col.separator()

        # Bakelist
        col_bakelist = col.column()
        col_bakelist.label(text="Bake List:")
        col_bakelist.template_list("PBAKER_UL_List", "Bake_List", context.scene,
                                   "principled_baker_bakelist",
                                   context.scene, "principled_baker_bakelist_index")

        row = col_bakelist.row(align=True)
        row.operator('principled_baker_bakelist.update',
                     text='Detect')
        row.separator()
        row.operator('principled_baker_bakelist.disable_all',
                     text='Disable All')
        row.separator()
        row.operator('principled_baker_bakelist.reset',
                     text='Reset')
        row.separator()
        row.operator('principled_baker_bakelist.move_up',
                     text="", icon='TRIA_UP')
        row.operator('principled_baker_bakelist.move_down',
                     text="", icon='TRIA_DOWN')
        # row.operator('principled_baker_bakelist.delete', text='Delete')  # TODO debug only?

        # TODO short list
        # row.separator()
        # row.prop(self.settings, "use_shortlist", toggle=True)

        # Presets
        row = col_bakelist.row(align=True)
        row.menu(PBAKER_MT_display_presets.__name__,
                 text=PBAKER_MT_display_presets.bl_label)
        if is_2_80:
            row.operator(PBAKER_AddPresetObjectDisplay.bl_idname,
                         text="", icon='ADD')
            row.operator(PBAKER_AddPresetObjectDisplay.bl_idname,
                         text="", icon='REMOVE').remove_active = True
        else:
            row.operator(PBAKER_AddPresetObjectDisplay.bl_idname,
                         text="", icon='ZOOM_IN')
            row.operator(PBAKER_AddPresetObjectDisplay.bl_idname,
                         text="", icon='ZOOM_OUT').remove_active = True

        if self.settings.use_autodetect:
            col_bakelist.active = False

        col.separator()
        col.label(text="Additional Bake Types:")

        # Diffuse
        col1 = col.column(align=True)
        row = col1.split()
        row.prop(self.settings, "use_Diffuse")
        row.prop(self.settings, "suffix_diffuse", text="")
        row_diff = col.row(align=True)
        if self.settings.use_Diffuse:
            row_diff.prop(self.render_settings, "use_pass_direct",
                          text="Direct", toggle=True)
            row_diff.prop(self.render_settings, "use_pass_indirect",
                          text="Indirect", toggle=True)
            row_diff.prop(self.render_settings, "use_pass_color",
                          text="Color", toggle=True)
        if self.settings.bake_mode == 'SELECTED_TO_ACTIVE':
            col1.active = False
            row_diff.active = False

        col2 = col.column(align=True)

        row = col2.split()
        row.prop(self.settings, "use_invert_roughness")
        row.prop(self.settings, "suffix_glossiness", text="")

        row = col2.split()
        row.prop(self.settings, "use_Bump")
        row.prop(self.settings, "suffix_bump", text="")

        row = col2.split()
        row.prop(self.settings, "use_vertex_color")
        row.prop(self.settings, "suffix_vertex_color", text="")

        row = col2.split()
        row.prop(self.settings, "use_material_id")
        row.prop(self.settings, "suffix_material_id", text="")

        row = col2.split()
        row.prop(self.settings, "use_wireframe")        
        row.prop(self.settings, "suffix_wireframe", text="")
        if self.settings.use_wireframe:
            wf_row = col2.split()
            wf_row.prop(self.settings, "wireframe_size")
            wf_row.prop(self.settings, "use_pixel_size")


class PBAKER_PT_OutputSettings(PBAKER_PT_SubPanel):
    bl_parent_id = "PBAKER_PT_Main"
    bl_label = "Output Settings/Bake Settings"

    def draw(self, context):
        # output options:
        col = self.layout.column(align=True)
        row = col.row()
        row.prop(self.settings, "resolution", expand=True)
        if self.settings.resolution == 'CUSTOM':
            col.prop(self.settings, "custom_resolution")
        col.separator()
        col.prop(self.settings, "file_path")
        col.prop(self.settings, "use_overwrite")

        col.separator()

        # image settings:
        col.prop(self.settings, "file_format")

        row = col.row()
        row.prop(self.settings, "color_mode", text="Color", expand=True)
        row = col.row()
        row.prop(self.settings, "color_depth", text="Color Depth", expand=True)

        if self.settings.file_format == 'PNG':
            col.prop(self.settings, "compression", text="Compression")

        if self.settings.file_format == 'OPEN_EXR':
            col.prop(self.settings, "exr_codec", text="Codec")

        if self.settings.file_format == 'TIFF':
            col.prop(self.settings, "tiff_codec", text="Compression")

        if self.settings.file_format == 'JPEG':
            col.prop(self.settings, "quality", text="Quality")

        col.separator()
        col.prop(self.settings, "samples")
        col.prop(self.render_settings, "margin")

        # Alpha to Color
        col_alpha_to_col = col.row()
        col_alpha_to_col.prop(self.settings, "use_alpha_to_color")
        if self.settings.color_mode == 'RGB':
            col_alpha_to_col.active = False


class PBAKER_PT_SelectedToActiveSettings(PBAKER_PT_SubPanel):
    bl_parent_id = "PBAKER_PT_Main"
    bl_label = "Selected to Active Settings"

    def draw(self, context):
        col2 = self.layout
        sub = col2.column()
        sub.prop(self.render_settings, "use_cage", text="Cage")
        if self.render_settings.use_cage:
            sub.prop(self.render_settings, "cage_extrusion", text="Extrusion")
            sub.prop(self.render_settings, "cage_object", text="Cage Object")
        else:
            sub.prop(self.render_settings,
                     "cage_extrusion", text="Ray Distance")

        if not self.settings.bake_mode == 'SELECTED_TO_ACTIVE':
            col2.active = False


class PBAKER_PT_PrefixSuffixSettings(PBAKER_PT_SubPanel):
    bl_parent_id = "PBAKER_PT_Main"
    bl_label = "Prefix/Suffix Settings"

    def draw(self, context):
        col = self.layout
        col.label(text="Prefix Settings:")
        col.prop(self.settings, "image_prefix")
        col.prop(self.settings, "use_object_name")
        # col.separator()
        col.label(text="Suffix Settings:")
        row = col.row()
        row.prop(self.settings, 'suffix_text_mod', expand=True)


class PBAKER_PT_NewMaterial(PBAKER_PT_SubPanel):
    bl_parent_id = "PBAKER_PT_Main"
    bl_label = "New Material"

    def draw(self, context):
        col = self.layout
        col.prop(self.settings, "make_new_material")
        col.prop(self.settings, "add_new_material")
        col.prop(self.settings, "new_material_prefix")


class PBAKER_PT_AutoSmooth(PBAKER_PT_SubPanel):
    bl_parent_id = "PBAKER_PT_Main"
    bl_label = "Auto Smooth"

    def draw(self, context):
        self.layout.prop(self.settings, "auto_smooth",
                         text="Auto Smooth", expand=True)


class PBAKER_PT_AutoUVUnwrap(PBAKER_PT_SubPanel):
    bl_parent_id = "PBAKER_PT_Main"
    bl_label = "Auto UV unwrap"

    def draw(self, context):
        if is_2_79 and self.settings.bake_mode == 'COMBINED':
            self.layout.label(
                text="Auto UV unwrap not available in Blender 2.79 for multiple objects.", icon='INFO')
        else:

            row = self.layout
            row.prop(self.settings, "auto_uv_project",
                     text="Auto UV Project", expand=True)
            if not self.settings.auto_uv_project == 'OFF':
                self.layout.label(text="UV Map will be altered!", icon='ERROR')
            if self.settings.auto_uv_project == 'SMART':
                col = self.layout
                col.prop(self.settings, "angle_limit")
                col.prop(self.settings, "island_margin")
                col.prop(self.settings, "user_area_weight")
                col.prop(self.settings, "use_aspect")
                col.prop(self.settings, "stretch_to_bounds")
            elif self.settings.auto_uv_project == 'LIGHTMAP':
                col = self.layout
                col.prop(self.settings, "share_tex_space")
                col.prop(self.settings, "new_uv_map")
                col.prop(self.settings, "new_image")
                col.prop(self.settings, "image_size")
                col.prop(self.settings, "pack_quality")
                col.prop(self.settings, "lightmap_margin")


class PBAKER_PT_SelectUVMap(PBAKER_PT_SubPanel):
    bl_parent_id = "PBAKER_PT_Main"
    bl_label = "Select UV Map"

    def draw(self, context):
        col = self.layout
        col.prop(self.settings, "select_uv_map", text="UV Map")
        col.prop(self.settings, "set_selected_uv_map")
        # col.prop(self.settings, "set_active_render_uv_map") # TODO


class PBAKER_PT_Misc(PBAKER_PT_SubPanel):
    bl_parent_id = "PBAKER_PT_Main"
    bl_label = "Misc Settings"

    def draw(self, context):
        self.layout.prop(self.settings, "use_exclude_transparent_colors")


class PBAKER_PT_Main(Panel):
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_label = "Principled Baker"
    bl_context = "objectmode"
    bl_category = "Principled Baker"

    @classmethod
    def poll(cls, context):
        if context.space_data.tree_type == 'ShaderNodeTree':
            return True
        return False

    def draw(self, context):
        self.settings = context.scene.principled_baker_settings

        # 2.79
        if is_2_79:
            prefs = context.user_preferences.addons[__package__].preferences
        # 2.80
        else:
            prefs = context.preferences.addons[__package__].preferences

        if bpy.context.scene.render.engine == 'CYCLES' or prefs.switch_to_cycles:
            self.layout.operator('object.principled_baker_bake',
                                 text='Bake', icon='RENDER_STILL')
        else:
            self.layout.label(text="Set Render engine to Cycles! {} is not supported.".format(
                bpy.context.scene.render.engine), icon='ERROR')

        # bake mode
        self.layout.prop(self.settings, "bake_mode",
                         text="Bake Mode", expand=True)
