import bpy

from .pbaker_functions import *
from .pbaker_preset import *


class PBAKER_PT_panel(bpy.types.Panel):
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
        settings = context.scene.principled_baker_settings
        render_settings = context.scene.render.bake

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

        col = self.layout.box().column(align=True)
        row = col.row()
        row.prop(settings, "bake_mode", text="Bake Mode", expand=True)

        # output options:
        col = self.layout.box().column(align=True)
        row = col.row()
        row.prop(settings, "resolution", expand=True)
        if settings.resolution == 'CUSTOM':
            col.prop(settings, "custom_resolution")
        col.separator()
        col.prop(settings, "file_path")
        col.prop(settings, "use_overwrite")

        col.separator()

        # image settings:
        col.prop(settings, "file_format")

        row = col.row()
        row.prop(settings, "color_mode", text="Color", expand=True)
        row = col.row()
        row.prop(settings, "color_depth", text="Color Depth", expand=True)

        if settings.file_format == 'OPEN_EXR':
            col.prop(settings, "exr_codec", text="Codec")

        if settings.file_format == 'TIFF':
            col.prop(settings, "tiff_codec", text="Compression")

        if settings.file_format == 'JPEG':
            col.prop(settings, "quality", text="Quality")

        col.separator()
        col.prop(settings, "samples")
        col.prop(render_settings, "margin")

        # Alpha to Color
        col_alpha_to_col = col.row()
        col_alpha_to_col.prop(settings, "use_alpha_to_color")
        if settings.color_mode == 'RGB':
            col_alpha_to_col.active = False


        col2 = self.layout.box().column(align=True)
        col2.label(text="Selected to Active:")
        sub = col2.column()
        sub.prop(render_settings, "use_cage", text="Cage")
        if render_settings.use_cage:
            sub.prop(render_settings, "cage_extrusion", text="Extrusion")
            sub.prop(render_settings, "cage_object", text="Cage Object")
        else:
            sub.prop(render_settings, "cage_extrusion", text="Ray Distance")

        if not settings.bake_mode == 'SELECTED_TO_ACTIVE':
            col2.active = False

        # Autodetect
        col = self.layout.box().column(align=True)
        col.prop(settings, "use_autodetect", toggle=True)
        col.separator()

        # Bakelist
        # col_bakelist = col.column(align=True)
        col_bakelist = col.column()
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
        # row.prop(settings, "use_shortlist", toggle=True)

        # Presets
        row = col_bakelist.row(align=True)
        row.menu(PBAKER_MT_display_presets.__name__, text=PBAKER_MT_display_presets.bl_label)
        row.operator(PBAKER_AddPresetObjectDisplay.bl_idname, text="", icon='ZOOM_IN')
        row.operator(PBAKER_AddPresetObjectDisplay.bl_idname, text="", icon='ZOOM_OUT').remove_active = True

        if settings.use_autodetect:
            col_bakelist.active = False

        col.separator()
        col.label(text="Additional Bake Types:")

        # Diffuse
        col1 = col.column(align=True)
        row = col1.split()
        row.prop(settings, "use_Diffuse")
        row.prop(settings, "suffix_diffuse", text="")
        row_diff = col.row(align=True)
        if settings.use_Diffuse:
            row_diff.prop(render_settings, "use_pass_direct",
                          text="Direct", toggle=True)
            row_diff.prop(render_settings, "use_pass_indirect",
                          text="Indirect", toggle=True)
            row_diff.prop(render_settings, "use_pass_color",
                          text="Color", toggle=True)
        if settings.bake_mode == 'SELECTED_TO_ACTIVE':
            col1.active = False
            row_diff.active = False

        col2 = col.column(align=True)

        row = col2.split()
        row.prop(settings, "use_invert_roughness")
        row.prop(settings, "suffix_glossiness", text="")

        row = col2.split()
        row.prop(settings, "use_Bump")
        row.prop(settings, "suffix_bump", text="")

        row = col2.split()
        row.prop(settings, "use_vertex_color")
        row.prop(settings, "suffix_vertex_color", text="")

        row = col2.split()
        row.prop(settings, "use_material_id")
        row.prop(settings, "suffix_material_id", text="")

        # prefix and suffix settings:
        col = self.layout.box().column(align=True)
        col.label(text="Prefix Settings:")
        col.prop(settings, "image_prefix")
        col.prop(settings, "use_object_name")
        col.separator()
        col.label(text="Suffix Settings:")
        row = col.row()
        row.prop(settings, 'suffix_text_mod', expand=True)

        # new material:
        col = self.layout.box().column(align=True)
        col.prop(settings, "make_new_material")
        col.prop(settings, "add_new_material")
        col.prop(settings, "new_material_prefix")

        # Auto Smooth
        col = self.layout.box().column(align=True)
        col.label(text="Auto Smooth:")
        row = col.row()
        row.prop(settings, "auto_smooth", text="Auto Smooth", expand=True)

        # Auto UV unwrap
        if is_2_79 and settings.bake_mode == 'COMBINED':
            self.layout.label(
                text="Auto UV unwrap not available in Blender 2.79 for multiple objects.", icon='INFO')
        else:
            col = self.layout.box().column(align=True)
            col.label(text="Auto UV unwrap:")
            row = col.row()
            row.prop(settings, "auto_uv_project",
                     text="Auto UV Project", expand=True)
            if settings.auto_uv_project == 'SMART':
                col.prop(settings, "angle_limit")
                col.prop(settings, "island_margin")
                col.prop(settings, "user_area_weight")
                col.prop(settings, "use_aspect")
                col.prop(settings, "stretch_to_bounds")
            elif settings.auto_uv_project == 'LIGHTMAP':
                col.prop(settings, "share_tex_space")
                col.prop(settings, "new_uv_map")
                col.prop(settings, "new_image")
                col.prop(settings, "image_size")
                col.prop(settings, "pack_quality")
                col.prop(settings, "lightmap_margin")

        # UV Map selection
        col = self.layout.box().column(align=True)
        col.label(text="Select UV Map:")
        col.prop(settings, "select_uv_map", text="UV Map")
        col.prop(settings, "set_selected_uv_map")
        # col.prop(settings, "set_active_render_uv_map") # TODO

        col = self.layout.box().column(align=True)
        col.prop(settings, "use_exclude_transparent_colors")
