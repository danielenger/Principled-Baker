import bpy
from bpy.types import Panel

from .presets import (PBAKER_AddCombinePresetObjectDisplay,
                      PBAKER_AddPresetObjectDisplay,
                      PBAKER_AddSuffixPresetObjectDisplay,
                      PBAKER_MT_display_combine_presets,
                      PBAKER_MT_display_presets,
                      PBAKER_MT_display_suffix_presets)


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
        col.prop(self.settings, "use_autodetect")
        col.separator()

        # Bakelist
        col_bakelist = col.column()
        col_bakelist.label(text="Bake List:")
        col_bakelist.template_list("PBAKER_UL_List", "Bake_List", context.scene,
                                   "principled_baker_bakelist",
                                   context.scene, "principled_baker_bakelist_index")

        # Bakelist: Dected and Disable All
        row = col_bakelist.row(align=True)
        row.operator('principled_baker_bakelist.detect',
                     text='Detect')
        row.separator()
        row.operator('principled_baker_bakelist.disable_all',
                     text='Disable All')

        # Bakelist: Create and Delete
        row2 = col_bakelist.row(align=True)
        row2_create = row2.row()
        row2_create.operator('principled_baker_bakelist.init', text='Create')
        row2.separator()
        row2_delete = row2.row()
        row2_delete.operator('principled_baker_bakelist.delete', text='Delete')

        if len(bpy.context.scene.principled_baker_bakelist) != 0:
            row2_create.active = False

        if len(bpy.context.scene.principled_baker_bakelist) == 0:
            row2_delete.active = False

        # Bakelist: Up, Down and Short List
        row3 = col_bakelist.row(align=True)
        row3.operator('principled_baker_bakelist.move_up',
                      text="", icon='TRIA_UP')
        row3.operator('principled_baker_bakelist.move_down',
                      text="", icon='TRIA_DOWN')
        row3.separator()
        row3.prop(self.settings, "use_shortlist")

        if len(bpy.context.scene.principled_baker_bakelist) == 0:
            row3.active = False

        # Bakelist Presets
        row = col_bakelist.row(align=True)
        row.menu(PBAKER_MT_display_presets.__name__,
                 text=PBAKER_MT_display_presets.bl_label)
        row.operator(PBAKER_AddPresetObjectDisplay.bl_idname,
                     text="", icon='ADD')
        row.operator(PBAKER_AddPresetObjectDisplay.bl_idname,
                     text="", icon='REMOVE').remove_active = True

        if self.settings.use_autodetect:
            col_bakelist.active = False

        col.separator()
        col.label(text="Detection Options:")
        col.prop(self.settings, "use_value_differ")
        col.prop(self.settings, "use_connected_inputs")

        # col.separator()
        # col.label(text="Additional Bake Types:")

        # # Glossiness
        # row = col.split()
        # row.prop(self.settings, "use_invert_roughness")

        # # Diffuse
        # col1 = col.column(align=True)
        # row = col1.split()
        # row.prop(self.settings, "use_Diffuse")
        # if self.settings.individual_samples:
        #     row.prop(self.settings, "samples_diffuse", text="")
        # if self.settings.color_depth == 'INDIVIDUAL':
        #     row_cd = row.row()
        #     row_cd.prop(self.settings, "color_depth_diffuse", expand=True)
        # row_diff = col.row(align=True)
        # if self.settings.use_Diffuse:
        #     row_diff.prop(self.render_settings, "use_pass_direct",
        #                   text="Direct", toggle=True)
        #     row_diff.prop(self.render_settings, "use_pass_indirect",
        #                   text="Indirect", toggle=True)
        #     row_diff.prop(self.render_settings, "use_pass_color",
        #                   text="Color", toggle=True)
        # if self.settings.bake_mode == 'SELECTED_TO_ACTIVE':
        #     col1.active = False
        #     row_diff.active = False

        # col2 = col.column(align=True)

        # row = col2.split()
        # row.prop(self.settings, "use_Bump")
        # if self.settings.individual_samples:
        #     row.prop(self.settings, "samples_bump", text="")
        # if self.settings.color_depth == 'INDIVIDUAL':
        #     row_cd = row.row()
        #     row_cd.prop(self.settings, "color_depth_bump", expand=True)

        # row = col2.split()
        # row.prop(self.settings, "use_vertex_color")
        # if self.settings.individual_samples:
        #     row.prop(self.settings, "samples_vertex_color", text="")
        # if self.settings.color_depth == 'INDIVIDUAL':
        #     row_cd = row.row()
        #     row_cd.prop(self.settings, "color_depth_vertex_color", expand=True)
        # if self.settings.use_vertex_color:
        #     col2.row().prop(self.settings, "bake_vertex_colors")

        # row = col2.split()
        # row.prop(self.settings, "use_material_id")
        # if self.settings.individual_samples:
        #     row.prop(self.settings, "samples_material_id", text="")
        # if self.settings.color_depth == 'INDIVIDUAL':
        #     row_cd = row.row()
        #     row_cd.prop(self.settings, "color_depth_material_id", expand=True)

        # row = col2.split()
        # row.prop(self.settings, "use_wireframe")
        # if self.settings.individual_samples:
        #     row.prop(self.settings, "samples_wireframe", text="")
        # if self.settings.color_depth == 'INDIVIDUAL':
        #     row_cd = row.row()
        #     row_cd.prop(self.settings, "color_depth_wireframe", expand=True)

        # if self.settings.use_wireframe:
        #     wf_row = col2.split()
        #     wf_row.prop(self.settings, "wireframe_size")
        #     wf_row.prop(self.settings, "use_pixel_size")


