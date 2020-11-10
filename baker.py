from pathlib import Path

import bpy

from .check_path_access import check_path_access
from .const import (ALPHA_NODES, IMAGE_FILE_FORMAT_ENDINGS, MATERIAL_TAG,
                    MATERIAL_TAG_VERTEX, NODE_INPUTS, NODE_INPUTS_SORTED,
                    NODE_TAG, NORMAL_INPUTS)
from .duplicate import *
from .functions import (get_bake_type_by, get_only_meshes, is_list_equal,
                        remove_not_allowed_signs)
from .image.combine import combine_channels_to_image, get_combined_images
from .image.invert import get_invert_image
from .image.prefix import get_image_prefix
from .image.save import save_image
from .image.save_as import save_image_as
from .image.suffix import get_image_suffix
from .joblist import (get_joblist_from_objects,
                      get_vertex_colors_to_bake_from_objects)
from .material.add_images import add_images_to_material
from .material.add_temp_material import add_temp_material
from .material.delete_tagged_materials import delete_tagged_materials
from .material.has_material import has_material
from .material.new import new_material
from .nodes.delete_tagged import delete_tagged_nodes_in_object
from .nodes.find import find_node_by_type
from .nodes.new import (create_bake_image_nodes, new_image_node,
                        new_mixrgb_node, new_pb_emission_node,
                        new_pb_output_node)
from .nodes.node import get_sibling_node, is_node_type_in_node_tree
from .nodes.outputs import (deactivate_material_outputs, get_active_output,
                            get_active_outputs, get_all_material_outputs,
                            set_material_outputs_target_to_all)
from .nodes.principled_node import get_principled_node_values
from .prepare.objects import (prepare_objects_for_bake,
                              prepare_objects_for_bake_matid,
                              prepare_objects_for_bake_vertex_color,
                              prepare_objects_for_bake_wireframe)
from .set_samples import set_samples
from .uv.project import *
from .uv.select import *


