import bpy
import os
import pathlib
import time
from mathutils import Color
import hashlib

from . pbaker_functions import *


class PBAKER_OT_bake(bpy.types.Operator):
    bl_idname = "object.principled_baker_bake"
    bl_label = "Bake"
    bl_description = "bake all inputs of a Principled BSDF to image textures" 
    bl_options = {'REGISTER', 'UNDO'} 

    settings = None

    def get_joblist_manual(self):
        joblist = []

        if self.settings.use_Alpha:
            joblist.append("Alpha")
        if self.settings.use_Emission:
            joblist.append("Emission")
        if self.settings.use_AO:
            joblist.append("AO")

        if self.settings.use_Base_Color:
            joblist.append("Color")
        if self.settings.use_Metallic:
            joblist.append("Metallic")
        if self.settings.use_Roughness:
            joblist.append("Roughness")
        if self.settings.use_Normal:
            joblist.append("Normal")
        if self.settings.use_Bump:
            joblist.append("Bump")
        if self.settings.use_Displacement:
            joblist.append("Displacement")

        if self.settings.use_Specular:
            joblist.append("Specular")
        if self.settings.use_Anisotropic:
            joblist.append("Anisotropic")
        if self.settings.use_Anisotropic_Rotation:
            joblist.append("Anisotropic Rotation")
        if self.settings.use_Clearcoat:
            joblist.append("Clearcoat")
        if self.settings.use_Clearcoat_Normal:
            joblist.append("Clearcoat Normal")
        if self.settings.use_Clearcoat_Roughness:
            joblist.append("Clearcoat Roughness")
        if self.settings.use_IOR:
            joblist.append("IOR")
        if self.settings.use_Sheen:
            joblist.append("Sheen")
        if self.settings.use_Sheen_Tint:
            joblist.append("Sheen Tint")
        if self.settings.use_Specular_Tint:
            joblist.append("Specular Tint")
        if self.settings.use_Subsurface:
            joblist.append("Subsurface")
        if self.settings.use_Subsurface_Color:
            joblist.append("Subsurface Color")
        if self.settings.use_Subsurface_Radius:
            joblist.append("Subsurface Radius")
        if self.settings.use_Tangent:
            joblist.append("Tangent")
        if self.settings.use_Transmission:
            joblist.append("Transmission")
        return joblist

    def get_joblist_from_object(self, obj):
        joblist = []

        # add to joblist if values differ
        for value_name in NODE_INPUTS:
            if value_name not in joblist:
                if value_name not in ['Subsurface Radius', 'Normal', 'Clearcoat Normal', 'Tangent']:
                    value_list = []
                    for mat_slot in obj.material_slots:
                        if mat_slot.material:
                            mat = mat_slot.material
                            if not MATERIAL_TAG in mat.keys():
                                material_output = get_active_output(mat)
                                value_list.extend(self.get_value_list(material_output, value_name))
                    # if len(value_list) >= 1:
                    if value_list:
                        if is_list_equal(value_list):
                            if self.settings.make_new_material or self.settings.bake_mode == 'SELECTED_TO_ACTIVE':
                                self.new_principled_node_settings[value_name] = value_list[0]
                        else:
                            joblist.append(value_name)
                    
        # search material for jobs
        for mat_slot in obj.material_slots:
            if mat_slot.material:
                if not MATERIAL_TAG in mat_slot.material.keys():
                    # material_output = find_node_by_type(mat_slot.material, 'OUTPUT_MATERIAL')
                    material_output = get_active_output(mat_slot.material)
                    # add special cases:
                    # Alpha for nodes: Transparent, Translucent, Glass
                    for alpha_name, n_type in ALPHA_NODES.items():
                        if is_node_type_in_node_tree(material_output, n_type):
                            if not alpha_name in joblist:
                                joblist.append(alpha_name)
                    # Emission
                    if is_node_type_in_node_tree(material_output, 'EMISSION'):
                        if not 'Emission' in joblist:
                            joblist.append('Emission')

                    # AO
                    if is_node_type_in_node_tree(material_output, 'AMBIENT_OCCLUSION'):
                        if not 'AO' in joblist:
                            joblist.append('AO')

                    # Displacement
                    socket_name = 'Displacement'
                    if is_socket_linked_in_node_tree(material_output, socket_name):
                        # 2.79
                        if bpy.app.version_string.startswith('2.7'):
                            if not socket_name in joblist:
                                joblist.append(socket_name)
                        # 2.80
                        else:
                            if is_node_type_in_node_tree(material_output, 'DISPLACEMENT'):
                                if not socket_name in joblist:
                                    joblist.append(socket_name)
                    # Bump
                    socket_name = 'Bump'
                    if self.settings.use_Bump and is_node_type_in_node_tree(material_output, 'BUMP'):
                            if not socket_name in joblist:
                                joblist.append(socket_name)
    
                    # add linked inputs to joblist
                    if are_node_types_in_node_tree(material_output, BSDF_NODES):
                        for socket_name in NODE_INPUTS:
                            if is_socket_linked_in_node_tree(material_output, socket_name):
                                if not socket_name in joblist:
                                    joblist.append(socket_name)
                
        # force bake of Color, if user wants alpha in color
        if self.settings.use_alpha_to_color and self.settings.color_mode == 'RGBA':
            if not 'Color' in joblist:
                joblist.append('Color')

        return joblist

    def get_suffix(self, input_name):
        suffix = ""
        if input_name == 'Color':
            suffix = self.settings.suffix_color
        elif input_name == 'Metallic':
            suffix = self.settings.suffix_metallic
        elif input_name == 'Roughness':
            suffix = self.settings.suffix_roughness
        elif input_name == 'Glossiness':
            suffix = self.settings.suffix_glossiness
        elif input_name == 'Normal':
            suffix = self.settings.suffix_normal
        elif input_name == 'Bump':
            suffix = self.settings.suffix_bump
        elif input_name == 'Displacement':
            suffix = self.settings.suffix_displacement
        elif input_name == 'Vertex_Color':
            suffix = self.settings.suffix_vertex_color
        else:
            suffix = '_' + input_name

        if self.settings.suffix_text_mod == 'lower':
            suffix = suffix.lower()
        elif self.settings.suffix_text_mod == 'upper':
            suffix = suffix.upper()
        elif self.settings.suffix_text_mod == 'title':
            suffix = suffix.title()
        return suffix

    def delete_tagged_nodes(self, obj, tag):
        for mat_slot in obj.material_slots:
            if mat_slot.material:
                for node in mat_slot.material.node_tree.nodes:
                    if tag in node.keys():
                        mat_slot.material.node_tree.nodes.remove(node)

    def delete_tagged_materials(self, obj, tag):
        for mat_index in range(0,len(obj.material_slots)):
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
                    if job_name == "Emission":
                        node_types = 'EMISSION'
                    else:
                        node_types = ALPHA_NODES[job_name]
                    color_list = self.get_value_list_from_node_types(mat_out, 'Color', node_types)
                    if len(color_list) >= 1:
                        self.new_node_colors[job_name] = color_list[0]

    def create_bake_image_node(self, mat, image):
        bake_image_node = new_image_node(mat)
        bake_image_node.color_space = 'COLOR' if image.colorspace_settings.name == 'sRGB' else 'NONE'
        bake_image_node.image = image  # add image to node
        bake_image_node[NODE_TAG] = 1  # tag for clean up
        # make only bake_image_node active
        bake_image_node.select = True
        mat.node_tree.nodes.active = bake_image_node

    def new_material(self, name):
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        mat[MATERIAL_TAG] = 1

        mat_output = mat.node_tree.nodes['Material Output']
        mat_output.location = (300.0, 300.0)

        # 2.79
        if bpy.app.version_string.startswith('2.7'):
            mat.node_tree.nodes.remove(mat.node_tree.nodes['Diffuse BSDF'])
            principled_node = mat.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
        # 2.80
        else:
            principled_node = mat.node_tree.nodes['Principled BSDF']

        principled_node.location = (10.0, 300.0)
        
        # copy settings to new principled_node
        for k, v in self.new_principled_node_settings.items():
            if k == 'Color':
                k = 'Base Color'
            principled_node.inputs[k].default_value = v

        mat.node_tree.links.new(principled_node.outputs['BSDF'], mat_output.inputs['Surface'])
        return mat

    def add_images_to_material(self, new_mat, new_images):
        node_offset_index = 0

        principled_node = find_node_by_type(new_mat, 'BSDF_PRINCIPLED')
        material_output = find_node_by_type(new_mat, 'OUTPUT_MATERIAL')

        if new_images:
            tex_coord_node = new_mat.node_tree.nodes.new(type="ShaderNodeTexCoord")
            mapping_node = new_mat.node_tree.nodes.new(type="ShaderNodeMapping")
            new_mat.node_tree.links.new(tex_coord_node.outputs["UV"], mapping_node.inputs["Vector"])
            mapping_node.location.x = principled_node.location.x + IMAGE_NODE_OFFSET_X - mapping_node.width - 100
            tex_coord_node.location.x = mapping_node.location.x - tex_coord_node.width - 100

        for name, image in new_images.items():
            if name not in ["AO"]:  # "Vertex_Color", "MatID"
                image_node = new_image_node(new_mat)
                image_node.label = name

                image_node.color_space = 'COLOR' if name in SRGB_INPUTS else 'NONE'

                image_node.image = image

                # link to mapping node
                new_mat.node_tree.links.new(mapping_node.outputs["Vector"], image_node.inputs["Vector"])

                # rearrange nodes
                image_node.width = IMAGE_NODE_WIDTH
                image_node.location.x = principled_node.location.x + IMAGE_NODE_OFFSET_X
                image_node.location.y = principled_node.location.y + IMAGE_NODE_OFFSET_Y * node_offset_index

            # link nodes
            if name in NORMAL_INPUTS:
                normal_node = new_mat.node_tree.nodes.new(type="ShaderNodeNormalMap")
                normal_node.location.x = IMAGE_NODE_OFFSET_X + 1.5*IMAGE_NODE_WIDTH
                normal_node.location.y = IMAGE_NODE_OFFSET_Y * node_offset_index
                new_mat.node_tree.links.new(image_node.outputs['Color'], normal_node.inputs['Color'])
                new_mat.node_tree.links.new(normal_node.outputs[name], principled_node.inputs[name])
            elif name == 'Bump':
                bump_node = new_mat.node_tree.nodes.new(type="ShaderNodeBump")
                bump_node.location.x = IMAGE_NODE_OFFSET_X + 1.5*IMAGE_NODE_WIDTH
                bump_node.location.y = IMAGE_NODE_OFFSET_Y * node_offset_index
                new_mat.node_tree.links.new(image_node.outputs['Color'], bump_node.inputs['Height'])
                new_mat.node_tree.links.new(bump_node.outputs['Normal'], principled_node.inputs['Normal'])
            elif name == "Displacement":
                # 2.79
                if bpy.app.version_string.startswith('2.7'):
                    new_mat.node_tree.links.new(image_node.outputs['Color'],
                                                material_output.inputs["Displacement"])
                # 2.80
                else:
                    disp_node = new_mat.node_tree.nodes.new(type='ShaderNodeDisplacement')
                    new_mat.node_tree.links.new(image_node.outputs['Color'],
                                                disp_node.inputs["Height"])
                    new_mat.node_tree.links.new(disp_node.outputs["Displacement"],
                                                material_output.inputs["Displacement"])
                    disp_node.location.x = NODE_OFFSET_X
            elif name in ALPHA_NODES.keys():
                if not self.settings.use_alpha_to_color:
                    if name == "Alpha":
                        alpha_node = new_mat.node_tree.nodes.new(type='ShaderNodeBsdfTransparent')
                    elif name == "Translucent_Alpha":
                        alpha_node = new_mat.node_tree.nodes.new(type='ShaderNodeBsdfTranslucent')
                    elif name == "Glass_Alpha":
                        alpha_node = new_mat.node_tree.nodes.new(type='ShaderNodeBsdfGlass')
                    # color
                    alpha_node.inputs['Color'].default_value = self.new_node_colors[name]
                    
                    mixshader_node = new_mat.node_tree.nodes.new(type='ShaderNodeMixShader')

                    # links
                    new_mat.node_tree.links.new(material_output.inputs[0].links[0].from_socket,
                                                mixshader_node.inputs[2])
                    new_mat.node_tree.links.new(material_output.inputs[0], mixshader_node.outputs['Shader'])
                    new_mat.node_tree.links.new(alpha_node.outputs['BSDF'],
                                                mixshader_node.inputs[1])
                    new_mat.node_tree.links.new(image_node.outputs['Color'],
                                                mixshader_node.inputs['Fac'])

                    # node locations
                    sib = get_sibling_node(alpha_node)
                    alpha_node.location = (sib.location.x, sib.location.y + NODE_OFFSET_Y)
                    mid_offset_y = alpha_node.location.y
                    mixshader_node.location = (sib.location.x + NODE_OFFSET_X, mid_offset_y)
                    
            elif name == 'Emission':
                emission_node = new_mat.node_tree.nodes.new(type='ShaderNodeEmission')
                emission_node.inputs['Color'].default_value = self.new_node_colors[name]
                
                addshader_node = new_mat.node_tree.nodes.new(type='ShaderNodeAddShader')

                # links
                new_mat.node_tree.links.new(material_output.inputs[0].links[0].from_socket,
                                            addshader_node.inputs[1])
                new_mat.node_tree.links.new(emission_node.outputs['Emission'],
                                            addshader_node.inputs[0])
                new_mat.node_tree.links.new(addshader_node.outputs['Shader'], material_output.inputs[0])
                new_mat.node_tree.links.new(image_node.outputs['Color'], emission_node.inputs['Color'])

                # node locations
                sib = get_sibling_node(emission_node)
                emission_node.location = (sib.location.x, sib.location.y + NODE_OFFSET_Y)
                mid_offset_y = emission_node.location.y
                addshader_node.location = (sib.location.x + NODE_OFFSET_X, mid_offset_y)

            elif name == 'Color':
                name = 'Base Color'
                new_mat.node_tree.links.new(image_node.outputs['Color'],
                                            principled_node.inputs[name])
                                            
                if self.settings.use_alpha_to_color and "Alpha" in new_images.keys():
                    alpha_node = new_mat.node_tree.nodes.new(type='ShaderNodeBsdfTransparent')
                    mixshader_node = new_mat.node_tree.nodes.new(type='ShaderNodeMixShader')

                    # links
                    new_mat.node_tree.links.new(material_output.inputs[0].links[0].from_socket,
                                                mixshader_node.inputs[2])
                    new_mat.node_tree.links.new(material_output.inputs[0], mixshader_node.outputs['Shader'])
                    new_mat.node_tree.links.new(alpha_node.outputs['BSDF'],
                                                mixshader_node.inputs[1])
                    new_mat.node_tree.links.new(image_node.outputs["Alpha"],
                                                mixshader_node.inputs['Fac'])

                    # node locations
                    sib = get_sibling_node(alpha_node)
                    alpha_node.location = (sib.location.x, sib.location.y + NODE_OFFSET_Y)
                    mid_offset_y = alpha_node.location.y
                    mixshader_node.location = (sib.location.x + NODE_OFFSET_X, mid_offset_y)
                
                # mix AO with color
                if 'AO' in new_images.keys():
                    ao_image_node = new_image_node(new_mat)
                    ao_image_node.label = 'Ambient Occlusion'
                    ao_image_node.color_space = 'NONE'
                    ao_image_node.image = new_images['AO']
                    ao_image_node.width = IMAGE_NODE_WIDTH
                    ao_image_node.location.x = principled_node.location.x + IMAGE_NODE_OFFSET_X
                    ao_image_node.location.y = principled_node.location.y + IMAGE_NODE_OFFSET_Y * (1 + node_offset_index)

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

            # skip some
            elif name in ["AO", "Vertex_Color", "MatID", "Diffuse"]:
                pass

            else:
                new_mat.node_tree.links.new(image_node.outputs['Color'],
                                            principled_node.inputs[name])
            node_offset_index += 1

    def new_pb_emission_node(self, material, color=[0, 0, 0, 1]):
        node = material.node_tree.nodes.new(type='ShaderNodeEmission')
        node.inputs['Color'].default_value = color#[0, 0, 0, 1]
        node[NODE_TAG] = 1
        return node

    def new_pb_output_node(self, material):
        node = material.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
        node.is_active_output = True
        node[NODE_TAG] = 1
        return node

    def is_image_file(self, image_file_name):
        cwd = os.path.dirname(bpy.data.filepath)
        abs_image_path = os.path.join( cwd, os.path.normpath(self.settings.file_path.lstrip("/").rstrip("\\")), image_file_name )
        return os.path.isfile( abs_image_path )

    def get_image_file_name(self, object_name, job_name):
        prefix = self.settings.image_prefix
        if prefix == "" or len(self.selected_objects) > 1 or self.settings.use_object_name:
            prefix = self.settings.image_prefix + object_name
        image_file_format = IMAGE_FILE_FORMAT_ENDINGS[self.settings.file_format]
        image_file_name = "{0}{1}.{2}".format(prefix, self.get_suffix(job_name), image_file_format)
        return image_file_name

    def get_image_file_path(self, image_file_name):
        path = self.settings.file_path.rstrip("\\").rstrip("\\")
        return os.path.join(path, image_file_name)

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
        name = "{0}{1}.{2}".format(prefix, self.get_suffix(job_name), file_format)  # include ending
        path = self.get_image_file_path(name)

        # create dir
        cwd = os.path.dirname(bpy.data.filepath)
        abs_path = self.settings.file_path
        if self.settings.file_path.startswith("//"):
            abs_path = os.path.join(cwd, os.path.normpath(self.settings.file_path.lstrip("//").rstrip("\\")))
        if not os.path.exists(abs_path):
            os.makedirs(abs_path)

        # alpha
        alpha = False
        if self.settings.color_mode == 'RGBA':
            alpha = True

        # color
        color = (0.5, 0.5, 1.0, 1.0) if get_bake_type(job_name) == 'NORMAL' else (0.0, 0.0, 0.0, 1.0)

        # resolution
        res = int(self.settings.custom_resolution) if self.settings.resolution == 'CUSTOM' else int(self.settings.resolution)

        is_float = False if self.settings.color_depth == '8' else True

        image = bpy.data.images.new(name=name, width=res, height=res, alpha=alpha, float_buffer=is_float)

        image.colorspace_settings.name = 'sRGB' if job_name == 'Color' else 'Non-Color'
        image.generated_color = color
        image.generated_type = 'BLANK'
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

        save_image_as(gloss_image,
            file_path=gloss_image.filepath,
            file_format=self.settings.file_format, 
            color_mode=self.settings.color_mode, 
            color_depth=self.settings.color_depth)

    def can_bake(self, objects):
        for obj in objects:
            # enabled for rendering?
            if obj.hide_render:
                self.report({'INFO'}, "baking cancelled. '{0}' not enabled for rendering.".format(obj.name))
                return False
            # no material or missing output?
            if not has_material(obj):
                if not self.settings.use_vertex_color:
                    self.report({'INFO'}, "baking cancelled. '{0}' Material missing, Material Output missing, or Material Output input missing.".format(obj.name))
                    return False
            # no UV map?
            if self.settings.auto_uv_project == 'OFF':
                if len(obj.data.uv_layers) == 0:
                    self.report({'INFO'}, "baking cancelled. '{0}' UV map missing.".format(obj.name))
                    return False
            # has vertex color?
            if not self.settings.bake_mode == 'BATCH':
                if self.settings.use_vertex_color and len(obj.data.vertex_colors) == 0:
                    self.report({'INFO'}, "baking cancelled. '{0}' has no Vertex Color.".format(obj.name))
                    return False
            # empty material slots?
            for mat_slot in obj.material_slots:
                if not mat_slot.material:
                    self.report({'INFO'}, "baking cancelled. '{0}' has empty Material Slots.".format(obj.name))
                    return False
        return True

    def prepare_objects_for_bake_matid(self, objects):

        def prepare_material(mat, color):
            pb_output_node = self.new_pb_output_node(mat)
            pb_emission_node = self.new_pb_emission_node(mat, color)
            socket_to_pb_emission_node_color = pb_emission_node.inputs['Color']

            # activate temp output
            material_output = get_active_output(mat)  # orig material output
            if material_output:
                material_output.is_active_output = False
            pb_output_node.is_active_output = True

            # link pb_emission_node to material_output
            mat.node_tree.links.new(pb_emission_node.outputs[0], pb_output_node.inputs['Surface'])

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

                prepare_material(mat, color)

        elif self.prefs.mat_id_algorithm == 'NAME':
            for mat in materials:
                s = mat.name.encode('utf-8')
                h = int(hashlib.sha1(s).hexdigest(), base=16)
                r = h % 256 / 256
                g = (h >> 32) % 256 / 256
                b = (h >> 16) % 256 / 256
                color = r, g, b, 1.0

                prepare_material(mat, color)

    def prepare_objects_for_bake_vertex_color(self, objects):
        for obj in objects:
            for mat_slot in obj.material_slots:
                if mat_slot.material:
                    mat = mat_slot.material

                    pb_output_node = self.new_pb_output_node(mat)
                    # pb_output_node[NODE_TAG] = 1
                    pb_emission_node = self.new_pb_emission_node(mat)
                    socket_to_pb_emission_node_color = pb_emission_node.inputs['Color']

                    # activate temp output
                    material_output = get_active_output(mat)  # orig material output
                    if material_output:
                        material_output.is_active_output = False
                    pb_output_node.is_active_output = True

                    for name, vert_col in obj.data.vertex_colors.items():
                        if vert_col.active_render:
                            active_vert_col = name
                    attr_node = mat.node_tree.nodes.new(type='ShaderNodeAttribute')
                    attr_node[NODE_TAG] = 1  # tag for clean up
                    attr_node.attribute_name = active_vert_col
                    mat.node_tree.links.new(attr_node.outputs['Color'], socket_to_pb_emission_node_color)

                    # link pb_emission_node to material_output
                    mat.node_tree.links.new(pb_emission_node.outputs[0], pb_output_node.inputs['Surface'])
        
    def prepare_objects_for_bake(self, objects, job_name):
        for obj in objects:
            for mat_slot in obj.material_slots:
                if mat_slot.material:
                    mat = mat_slot.material
                    # 2.79 Normal Map
                    if bpy.app.version_string.startswith('2.7') and job_name == "Normal":
                        self.prepare_material_for_bake(mat, job_name)
                    # 2.80
                    if job_name not in ["Emission", "Normal"]:
                        self.prepare_material_for_bake(mat, job_name)

    def prepare_material_for_bake(self, mat, job_name):
        # skip already prepared materials
        for n in mat.node_tree.nodes:
            if NODE_TAG in n.keys():
                return
        
        # orig material output
        material_output = get_active_output(mat)
        socket_to_surface = material_output.inputs['Surface'].links[0].from_socket

        # temp nodes
        pb_output_node = self.new_pb_output_node(mat)
        pb_output_node[NODE_TAG] = 1
        pb_emission_node = self.new_pb_emission_node(mat, [1, 1, 1, 1])
        socket_to_pb_emission_node_color = pb_emission_node.inputs['Color']

        # activate temp output
        material_output.is_active_output = False
        pb_output_node.is_active_output = True

        bake_type = get_bake_type(job_name)

        if bake_type == 'EMIT':
            if job_name in ALPHA_NODES.keys():
                node_type = ALPHA_NODES[job_name]
                prepare_bake_factor(mat, socket_to_surface, socket_to_pb_emission_node_color, node_type, 'Fac')

            elif job_name == 'Displacement':
                if material_output.inputs['Displacement'].is_linked:
                    socket_to_displacement = material_output.inputs['Displacement'].links[0].from_socket
                    # 2.79
                    if bpy.app.version_string.startswith('2.7'):
                        from_socket = socket_to_displacement.links[0].from_socket
                        mat.node_tree.links.new(from_socket, socket_to_pb_emission_node_color)
                    # 2.80
                    else:
                        prepare_bake(mat, socket_to_displacement, socket_to_pb_emission_node_color, 'Height')

            elif job_name == 'Bump':
                prepare_bake(mat, socket_to_surface, socket_to_pb_emission_node_color, 'Height')
            elif job_name == 'AO':
                prepare_bake_ao(mat, socket_to_surface, socket_to_pb_emission_node_color)
            else:
                prepare_bake(mat, socket_to_surface, socket_to_pb_emission_node_color, job_name)

            # link pb_emission_node to material_output
            mat.node_tree.links.new(pb_emission_node.outputs[0], pb_output_node.inputs['Surface'])

        # 2.79
        elif bake_type == 'NORMAL' and bpy.app.version_string.startswith('2.7'):
            if self.settings.use_Bump:
                prepare_bake(mat, socket_to_surface, socket_to_pb_emission_node_color, job_name)
                # link pb_emission_node to material_output
                mat.node_tree.links.new(pb_emission_node.outputs[0], pb_output_node.inputs['Surface'])
            # normal
            prepare_bake(mat, socket_to_surface, socket_to_pb_emission_node_color, 'Normal')
            # link pb_emission_node to material_output
            mat.node_tree.links.new(pb_emission_node.outputs[0], pb_output_node.inputs['Surface'])
            s = pb_emission_node.inputs['Color'].links[0].from_socket
            mat.node_tree.links.new(s, pb_output_node.inputs['Displacement'])

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
                        value_list.append(node.inputs[value_name].default_value)

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

    def bake_single(self, obj, bake_type):
        org_selected_objects = bpy.context.selected_objects
        for o in bpy.context.selected_objects:
            select_set(o, False)
        select_set(obj, True)

        org_samples = bpy.context.scene.cycles.samples
        bpy.context.scene.cycles.samples = self.settings.samples
    
        bpy.ops.object.bake(type=bake_type, use_selected_to_active=False)

        for o in org_selected_objects:
            select_set(o, True)

        bpy.context.scene.cycles.samples = org_samples

    def bake_selected_to_active(self, bake_type):
        org_samples = bpy.context.scene.cycles.samples
        bpy.context.scene.cycles.samples = self.settings.samples
        bpy.ops.object.bake(type=bake_type, use_selected_to_active=True)
        bpy.context.scene.cycles.samples = org_samples

    def final_cleanup(self):
        # Auto Smooth - Clean up!
        if not self.settings.auto_smooth == 'OBJECT':
            for obj in self.auto_smooth_list:
                obj.data.use_auto_smooth = self.auto_smooth_list[obj]

        # Render Engine - Clean up!
        if self.prefs.switch_to_cycles:
            bpy.context.scene.render.engine = self.render_engine
            bpy.context.scene.cycles.preview_pause = self.preview_pause


    def execute(self, context):
        # 2.79
        if bpy.app.version_string.startswith('2.7'):
            self.prefs = context.user_preferences.addons[__package__].preferences
        # 2.80
        else:
            self.prefs = context.preferences.addons[__package__].preferences

        self.settings = context.scene.principled_baker_settings
        self.render_settings = context.scene.render.bake
        self.active_object = context.active_object
        self.selected_objects = bpy.context.selected_objects

        self.new_principled_node_settings = {}
        self.new_node_colors = {
            "Alpha":[1.0, 1.0, 1.0, 1.0],
            "Translucent_Alpha":[0.8, 0.8, 0.8, 1.0],
            "Glass_Alpha":[1.0, 1.0, 1.0, 1.0],
            'Emission':[1.0, 1.0, 1.0, 1.0],
            }

        new_images = {}

        # File needs to be saved
        if bpy.data.is_saved == False and self.settings.file_path.startswith("//"):
            self.report({'ERROR'}, 'Blendfile needs to be saved to get relative output path')
            return {'CANCELLED'}

        # Input error handling
        if not self.active_object.type == 'MESH':
            self.report({'ERROR'}, '{0} is not a mesh object'.format(self.active_object.name))
            return {'CANCELLED'}
        if self.settings.bake_mode == 'SELECTED_TO_ACTIVE':
            if len(self.selected_objects) < 2:
                self.report({'ERROR'}, 'Select at least 2 objects!')
                return {'CANCELLED'}

        # Temp switch to Cycles - see clean up!
        self.render_engine = bpy.context.scene.render.engine
        self.preview_pause = bpy.context.scene.cycles.preview_pause
        if not self.render_engine == 'CYCLES' and self.prefs.switch_to_cycles:
            bpy.context.scene.cycles.preview_pause = True
            bpy.context.scene.render.engine = 'CYCLES'

        # Bake only works in cycles (for now)
        if not bpy.context.scene.render.engine == 'CYCLES':
            self.report({'ERROR'}, 'Error: Current render engine ({0}) does not support baking'.format(bpy.context.scene.render.engine))
            return {'CANCELLED'}
        
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


        bake_objects = []
        bake_objects = get_only_meshes(self.selected_objects)

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
                    joblist = self.get_joblist_from_object(obj)
                else:
                    joblist = self.get_joblist_manual()

                if self.settings.use_Diffuse:
                    if "Diffuse" not in joblist:
                        joblist.append("Diffuse")

                if self.settings.use_material_id:
                    if "MatID" not in joblist:
                        joblist.append("MatID")

                if self.settings.use_vertex_color:
                    if len(obj.data.vertex_colors) > 0:
                        if "Vertex_Color" not in joblist:
                            joblist.append("Vertex_Color")
                    else:
                        self.report({'INFO'}, "Vertex Color baking skipped. '{0}' has no Vertex Color".format(obj.name))

                # empty joblist -> nothing to do
                if not joblist:
                    self.report({'INFO'}, "Nothing to do for {}.".format(obj.name))
                    continue

                # material outpus for later clean up
                active_outputs = get_active_outputs(obj_list)
                all_material_outputs = get_all_material_outputs(obj_list)
                # 2.80
                if not bpy.app.version_string.startswith('2.7'):
                    set_material_outputs_target_to_all(obj_list)

                # Auto UV project
                if not self.settings.auto_uv_project == 'OFF':
                    self.auto_uv_project(obj)

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
                    image_file_name = self.get_image_file_name(obj.name, job_name)
                    if not self.settings.use_overwrite and self.is_image_file(image_file_name):
                        self.report({'INFO'}, "baking skipped for '{0}'. File exists.".format(self.get_image_file_name(obj.name, job_name)))

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
                            self.create_bake_image_node(mat_slot.material, image)

                    # Bake!
                    self.report({'INFO'}, "baking '{0}'".format(image.name))
                    self.bake(get_bake_type(job_name))

                    # Save!
                    save_image_as(image,
                        file_path=image.filepath,
                        file_format=self.settings.file_format, 
                        color_mode=self.settings.color_mode, 
                        color_depth=self.settings.color_depth)

                    # Clean up!
                    # delete temp materials
                    self.delete_tagged_materials(obj, MATERIAL_TAG_VERTEX)
                    # delete temp nodes
                    self.delete_tagged_nodes(obj, NODE_TAG)
                    # reactivate Material Outputs
                    self.disable_material_outputs(obj)
                    for mat_output in active_outputs:
                        mat_output.is_active_output = True

                    # glossiness
                    if job_name == "Roughness" and self.settings.use_invert_roughness:
                        self.create_gloss_image(obj.name, image)

                    # add alpha channel to color
                    if self.settings.use_alpha_to_color and self.settings.color_mode == 'RGBA':
                        if "Color" in new_images.keys() and "Alpha" in new_images.keys():
                            new_images["Color"].pixels = get_combined_images(new_images["Color"], new_images["Alpha"], 0, 3)
                            new_images["Color"].save()

                # jobs DONE

                # add new images to new material
                if self.settings.make_new_material:
                    self.add_images_to_material(new_mat, new_images)
                    self.report({'INFO'}, "Mew Material created. '{0}'".format(new_mat.name))

                    # (optional) add new material
                    if self.settings.add_new_material:
                        obj.data.materials.append(new_mat)

                # Clean up!
                # 2.80
                if not bpy.app.version_string.startswith('2.7'):
                    for mat_output, target in all_material_outputs.items():
                        mat_output.target = target

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
            for obj in bake_objects:
                if self.settings.use_autodetect:
                    joblist = list(set(joblist).union(set(self.get_joblist_from_object(obj))))

            if self.settings.use_Diffuse:
                if "Diffuse" not in joblist:
                    joblist.append("Diffuse")

            if self.settings.use_material_id:
                if "MatID" not in joblist:
                    joblist.append("MatID")

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
            if not bpy.app.version_string.startswith('2.7'):
                set_material_outputs_target_to_all(bake_objects)

            # Auto UV project            
            if bpy.app.version_string.startswith('2.8'):  # no Auto Smart UV Project in 2.79
                if self.settings.auto_uv_project == 'SMART':
                    self.smart_project()
                elif self.settings.auto_uv_project == 'LIGHTMAP':
                    self.lightmap_pack()

            # (optional) new material
            if self.settings.make_new_material:
                new_mat_name = self.active_object.name if self.settings.new_material_prefix == "" else self.settings.new_material_prefix
                new_mat = self.new_material(new_mat_name)

            # Go through joblist
            for job_name in joblist:

                # skip, if no overwrite and image exists. load existing image
                image_file_name = self.get_image_file_name(self.active_object.name, job_name)
                if not self.settings.use_overwrite and self.is_image_file(image_file_name):
                    self.report({'INFO'}, "baking skipped for '{0}'. File exists.".format(self.get_image_file_name(obj.name, job_name)))

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
                            self.create_bake_image_node(mat_slot.material, image)

                # Bake!
                self.report({'INFO'}, "baking '{0}'".format(image.name))
                self.bake(get_bake_type(job_name))

                # Save!
                save_image_as(image,
                    file_path=image.filepath,
                    file_format=self.settings.file_format, 
                    color_mode=self.settings.color_mode, 
                    color_depth=self.settings.color_depth)

                # Clean up!
                for obj in bake_objects:
                    # delete temp materials
                    self.delete_tagged_materials(obj, MATERIAL_TAG_VERTEX)
                    # delete temp nodes
                    self.delete_tagged_nodes(obj, NODE_TAG)
                    # reactivate Material Outputs
                    self.disable_material_outputs(obj)
                for mat_output in active_outputs:
                    mat_output.is_active_output = True

                # glossiness
                if job_name == "Roughness" and self.settings.use_invert_roughness:
                    self.create_gloss_image(obj.name, image)

                # add alpha channel to color
                if self.settings.use_alpha_to_color and self.settings.color_mode == 'RGBA':
                    if "Color" in new_images.keys() and "Alpha" in new_images.keys():
                        new_images["Color"].pixels = get_combined_images(new_images["Color"], new_images["Alpha"], 0, 3)
                        new_images["Color"].save()

                # UPDATE progress report
                progress += 1/len(joblist)
                bpy.context.window_manager.progress_update(progress)

            # jobs DONE

            # add new images to new material
            if self.settings.make_new_material:
                self.add_images_to_material(new_mat, new_images)
                self.report({'INFO'}, "Mew Material created. '{0}'".format(new_mat.name))

                # (optional) add new material
                if self.settings.add_new_material:
                    self.active_object.data.materials.append(new_mat)

            # Clean up!
            # 2.80
            if not bpy.app.version_string.startswith('2.7'):
                for mat_output, target in all_material_outputs.items():
                    mat_output.target = target

            # END progress report
            bpy.context.window_manager.progress_end()

        ########
        # Bake Selected to Active:
        ########
        elif self.settings.bake_mode == 'SELECTED_TO_ACTIVE':

            # exclude active object from selected objects
            if self.active_object in bake_objects:
                bake_objects.remove(self.active_object)

            # Can bake?            
            if not self.can_bake(bake_objects):
                self.final_cleanup()
                return {'CANCELLED'}

            # Populate joblist
            joblist = []
            for obj in bake_objects:
                if self.settings.use_autodetect:
                    joblist = list(set(joblist).union(set(self.get_joblist_from_object(obj))))

            # if self.settings.use_Diffuse: # TODO does not work properly
            #     if "Diffuse" not in joblist:
            #         joblist.append("Diffuse")

            if self.settings.use_material_id:
                if "MatID" not in joblist:
                    joblist.append("MatID")

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
            if not bpy.app.version_string.startswith('2.7'):
                set_material_outputs_target_to_all(bake_objects)

            # Auto UV project
            if not self.settings.auto_uv_project == 'OFF':
                self.auto_uv_project(self.active_object)

            # new material
            new_mat_name = self.active_object.name if self.settings.new_material_prefix == "" else self.settings.new_material_prefix
            new_mat = self.new_material(new_mat_name)
            self.active_object.data.materials.append(new_mat)

            # Go through joblist
            for job_name in joblist:

                # skip, if no overwrite and image exists. load existing image
                image_file_name = self.get_image_file_name(self.active_object.name, job_name)
                if not self.settings.use_overwrite and self.is_image_file(image_file_name):
                    self.report({'INFO'}, "baking skipped for '{0}'. File exists.".format(self.get_image_file_name(obj.name, job_name)))

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

                # Bake!
                self.report({'INFO'}, "baking '{0}'".format(image.name))
                self.bake(get_bake_type(job_name), selected_to_active=True)

                # Save!
                save_image_as(image,
                    file_path=image.filepath,
                    file_format=self.settings.file_format, 
                    color_mode=self.settings.color_mode, 
                    color_depth=self.settings.color_depth)

                # Clean up!
                for obj in bake_objects:
                    # delete temp materials
                    self.delete_tagged_materials(obj, MATERIAL_TAG_VERTEX)
                    # delete temp nodes
                    self.delete_tagged_nodes(obj, NODE_TAG)
                    # reactivate Material Outputs
                    self.disable_material_outputs(obj)
                # delete temp materials
                self.delete_tagged_materials(self.active_object, MATERIAL_TAG_VERTEX)
                # delete temp nodes
                self.delete_tagged_nodes(self.active_object, NODE_TAG)
                # reactivate Material Outputs
                self.disable_material_outputs(self.active_object)
                for mat_output in active_outputs:
                    mat_output.is_active_output = True

                # glossiness
                if job_name == "Roughness" and self.settings.use_invert_roughness:
                    self.create_gloss_image(self.active_object.name, image)

                # add alpha channel to color
                if self.settings.use_alpha_to_color and self.settings.color_mode == 'RGBA':
                    if "Color" in new_images.keys() and "Alpha" in new_images.keys():
                        new_images["Color"].pixels = get_combined_images(new_images["Color"], new_images["Alpha"], 0, 3)
                        new_images["Color"].save()

                # UPDATE progress report
                progress += 1/len(joblist)
                bpy.context.window_manager.progress_update(progress)

            # jobs DONE

            # add new images to new material
            self.add_images_to_material(new_mat, new_images)
            self.report({'INFO'}, "Mew Material created. '{0}'".format(new_mat.name))

            # Clean up!
            # 2.80
            if not bpy.app.version_string.startswith('2.7'):
                for mat_output, target in all_material_outputs.items():
                    mat_output.target = target

            # END progress report
            bpy.context.window_manager.progress_end()


        self.final_cleanup()

        return {'FINISHED'}