class PBAKER_PT_AdditionalBakeTypes(PBAKER_PT_SubPanel):
    bl_parent_id = "PBAKER_PT_Main"
    bl_label = "Additional Bake Types"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        col = self.layout.column(align=True)
        col.label(text="Additional Bake Types:")

        # Glossiness
        row = col.split()
        row.prop(self.settings, "use_invert_roughness")

        # Diffuse
        col1 = col.column(align=True)
        row = col1.split()
        row.prop(self.settings, "use_Diffuse")
        if self.settings.individual_samples:
            row.prop(self.settings, "samples_diffuse", text="")
        if self.settings.color_depth == 'INDIVIDUAL':
            row_cd = row.row()
            row_cd.prop(self.settings, "color_depth_diffuse", expand=True)
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
        row.prop(self.settings, "use_Bump")
        if self.settings.individual_samples:
            row.prop(self.settings, "samples_bump", text="")
        if self.settings.color_depth == 'INDIVIDUAL':
            row_cd = row.row()
            row_cd.prop(self.settings, "color_depth_bump", expand=True)

        row = col2.split()
        row.prop(self.settings, "use_vertex_color")
        if self.settings.individual_samples:
            row.prop(self.settings, "samples_vertex_color", text="")
        if self.settings.color_depth == 'INDIVIDUAL':
            row_cd = row.row()
            row_cd.prop(self.settings, "color_depth_vertex_color", expand=True)
        if self.settings.use_vertex_color:
            col2.row().prop(self.settings, "bake_vertex_colors")

        row = col2.split()
        row.prop(self.settings, "use_material_id")
        if self.settings.individual_samples:
            row.prop(self.settings, "samples_material_id", text="")
        if self.settings.color_depth == 'INDIVIDUAL':
            row_cd = row.row()
            row_cd.prop(self.settings, "color_depth_material_id", expand=True)

        row = col2.split()
        row.prop(self.settings, "use_wireframe")
        if self.settings.individual_samples:
            row.prop(self.settings, "samples_wireframe", text="")
        if self.settings.color_depth == 'INDIVIDUAL':
            row_cd = row.row()
            row_cd.prop(self.settings, "color_depth_wireframe", expand=True)

        if self.settings.use_wireframe:
            wf_row = col2.split()
            wf_row.prop(self.settings, "wireframe_size")
            wf_row.prop(self.settings, "use_pixel_size")