class PBAKER_OT_bake(bpy.types.Operator):
    bl_idname = "object.principled_baker_bake"
    bl_label = "Bake"
    bl_description = "bake all inputs of a Principled BSDF to image textures"
    bl_options = {'REGISTER', 'UNDO'}

    def load_image_by(self, image_file_name) -> bpy.types.Image:
        """:returns: Reference to image."""

        path = self.get_image_file_path(image_file_name)
        image = bpy.data.images.load(path)
        return image

    def skip_job_if_file_exists(self, obj):
        if self.settings.use_overwrite:
            return False

        img_file_name = self.get_image_file_name(obj.name)
        tex_dir = Path(self.texture_folder)
        path = Path(bpy.path.abspath(self.settings.file_path)) / \
            tex_dir / img_file_name

        if path.is_file():
            self.report({'INFO'}, "baking skipped for '{0}'. File exists.".format(
                self.get_image_file_name(obj.name)))

            # load image for new material
            image = self.load_image_by(img_file_name)
            if not self.jobname in {'Color', 'Diffuse'}:
                image.colorspace_settings.name = 'Non-Color'
            self.new_images[self.jobname] = image

            return True
        return False

    def get_image_file_name(self, object_name):
        prefix = get_image_prefix(object_name)
        name = object_name if self.settings.use_object_name else ""
        suffix = get_image_suffix(self.jobname)
        if self.jobname == "Vertex Color":
            suffix += self.suffix_extension
        ending = IMAGE_FILE_FORMAT_ENDINGS[self.settings.file_format]
        img_name = f"{prefix}{name}{suffix}.{ending}"
        return img_name

    def get_image_file_path(self, image_file_name):
        img_file_name = remove_not_allowed_signs(image_file_name)
        tex_dir = Path(self.texture_folder)
        if self.settings.file_path.startswith("//"):
            rel_path = bpy.path.relpath(self.settings.file_path)
            path = rel_path + str(tex_dir / img_file_name)
        else:
            abs_path = bpy.path.abspath(self.settings.file_path)
            path = Path(abs_path) / tex_dir / img_file_name
        return str(path)

    def new_bake_image(self, object_name):
        img_name = self.get_image_file_name(object_name)
        path = self.get_image_file_path(img_name)

        # alpha
        alpha = False
        if self.settings.color_mode == 'RGBA' or (self.jobname == 'Color' and self.settings.use_alpha_to_color):
            alpha = True

        # color
        color = (0.0, 0.0, 0.0, 1.0)
        if get_bake_type_by(self.jobname) == 'NORMAL':
            color = (0.5, 0.5, 1.0, 1.0)

        # resolution
        res = int(self.settings.custom_resolution) if self.settings.resolution == 'CUSTOM' else int(
            self.settings.resolution)

        is_float = False if self.settings.color_depth == '8' else True

        image = bpy.data.images.new(
            name=img_name, width=res, height=res, alpha=alpha, float_buffer=is_float)

        if not self.jobname in {'Color', 'Diffuse'}:
            image.colorspace_settings.name = 'Non-Color'

        image.generated_color = color
        image.generated_type = 'BLANK'
        image.filepath = path

        return image

    def create_gloss_image(self, obj_name):
        if "Roughness" in self.new_images:
            self.jobname = "Glossiness"  # for suffix
            gloss_image = self.new_bake_image(obj_name)
            gloss_img_name = self.get_image_file_name(obj_name)
            gloss_image.filepath = self.get_image_file_path(gloss_img_name)
            rough_img = self.new_images["Roughness"]
            gloss_image.pixels = get_invert_image(rough_img)
            gloss_image.save()
            save_image(gloss_image, self.get_color_mode(self.jobname))
            gloss_image.reload()
            self.new_images[self.jobname] = gloss_image

    def check_texture_folder(self):
        abs_path = Path(bpy.path.abspath(self.settings.file_path))
        path = str(abs_path / self.texture_folder)
        return check_path_access(path)

    def check_file_path(self):
        path = self.settings.file_path

        if path in {'', ' ', '/', '///', '\\', '//\\'}:
            self.report({'ERROR'}, f"'{path}' not a valid path")
            return False

        if check_path_access(path):
            return True
        else:
            self.report({'ERROR'}, f"No write permission to '{path}'!")

    def alpha_channel_to_color(self):
        """Add an alpha channel to the Color image in the list of newly created images."""

        if "Color" in self.new_images.keys() and "Alpha" in self.new_images.keys():
            img = get_combined_images(
                self.new_images["Color"], self.new_images["Alpha"], 0, 3)
            self.new_images["Color"].pixels = img
            self.new_images["Color"].save()

    def combine_channels(self, obj):
        """Combine all channels defined under 'Combined Channels'."""

        if len(bpy.context.scene.principled_baker_combinelist) == 0:
            return

        for combi in bpy.context.scene.principled_baker_combinelist:
            if not combi.do_combine:
                continue

            # Color Mode
            if combi.channel_a in self.new_images:
                alpha = True
                color_mode = 'RGBA'
            else:
                alpha = False
                color_mode = 'RGB'

            # create new image
            object_name = obj.name
            prefix = get_image_prefix(object_name)
            name = object_name if self.settings.use_object_name else ""
            suffix = combi.suffix
            ending = IMAGE_FILE_FORMAT_ENDINGS[self.settings.file_format]
            img_name = f"{prefix}{name}{suffix}.{ending}"
            path = self.get_image_file_path(img_name)

            # resolution
            res = int(self.settings.custom_resolution) if self.settings.resolution == 'CUSTOM' else int(
                self.settings.resolution)

            is_float = False if self.settings.color_depth == '8' else True

            image = bpy.data.images.new(
                name=img_name, width=res, height=res, alpha=alpha, float_buffer=is_float)

            image.colorspace_settings.name = 'Non-Color'
            image.generated_color = (0, 0, 0, 1)
            image.generated_type = 'BLANK'
            image.filepath = path

            image.save()

            # combine
            r, g, b, a = None, None, None, None
            if combi.channel_r in self.new_images:
                r = self.new_images[combi.channel_r]
            if combi.channel_g in self.new_images:
                g = self.new_images[combi.channel_g]
            if combi.channel_b in self.new_images:
                b = self.new_images[combi.channel_b]
            if combi.channel_a in self.new_images:
                a = self.new_images[combi.channel_a]
            combine_channels_to_image(
                image,
                R=r,
                G=g,
                B=b,
                A=a,
                channel_r=int(combi.channel_r_from_channel),
                channel_g=int(combi.channel_g_from_channel),
                channel_b=int(combi.channel_b_from_channel),
                channel_a=int(combi.channel_a_from_channel),
                invert_r=combi.channel_r_invert,
                invert_g=combi.channel_g_invert,
                invert_b=combi.channel_b_invert,
                invert_a=combi.channel_a_invert,
            )

            # Color Depth
            color_depth = '8'
            for img in {r, g, b, a}:
                if img:
                    if img.is_float:
                        if self.settings.file_format == 'OPEN_EXR':
                            color_depth = '32'
                        else:
                            color_depth = '16'
                        break

            # save image
            save_image_as(image,
                          file_path=image.filepath,
                          file_format=self.settings.file_format,
                          color_mode=color_mode,
                          color_depth=color_depth,
                          compression=self.settings.compression,
                          quality=self.settings.quality,
                          tiff_codec=self.settings.tiff_codec,
                          exr_codec=self.settings.exr_codec)
            image.reload()

    def bake(self, bake_type):
        """Wrapper for bpy.ops.object.bake() to get all parameters from settings"""

        pass_filter = []
        if self.settings.use_Diffuse:
            if self.render_settings.use_pass_direct:
                pass_filter.append('DIRECT')
            if self.render_settings.use_pass_indirect:
                pass_filter.append('INDIRECT')
            if self.render_settings.use_pass_color:
                pass_filter.append('COLOR')
        pass_filter = set(pass_filter)

        selected_to_active = True if self.settings.bake_mode == 'SELECTED_TO_ACTIVE' else False

        bpy.ops.object.bake(
            type=bake_type,
            pass_filter=pass_filter,
            use_selected_to_active=selected_to_active,
            normal_space=self.render_settings.normal_space,
            normal_r=self.render_settings.normal_r,
            normal_g=self.render_settings.normal_g,
            normal_b=self.render_settings.normal_b, )

    def bake_and_save(self, image, bake_type='EMIT'):
        """Bake and save image."""

        image.save()
        self.report({'INFO'}, "baking '{0}'".format(image.name))
        self.bake(bake_type)
        save_image(image, self.get_color_mode(self.jobname))
        image.reload()

    def get_color_mode(self, jobname):
        if jobname == 'Color' and self.settings.use_alpha_to_color:
            return 'RGBA'
        else:
            return self.settings.color_mode

    # -------------------------------------------------------------------------
    # CLEAN UPS!
    # -------------------------------------------------------------------------
    def final_cleanup(self):
        """Restore temporarily changed settings."""

        # Auto Smooth - Clean up!
        if not self.settings.auto_smooth == 'OBJECT':
            for obj in self.auto_smooth_list:
                obj.data.use_auto_smooth = self.auto_smooth_list[obj]

        # Render Engine - Clean up!
        if self.prefs.switch_to_cycles:
            bpy.context.scene.render.engine = self.render_engine
            bpy.context.scene.cycles.preview_pause = self.preview_pause

        # Samples
        bpy.context.scene.cycles.samples = self.org_samples

        # Restore orig selection
        for obj in bpy.context.selected_objects:
            obj.select_set(False)
        for obj in self.selected_objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = self.active_object

    def clean_after_bake(self, objects):
        for obj in objects:
            # delete temp materials
            delete_tagged_materials(obj, MATERIAL_TAG_VERTEX)

            # delete temp nodes
            delete_tagged_nodes_in_object(obj)

            # reselect UV Map
            if not self.settings.set_selected_uv_map:
                if obj in self.orig_uv_layers_active_indices:
                    uv_layers = obj.data.uv_layers
                    uv_layers.active_index = self.orig_uv_layers_active_indices[obj]

            # deactivate all Material Outputs before reactivating
            for mat_slot in obj.material_slots:
                if mat_slot.material:
                    deactivate_material_outputs(mat_slot.material)

        # reactivate Material Outputs
        for mat_output in self.active_outputs:
            mat_output.is_active_output = True

    # -------------------------------------------------------------------------
    # TEST CONDITIONS
    # -------------------------------------------------------------------------
    def can_execute(self, context):
        """Test necessary conditions and report errors.

        :returns: True, if baking is possible, else False.
        """

        # Bake only works in cycles (for now)
        if not bpy.context.scene.render.engine == 'CYCLES' and not self.prefs.switch_to_cycles:
            self.report({'ERROR'}, 'Error: Current render engine ({0}) does not support baking'.format(
                bpy.context.scene.render.engine))
            return False

        if not context.selected_objects:
            self.report({'INFO'}, "Nothing selected.")
            return False

        # File needs to be saved
        if not bpy.data.is_saved:
            self.report(
                {'ERROR'}, 'Blendfile needs to be saved to get relative output paths')
            return False

        # Check file path
        if not self.check_file_path():
            return False

        if self.settings.bake_mode == 'SELECTED_TO_ACTIVE':
            if len(context.selected_objects) < 2:
                self.report({'ERROR'}, 'Select at least 2 objects!')
                return False

        if self.settings.use_Diffuse:
            d = self.render_settings.use_pass_direct
            i = self.render_settings.use_pass_indirect
            c = self.render_settings.use_pass_color
            if not d and not i and not c:
                self.report(
                    {'ERROR'}, "Error: Bake pass requires Direct, Indirect, or Color contributions to be enabled.")
                return False

        # all fine
        return True

    def can_bake(self, objects):
        """Test conditions and report errors.

        Objects must:
        not be hidden,
        have a material (expect baking vertex color),
        have no empty material slots.

        :returns: True, if baking is possible, else False.
        """

        for obj in objects:
            # enabled for rendering?
            if obj.hide_render:
                self.report(
                    {'INFO'}, "baking cancelled. '{0}' not enabled for rendering.".format(obj.name))
                return False
            # no material or missing output?
            if not has_material(obj):
                if not self.settings.use_vertex_color:
                    self.report(
                        {'INFO'}, "baking cancelled. '{0}' Material missing, Material Output missing, or Material Output input missing.".format(obj.name))
                    return False

            # empty material slots?
            for mat_slot in obj.material_slots:
                if not mat_slot.material:
                    self.report(
                        {'INFO'}, "baking cancelled. '{0}' has empty Material Slots.".format(obj.name))
                    return False

        # has every object a UV map?
        if self.settings.auto_uv_project == 'OFF':
            objs_with_missing_uv_map = []
            for obj in objects:
                if len(obj.data.uv_layers) == 0:
                    objs_with_missing_uv_map.append(obj.name)
            if len(objs_with_missing_uv_map) > 0:
                self.report({'ERROR'},
                            "UV map missing: '{0}'".format(objs_with_missing_uv_map))
                return False

        return True

    def is_joblist_empty(self):
        if not self.joblist:
            self.final_cleanup()
            self.report({'INFO'}, "Nothing to do.")
            return True

    # -------------------------------------------------------------------------
    # PREPARATIONS
    # -------------------------------------------------------------------------
    def prepare_materials_of_objects_by_jobname(self, objects, jobname, vertex_color_name=""):
        """Prepares the all materials for all bake objects for baking.

        Temporay nodes must be removed afer baking!
        """

        if jobname == 'Material ID':
            prepare_objects_for_bake_matid(objects)
        elif jobname == 'Vertex Color':
            prepare_objects_for_bake_vertex_color(objects, vertex_color_name)
        elif jobname == 'Wireframe':
            prepare_objects_for_bake_wireframe(objects)
        elif jobname == 'Diffuse':
            pass  # prepare nothing
        else:
            prepare_objects_for_bake(objects, jobname)

    # -------------------------------------------------------------------------
    # BAKE COMBINED:
    # -------------------------------------------------------------------------
    def bake_combined(self, context, bake_objects):
        if not self.can_bake(bake_objects):
            self.final_cleanup()
            return {'CANCELLED'}

        # Populate joblist
        self.joblist = get_joblist_from_objects(bake_objects)

        # skip, if one object has no vertex color
        if self.settings.use_vertex_color:
            objects_without_vertex_color = []
            for obj in bake_objects:
                if len(obj.data.vertex_colors) == 0:
                    objects_without_vertex_color.append(obj.name)
            if len(objects_without_vertex_color) > 0:
                self.report(
                    {'INFO'}, f"Objects have no Vertex Color: '{objects_without_vertex_color}'")
                return {'CANCELLED'}

        # empty joblist -> nothing to do
        if self.is_joblist_empty():
            return {'CANCELLED'}

        # material outpus for later clean up
        self.active_outputs = set(get_active_outputs(bake_objects))
        self.all_material_outputs = get_all_material_outputs(bake_objects)
        set_material_outputs_target_to_all(bake_objects)

        # Auto UV project
        auto_uv_project(bake_objects)

        # UV Map selection
        for obj in bake_objects:
            self.orig_uv_layers_active_indices[obj] = obj.data.uv_layers.active_index
            select_uv_map(obj)

        active_object = self.active_object
        if self.settings.bake_mode == "BATCH":
            active_object = bake_objects[0]

        # (optional) new material
        self.new_pri_node_values = get_principled_node_values(bake_objects)

        new_mat_name = self.settings.new_material_prefix
        if self.settings.make_new_material or self.settings.duplicate_objects:
            if self.settings.new_material_prefix == "":
                if self.settings.bake_mode == "BATCH":
                    new_mat_name = bake_objects[0].name
                else:
                    new_mat_name = active_object.name
            new_mat = new_material(new_mat_name, self.new_pri_node_values)

        # texture folder
        if self.settings.use_texture_folder:
            if self.settings.bake_mode == "BATCH":
                tex_dir = bake_objects[0].name
            else:
                tex_dir = active_object.name
            self.texture_folder = remove_not_allowed_signs(tex_dir)

        if not self.check_texture_folder():
            self.report({'ERROR'}, 'Error: Texture Folder')
            return {'CANCELLED'}

        # Go through joblist
        for self.jobname in self.joblist:

            # [""] <- empty string as the one object to iterate over for non-vertex-colors-jobs
            subjobs = [""]
            if self.jobname == "Vertex Color":
                subjobs = get_vertex_colors_to_bake_from_objects(bake_objects)

            for subname in subjobs:
                self.suffix_extension = subname

                # skip job, if no overwrite and image exists. load existing image
                if self.skip_job_if_file_exists(active_object):
                    continue

                # set individual samples
                set_samples(self.jobname)

                # Prepare materials
                self.prepare_materials_of_objects_by_jobname(
                    bake_objects, self.jobname, subname)

                # image to bake on
                image = self.new_bake_image(active_object.name)

                # append image to image dict for new material
                self.new_images[self.jobname + self.suffix_extension] = image

                # image nodes to bake
                create_bake_image_nodes(bake_objects, image)

                # Bake and Save image!
                self.bake_and_save(
                    image,
                    bake_type=get_bake_type_by(self.jobname))

                self.clean_after_bake(bake_objects)

        # jobs DONE

        # Glossiness
        if self.settings.use_invert_roughness:
            self.create_gloss_image(obj.name)

        # Add alpha channel to color
        if self.settings.use_alpha_to_color:
            self.alpha_channel_to_color()

        # Duplicate objects
        if self.settings.duplicate_objects:
            if self.settings.bake_mode == "BATCH":
                self.dup_objects.append(
                    duplicate_object(bake_objects[0], new_mat))
            else:
                self.dup_objects.extend(duplicate_objects(
                    self.active_object, bake_objects, new_mat))

        # add new images to new material
        if self.settings.make_new_material or self.settings.duplicate_objects:
            add_images_to_material(self.new_images, new_mat)
            self.report(
                {'INFO'}, "Mew Material created. '{0}'".format(new_mat.name))

            # (optional) add new material
            if self.settings.add_new_material:
                active_object.data.materials.append(new_mat)

        # Clean up!
        for mat_output, target in self.all_material_outputs.items():
            mat_output.target = target

        # remove tag from new material
        if self.settings.make_new_material or self.settings.duplicate_objects:
            if MATERIAL_TAG in new_mat:
                del(new_mat[MATERIAL_TAG])

        # Combine channels
        self.combine_channels(active_object)

    # -------------------------------------------------------------------------
    # BAKE BATCH:
    # -------------------------------------------------------------------------
    def bake_batch(self, context, bake_objects):
        if not self.can_bake(bake_objects):
            self.final_cleanup()
            return {'CANCELLED'}

        # Deselect all
        context.view_layer.objects.active = None
        for obj in bake_objects:
            obj.select_set(False)

        for obj in bake_objects:
            self.new_images.clear()

            obj.select_set(True)
            context.view_layer.objects.active = obj
            self.bake_combined(context, [obj])
            obj.select_set(False)

    # -------------------------------------------------------------------------
    # BAKE SELECTED TO ACTIVE:
    # -------------------------------------------------------------------------
    def bake_selected_to_active(self, context, bake_objects):
        active_object = self.active_object

        # exclude active object from selected objects
        if self.settings.bake_mode == 'SELECTED_TO_ACTIVE':
            if active_object in bake_objects:
                bake_objects.remove(active_object)

        if not self.can_bake(bake_objects):
            self.final_cleanup()
            return {'CANCELLED'}

        for mat_slot in active_object.material_slots:
            if not mat_slot.material:
                self.report({'INFO'}, "baking cancelled. '{0}' has empty Material Slots.".format(
                    active_object.name))
                return False

        # has active object UV map?
        if self.settings.auto_uv_project == 'OFF':
            if len(active_object.data.uv_layers) == 0:
                self.report(
                    {'INFO'}, "baking cancelled. '{0}' UV map missing.".format(active_object.name))
                self.final_cleanup()
                return {'CANCELLED'}

        # Can bake?
        for obj in bake_objects:
            # enabled for rendering?
            if obj.hide_render:
                self.report(
                    {'INFO'}, "baking cancelled. '{0}' not enabled for rendering.".format(obj.name))
                self.final_cleanup()
                return {'CANCELLED'}

        # Populate joblist
        self.joblist = get_joblist_from_objects(bake_objects)

        # empty joblist -> nothing to do
        if self.is_joblist_empty():
            return {'CANCELLED'}

        # material outpus for later clean up
        self.active_outputs = set(get_active_outputs(bake_objects))
        self.all_material_outputs = get_all_material_outputs(bake_objects)
        set_material_outputs_target_to_all(bake_objects)

        # Auto UV project
        if not self.settings.auto_uv_project == 'OFF':
            auto_uv_project(active_object)

        # UV Map selection
        self.orig_uv_layers_active_indices[active_object] = active_object.data.uv_layers.active_index
        select_uv_map(active_object)

        # new material
        self.new_pri_node_values = get_principled_node_values(bake_objects)
        new_mat_name = self.settings.new_material_prefix
        if self.settings.new_material_prefix == "":
            new_mat_name = active_object.name
        new_mat = new_material(new_mat_name, self.new_pri_node_values)
        active_object.data.materials.append(new_mat)

        # texture folder
        if self.settings.use_texture_folder:
            tex_dir = active_object.name
            self.texture_folder = remove_not_allowed_signs(tex_dir)

        # Go through joblist
        for self.jobname in self.joblist:

            # skip, if job is not "Vertex Color" and has no material
            if not self.jobname == "Vertex Color":
                skip = any(not has_material(obj) for obj in bake_objects)
                if skip:
                    self.report(
                        {'INFO'}, "{0} baking skipped for '{1}'".format(self.jobname, obj.name))
                    continue

            # [""] <- empty string as the one object to iterate over for non-vertex-colors-jobs
            subjobs = [""]
            if self.jobname == "Vertex Color":
                subjobs = get_vertex_colors_to_bake_from_objects(bake_objects)

            for subname in subjobs:
                self.suffix_extension = subname

                # skip job, if no overwrite and image exists. load existing image
                if self.skip_job_if_file_exists(active_object):
                    continue

                # set individual samples
                set_samples(self.jobname)

                # temp material for vertex color or wireframe
                if self.settings.use_vertex_color or self.settings.use_wireframe:
                    for obj in bake_objects:
                        if not has_material(obj):
                            add_temp_material(obj)

                # Prepare materials
                self.prepare_materials_of_objects_by_jobname(
                    bake_objects, self.jobname, subname)

                # image to bake on
                image = self.new_bake_image(active_object.name)

                # append image to image dict for new material
                self.new_images[self.jobname + self.suffix_extension] = image

                # image nodes to bake
                create_bake_image_nodes([active_object], image)

                # Bake and Save image!
                self.bake_and_save(
                    image,
                    bake_type=get_bake_type_by(self.jobname))

                self.clean_after_bake(bake_objects)
                self.clean_after_bake([active_object])

        # jobs DONE

        # Glossiness
        if self.settings.use_invert_roughness:
            self.create_gloss_image(obj.name)

        # Add alpha channel to color
        if self.settings.use_alpha_to_color:
            self.alpha_channel_to_color()

        # add new images to new material
        if self.settings.make_new_material or self.settings.duplicate_objects:
            add_images_to_material(self.new_images, new_mat)
            self.report(
                {'INFO'}, "Mew Material created. '{0}'".format(new_mat.name))

            # (optional) add new material
            if self.settings.add_new_material:
                active_object.data.materials.append(new_mat)

        # Clean up!
        for mat_output, target in self.all_material_outputs.items():
            mat_output.target = target

        # remove tag from new material
        if self.settings.make_new_material or self.settings.duplicate_objects:
            if MATERIAL_TAG in new_mat:
                del(new_mat[MATERIAL_TAG])

        # Combine channels
        self.combine_channels(active_object)

    # -------------------------------------------------------------------------
    # EXECUTE
    # -------------------------------------------------------------------------
    def execute(self, context):

        self.prefs = context.preferences.addons[__package__].preferences

        self.settings = context.scene.principled_baker_settings
        self.render_settings = context.scene.render.bake

        if not self.can_execute(context):
            return {'CANCELLED'}

        self.active_object = context.active_object
        if not self.active_object:
            context.view_layer.objects.active = context.selected_objects[0]
            self.active_object = context.active_object
        if not self.active_object.type == 'MESH':
            self.report({'ERROR'}, '{0} is not a mesh object'.format(
                self.active_object.name))
            return {'CANCELLED'}

        self.selected_objects = context.selected_objects
        for obj in self.selected_objects:
            if not obj.type == 'MESH':
                obj.select_set(False)

        self.bake_objects = []

        # active object is first item in bake_objects
        self.bake_objects.append(self.active_object)
        self.bake_objects.extend(get_only_meshes(self.selected_objects))
        self.bake_objects = list(set(self.bake_objects))

        self.dup_objects = []

        self.texture_folder = ""

        # Temp switch to Cycles - see clean up!
        self.render_engine = context.scene.render.engine
        self.preview_pause = context.scene.cycles.preview_pause
        if not self.render_engine == 'CYCLES' and self.prefs.switch_to_cycles:
            context.scene.cycles.preview_pause = True
            context.scene.render.engine = 'CYCLES'

        # Init Suffix List, if not existing
        if not len(context.scene.principled_baker_suffixlist):
            bpy.ops.principled_baker_suffixlist.init()

        # Auto Smooth - See clean up!
        self.auto_smooth_list = {}
        if not self.settings.auto_smooth == 'OBJECT':
            for obj in self.bake_objects:
                self.auto_smooth_list[obj] = obj.data.use_auto_smooth
            if self.settings.auto_smooth == 'ON':
                for obj in self.bake_objects:
                    obj.data.use_auto_smooth = True
            elif self.settings.auto_smooth == 'OFF':
                for obj in self.bake_objects:
                    obj.data.use_auto_smooth = False

        # Samples to restore - See clean up!
        self.org_samples = context.scene.cycles.samples

        # images for new material. "name":image
        self.new_images = {}

        self.joblist = []

        self.jobname = ""  # current bake job

        # current suffix extension used for vertex colors only
        self.suffix_extension = ""

        # store equal node values for the Principled BSDF node in new material
        # TODO option to copy principled node values
        self.new_pri_node_values = {}

        self.orig_uv_layers_active_indices = {}
        self.active_outputs = []

        # deligate bake modes
        if self.settings.bake_mode == 'COMBINED':
            self.bake_combined(context, self.bake_objects)
        elif self.settings.bake_mode == 'BATCH':
            self.bake_batch(context, self.bake_objects)
        elif self.settings.bake_mode == 'SELECTED_TO_ACTIVE':
            self.bake_selected_to_active(context, self.bake_objects)

        # join duplicate objects
        if self.settings.join_duplicate_objects and len(self.dup_objects) > 1:
            for obj in self.dup_objects:
                obj.select_set(True)
            bpy.ops.object.join()

            # copy modifiers from active object
            if self.settings.copy_modifiers:
                dup_obj = bpy.context.view_layer.objects.active
                dup_obj.modifiers.clear()
                bpy.context.view_layer.objects.active = self.active_object
                bpy.ops.object.make_links_data(type='MODIFIERS')

        self.final_cleanup()

        return {'FINISHED'}
