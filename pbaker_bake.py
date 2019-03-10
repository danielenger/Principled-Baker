import bpy
import os
import pathlib
import time

from . pbaker_functions import *

NODE_TAG = 'p_baker_node'
MATERIAL_TAG = 'p_baker_material'

NODE_INPUTS = [
    'Color',
    'Subsurface',
    # 'Subsurface Radius', # TODO
    'Subsurface Color',
    'Metallic',
    'Specular',
    'Specular Tint',
    'Roughness',
    'Anisotropic',
    'Anisotropic Rotation',
    'Sheen',
    'Sheen Tint',
    'Clearcoat',
    'Clearcoat Roughness',
    'IOR',
    'Transmission',
    'Transmission Roughness',
    'Normal',
    'Clearcoat Normal',
    'Tangent'
]

NORMAL_INPUTS = ['Normal', 'Clearcoat Normal', 'Tangent']

SRGB_INPUTS = ['Color', 'Base Color']

ALPHA_NODES = {
    "Alpha":'BSDF_TRANSPARENT',
    "Translucent_Alpha":'BSDF_TRANSLUCENT',
    "Glass_Alpha":'BSDF_GLASS'
}

BSDF_NODES = [
    'BSDF_PRINCIPLED',
    'BSDF_DIFFUSE',
    'BSDF_TOON',
    'BSDF_VELVET',
    'BSDF_GLOSSY',
    'BSDF_TRANSPARENT',
    'BSDF_TRANSLUCENT',
    'BSDF_GLASS'
    ]

IMAGE_FILE_FORMAT_ENDINGS = {
    "BMP": "bmp",
    "PNG": "png",
    "JPEG": "jpg",
    "TIFF": "tif",
    "TARGA": "tga",
    "OPEN_EXR": "exr",
}

NODE_OFFSET_X = 300
NODE_OFFSET_Y = 200

IMAGE_NODE_OFFSET_X = -900
IMAGE_NODE_OFFSET_Y = -260
IMAGE_NODE_WIDTH = 300

PRINCIPLED_BAKER_TEMP_MATERIAL_NAME = "PRINCIPLED_BAKER_TEMP_MATERIAL_{}".format(time.time())