class PBAKER_PT_OutputSettings(PBAKER_PT_SubPanel):
    bl_parent_id = "PBAKER_PT_Main"
    bl_label = "Output Settings/Bake Settings"
    bl_options = {'DEFAULT_CLOSED'}

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
        col.prop(self.settings, "use_texture_folder")

        col.separator()

        # image settings:
        col.prop(self.settings, "file_format")

        row = col.row()
        row.prop(self.settings, "color_mode", text="Color", expand=True)

        if self.settings.color_depth == 'INDIVIDUAL' and self.settings.use_autodetect:
            col.label(text="Set Color Depth for Autodetect!", icon='ERROR')
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

        # Samples
        col.separator()
        row_samples = col.row()
        row_samples.prop(self.settings, "samples")
        row_indi_samples = col.row()
        row_indi_samples.prop(self.settings, "individual_samples")
        if self.settings.individual_samples:
            row_samples.active = False

        col.separator()
        col.prop(self.render_settings, "margin")


class PBAKER_PT_NewMaterial(PBAKER_PT_SubPanel):
    bl_parent_id = "PBAKER_PT_Main"
    bl_label = "New Material"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        col = self.layout
        col.prop(self.settings, "make_new_material")
        col.prop(self.settings, "add_new_material")
        col.prop(self.settings, "new_material_prefix")


class PBAKER_PT_SelectedToActiveSettings(PBAKER_PT_SubPanel):
    bl_parent_id = "PBAKER_PT_Main"
    bl_label = "Selected to Active Settings"
    bl_options = {'DEFAULT_CLOSED'}

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
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):

        # Prefix
        col = self.layout
        col.label(text="Prefix Settings:")
        col.prop(self.settings, "image_prefix")
        col.prop(self.settings, "use_first_material_name")
        col.prop(self.settings, "use_object_name")

        if not self.settings.use_object_name:
            col.label(text="Possible Overwrites!", icon='ERROR')

        # Suffix
        col.label(text="Suffix Settings:")
        col = self.layout.column(align=True)
        col_suffixlist = col.column()
        col_suffixlist.template_list("PBAKER_UL_SuffixList", "Suffix_List", context.scene,
                                     "principled_baker_suffixlist",
                                     context.scene, "principled_baker_suffixlist_index")

        row = col_suffixlist.row(align=True)
        init_slist = row.row()
        init_slist.operator('principled_baker_suffixlist.init',
                            text='Create')
        if len(bpy.context.scene.principled_baker_suffixlist):
            init_slist.active = False
        row.separator()
        row.operator('principled_baker_suffixlist.reset',
                     text='Default')

        # Suffix Presets
        row = col_suffixlist.row(align=True)
        row.menu(PBAKER_MT_display_suffix_presets.__name__,
                 text=PBAKER_MT_display_suffix_presets.bl_label)
        row.operator(PBAKER_AddSuffixPresetObjectDisplay.bl_idname,
                     text="", icon='ADD')
        row.operator(PBAKER_AddSuffixPresetObjectDisplay.bl_idname,
                     text="", icon='REMOVE').remove_active = True

        # Suffix mods
        col.label(text="Suffix String Modifier:")
        row = col.row()
        row.prop(self.settings, 'suffix_text_mod', expand=True)


class PBAKER_PT_AutoSmooth(PBAKER_PT_SubPanel):
    bl_parent_id = "PBAKER_PT_Main"
    bl_label = "Auto Smooth"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        self.layout.prop(self.settings, "auto_smooth",
                         text="Auto Smooth", expand=True)


class PBAKER_PT_AutoUVUnwrap(PBAKER_PT_SubPanel):
    bl_parent_id = "PBAKER_PT_Main"
    bl_label = "Auto UV unwrap"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        row = self.layout
        row.prop(self.settings, "auto_uv_project",
                 text="Auto UV Project", expand=True)

        if not self.settings.auto_uv_project == 'OFF':
            # new UV Map
            row.prop(self.settings, "new_uv_map")
            if not self.settings.new_uv_map:
                self.layout.label(
                    text="Selected UV Map will be altered!", icon='ERROR')
            self.layout.label(text="UV Map settings:")

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
            # col.prop(self.settings, "new_uv_map")  # see new UV Map
            col.prop(self.settings, "new_image")
            col.prop(self.settings, "image_size")
            col.prop(self.settings, "pack_quality")
            col.prop(self.settings, "lightmap_margin")


