import hashlib
import os
import pathlib
import time

import bpy
from mathutils import Color

from .pbaker_functions import *


class PBAKER_OT_bake(bpy.types.Operator):
    bl_idname = "object.principled_baker_bake"
    bl_label = "Bake"
    bl_description = "bake all inputs of a Principled BSDF to image textures"
    bl_options = {'REGISTER', 'UNDO'}

    def extend_joblist(self, joblist):
        if self.settings.use_Diffuse:
            if "Diffuse" not in joblist:
                joblist.append("Diffuse")
        if self.settings.use_invert_roughness:
            if "Glossiness" not in joblist:
                joblist.append("Roughness")
        if self.settings.use_Bump:
            if "Bump" not in joblist:
                joblist.append("Bump")
        if self.settings.use_material_id:
            if "MatID" not in joblist:
                joblist.append("MatID")

    def get_suffix(self, input_name):
        bakelist = bpy.context.scene.principled_baker_bakelist

        if input_name == 'Diffuse':
            suffix = self.settings.suffix_diffuse
        elif input_name == 'Glossiness':
            suffix = self.settings.suffix_glossiness
        elif input_name == 'Bump':
            suffix = self.settings.suffix_bump
        elif input_name == 'Vertex_Color':
            suffix = self.settings.suffix_vertex_color
        elif input_name == 'MatID':
            suffix = self.settings.suffix_material_id
        else:
            suffix = bakelist[input_name]['suffix']

        if self.settings.suffix_text_mod == 'lower':
            suffix = suffix.lower()
        elif self.settings.suffix_text_mod == 'upper':
            suffix = suffix.upper()
        elif self.settings.suffix_text_mod == 'title':
            suffix = suffix.title()
        return suffix

    def delete_tagged_nodes(self, obj):
        for mat_slot in obj.material_slots:
            if mat_slot.material:
                delete_tagged_nodes(mat_slot.material, NODE_TAG)

    def delete_tagged_materials(self, obj, tag):
        for mat_index in range(0, len(obj.material_slots)):
            mat_slot = obj.material_slots[mat_index]
            if mat_slot.material:
                if tag in mat_slot.material.keys():
                    bpy.context.object.active_material_index = mat_index
                    bpy.ops.object.material_slot_remove({'object': obj})

    def disable_material_outputs(self, obj):
        for mat_slot in obj.material_slots:
            if mat_slot.material:
                for node in mat_slot.material.node_tree.nodes:
                    if node.type == "OUTPUT_MATERIAL":
                        node.is_active_output = False

    def guess_colors(self, obj, job_name):
        for mat_slot in obj.material_slots:
            if mat_slot.material:
                mat = mat_slot.material
                if not MATERIAL_TAG in mat.keys():
                    mat_out = get_active_output(mat_slot.material)
                    if job_name == 'Emission':
                        node_types = 'EMISSION'
                    elif job_name == 'Alpha':
                        node_types = 'BSDF_TRANSPARENT'
                    else:
                        node_types = ALPHA_NODES[job_name]
                    color_list = self.get_value_list_from_node_types(
                        mat_out, 'Color', node_types)
                    if len(color_list) >= 1:
                        self.new_node_colors[job_name] = color_list[0]

    def create_bake_image_node(self, mat, image):
        bake_image_node = new_image_node(mat)
        # 2.79
        if is_2_79:
            bake_image_node.color_space = 'COLOR' if image.colorspace_settings.name == 'sRGB' else 'NONE'
        bake_image_node.image = image  # add image to node
        bake_image_node[NODE_TAG] = 1  # tag for clean up
        bake_image_node.label = "TEMP BAKE NODE (If you see this, something went wrong!)"
        bake_image_node.use_custom_color = True
        bake_image_node.color = (1, 0, 0)

        # make only bake_image_node active
        bake_image_node.select = True
        mat.node_tree.nodes.active = bake_image_node

    def save_image(self, image):
        save_image_as(image,
                      file_path=image.filepath,
                      file_format=self.settings.file_format,
                      color_mode=self.settings.color_mode,
                      color_depth=self.settings.color_depth,
                      compression=self.settings.compression,
                      quality=self.settings.quality,
                      tiff_codec=self.settings.tiff_codec,
                      exr_codec=self.settings.exr_codec)

    def new_material(self, name):
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        mat[MATERIAL_TAG] = 1

        mat_output = mat.node_tree.nodes['Material Output']
        mat_output.location = (300.0, 300.0)

        # 2.79
        if is_2_79:
            mat.node_tree.nodes.remove(mat.node_tree.nodes['Diffuse BSDF'])
            principled_node = mat.node_tree.nodes.new(
                type='ShaderNodeBsdfPrincipled')
        # 2.80
        else:
            principled_node = mat.node_tree.nodes['Principled BSDF']

        principled_node.location = (10.0, 300.0)

        # copy settings to new principled_node
        for k, v in self.new_principled_node_settings.items():
            if k == 'Color':
                k = 'Base Color'
            principled_node.inputs[k].default_value = v

        mat.node_tree.links.new(
            principled_node.outputs['BSDF'], mat_output.inputs['Surface'])
        return mat

    def get_new_principled_node_settings(self, objs):
        """returns dictionary with equal node values in all materials in all objects, eg. metal, roughness"""

        n_pri_node_settings = {}
        for obj in objs:
            for value_name in NODE_INPUTS:
                if value_name not in ['Subsurface Radius', 'Normal', 'Clearcoat Normal', 'Tangent']:
                    value_list = []
                    for mat_slot in obj.material_slots:
                        if mat_slot.material:
                            mat = mat_slot.material
                            if not MATERIAL_TAG in mat.keys():
                                material_output = get_active_output(mat)
                                tmp_val_list = self.get_value_list(
                                    material_output, value_name)
                                value_list.extend(tmp_val_list)

                    if value_list:
                        if is_list_equal(value_list):
                            if self.settings.make_new_material or self.settings.bake_mode == 'SELECTED_TO_ACTIVE':
                                n_pri_node_settings[value_name] = value_list[0]
        return n_pri_node_settings

    def add_images_to_material(self, new_mat, new_images):

        principled_node = find_node_by_type(new_mat, 'BSDF_PRINCIPLED')
        material_output = find_node_by_type(new_mat, 'OUTPUT_MATERIAL')

        if new_images:
            tex_coord_node = new_mat.node_tree.nodes.new(
                type="ShaderNodeTexCoord")
            mapping_node = new_mat.node_tree.nodes.new(
                type="ShaderNodeMapping")
            new_mat.node_tree.links.new(
                tex_coord_node.outputs["UV"], mapping_node.inputs["Vector"])
            mapping_node.location.x = principled_node.location.x + \
                IMAGE_NODE_OFFSET_X - mapping_node.width - 100
            tex_coord_node.location.x = mapping_node.location.x - tex_coord_node.width - 100

        image_nodes = {}
        node_offset_index = 0
        for name, image in new_images.items():
            image_node = new_image_node(new_mat)
            image_node.label = name

            image_nodes[name] = image_node

            # 2.79
            if is_2_79:
                image_node.color_space = 'COLOR' if name in SRGB_INPUTS else 'NONE'

            image_node.image = image

            # link to mapping node
            new_mat.node_tree.links.new(
                mapping_node.outputs["Vector"], image_node.inputs["Vector"])

            # rearrange nodes
            image_node.width = IMAGE_NODE_WIDTH
            image_node.location.x = principled_node.location.x + IMAGE_NODE_OFFSET_X
            image_node.location.y = principled_node.location.y + \
                IMAGE_NODE_OFFSET_Y * node_offset_index
            node_offset_index += 1

        # link nodes
        for name, image_node in image_nodes.items():
            if name in NORMAL_INPUTS:
                normal_node = new_mat.node_tree.nodes.new(
                    type="ShaderNodeNormalMap")
                normal_node.location.x = IMAGE_NODE_OFFSET_X + 1.5*IMAGE_NODE_WIDTH
                normal_node.location.y = image_nodes[name].location.y
                new_mat.node_tree.links.new(
                    image_node.outputs['Color'], normal_node.inputs['Color'])
                new_mat.node_tree.links.new(
                    normal_node.outputs[name], principled_node.inputs[name])

            elif name == 'Bump':
                bump_node = new_mat.node_tree.nodes.new(type="ShaderNodeBump")
                bump_node.location.x = IMAGE_NODE_OFFSET_X + 1.5*IMAGE_NODE_WIDTH
                bump_node.location.y = image_nodes[name].location.y
                new_mat.node_tree.links.new(
                    image_node.outputs['Color'], bump_node.inputs['Height'])
                new_mat.node_tree.links.new(
                    bump_node.outputs['Normal'], principled_node.inputs['Normal'])

            elif name == "Displacement":
                # 2.79
                if is_2_79:
                    new_mat.node_tree.links.new(image_node.outputs['Color'],
                                                material_output.inputs["Displacement"])
                # 2.80
                else:
                    disp_node = new_mat.node_tree.nodes.new(
                        type='ShaderNodeDisplacement')
                    new_mat.node_tree.links.new(image_node.outputs['Color'],
                                                disp_node.inputs["Height"])
                    new_mat.node_tree.links.new(disp_node.outputs["Displacement"],
                                                material_output.inputs["Displacement"])
                    disp_node.location.x = NODE_OFFSET_X

            elif name == 'Alpha' or name in ALPHA_NODES.keys():
                if name == "Alpha":
                    alpha_node = new_mat.node_tree.nodes.new(
                        type='ShaderNodeBsdfTransparent')
                if name == "Translucent_Alpha":
                    alpha_node = new_mat.node_tree.nodes.new(
                        type='ShaderNodeBsdfTranslucent')
                elif name == "Glass_Alpha":
                    alpha_node = new_mat.node_tree.nodes.new(
                        type='ShaderNodeBsdfGlass')
                # color
                alpha_node.inputs['Color'].default_value = self.new_node_colors[name]

                mixshader_node = new_mat.node_tree.nodes.new(
                    type='ShaderNodeMixShader')

                # links
                new_mat.node_tree.links.new(material_output.inputs[0].links[0].from_socket,
                                            mixshader_node.inputs[2])
                new_mat.node_tree.links.new(
                    mixshader_node.outputs['Shader'], material_output.inputs[0])
                new_mat.node_tree.links.new(alpha_node.outputs['BSDF'],
                                            mixshader_node.inputs[1])
                if not self.settings.use_alpha_to_color:
                    new_mat.node_tree.links.new(image_node.outputs['Color'],
                                                mixshader_node.inputs['Fac'])

                # node locations
                sib = get_sibling_node(alpha_node)
                alpha_node.location = (
                    sib.location.x, sib.location.y + NODE_OFFSET_Y)
                mid_offset_y = alpha_node.location.y
                mixshader_node.location = (
                    sib.location.x + NODE_OFFSET_X, mid_offset_y)

                # 2.80
                # if is_2_80:
                if name == "Alpha":
                    if self.settings.use_alpha_to_color:
                        color_image_node = image_nodes['Color']
                        if is_2_80:
                            new_mat.node_tree.links.new(color_image_node.outputs['Alpha'],
                                                        principled_node.inputs['Alpha'])
                            new_mat.node_tree.links.new(
                                mixshader_node.inputs[2].links[0].from_socket,
                                material_output.inputs[0])
                        else:
                            new_mat.node_tree.links.new(color_image_node.outputs['Alpha'],
                                                        mixshader_node.inputs['Fac'])
                    else:
                        if is_2_80:
                            new_mat.node_tree.links.new(image_node.outputs['Color'],
                                                        principled_node.inputs['Alpha'])
                            new_mat.node_tree.links.new(
                                mixshader_node.inputs[2].links[0].from_socket,
                                material_output.inputs[0])
                        else:
                            new_mat.node_tree.links.new(image_node.outputs['Color'],
                                                        mixshader_node.inputs['Fac'])

            elif name == 'Emission':
                emission_node = new_mat.node_tree.nodes.new(
                    type='ShaderNodeEmission')
                emission_node.inputs['Color'].default_value = self.new_node_colors[name]

                addshader_node = new_mat.node_tree.nodes.new(
                    type='ShaderNodeAddShader')

                # links
                new_mat.node_tree.links.new(material_output.inputs[0].links[0].from_socket,
                                            addshader_node.inputs[1])
                new_mat.node_tree.links.new(emission_node.outputs['Emission'],
                                            addshader_node.inputs[0])
                new_mat.node_tree.links.new(
                    addshader_node.outputs['Shader'], material_output.inputs[0])
                new_mat.node_tree.links.new(
                    image_node.outputs['Color'], emission_node.inputs['Color'])

                # node locations
                sib = get_sibling_node(emission_node)
                emission_node.location = (
                    sib.location.x, sib.location.y + NODE_OFFSET_Y)
                mid_offset_y = emission_node.location.y
                addshader_node.location = (
                    sib.location.x + NODE_OFFSET_X, mid_offset_y)

            elif name == 'Color':
                name = 'Base Color'
                new_mat.node_tree.links.new(image_node.outputs['Color'],
                                            principled_node.inputs[name])

                if self.settings.use_alpha_to_color and "Alpha" in new_images.keys():
                    if is_2_80:
                        new_mat.node_tree.links.new(
                            image_node.outputs['Alpha'], principled_node.inputs['Alpha'])
                    else:
                        new_mat.node_tree.links.new(material_output.inputs[0].links[0].from_socket,
                                                    mixshader_node.inputs[2])
                        new_mat.node_tree.links.new(
                            material_output.inputs[0], mixshader_node.outputs['Shader'])
                        new_mat.node_tree.links.new(alpha_node.outputs['BSDF'],
                                                    mixshader_node.inputs[1])
                        new_mat.node_tree.links.new(image_node.outputs["Alpha"],
                                                    mixshader_node.inputs['Fac'])

                # mix AO with color
                if 'Ambient Occlusion' in image_nodes.keys():  # new_images.keys():
                    # new_image_node(new_mat)
                    ao_image_node = image_nodes['Ambient Occlusion']

                    # mix
                    mix_node = new_mixrgb_node(new_mat, 1.0)
                    mix_node.blend_type = 'MULTIPLY'
                    mix_node.location.x = image_node.location.x - IMAGE_NODE_OFFSET_X/2
                    mix_node.location.y = image_node.location.y

                    # links
                    new_mat.node_tree.links.new(mix_node.outputs["Color"],
                                                principled_node.inputs['Base Color'])
                    new_mat.node_tree.links.new(image_node.outputs["Color"],
                                                mix_node.inputs['Color1'])
                    new_mat.node_tree.links.new(ao_image_node.outputs["Color"],
                                                mix_node.inputs['Color2'])

            elif name in ["Glossiness", "Ambient Occlusion", "Vertex_Color", "MatID", "Diffuse"]:
                pass  # skip some

            else:
                new_mat.node_tree.links.new(image_node.outputs['Color'],
                                            principled_node.inputs[name])

    def new_pb_emission_node(self, material, color=[0, 0, 0, 1]):
        node = material.node_tree.nodes.new(type='ShaderNodeEmission')
        node.inputs['Color'].default_value = color  # [0, 0, 0, 1]
        node[NODE_TAG] = 1
        return node

    def new_pb_output_node(self, material):
        node = material.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
        node.is_active_output = True
        node[NODE_TAG] = 1
        return node

    def is_image_file(self, image_file_name):
        cwd = os.path.normpath(os.path.dirname(bpy.data.filepath))
        abs_path = os.path.normpath(self.get_image_file_path(image_file_name))
        if not os.path.isabs(abs_path):
            abs_path = os.path.normpath(cwd + abs_path)
        return os.path.isfile(abs_path)

    def get_image_file_name(self, object_name, job_name):
        prefix = self.settings.image_prefix
        if prefix == "" or len(self.selected_objects) > 1 or self.settings.use_object_name:
            prefix = self.settings.image_prefix + object_name
        image_file_format = IMAGE_FILE_FORMAT_ENDINGS[self.settings.file_format]
        image_file_name = "{0}{1}.{2}".format(
            prefix, self.get_suffix(job_name), image_file_format)
        return image_file_name

    def get_image_file_path(self, image_file_name):
        path = self.settings.file_path
        if path == "//":
            path += image_file_name
        else:
            if path.startswith("//"):
                path = bpy.path.relpath(path)
            else:
                path = os.path.abspath(path)
                path = bpy.path.abspath(path)
            if not path.endswith(os.path.sep):
                path += os.path.sep
            path += image_file_name
        return path

    def load_image(self, image_file_name):
        if image_file_name in bpy.data.images:
            image = bpy.data.images[image_file_name]
        else:
            path = self.get_image_file_path(image_file_name)
            image = bpy.data.images.load(path)
        return image

    def new_bake_image(self, object_name, job_name):
        if self.settings.bake_mode == 'BATCH':
            prefix = self.settings.image_prefix + object_name
        else:
            if self.settings.use_object_name:
                prefix = self.settings.image_prefix + object_name
            else:
                if self.settings.image_prefix:
                    prefix = self.settings.image_prefix
                else:
                    prefix = object_name

        file_format = IMAGE_FILE_FORMAT_ENDINGS[self.settings.file_format]
        name = "{0}{1}.{2}".format(prefix, self.get_suffix(
            job_name), file_format)  # include ending
        path = self.get_image_file_path(name)

        # alpha
        alpha = False
        if self.settings.color_mode == 'RGBA':
            alpha = True

        # color
        color = (0.5, 0.5, 1.0, 1.0) if get_bake_type(
            job_name) == 'NORMAL' else (0.0, 0.0, 0.0, 1.0)

        # resolution
        res = int(self.settings.custom_resolution) if self.settings.resolution == 'CUSTOM' else int(
            self.settings.resolution)

        is_float = False if self.settings.color_depth == '8' else True

        image = bpy.data.images.new(
            name=name, width=res, height=res, alpha=alpha, float_buffer=is_float)

        image.colorspace_settings.name = 'sRGB' if job_name in [
            'Color', 'Diffuse'] else 'Non-Color'
        image.generated_color = color
        image.generated_type = 'BLANK'
        # 2.79
        if is_2_79:
            image.use_alpha = alpha
        image.filepath = path

        return image

    def create_gloss_image(self, obj_name, img):
        img_name = self.get_image_file_name(obj_name, "Glossiness")
        if img_name in bpy.data.images:
            bpy.data.images.remove(bpy.data.images[img_name])
        gloss_image = self.new_bake_image(obj_name, "Glossiness")
        gloss_image.filepath = self.get_image_file_path(img_name)
        gloss_image.pixels = get_invert_image(img)
        self.save_image(gloss_image)

    def can_bake(self, objects):
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
            # no UV map?
            if not self.settings.bake_mode == 'SELECTED_TO_ACTIVE':
                if self.settings.auto_uv_project == 'OFF':
                    if len(obj.data.uv_layers) == 0:
                        self.report(
                            {'INFO'}, "baking cancelled. '{0}' UV map missing.".format(obj.name))
                        return False
            # has vertex color?
            if not self.settings.bake_mode == 'BATCH':
                if self.settings.use_vertex_color and len(obj.data.vertex_colors) == 0:
                    self.report(
                        {'INFO'}, "baking cancelled. '{0}' has no Vertex Color.".format(obj.name))
                    return False
            # empty material slots?
            for mat_slot in obj.material_slots:
                if not mat_slot.material:
                    self.report(
                        {'INFO'}, "baking cancelled. '{0}' has empty Material Slots.".format(obj.name))
                    return False
        return True

    def prepare_objects_for_bake_matid(self, objects):

        def create_temp_nodes(mat, color):
            pb_output_node = self.new_pb_output_node(mat)
            pb_emission_node = self.new_pb_emission_node(mat, color)
            socket_to_pb_emission_node_color = pb_emission_node.inputs['Color']

            # activate temp output
            material_output = get_active_output(mat)  # orig material output
            if material_output:
                material_output.is_active_output = False
            pb_output_node.is_active_output = True

            # link pb_emission_node to material_output
            mat.node_tree.links.new(
                pb_emission_node.outputs[0], pb_output_node.inputs['Surface'])

        materials = []
        for obj in objects:
            for mat_slot in obj.material_slots:
                if mat_slot.material:
                    if mat_slot.material not in materials:
                        materials.append(mat_slot.material)

        color = [0, 0, 0, 1]

        if self.prefs.mat_id_algorithm == 'HUE':
            n_materials = len(materials)
            # for mat_index, mat in enumerate(materials):
            for mat_index, mat in enumerate(materials):
                c = Color()
                c.hsv = mat_index/n_materials, self.prefs.mat_id_saturation, self.prefs.mat_id_value
                color = c.r, c.g, c.b, 1.0

                create_temp_nodes(mat, color)

        elif self.prefs.mat_id_algorithm == 'NAME':
            for mat in materials:
                s = mat.name.encode('utf-8')
                h = int(hashlib.sha1(s).hexdigest(), base=16)
                r = h % 256 / 256
                g = (h >> 32) % 256 / 256
                b = (h >> 16) % 256 / 256
                color = r, g, b, 1.0

                create_temp_nodes(mat, color)

    def prepare_objects_for_bake_vertex_color(self, objects):
        for obj in objects:
            for mat_slot in obj.material_slots:
                if mat_slot.material:
                    mat = mat_slot.material

                    pb_output_node = self.new_pb_output_node(mat)
                    pb_emission_node = self.new_pb_emission_node(mat)
                    socket_to_pb_emission_node_color = pb_emission_node.inputs['Color']

                    # activate temp output
                    material_output = get_active_output(
                        mat)  # orig material output
                    if material_output:
                        material_output.is_active_output = False
                    pb_output_node.is_active_output = True

                    for name, vert_col in obj.data.vertex_colors.items():
                        if vert_col.active_render:
                            active_vert_col = name
                    attr_node = mat.node_tree.nodes.new(
                        type='ShaderNodeAttribute')
                    attr_node[NODE_TAG] = 1  # tag for clean up
                    attr_node.attribute_name = active_vert_col
                    mat.node_tree.links.new(
                        attr_node.outputs['Color'], socket_to_pb_emission_node_color)

                    # link pb_emission_node to material_output
                    mat.node_tree.links.new(
                        pb_emission_node.outputs[0], pb_output_node.inputs['Surface'])

    def prepare_objects_for_bake(self, objects, job_name):
        for obj in objects:
            for mat_slot in obj.material_slots:
                if mat_slot.material:
                    mat = mat_slot.material
                    # 2.79 Normal Map
                    if is_2_79 and job_name == "Normal":
                        self.prepare_material_for_bake_job(mat, job_name)
                    # 2.80
                    if job_name not in ["Emission", "Normal"]:
                        self.prepare_material_for_bake_job(mat, job_name)

    def prepare_material_for_bake_job(self, mat, job_name):

        active_output = prepare_material_for_bake(mat)

        # Deselect all nodes
        for node in mat.node_tree.nodes:
            node.select = False

        # temp nodes
        for node in mat.node_tree.nodes:
            if node.type == "OUTPUT_MATERIAL" and NODE_TAG in node.keys():
                material_output = node
        pb_output_node = self.new_pb_output_node(mat)
        pb_emission_node = self.new_pb_emission_node(mat, [1, 1, 1, 1])
        pb_output_node.location.x = active_output.location.x
        pb_emission_node.location.x = active_output.location.x

        socket_to_pb_emission_node_color = pb_emission_node.inputs['Color']

        # activate temp output and deactivate others
        deactivate_material_outputs(mat)
        pb_output_node.is_active_output = True

        socket_to_surface = material_output.inputs['Surface'].links[0].from_socket
        bake_type = get_bake_type(job_name)

        if bake_type == 'EMIT':
            if job_name in ALPHA_NODES.keys():
                prepare_bake_factor(
                    mat, socket_to_surface, socket_to_pb_emission_node_color, ALPHA_NODES[job_name], 'Fac')

            elif job_name == 'Alpha':
                # 2.79
                if is_2_79:
                    prepare_bake_factor(
                        mat, socket_to_surface, socket_to_pb_emission_node_color, 'BSDF_TRANSPARENT', 'Fac')
                # 2.80
                else:
                    if is_node_type_in_node_tree(material_output, 'BSDF_TRANSPARENT'):
                        prepare_bake_factor(
                            mat, socket_to_surface, socket_to_pb_emission_node_color, 'BSDF_TRANSPARENT', 'Fac')
                    else:
                        prepare_bake(mat, socket_to_surface,
                                     socket_to_pb_emission_node_color, 'Alpha')

            elif job_name == 'Displacement':
                if material_output.inputs['Displacement'].is_linked:
                    socket_to_displacement = material_output.inputs['Displacement'].links[0].from_socket
                    # 2.79
                    if is_2_79:
                        from_socket = socket_to_displacement.links[0].from_socket
                        mat.node_tree.links.new(
                            from_socket, socket_to_pb_emission_node_color)
                    # 2.80
                    else:
                        prepare_bake(mat, socket_to_displacement,
                                     socket_to_pb_emission_node_color, 'Height')

            elif job_name == 'Bump':
                prepare_bake(mat, socket_to_surface,
                             socket_to_pb_emission_node_color, 'Height')
            elif job_name == 'Ambient Occlusion':
                prepare_bake(mat, socket_to_surface,
                             socket_to_pb_emission_node_color, 'Ambient Occlusion')
            else:
                prepare_bake(mat, socket_to_surface,
                             socket_to_pb_emission_node_color, job_name)

            # link pb_emission_node to material_output
            mat.node_tree.links.new(
                pb_emission_node.outputs[0], pb_output_node.inputs['Surface'])

        # 2.79
        elif bake_type == 'NORMAL' and is_2_79:
            if self.settings.use_Bump:
                prepare_bake(mat, socket_to_surface,
                             socket_to_pb_emission_node_color, job_name)
                # link pb_emission_node to material_output
                mat.node_tree.links.new(
                    pb_emission_node.outputs[0], pb_output_node.inputs['Surface'])
            # normal
            prepare_bake(mat, socket_to_surface,
                         socket_to_pb_emission_node_color, 'Normal')
            # link pb_emission_node to material_output
            mat.node_tree.links.new(
                pb_emission_node.outputs[0], pb_output_node.inputs['Surface'])
            s = pb_emission_node.inputs['Color'].links[0].from_socket
            mat.node_tree.links.new(s, pb_output_node.inputs['Displacement'])

        # put temp nodes in a frame
        p_baker_frame = mat.node_tree.nodes["p_baker_temp_frame"]
        for node in mat.node_tree.nodes:
            if NODE_TAG in node.keys():
                node.parent = p_baker_frame

    def get_value_list(self, node, value_name):
        value_list = []

        def find_values(node, value_name):
            if not node.type == 'NORMAL_MAP':
                if value_name == 'Color' and node.type == 'BSDF_PRINCIPLED':
                    tmp_value_name = 'Base Color'
                else:
                    tmp_value_name = value_name
                if tmp_value_name in node.inputs.keys():
                    if node.inputs[tmp_value_name].type == 'RGBA':
                        [r, g, b, a] = node.inputs[tmp_value_name].default_value
                        value_list.append([r, g, b, a])
                    else:
                        value_list.append(
                            node.inputs[value_name].default_value)

                for socket in node.inputs:
                    if socket.is_linked:
                        from_node = socket.links[0].from_node
                        find_values(from_node, value_name)
        find_values(node, value_name)
        return value_list

    def get_value_list_from_node_types(self, node, value_name, node_types):
        value_list = []

        def find_values(node, value_name, node_types):
            if value_name == 'Color' and node.type == 'BSDF_PRINCIPLED':
                tmp_value_name = 'Base Color'
            else:
                tmp_value_name = value_name
            if node.type in node_types and tmp_value_name in node.inputs.keys():
                if node.inputs[tmp_value_name].type == 'RGBA':
                    [r, g, b, a] = node.inputs[tmp_value_name].default_value
                    value_list.append([r, g, b, a])
                else:
                    value_list.append(node.inputs[value_name].default_value)

            for socket in node.inputs:
                if socket.is_linked:
                    from_node = socket.links[0].from_node
                    find_values(from_node, value_name, node_types)
        find_values(node, value_name, node_types)
        return value_list

    def smart_project(self):
        bpy.ops.uv.smart_project(angle_limit=self.settings.angle_limit,
                                 island_margin=self.settings.island_margin,
                                 user_area_weight=self.settings.user_area_weight,
                                 use_aspect=self.settings.use_aspect,
                                 stretch_to_bounds=self.settings.stretch_to_bounds)

    def lightmap_pack(self):
        bpy.ops.uv.lightmap_pack(PREF_CONTEXT='ALL_FACES',
                                 PREF_PACK_IN_ONE=self.settings.share_tex_space,
                                 PREF_NEW_UVLAYER=self.settings.new_uv_map,
                                 PREF_APPLY_IMAGE=self.settings.new_image,
                                 PREF_IMG_PX_SIZE=self.settings.image_size,
                                 PREF_BOX_DIV=self.settings.pack_quality,
                                 PREF_MARGIN_DIV=self.settings.lightmap_margin)

    def auto_uv_project(self, obj):
        orig_selected_objects = self.selected_objects
        for o in self.selected_objects:
            select_set(o, False)
        select_set(obj, True)

        if self.settings.auto_uv_project == 'SMART':
            self.smart_project()
        elif self.settings.auto_uv_project == 'LIGHTMAP':
            self.lightmap_pack()

        for o in orig_selected_objects:
            select_set(o, True)

    def bake_and_save(self, image, bake_type='EMIT', selected_to_active=False):
        if is_2_80:
            image.save()

        self.report({'INFO'}, "baking '{0}'".format(image.name))
        self.bake(bake_type, selected_to_active)

        self.save_image(image)
        if is_2_80:
            image.reload()

    def bake(self, bake_type, selected_to_active=False):
        org_samples = bpy.context.scene.cycles.samples
        bpy.context.scene.cycles.samples = self.settings.samples

        pass_filter = []
        if self.settings.use_Diffuse:
            if self.render_settings.use_pass_direct:
                pass_filter.append('DIRECT')
            if self.render_settings.use_pass_indirect:
                pass_filter.append('INDIRECT')
            if self.render_settings.use_pass_color:
                pass_filter.append('COLOR')
        pass_filter = set(pass_filter)

        bpy.ops.object.bake(
            type=bake_type,
            pass_filter=pass_filter,
            use_selected_to_active=selected_to_active,
            normal_space=self.render_settings.normal_space,
            normal_r=self.render_settings.normal_r,
            normal_g=self.render_settings.normal_g,
            normal_b=self.render_settings.normal_b, )
        bpy.context.scene.cycles.samples = org_samples

    def final_cleanup(self):
        # Auto Smooth - Clean up!
        if not self.settings.auto_smooth == 'OBJECT':
            for obj in self.auto_smooth_list:
                obj.data.use_auto_smooth = self.auto_smooth_list[obj]

        # Clean up! - Re-Select objects
        for obj in self.orig_selected_objects:
            select_set(obj, True)

        # Render Engine - Clean up!
        if self.prefs.switch_to_cycles:
            bpy.context.scene.render.engine = self.render_engine
            bpy.context.scene.cycles.preview_pause = self.preview_pause

    def select_uv_map(self, obj):
        # 2.79/2.80
        uv_layers = obj.data.uv_textures if is_2_79 else obj.data.uv_layers

        if self.settings.select_uv_map == 'ACTIVE_RENDER':
            for i in range(0, len(obj.data.uv_layers)):
                if uv_layers[i].active_render:
                    uv_layers.active_index = i
                    break
        else:
            index_uv_layer = int(self.settings.select_uv_map) - 1
            if index_uv_layer <= len(obj.data.uv_layers) - 1:
                uv_layers.active_index = index_uv_layer

    def check_file_path(self):
        path = self.settings.file_path

        if path in ['', ' ', '/', '///', '\\', '//\\']:
            self.report(
                {'ERROR'}, "'{}' not a valid path or no permission".format(path))
            return False

        cwd = os.path.dirname(bpy.data.filepath)
        if path == "//":
            abs_path = os.path.normpath(cwd)
        else:
            if path.startswith("//"):
                path = path[2:]
            if os.path.isabs(path):
                abs_path = bpy.path.abspath(path)
            else:
                abs_path = bpy.path.abspath(cwd + os.path.sep + path)

        os_abs_path = os.path.abspath(abs_path)

        if not os.path.exists(os_abs_path):
            try:
                os.makedirs(os_abs_path)
            except OSError as e:
                return False

        if check_permission(os_abs_path):
            return True

    # def excecute(self, context):
    def invoke(self, context, event):
        # 2.79
        if is_2_79:
            self.prefs = context.user_preferences.addons[__package__].preferences
        # 2.80
        else:
            self.prefs = context.preferences.addons[__package__].preferences

        self.settings = context.scene.principled_baker_settings
        self.render_settings = context.scene.render.bake
        self.active_object = context.active_object
        self.selected_objects = bpy.context.selected_objects

        self.new_node_colors = {
            "Alpha": [1.0, 1.0, 1.0, 1.0],
            "Translucent_Alpha": [0.8, 0.8, 0.8, 1.0],
            "Glass_Alpha": [1.0, 1.0, 1.0, 1.0],
            'Emission': [1.0, 1.0, 1.0, 1.0],
        }

        # File needs to be saved
        if not bpy.data.is_saved:
            self.report(
                {'ERROR'}, 'Blendfile needs to be saved to get relative output paths')
            return {'CANCELLED'}

        # Check file path
        check = self.check_file_path()
        if not check:
            self.report({'ERROR'},
                        "'{}' Permission denied".format(self.settings.file_path))
            return {'CANCELLED'}

        # Input error handling
        if not self.active_object.type == 'MESH':
            self.report({'ERROR'}, '{0} is not a mesh object'.format(
                self.active_object.name))
            return {'CANCELLED'}
        if self.settings.bake_mode == 'SELECTED_TO_ACTIVE':
            if len(self.selected_objects) < 2:
                self.report({'ERROR'}, 'Select at least 2 objects!')
                return {'CANCELLED'}
        if self.settings.use_Diffuse:
            d, i, c = self.render_settings.use_pass_direct, self.render_settings.use_pass_indirect, self.render_settings.use_pass_color
            if not d and not i and not c:
                self.report(
                    {'ERROR'}, "Error: Bake pass requires Direct, Indirect, or Color contributions to be enabled.")
                return {'CANCELLED'}

        # Temp switch to Cycles - see clean up!
        self.render_engine = bpy.context.scene.render.engine
        self.preview_pause = bpy.context.scene.cycles.preview_pause
        if not self.render_engine == 'CYCLES' and self.prefs.switch_to_cycles:
            bpy.context.scene.cycles.preview_pause = True
            bpy.context.scene.render.engine = 'CYCLES'

        # Bake only works in cycles (for now)
        if not bpy.context.scene.render.engine == 'CYCLES':
            self.report({'ERROR'}, 'Error: Current render engine ({0}) does not support baking'.format(
                bpy.context.scene.render.engine))
            return {'CANCELLED'}

        # Select only meshes
        self.orig_selected_objects = bpy.context.selected_objects
        for obj in self.selected_objects:
            if not obj.type == 'MESH':
                select_set(obj, False)

        # Auto Smooth - See clean up!
        self.auto_smooth_list = {}
        if not self.settings.auto_smooth == 'OBJECT':
            for obj in self.selected_objects:
                self.auto_smooth_list[obj] = obj.data.use_auto_smooth
            if self.settings.auto_smooth == 'ON':
                for obj in self.selected_objects:
                    obj.data.use_auto_smooth = True
            elif self.settings.auto_smooth == 'OFF':
                for obj in self.selected_objects:
                    obj.data.use_auto_smooth = False

        new_images = {}

        bake_objects = []
        bake_objects = get_only_meshes(self.selected_objects)

        # exclude active object from selected objects
        if self.settings.bake_mode == 'SELECTED_TO_ACTIVE':
            if self.active_object in bake_objects:
                bake_objects.remove(self.active_object)

        self.new_principled_node_settings = self.get_new_principled_node_settings(
            bake_objects)

        ########
        # Bake Single/Batch:
        ########
        if self.settings.bake_mode == 'BATCH':

            # BEGIN progress report
            bpy.context.window_manager.progress_begin(0, len(bake_objects))
            progress = 0

            # Deselect all
            for obj in bake_objects:
                select_set(obj, False)

            for obj in bake_objects:

                new_images.clear()

                # Select only one
                select_set(obj, True)

                obj_list = [obj]

                # Can bake?
                if not self.can_bake(obj_list):
                    continue

                # Populate joblist
                joblist = []
                if self.settings.use_autodetect:
                    joblist = get_joblist_from_object(obj)
                else:
                    joblist = get_joblist_manual()

                self.extend_joblist(joblist)

                if self.settings.use_vertex_color:
                    if len(obj.data.vertex_colors) > 0:
                        if "Vertex_Color" not in joblist:
                            joblist.append("Vertex_Color")
                    else:
                        self.report(
                            {'INFO'}, "Vertex Color baking skipped. '{0}' has no Vertex Color".format(obj.name))

                # empty joblist -> nothing to do
                if not joblist:
                    self.report(
                        {'INFO'}, "Nothing to do for {}.".format(obj.name))
                    continue

                # material outpus for later clean up
                active_outputs = get_active_outputs(obj_list)
                all_material_outputs = get_all_material_outputs(obj_list)
                # 2.80
                if not is_2_79:
                    set_material_outputs_target_to_all(obj_list)

                # Auto UV project
                if not self.settings.auto_uv_project == 'OFF':
                    self.auto_uv_project(obj)

                # UV Map selection
                orig_uv_layers_active_index = obj.data.uv_layers.active_index
                if not self.settings.select_uv_map == 'SELECTED':
                    self.select_uv_map(obj)

                # (optional) new material
                if self.settings.make_new_material:
                    # guess colors for Transparent, Translucent, Glass, Emission
                    for job_name in joblist:
                        if job_name in self.new_node_colors.keys():
                            self.guess_colors(obj, job_name)
                    # new material
                    new_mat_name = obj.name if self.settings.new_material_prefix == "" else self.settings.new_material_prefix
                    new_mat = self.new_material(new_mat_name)

                # Go through joblist
                for job_name in joblist:

                    # skip, if no overwrite and image exists. load existing image
                    image_file_name = self.get_image_file_name(
                        obj.name, job_name)
                    if not self.settings.use_overwrite and self.is_image_file(image_file_name):
                        self.report({'INFO'}, "baking skipped for '{0}'. File exists.".format(
                            self.get_image_file_name(obj.name, job_name)))

                        # load image for new material
                        new_images[job_name] = self.load_image(image_file_name)

                        continue  # skip job

                    # else: do bake
                    # image to bake on
                    image = self.new_bake_image(obj.name, job_name)

                    # append image to image dict for new material
                    new_images[job_name] = image

                    # temp material for vertex color
                    if self.settings.use_vertex_color:
                        if not has_material(obj):
                            add_temp_material(obj)

                    # Prepare materials
                    if job_name == 'MatID':
                        self.prepare_objects_for_bake_matid(obj_list)
                    elif job_name == 'Vertex_Color':
                        self.prepare_objects_for_bake_vertex_color(obj_list)
                    elif job_name == 'Diffuse':
                        pass  # prepare nothing
                    else:
                        self.prepare_objects_for_bake(obj_list, job_name)

                    # image nodes to bake
                    for mat_slot in obj.material_slots:
                        if mat_slot.material:
                            self.create_bake_image_node(
                                mat_slot.material, image)

                    # Bake and Save image!
                    self.bake_and_save(
                        image, bake_type=get_bake_type(job_name))

                    # Clean up!
                    # delete temp materials
                    self.delete_tagged_materials(obj, MATERIAL_TAG_VERTEX)

                    # delete temp nodes
                    self.delete_tagged_nodes(obj)

                    # reactivate Material Outputs
                    self.disable_material_outputs(obj)
                    for mat_output in active_outputs:
                        mat_output.is_active_output = True

                    # reselect UV Map
                    if not self.settings.set_selected_uv_map:
                        uv_layers = obj.data.uv_textures if is_2_79 else obj.data.uv_layers
                        uv_layers.active_index = orig_uv_layers_active_index

                    # glossiness
                    if job_name == "Roughness" and self.settings.use_invert_roughness:
                        self.create_gloss_image(obj.name, image)

                    # add alpha channel to color
                    if self.settings.use_alpha_to_color and self.settings.color_mode == 'RGBA':
                        if "Color" in new_images.keys() and "Alpha" in new_images.keys():
                            new_images["Color"].pixels = get_combined_images(
                                new_images["Color"], new_images["Alpha"], 0, 3)
                            new_images["Color"].save()

                # jobs DONE

                # add new images to new material
                if self.settings.make_new_material:
                    self.add_images_to_material(new_mat, new_images)
                    self.report(
                        {'INFO'}, "Mew Material created. '{0}'".format(new_mat.name))

                    # (optional) add new material
                    if self.settings.add_new_material:
                        obj.data.materials.append(new_mat)

                # Clean up!
                # 2.80
                if is_2_80:
                    for mat_output, target in all_material_outputs.items():
                        mat_output.target = target

                # remove tag from new material
                if self.settings.make_new_material:
                    if MATERIAL_TAG in new_mat:
                        del(new_mat[MATERIAL_TAG])

                # UPDATE progress report
                progress += 1/len(bake_objects)
                bpy.context.window_manager.progress_update(progress)

            # END progress report
            bpy.context.window_manager.progress_end()

        ########
        # Bake Combined:
        ########
        elif self.settings.bake_mode == 'COMBINED':

            # Can bake?
            if not self.can_bake(bake_objects):
                self.final_cleanup()
                return {'CANCELLED'}

            # Populate joblist
            joblist = []
            if self.settings.use_autodetect:
                joblist = get_joblist_from_objects(bake_objects)
            else:
                joblist = get_joblist_manual()

            self.extend_joblist(joblist)

            if self.settings.use_vertex_color:
                if "Vertex_Color" not in joblist:
                    joblist.append("Vertex_Color")

            # empty joblist -> nothing to do
            if not joblist:
                self.final_cleanup()
                self.report({'INFO'}, "Nothing to do.")
                return {'CANCELLED'}

            # BEGIN progress report
            bpy.context.window_manager.progress_begin(0, len(bake_objects))
            progress = 0

            # material outpus for later clean up
            active_outputs = get_active_outputs(bake_objects)
            all_material_outputs = get_all_material_outputs(bake_objects)
            # 2.80
            if not is_2_79:
                set_material_outputs_target_to_all(bake_objects)

            # Auto UV project
            # no Auto Smart UV Project in 2.79
            if is_2_80:
                if self.settings.auto_uv_project == 'SMART':
                    self.smart_project()
                elif self.settings.auto_uv_project == 'LIGHTMAP':
                    self.lightmap_pack()

            # UV Map selection
            orig_uv_layers_active_indices = {}
            for obj in bake_objects:
                orig_uv_layers_active_indices[obj] = obj.data.uv_layers.active_index
                if not self.settings.select_uv_map == 'SELECTED':
                    self.select_uv_map(obj)

            # (optional) new material
            if self.settings.make_new_material:
                new_mat_name = self.active_object.name if self.settings.new_material_prefix == "" else self.settings.new_material_prefix
                new_mat = self.new_material(new_mat_name)

            # Go through joblist
            for job_name in joblist:

                # skip, if no overwrite and image exists. load existing image
                image_file_name = self.get_image_file_name(
                    self.active_object.name, job_name)
                if not self.settings.use_overwrite and self.is_image_file(image_file_name):
                    self.report({'INFO'}, "baking skipped for '{0}'. File exists.".format(
                        self.get_image_file_name(obj.name, job_name)))

                    # load image for new material
                    new_images[job_name] = self.load_image(image_file_name)

                    continue  # skip job

                # else: do bake
                # image to bake on
                image = self.new_bake_image(self.active_object.name, job_name)

                # append image to image dict for new material
                new_images[job_name] = image

                # temp material for vertex color
                if self.settings.use_vertex_color:
                    for obj in bake_objects:
                        if not has_material(obj):
                            add_temp_material(obj)

                # Prepare materials
                if job_name == 'MatID':
                    self.prepare_objects_for_bake_matid(bake_objects)
                elif job_name == 'Vertex_Color':
                    self.prepare_objects_for_bake_vertex_color(bake_objects)
                elif job_name == 'Diffuse':
                    pass  # prepare nothing
                else:
                    self.prepare_objects_for_bake(bake_objects, job_name)

                # image nodes to bake
                for obj in bake_objects:
                    for mat_slot in obj.material_slots:
                        if mat_slot.material:
                            self.create_bake_image_node(
                                mat_slot.material, image)

                # Bake and Save image!
                self.bake_and_save(image, bake_type=get_bake_type(job_name))

                # Clean up!
                for obj in bake_objects:
                    # delete temp materials
                    self.delete_tagged_materials(obj, MATERIAL_TAG_VERTEX)

                    # delete temp nodes
                    self.delete_tagged_nodes(obj)

                    # reactivate Material Outputs
                    self.disable_material_outputs(obj)

                    # reselect UV Map
                    if not self.settings.set_selected_uv_map:
                        uv_layers = obj.data.uv_textures if is_2_79 else obj.data.uv_layers
                        uv_layers.active_index = orig_uv_layers_active_indices[obj]

                for mat_output in active_outputs:
                    mat_output.is_active_output = True

                # glossiness
                if job_name == "Roughness" and self.settings.use_invert_roughness:
                    self.create_gloss_image(obj.name, image)

                # add alpha channel to color
                if self.settings.use_alpha_to_color and self.settings.color_mode == 'RGBA':
                    if "Color" in new_images.keys() and "Alpha" in new_images.keys():
                        new_images["Color"].pixels = get_combined_images(
                            new_images["Color"], new_images["Alpha"], 0, 3)
                        new_images["Color"].save()

                # UPDATE progress report
                progress += 1/len(joblist)
                bpy.context.window_manager.progress_update(progress)

            # jobs DONE

            # add new images to new material
            if self.settings.make_new_material:
                self.add_images_to_material(new_mat, new_images)
                self.report(
                    {'INFO'}, "Mew Material created. '{0}'".format(new_mat.name))

                # (optional) add new material
                if self.settings.add_new_material:
                    self.active_object.data.materials.append(new_mat)

            # Clean up!
            # 2.80
            if is_2_80:
                for mat_output, target in all_material_outputs.items():
                    mat_output.target = target

            # remove tag from new material
            if self.settings.make_new_material:
                if MATERIAL_TAG in new_mat:
                    del(new_mat[MATERIAL_TAG])

            # END progress report
            bpy.context.window_manager.progress_end()

        ########
        # Bake Selected to Active:
        ########
        elif self.settings.bake_mode == 'SELECTED_TO_ACTIVE':

            # # exclude active object from selected objects
            # if self.active_object in bake_objects:
            #     bake_objects.remove(self.active_object)

            # Can bake?
            if not self.can_bake(bake_objects):
                self.final_cleanup()
                return {'CANCELLED'}

            # has active object UV map?
            if self.settings.auto_uv_project == 'OFF':
                if len(self.active_object.data.uv_layers) == 0:
                    self.report(
                        {'INFO'}, "baking cancelled. '{0}' UV map missing.".format(self.active_object.name))
                    self.final_cleanup()
                    return {'CANCELLED'}

            # Populate joblist
            joblist = []
            if self.settings.use_autodetect:
                joblist = get_joblist_from_objects(bake_objects)
            else:
                joblist = get_joblist_manual()

            self.extend_joblist(joblist)

            if self.settings.use_vertex_color:
                if "Vertex_Color" not in joblist:
                    joblist.append("Vertex_Color")

            # empty joblist -> nothing to do
            if not joblist:
                self.final_cleanup()
                self.report({'INFO'}, "Nothing to do.")
                return {'CANCELLED'}

            # BEGIN progress report
            bpy.context.window_manager.progress_begin(0, len(bake_objects))
            progress = 0

            # material outpus for later clean up
            active_outputs = get_active_outputs(bake_objects)
            all_material_outputs = get_all_material_outputs(bake_objects)
            # 2.80
            if not is_2_79:
                set_material_outputs_target_to_all(bake_objects)

            # Auto UV project
            if not self.settings.auto_uv_project == 'OFF':
                self.auto_uv_project(self.active_object)

            # UV Map selection
            orig_uv_layers_active_index = self.active_object.data.uv_layers.active_index
            if not self.settings.select_uv_map == 'SELECTED':
                self.select_uv_map(self.active_object)

            # new material
            new_mat_name = self.active_object.name if self.settings.new_material_prefix == "" else self.settings.new_material_prefix
            new_mat = self.new_material(new_mat_name)
            self.active_object.data.materials.append(new_mat)

            # Go through joblist
            for job_name in joblist:

                # skip, if no overwrite and image exists. load existing image
                image_file_name = self.get_image_file_name(
                    self.active_object.name, job_name)
                if not self.settings.use_overwrite and self.is_image_file(image_file_name):
                    self.report({'INFO'}, "baking skipped for '{0}'. File exists.".format(
                        self.get_image_file_name(obj.name, job_name)))

                    # load image for new material
                    new_images[job_name] = self.load_image(image_file_name)

                    continue  # skip job

                # else: do bake
                # image to bake on
                image = self.new_bake_image(self.active_object.name, job_name)

                # append image to image dict for new material
                new_images[job_name] = image

                # temp material for vertex color
                if self.settings.use_vertex_color:
                    for obj in bake_objects:
                        if not has_material(obj):
                            add_temp_material(obj)

                # Prepare materials
                if job_name == 'MatID':
                    self.prepare_objects_for_bake_matid(bake_objects)
                elif job_name == 'Vertex_Color':
                    self.prepare_objects_for_bake_vertex_color(bake_objects)
                elif job_name == 'Diffuse':
                    pass  # prepare nothing
                else:
                    self.prepare_objects_for_bake(bake_objects, job_name)

                # image nodes to bake
                for mat_slot in self.active_object.material_slots:
                    if mat_slot.material:
                        self.create_bake_image_node(mat_slot.material, image)

                # Bake and Save image!
                self.bake_and_save(image, bake_type=get_bake_type(
                    job_name), selected_to_active=True)

                # Clean up!
                for obj in bake_objects:
                    # delete temp materials
                    self.delete_tagged_materials(obj, MATERIAL_TAG_VERTEX)

                    # delete temp nodes
                    self.delete_tagged_nodes(obj)

                    # reactivate Material Outputs
                    self.disable_material_outputs(obj)

                # delete temp materials
                self.delete_tagged_materials(
                    self.active_object, MATERIAL_TAG_VERTEX)

                # delete temp nodes
                self.delete_tagged_nodes(self.active_object)

                # reactivate Material Outputs
                self.disable_material_outputs(self.active_object)
                for mat_output in active_outputs:
                    mat_output.is_active_output = True
                    
                # reselect UV Map
                if not self.settings.set_selected_uv_map:
                    obj = self.active_object
                    uv_layers = obj.data.uv_textures if is_2_79 else obj.data.uv_layers
                    uv_layers.active_index = orig_uv_layers_active_index

                # glossiness
                if job_name == "Roughness" and self.settings.use_invert_roughness:
                    self.create_gloss_image(self.active_object.name, image)

                # add alpha channel to color
                if self.settings.use_alpha_to_color and self.settings.color_mode == 'RGBA':
                    if "Color" in new_images.keys() and "Alpha" in new_images.keys():
                        new_images["Color"].pixels = get_combined_images(
                            new_images["Color"], new_images["Alpha"], 0, 3)
                        new_images["Color"].save()

                # UPDATE progress report
                progress += 1/len(joblist)
                bpy.context.window_manager.progress_update(progress)

            # jobs DONE

            # add new images to new material
            self.add_images_to_material(new_mat, new_images)
            self.report(
                {'INFO'}, "Mew Material created. '{0}'".format(new_mat.name))

            # Clean up!
            # 2.80
            if is_2_80:
                for mat_output, target in all_material_outputs.items():
                    mat_output.target = target

            # remove tag from new material
            if self.settings.make_new_material:
                if MATERIAL_TAG in new_mat:
                    del(new_mat[MATERIAL_TAG])

            # END progress report
            bpy.context.window_manager.progress_end()

        self.final_cleanup()

        return {'FINISHED'}