class PBAKER_OT_bake(bpy.types.Operator):
    bl_idname = "object.principled_baker_bake"
    bl_label = "Bake"
    bl_description = "bake all inputs of a Principled BSDF to image textures" 
    bl_options = {'REGISTER', 'UNDO'} 

    settings = None

    def has_material(self, obj):
        if len(obj.material_slots) >= 1:
            for mat_slot in obj.material_slots:
                # TODO 
                try:
                    if not MATERIAL_TAG in mat_slot.material.keys():
                        material_output = find_active_output(mat_slot.material)
                        if material_output == None:
                            return False
                        else:
                            if not material_output.inputs['Surface'].is_linked:
                                return False
                            else:
                                return True                    
                except:
                    pass
        else:
            return False

    def get_bake_type(self, job_name):
        if job_name in NORMAL_INPUTS:
            return 'NORMAL'
        else:
            return 'EMIT'
            
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
                        mat = mat_slot.material
                        if not MATERIAL_TAG in mat.keys():
                            material_output = find_active_output(mat)
                            value_list.extend(self.get_value_list(material_output, value_name))
                    if len(value_list) >= 1:
                        if is_list_equal(value_list):
                            if self.settings.use_new_material or self.render_settings.use_selected_to_active:
                                self.new_principled_node_settings[value_name] = value_list[0]
                        else:
                            joblist.append(value_name)
                    
        # search material for jobs
        for mat_slot in obj.material_slots:
            if not MATERIAL_TAG in mat_slot.material.keys():
                # material_output = find_node_by_type(mat_slot.material, 'OUTPUT_MATERIAL')
                material_output = find_active_output(mat_slot.material)
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
                if self.is_socket_linked_in_node_tree(material_output, socket_name):
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
                        if self.is_socket_linked_in_node_tree(material_output, socket_name):
                            if not socket_name in joblist:
                                joblist.append(socket_name)
                
                # TODO remove 'color' from joblist, if added from Normal Map Color input?

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


    def guess_colors(self, obj, job_name):
        for mat_slot in obj.material_slots:
            mat = mat_slot.material
            if not MATERIAL_TAG in mat.keys():
                mat_out = find_active_output(mat_slot.material)
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


    def get_active_outputs(self, obj):
        act_out = []
        for mat_slot in obj.material_slots:
            if mat_slot.material:
                if not MATERIAL_TAG in mat_slot.material.keys():
                    act_out.append( find_active_output(mat_slot.material) )
        return act_out

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

        for name, image in new_images.items():
            if name not in ["AO", "Vertex_Color"]:
                image_node = new_image_node(new_mat)
                image_node.label = name

                image_node.color_space = 'COLOR' if name in SRGB_INPUTS else 'NONE'

                image_node.image = image

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
                
                # AO
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

            # AO
            elif name == 'AO':
                pass
            
            elif name == "Vertex_Color":
                pass

            else:
                new_mat.node_tree.links.new(image_node.outputs['Color'],
                                            principled_node.inputs[name])
            node_offset_index += 1


    def new_pb_diffuse_node(self, material, color=[0, 0, 0, 1]):
        # node = material.node_tree.nodes.new(type='ShaderNodeBsdfDiffuse')
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

    def new_bake_image(self, object_name, job_name):
        prefix = self.settings.image_prefix
        if prefix == "" or len(self.selected_objects) > 1 or self.settings.use_object_name:
            prefix = self.settings.image_prefix + object_name
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
        color = (0.5, 0.5, 1.0, 1.0) if self.get_bake_type(job_name) == 'NORMAL' else (0.0, 0.0, 0.0, 1.0)

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


    def prepare_for_bake_ao(self, mat, socket, new_socket):
        node = socket.node
        if node.type == 'AMBIENT_OCCLUSION':
            mat.node_tree.links.new(node.outputs['AO'], new_socket)
        else:
            for input_socket in node.inputs:
                if input_socket.is_linked:
                    from_socket = input_socket.links[0].from_socket
                    self.prepare_for_bake_ao(mat, from_socket, new_socket)

    def prepare_for_bake_vertex_color(self, obj, mat, new_socket):
        for name, vert_col in obj.data.vertex_colors.items():
            if vert_col.active_render:
                active_vert_col = name
        node = mat.node_tree.nodes.new(type='ShaderNodeAttribute')
        node[NODE_TAG] = 1  # tag for clean up
        node.attribute_name = active_vert_col
        mat.node_tree.links.new(node.outputs['Color'], new_socket)


    def prepare_for_bake_factor(self, mat, socket, new_socket, node_type, factor_name='Fac'):
        node = socket.node
        if node.type == node_type:
            to_node = node.outputs[0].links[0].to_node
            if factor_name in to_node.inputs.keys():
                socket = to_node.inputs[factor_name]
                self.prepare_for_bake(mat, socket, new_socket, factor_name)
        else:
            for input_socket in node.inputs:
                if input_socket.is_linked:
                    from_socket = input_socket.links[0].from_socket
                    self.prepare_for_bake_factor(mat, from_socket, new_socket, node_type, factor_name)

    def prepare_for_bake(self, mat, socket, new_socket, input_socket_name):
        if input_socket_name in NORMAL_INPUTS:
            color = (0.5, 0.5, 1.0, 1.0)
        else:
            color = (0.0, 0.0, 0.0, 0.0)
        
        # 2.79
        if bpy.app.version_string.startswith('2.7'):
            if input_socket_name == 'Displacement':
                if socket.is_linked:
                    from_socket = socket.links[0].from_socket
                    mat.node_tree.links.new(from_socket, new_socket)

        node = socket.node

        if node.type == 'OUTPUT_MATERIAL':
            from_socket = socket.links[0].from_socket
            self.prepare_for_bake(mat, from_socket, new_socket, input_socket_name)

        elif node.type == 'MIX_SHADER':
            color2 = [1,1,1,0] if input_socket_name == 'Fac' else color
            fac = node.inputs['Fac'].default_value
            mix_node = new_mixrgb_node(mat, fac, color, color2)
            mat.node_tree.links.new(mix_node.outputs[0], new_socket)
            mix_node.label = input_socket_name

            if node.inputs['Fac'].is_linked:
                from_socket = node.inputs[0].links[0].from_socket
                new_socket = mix_node.inputs[0]
                mat.node_tree.links.new(from_socket, new_socket)

            for i in range(1, 3):
                if node.inputs[i].is_linked:
                    next_node = node.inputs[i].links[0].from_node
                    if next_node.type in ALPHA_NODES.values() and self.settings.use_exclude_transparent_colors:
                        other_i = i % 2 + 1
                        if node.inputs[other_i].is_linked:
                            from_socket = node.inputs[other_i].links[0].from_socket
                            new_socket = mix_node.inputs[i]
                    else:
                        from_socket = node.inputs[i].links[0].from_socket
                        new_socket = mix_node.inputs[i]
                    self.prepare_for_bake(mat, from_socket, new_socket, input_socket_name)

        elif node.type == 'ADD_SHADER' and not input_socket_name == 'Fac':
            mix_node = new_mixrgb_node(mat, 1, color, color)
            mix_node.blend_type = 'ADD'
            mat.node_tree.links.new(mix_node.outputs[0], new_socket)
            mix_node.label = input_socket_name

            for i in range(0, 2):
                if node.inputs[i].is_linked:
                    from_socket = node.inputs[i].links[0].from_socket
                    new_socket = mix_node.inputs[i + 1]
                    self.prepare_for_bake(mat, from_socket, new_socket, input_socket_name)

        # exclude some colors from color
        elif node.type in ['EMISSION']:
            return

        # 2.79
        elif node.type == 'NORMAL_MAP' and bpy.app.version_string.startswith('2.7'):
            if node.inputs['Color'].is_linked:
                from_socket = node.inputs['Color'].links[0].from_socket
                mat.node_tree.links.new(from_socket, new_socket)

        # 2.79
        elif node.type == 'BUMP' and bpy.app.version_string.startswith('2.7'):
            if node.inputs['Height'].is_linked:
                from_socket = node.inputs['Height'].links[0].from_socket
                mat.node_tree.links.new(from_socket, new_socket)

        else:
            if node.type == 'BSDF_PRINCIPLED' and input_socket_name == 'Color':
                input_socket_name = 'Base Color'

            if input_socket_name in node.inputs.keys():
                input_socket = node.inputs[input_socket_name]
                
                if input_socket.type == 'RGBA':
                    if input_socket.is_linked:
                        o = input_socket.links[0].from_socket
                        prepare_for_bake_color(mat, o, new_socket)
                    else:
                        color = node.inputs[input_socket_name].default_value
                        rgb_node = new_rgb_node(mat, color)
                        mat.node_tree.links.new(rgb_node.outputs[0], new_socket)

                elif input_socket.type == 'VALUE':
                    if input_socket.is_linked:
                        from_socket = input_socket.links[0].from_socket
                        mat.node_tree.links.new(from_socket, new_socket)
                    else:
                        value_node = mat.node_tree.nodes.new(type="ShaderNodeValue")
                        value_node[NODE_TAG] = 1
                        value_node.outputs[0].default_value = node.inputs[input_socket_name].default_value
                        mat.node_tree.links.new(value_node.outputs[0], new_socket)

                elif input_socket.type == 'VECTOR':
                    if input_socket.name == input_socket_name:
                        # 2.79
                        if bpy.app.version_string.startswith('2.7'):
                            if input_socket.is_linked:
                                from_socket = input_socket.links[0].from_socket
                                if from_socket.node.type == 'NORMAL_MAP':
                                    self.prepare_for_bake(mat, from_socket, new_socket, 'Color')
                                if from_socket.node.type == 'BUMP':
                                    self.prepare_for_bake(mat, from_socket, new_socket, 'Height')
                        # 2.80
                        else:
                            if input_socket.is_linked:
                                from_socket = input_socket.links[0].from_socket
                                mat.node_tree.links.new(from_socket, new_socket)

            else:
                for input_socket in node.inputs:
                    if input_socket.is_linked:
                        from_socket = input_socket.links[0].from_socket
                        self.prepare_for_bake(mat, from_socket, new_socket, input_socket_name)

    def prepare_object_for_bake(self, obj, job_name):
        bake_type = self.get_bake_type(job_name)
        for mat_slot in obj.material_slots:
            mat = mat_slot.material
            if not MATERIAL_TAG in mat.keys():
                # material_output = find_node_by_type(mat, 'OUTPUT_MATERIAL')
                material_output = find_active_output(mat_slot.material)
                socket_to_surface = material_output.inputs['Surface'].links[0].from_socket

                # new temp Material Output node
                pb_output_node = self.new_pb_output_node(mat)
                pb_output_node[NODE_TAG] = 1
                pb_output_node.is_active_output = True

                material_output.is_active_output = False

                # temp Diffuse node
                pb_diffuse_node_color = [1, 1, 1, 1]
                pb_diffuse_node = self.new_pb_diffuse_node(mat, pb_diffuse_node_color)

                socket_to_pb_diffuse_node_color = pb_diffuse_node.inputs['Color']

                if bake_type == 'EMIT':
                    if job_name in ALPHA_NODES.keys():
                        node_type = ALPHA_NODES[job_name]
                        self.prepare_for_bake_factor(mat, socket_to_surface, socket_to_pb_diffuse_node_color, node_type, 'Fac')

                    elif job_name == 'Displacement':
                        if material_output.inputs['Displacement'].is_linked:
                            socket_to_displacement = material_output.inputs['Displacement'].links[0].from_socket
                            # 2.79
                            if bpy.app.version_string.startswith('2.7'):
                                from_socket = socket_to_displacement.links[0].from_socket
                                mat.node_tree.links.new(from_socket, socket_to_pb_diffuse_node_color)
                            # 2.80
                            else:
                                self.prepare_for_bake(mat, socket_to_displacement, socket_to_pb_diffuse_node_color, 'Height')

                    elif job_name == 'Bump':
                        self.prepare_for_bake(mat, socket_to_surface, socket_to_pb_diffuse_node_color, 'Height')
                    elif job_name == 'AO':
                        self.prepare_for_bake_ao(mat, socket_to_surface, socket_to_pb_diffuse_node_color)
                    elif job_name == 'Vertex_Color':
                        self.prepare_for_bake_vertex_color(obj, mat, socket_to_pb_diffuse_node_color)
                    else:
                        self.prepare_for_bake(mat, socket_to_surface, socket_to_pb_diffuse_node_color, job_name)

                    # link pb_diffuse_node to material_output
                    mat.node_tree.links.new(pb_diffuse_node.outputs[0], pb_output_node.inputs['Surface'])

                # 2.79
                elif bake_type == 'NORMAL' and bpy.app.version_string.startswith('2.7'):
                    if self.settings.use_Bump:
                        self.prepare_for_bake(mat, socket_to_surface, socket_to_pb_diffuse_node_color, job_name)
                        # link pb_diffuse_node to material_output
                        mat.node_tree.links.new(pb_diffuse_node.outputs[0], pb_output_node.inputs['Surface'])
                    # normal
                    self.prepare_for_bake(mat, socket_to_surface, socket_to_pb_diffuse_node_color, 'Normal')
                    # link pb_diffuse_node to material_output
                    mat.node_tree.links.new(pb_diffuse_node.outputs[0], pb_output_node.inputs['Surface'])
                    s = pb_diffuse_node.inputs['Color'].links[0].from_socket
                    mat.node_tree.links.new(s, pb_output_node.inputs['Displacement'])


    def is_socket_linked_in_node_tree(self, node, input_socket_name):
        if input_socket_name == 'Color':
            if node.type == 'NORMAL_MAP':
                return False # exclude 'Color' from Normal Map input!
            if node.type == 'BSDF_PRINCIPLED':
                input_socket_name = 'Base Color'
        for input_socket in node.inputs:
            if input_socket.is_linked:
                if input_socket_name == input_socket.name:
                    return True
                else:
                    from_node = input_socket.links[0].from_node
                    if self.is_socket_linked_in_node_tree(from_node, input_socket_name):
                        return True
        return False

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

    def smart_uv_project(self, obj):
        orig_selected_objects = self.selected_objects
        for o in self.selected_objects:
            select_set(o, False)
        select_set(obj, True)
        
        bpy.ops.uv.smart_project(angle_limit=self.settings.angle_limit, 
            island_margin=self.settings.island_margin, 
            user_area_weight=self.settings.user_area_weight, 
            use_aspect=self.settings.use_aspect, 
            stretch_to_bounds=self.settings.stretch_to_bounds)
        
        for o in orig_selected_objects:
            select_set(o, True)

    def bake(self, obj, bake_type, selected_to_active=False):
        org_selected_objects = bpy.context.selected_objects
        for o in bpy.context.selected_objects:
            select_set(o, False)
        select_set(obj, True)

        org_samples = bpy.context.scene.cycles.samples
        bpy.context.scene.cycles.samples = self.settings.samples
    
        bpy.ops.object.bake(type=bake_type, use_selected_to_active=selected_to_active)

        for o in org_selected_objects:
            select_set(o, True)

        bpy.context.scene.cycles.samples = org_samples


    def execute(self, context):
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

        # bake only works in cycles (for now)
        if not bpy.context.scene.render.engine == 'CYCLES':
            self.report({'ERROR'}, 'Error: Current render engine ({0}) does not support baking'.format(bpy.context.scene.render.engine))
            return {'CANCELLED'}

        # input error handling
        if not self.active_object.type == 'MESH':
            self.report({'ERROR'}, '{0} is not a mesh object'.format(self.active_object.name))
            return {'CANCELLED'}
        if self.render_settings.use_selected_to_active:
            if len(self.selected_objects) < 2:
                self.report({'ERROR'}, 'Select at least 2 objects!')
                return {'CANCELLED'}
        
        joblist = []
        if not self.settings.use_autodetect:
            joblist = self.get_joblist_manual()        

        # Auto Smooth - See clean up!
        if not self.settings.auto_smooth == 'OBJECT':
            auto_smooth_list = {}
            for obj in self.selected_objects:
                auto_smooth_list[obj] = obj.data.use_auto_smooth
            if self.settings.auto_smooth == 'ON':
                for obj in self.selected_objects:
                    obj.data.use_auto_smooth = True
            elif self.settings.auto_smooth == 'OFF':
                for obj in self.selected_objects:
                    obj.data.use_auto_smooth = False


        ########
        # bake single or batch:
        ########
        if not self.render_settings.use_selected_to_active:

            bake_objects = []
            for obj in self.selected_objects:
                if obj.type == 'MESH':
                    if obj.hide_render:
                        self.report({'INFO'}, "baking skipped for '{0}'. Not enabled for rendering.".format(obj.name))
                    else:
                        if len(obj.data.uv_layers) >= 1:
                            if self.has_material(obj):
                                bake_objects.append(obj)
                            else:
                                self.report({'INFO'}, "baking skipped for '{0}'. Material or Material Output missing.".format(obj.name))
                        else:
                            if self.has_material(obj):
                                if self.settings.use_smart_uv_project:
                                    self.smart_uv_project(obj)
                                    bake_objects.append(obj)
                                else:
                                    self.report({'INFO'}, "baking skipped for '{0}'. UV map missing.".format(obj.name))
                            else:
                                self.report({'INFO'}, "baking skipped for '{0}'. Material and UV map missing.".format(obj.name))

            bpy.context.window_manager.progress_begin(0, len(bake_objects))
            progress = 0

            for obj in bake_objects:
                
                new_images.clear()
                
                # find active material outpus for later clean up
                active_outputs = self.get_active_outputs(obj)

                # populate joblist
                if self.settings.use_autodetect:
                    joblist = self.get_joblist_from_object(obj)
                if self.settings.use_vertex_color:
                    if len(obj.data.vertex_colors) >= 1:
                        if "Vertex_Color" not in joblist:
                            joblist.append("Vertex_Color")
                    else:
                        self.report({'INFO'}, "Vertex Color baking skipped. '{0}' has no Vertex Color".format(obj.name))

                # create new material
                if self.settings.use_new_material:
                    new_mat_name = obj.name if self.settings.new_material_prefix == "" else self.settings.new_material_prefix
                    new_mat = self.new_material(new_mat_name)
                    obj.data.materials.append(new_mat)

                # go through joblist
                for job_name in joblist:

                    # guess colors for Transparent, Translucent, Glass, Emission
                    if self.settings.use_new_material:
                        if job_name in self.new_node_colors.keys():
                            self.guess_colors(obj, job_name)

                    # skip, if no overwrite and image exists
                    image_file_name = self.get_image_file_name(obj.name, job_name)
                    if not self.settings.use_overwrite and self.is_image_file(image_file_name):
                        self.report({'INFO'}, "baking skipped for '{0}'. File exists.".format(self.get_image_file_name(obj.name, job_name)))

                        # load image for new material
                        if self.settings.use_new_material:
                            if image_file_name in bpy.data.images:
                                image = bpy.data.images[image_file_name]
                            else:
                                path = self.get_image_file_path(image_file_name)
                                image = bpy.data.images.load(path)
                                new_images[job_name] = image
                    
                    # skip vertex color, if no

                    else:  # do bake

                        remove_empty_material_slots(obj)

                        # image to bake on
                        image = self.new_bake_image(obj.name, job_name)

                        # append image to image dict for new material
                        new_images[job_name] = image

                        # prepare materials before baking
                        # 2.79 Normal Map
                        if bpy.app.version_string.startswith('2.7') and job_name == "Normal":
                            self.prepare_object_for_bake(obj, job_name)
                        # 2.80
                        if not job_name in ["Emission", "Normal"]:
                            self.prepare_object_for_bake(obj, job_name)

                        # create temp image nodes to bake on
                        for mat_slot in obj.material_slots:
                            mat = mat_slot.material
                            if not MATERIAL_TAG in mat.keys():
                                self.create_bake_image_node(mat, image)

                        # bake!
                        self.report({'INFO'}, "baking '{0}'".format(image.name))
                        bake_type = self.get_bake_type(job_name)
                        self.bake(obj, bake_type=bake_type, selected_to_active=False)

                        # save!
                        save_image_as(image,
                            file_path=image.filepath,
                            file_format=self.settings.file_format, 
                            color_mode=self.settings.color_mode, 
                            color_depth=self.settings.color_depth)

                        # glossiness
                        if job_name == "Roughness" and self.settings.use_invert_roughness:
                            self.create_gloss_image(obj.name, image)


                        # clean up: delete all nodes with tag = NODE_TAG
                        self.delete_tagged_nodes(obj, NODE_TAG)
                        if self.settings.use_new_material:
                            for node in new_mat.node_tree.nodes:
                                if NODE_TAG in node.keys():
                                    new_mat.node_tree.nodes.remove(node)

                        # clean up: reactivate Material Outputs
                        for mat_slot in obj.material_slots:
                            for node in mat_slot.material.node_tree.nodes:
                                if node.type == "OUTPUT_MATERIAL":
                                    node.is_active_output = False
                        for mat_output in active_outputs:
                            mat_output.is_active_output = True


                        progress += 1/len(joblist)
                        bpy.context.window_manager.progress_update(progress)

                # add alpha channel to color
                if self.settings.use_alpha_to_color and self.settings.color_mode == 'RGBA':
                    if "Color" in new_images.keys() and "Alpha" in new_images.keys():
                        new_images["Color"].pixels = get_combined_images(new_images["Color"], new_images["Alpha"], 0, 3)
                        new_images["Color"].save()

                # add new images to new material
                if self.settings.use_new_material:
                    self.add_images_to_material(new_mat, new_images)

            bpy.context.window_manager.progress_end()

        ########
        # bake selected to active:
        ########
        elif self.render_settings.use_selected_to_active:
            new_images.clear()

            if self.active_object.hide_render:
                self.report({'INFO'}, "baking skipped for '{0}'. Not enabled for rendering.".format(self.active_object.name))
                return {'CANCELLED'}

            bake_objects = []
            for obj in self.selected_objects:
                if obj.type == 'MESH':
                    if self.has_material(obj):
                        bake_objects.append(obj)
            if self.active_object in bake_objects:
                bake_objects.remove(self.active_object)

            remove_empty_material_slots(self.active_object)

            # find active material outpus for later clean up
            for obj in bake_objects:
                active_outputs = self.get_active_outputs(obj)
                        
            # populate joblist
            for obj in bake_objects:
                if self.settings.use_autodetect:
                    job_extend = self.get_joblist_from_object(obj)
                    for j in job_extend:
                        if j not in joblist:
                            joblist.append(j)
            if self.settings.use_vertex_color:
                if len(obj.data.vertex_colors) >= 1:
                    if "Vertex_Color" not in joblist:
                        joblist.append("Vertex_Color")
                else:
                    self.report({'INFO'}, "Vertex Color baking skipped. '{0}' has no Vertex Color".format(obj.name))

            # create new material
            if self.settings.use_new_material:
                new_mat_name = self.active_object.name if self.settings.new_material_prefix == "" else self.settings.new_material_prefix
            else:
                new_mat_name = PRINCIPLED_BAKER_TEMP_MATERIAL_NAME
            new_mat = self.new_material(new_mat_name)
            self.active_object.data.materials.append(new_mat)

            # auto smart uv project
            if len(self.active_object.data.uv_layers) < 1:
                self.smart_uv_project(self.active_object)

            bpy.context.window_manager.progress_begin(0, len(joblist))
            progress = 0

            # go through joblist
            for job_name in joblist:

                bake_type = self.get_bake_type(job_name)

                # guess color for Transparent, Translucent, Glass, Emission
                if job_name in self.new_node_colors.keys():
                    for obj in bake_objects:
                        self.guess_colors(obj, job_name)

                # skip, if no overwrite and image exists
                obj_name = self.active_object.name
                image_file_name = self.get_image_file_name(obj_name, job_name)

                if not self.settings.use_overwrite and self.is_image_file(image_file_name):
                    # do not bake!
                    self.report({'INFO'}, "baking skipped for '{0}'. File exists.".format(image_file_name))

                    # load image for new material
                    if image_file_name in bpy.data.images:
                        image = bpy.data.images[image_file_name]
                    else:
                        path = self.get_image_file_path(image_file_name)
                        image = bpy.data.images.load(path)
                    new_images[job_name] = image

                else:  # do bake
                    
                    # image to bake on
                    image = self.new_bake_image(obj_name, job_name)
                    # append image to image dict for new material
                    new_images[job_name] = image

                    # prepare materials before baking
                    # 2.79 Normal Map
                    if bpy.app.version_string.startswith('2.7') and job_name == "Normal":
                        for obj in bake_objects:
                            self.prepare_object_for_bake(obj, job_name)
                    # 2.80
                    if not job_name in ["Emission", "Normal"]:
                        for obj in bake_objects:
                            self.prepare_object_for_bake(obj, job_name)

                    # create temp image node to bake on
                    for mat_slot in self.active_object.material_slots:
                        if mat_slot.material:
                            self.create_bake_image_node(mat_slot.material, image)

                    # bake!
                    self.report({'INFO'}, "baking '{0}'".format(image.name))
                    bake_type = self.get_bake_type(job_name)
                    # self.bake(type=bake_type, use_selected_to_active=True)
                    bpy.ops.object.bake(type=bake_type, use_selected_to_active=True)


                    # save!
                    save_image_as(image,
                        file_path=image.filepath,
                        file_format=self.settings.file_format, 
                        color_mode=self.settings.color_mode, 
                        color_depth=self.settings.color_depth)

                    # glossiness
                    if job_name == "Roughness" and self.settings.use_invert_roughness:
                        self.create_gloss_image(obj.name, image)

                    # clean up!
                    # delete all nodes with tag = NODE_TAG
                    self.delete_tagged_nodes(self.active_object, NODE_TAG)
                    for obj in bake_objects:
                        self.delete_tagged_nodes(obj, NODE_TAG)

                    for mat_slot in self.active_object.material_slots:
                        if mat_slot.material:
                            if MATERIAL_TAG in mat_slot.material.keys():
                                del new_mat[MATERIAL_TAG]


                    # reactivate Material Outputs
                    for mat_output in active_outputs:
                        mat_output.is_active_output = True

                    progress+=1
                    bpy.context.window_manager.progress_update(progress)
            
            # clean up!
            for mat_slot in self.active_object.material_slots:
                if mat_slot.material:
                    if PRINCIPLED_BAKER_TEMP_MATERIAL_NAME in mat_slot.material.name:
                        index = self.active_object.material_slots.find(PRINCIPLED_BAKER_TEMP_MATERIAL_NAME)
                        bpy.context.object.active_material_index = index
                        bpy.ops.object.material_slot_remove({'object': self.active_object})

            if PRINCIPLED_BAKER_TEMP_MATERIAL_NAME in bpy.data.materials.keys():
                bpy.data.materials.remove(bpy.data.materials[PRINCIPLED_BAKER_TEMP_MATERIAL_NAME])


            # add alpha channel to color
            if self.settings.use_alpha_to_color and self.settings.color_mode == 'RGBA':
                if "Color" in new_images.keys() and "Alpha" in new_images.keys():
                    new_images["Color"].pixels = get_combined_images(new_images["Color"], new_images["Alpha"], 0, 3)

            # add new images to new material
            if self.settings.use_new_material:
                self.add_images_to_material(new_mat, new_images)


        # Auto Smooth - Clean up!
        if not self.settings.auto_smooth == 'OBJECT':
            for obj in auto_smooth_list:
                obj.data.use_auto_smooth = auto_smooth_list[obj]


        return {'FINISHED'}