class PBAKER_PT_SelectUVMap(PBAKER_PT_SubPanel):
    bl_parent_id = "PBAKER_PT_Main"
    bl_label = "Select UV Map"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        col = self.layout
        col.prop(self.settings, "select_uv_map", text="UV Map")
        col.prop(self.settings, "set_selected_uv_map")
        col.prop(self.settings, "select_set_active_render_uv_map")


class PBAKER_PT_CombineChannels(PBAKER_PT_SubPanel):
    bl_parent_id = "PBAKER_PT_Main"
    bl_label = "Combine Channels"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):

        # Alpha to Color
        col = self.layout.column()
        col.prop(self.settings, "use_alpha_to_color")

        col.label(text="Custom Combined Images:")

        row = self.layout.row()
        row.template_list("PBAKER_UL_CombineList", "Combine_List", context.scene,
                          "principled_baker_combinelist",
                          context.scene, "principled_baker_combinelist_index")

        col = row.column(align=True)
        col.operator("principled_baker_combinelist.add", icon='ADD', text="")
        col.operator("principled_baker_combinelist.delete",
                     icon='REMOVE', text="")
        col.separator()
        col.operator("principled_baker_combinelist.move_up",
                     icon='TRIA_UP', text="")
        col.operator("principled_baker_combinelist.move_down",
                     icon='TRIA_DOWN', text="")

        col = self.layout.column()
        col.template_list("PBAKER_UL_CombineList", "Combine_List", context.scene,
                          "principled_baker_combinelist",
                          context.scene, "principled_baker_combinelist_index",
                          type='COMPACT')

        # Combine Presets
        row = col.row(align=True)
        row.menu(PBAKER_MT_display_combine_presets.__name__,
                 text=PBAKER_MT_display_combine_presets.bl_label)
        row.operator(PBAKER_AddCombinePresetObjectDisplay.bl_idname,
                     text="", icon='ADD')
        row.operator(PBAKER_AddCombinePresetObjectDisplay.bl_idname,
                     text="", icon='REMOVE').remove_active = True


class PBAKER_PT_DuplicateObjects(PBAKER_PT_SubPanel):
    bl_parent_id = "PBAKER_PT_Main"
    bl_label = "Duplicate Objects"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        col = self.layout
        col.prop(self.settings, "duplicate_objects")
        col2 = col.column(align=True)
        col2.prop(self.settings, "join_duplicate_objects")
        col2.prop(self.settings, "copy_modifiers")
        col2.prop(self.settings, "duplicate_objects_prefix")
        col2.prop(self.settings, "duplicate_objects_suffix")
        col3 = col.column(align=True)
        col3.prop(self.settings, "duplicate_object_loc_offset_x")
        col3.prop(self.settings, "duplicate_object_loc_offset_y")
        col3.prop(self.settings, "duplicate_object_loc_offset_z")

        if not self.settings.duplicate_objects:
            col2.active = False
            col3.active = False

        if self.settings.bake_mode == 'SELECTED_TO_ACTIVE':
            col.active = False


class PBAKER_PT_Misc(PBAKER_PT_SubPanel):
    bl_parent_id = "PBAKER_PT_Main"
    bl_label = "Misc Settings"
    bl_options = {'DEFAULT_CLOSED'}

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

        prefs = context.preferences.addons[__package__].preferences

        layout = self.layout

        can_bake = True

        if not bpy.context.scene.render.engine == 'CYCLES' and not prefs.switch_to_cycles:
            layout.label(text="Set Render engine to Cycles!", icon='INFO')
            can_bake = False

        if self.settings.use_autodetect and self.settings.color_depth == 'INDIVIDUAL':
            layout.label(text="Set Color Depth for Autodetect!", icon='INFO')
            can_bake = False

        if can_bake:
            layout.operator('object.principled_baker_bake',
                            text='Bake', icon='RENDER_STILL')

        # bake mode
        layout.prop(self.settings, "bake_mode",
                    text="Bake Mode", expand=True)
