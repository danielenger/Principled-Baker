import bpy
from bpy.types import Operator

import os
import pathlib

from . pbaker_functions import *

PRINCIPLED_NODE_TAG = 'p_baker_node'

PRINCIPLED_INPUTS = [
    'Color',
    'Subsurface',
    'Subsurface Radius',
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
    'Bump',  # special
    'Normal',
    'Clearcoat Normal',
    'Tangent'
]

IMAGE_FILE_ENDINGS = {
    "BMP": "bmp",
    "PNG": "png",
    "JPEG": "jpg",
    "TIFF": "tif",
    "TARGA": "tga",
}

NODE_OFFSET_X = -900
NODE_OFFSET_Y = -260


class PBAKER_OT_bake(Operator):
    bl_idname = "object.principled_baker_bake"
    bl_label = "Bake"
    bl_description = "bake all inputs of a Principled BSDF to image textures" 
    bl_options = {'REGISTER', 'UNDO'} 

    settings = None
    do_bake = False

    def fill_joblist(self):
        self.joblist = []
        if self.settings.use_Alpha:
            self.joblist.append("Alpha")
        if self.settings.use_Base_Color:
            self.joblist.append("Color")
        if self.settings.use_Metallic:
            self.joblist.append("Metallic")
        if self.settings.use_Roughness:
            self.joblist.append("Roughness")

        if self.settings.use_Normal:
            self.joblist.append("Normal")
        if self.settings.use_Bump:
            self.joblist.append("Bump")
        if self.settings.use_Displacement:
            self.joblist.append("Displacement")

        if self.settings.use_Specular:
            self.joblist.append("Specular")
        if self.settings.use_Anisotropic:
            self.joblist.append("Anisotropic")
        if self.settings.use_Anisotropic_Rotation:
            self.joblist.append("Anisotropic Rotation")
        if self.settings.use_Clearcoat:
            self.joblist.append("Clearcoat")
        if self.settings.use_Clearcoat_Normal:
            self.joblist.append("Clearcoat Normal")
        if self.settings.use_Clearcoat_Roughness:
            self.joblist.append("Clearcoat Roughness")
        if self.settings.use_IOR:
            self.joblist.append("IOR")
        if self.settings.use_Sheen:
            self.joblist.append("Sheen")
        if self.settings.use_Sheen_Tint:
            self.joblist.append("Sheen Tint")
        if self.settings.use_Specular_Tint:
            self.joblist.append("Specular Tint")
        if self.settings.use_Subsurface:
            self.joblist.append("Subsurface")
        if self.settings.use_Subsurface_Color:
            self.joblist.append("Subsurface Color")
        if self.settings.use_Subsurface_Radius:
            self.joblist.append("Subsurface Radius")
        if self.settings.use_Tangent:
            self.joblist.append("Tangent")
        if self.settings.use_Transmission:
            self.joblist.append("Transmission")

    def get_suffix(self, input_name):
        if input_name == 'Color':
            return self.settings.suffix_color
        elif input_name == 'Metallic':
            return self.settings.suffix_metallic
        elif input_name == 'Roughness':
            return self.settings.suffix_roughness
        elif input_name == 'Bump' and self.settings.use_bump_to_normal:
            return self.settings.suffix_bump_to_normal
        else:
            suffix = '_' + input_name
            return suffix

    def new_material(self, name, has_alpha=False):
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        mat.node_tree.nodes.remove(mat.node_tree.nodes['Diffuse BSDF'])
        mat['p_baker_material'] = 1

        mat_output = mat.node_tree.nodes['Material Output']

        principled_node = mat.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
        principled_node.location.x = NODE_OFFSET_X / 3
        principled_node.location.y = NODE_OFFSET_Y / 3

        # copy settings to new principled_node
        for k, v in self.new_principled_node_settings.items():
            if k == 'Color':
                k = 'Base Color'
            principled_node.inputs[k].default_value = v

        if has_alpha:
            transparency_node = mat.node_tree.nodes.new(type='ShaderNodeBsdfTransparent')
            transparency_node.location.x = NODE_OFFSET_X / 3
            transparency_node.location.y = -NODE_OFFSET_Y / 3

            mix_node = mat.node_tree.nodes.new(type='ShaderNodeMixShader')

            mat.node_tree.links.new(transparency_node.outputs['BSDF'],
                                    mix_node.inputs[1])
            mat.node_tree.links.new(principled_node.outputs['BSDF'],
                                    mix_node.inputs[2])
            mat.node_tree.links.new(mix_node.outputs[0],
                                    mat_output.inputs['Surface'])

        else:
            mat.node_tree.links.new(principled_node.outputs['BSDF'],
                                    mat_output.inputs['Surface'])
        return mat

    def add_images_to_material(self, new_mat, new_images):

        node_offset_index = 0

        new_principled_node = find_node_by_type(new_mat, 'BSDF_PRINCIPLED')
        new_material_output = find_node_by_type(new_mat, 'OUTPUT_MATERIAL')
        new_mixshader_node = find_node_by_type(new_mat, 'MIX_SHADER')

        for input_name in self.joblist:
            image_node = self.new_image_node(new_mat)
            image_node.label = input_name

            if input_name in ['Color']:
                image_node.color_space = 'COLOR'
            else:
                image_node.color_space = 'NONE'
            # add image to node
            image_node.image = new_images[input_name]

            # rearrange nodes
            image_node.width = 300
            image_node.location.x = NODE_OFFSET_X
            image_node.location.y = NODE_OFFSET_Y * node_offset_index

            if input_name == 'Alpha' and self.settings.use_alpha_to_color:
                new_mat.node_tree.nodes.remove(image_node)

            # link nodes
            if input_name == 'Normal':
                normal_node = new_mat.node_tree.nodes.new(type="ShaderNodeNormalMap")
                normal_node.location.x = NODE_OFFSET_X + 350
                normal_node.location.y = NODE_OFFSET_Y * node_offset_index
                new_mat.node_tree.links.new(image_node.outputs['Color'], normal_node.inputs['Color'])
                new_mat.node_tree.links.new(normal_node.outputs['Normal'], new_principled_node.inputs['Normal'])
            elif input_name == 'Bump':
                if self.settings.use_bump_to_normal:
                    normal_node = new_mat.node_tree.nodes.new(type="ShaderNodeNormalMap")
                    normal_node.location.x = NODE_OFFSET_X + 350
                    normal_node.location.y = NODE_OFFSET_Y * node_offset_index
                    new_mat.node_tree.links.new(image_node.outputs['Color'], normal_node.inputs['Color'])
                    new_mat.node_tree.links.new(normal_node.outputs['Normal'], new_principled_node.inputs['Normal'])
                else:
                    bump_node = new_mat.node_tree.nodes.new(type="ShaderNodeBump")
                    bump_node.location.x = NODE_OFFSET_X + 350
                    bump_node.location.y = NODE_OFFSET_Y * node_offset_index
                    new_mat.node_tree.links.new(image_node.outputs['Color'], bump_node.inputs['Height'])
                    new_mat.node_tree.links.new(bump_node.outputs['Normal'], new_principled_node.inputs['Normal'])
            elif input_name == 'Displacement':
                new_mat.node_tree.links.new(image_node.outputs['Color'],
                                            new_material_output.inputs['Displacement'])
            elif input_name == 'Alpha':
                if not self.settings.use_alpha_to_color:
                    new_mat.node_tree.links.new(image_node.outputs['Color'],
                                                new_mixshader_node.inputs['Fac'])
            elif input_name == 'Color':
                input_name = 'Base Color'
                new_mat.node_tree.links.new(image_node.outputs['Color'],
                                            new_principled_node.inputs[input_name])
                if self.settings.use_alpha_to_color and 'Alpha' in self.joblist:
                    new_mat.node_tree.links.new(image_node.outputs['Alpha'],
                                                new_mixshader_node.inputs['Fac'])
            else:
                new_mat.node_tree.links.new(image_node.outputs['Color'],
                                            new_principled_node.inputs[input_name])
            node_offset_index = node_offset_index + 1

    def new_pb_diffuse_node(self, material):
        node = material.node_tree.nodes.new(type='ShaderNodeBsdfDiffuse')
        node.inputs['Color'].default_value = [0, 0, 0, 1]
        node[PRINCIPLED_NODE_TAG] = 1
        return node

    def new_pb_emitter_node(self, material):
        node = material.node_tree.nodes.new(type='ShaderNodeEmission')
        node.inputs['Color'].default_value = [0, 0, 0, 1]
        node[PRINCIPLED_NODE_TAG] = 1
        return node

    def new_pb_output_node(self, material):
        node = material.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
        node[PRINCIPLED_NODE_TAG] = 1
        return node

    def get_file_path(self, image_file_name):
        path = os.path.join(
            os.path.dirname(bpy.data.filepath),  # absolute file path of current blend file
            self.settings.file_path.lstrip("/"),  # relativ file path from user input
            image_file_name)
        return path

    def new_image(self, image_file_name, alpha=False):
        image = bpy.data.images.new(
            name=image_file_name,
            alpha=alpha,  # self.settings.use_alpha,
            width=self.settings.resolution,
            height=self.settings.resolution)

        image.use_alpha = alpha  # self.settings.use_alpha
        image.alpha_mode = 'STRAIGHT'

        if alpha:  # self.settings.use_alpha:
            fill_image(image, (0.0, 0.0, 0.0, 0.0))

        image.filepath_raw = self.get_file_path(image_file_name)
        image.file_format = self.settings.file_format
        image.save()
        return image

    def new_image_node(self, material):
        image_node = material.node_tree.nodes.new(type="ShaderNodeTexImage")
        return image_node

    def get_value_list(self, socket, value_name):
        value_list = []

        def findvalue(socket, value_name):
            if socket.is_linked:
                node = socket.node
                if socket.type == 'SHADER':
                    if node.type == 'OUTPUT_MATERIAL':
                        from_socket = socket.links[0].from_socket
                        findvalue(from_socket, value_name)

                    elif node.type == 'REROUTE':
                        from_socket = node.inputs[0].links[0].from_socket
                        findvalue(from_socket, value_name)

                    elif node.type == 'MIX_SHADER':
                        for i in range(1, 3):
                            if node.inputs[i].is_linked:
                                from_socket = node.inputs[i].links[0].from_socket
                                findvalue(from_socket, value_name)

                    elif node.type in ['BSDF_PRINCIPLED', 'BSDF_DIFFUSE', 'BSDF_TRANSLUCENT']:
                        if value_name == 'Color' and node.type == 'BSDF_PRINCIPLED':
                            value_name = 'Base Color'
                        if value_name in node.inputs.keys():
                            if node.inputs[value_name].type == 'RGBA':
                                [r, g, b, a] = node.inputs[value_name].default_value
                                value_list.append([r, g, b, a])
                            else:
                                value = node.inputs[value_name].default_value
                                value_list.append(value)

        findvalue(socket, value_name)
        return value_list

    def has_node_type(self, mat, socket, node_type):
        if socket.is_linked:
            node = socket.node
            if node.type == node_type:
                return True
            elif node.type == 'REROUTE':
                from_socket = node.inputs[0].links[0].from_socket
                if self.has_node_type(mat, from_socket, node_type):
                    return True
            else:
                for input in node.inputs:
                    if input.is_linked:
                        from_socket = input.links[0].from_socket
                        if self.has_node_type(mat, from_socket, node_type):
                            return True

    def prepare_for_bake_factor(self, mat, socket, new_socket, node_type):
        if not socket.is_linked:
            return False
        else:
            node = socket.node

            if socket.type == 'VALUE' or socket.type == 'RGBA':
                mat.node_tree.links.new(socket, new_socket)

            elif socket.type == 'SHADER':
                if node.type == 'OUTPUT_MATERIAL':
                    from_socket = socket.links[0].from_socket
                    return self.prepare_for_bake_factor(mat, from_socket, new_socket, node_type)

                elif node.type == 'REROUTE':
                    reroute = mat.node_tree.nodes.new(type="NodeReroute")
                    reroute[PRINCIPLED_NODE_TAG] = 1
                    mat.node_tree.links.new(reroute.outputs[0], new_socket)
                    new_socket = reroute.inputs[0]
                    from_socket = node.inputs[0].links[0].from_socket
                    return self.prepare_for_bake_factor(mat, from_socket, new_socket, node_type)

                elif node.type == node_type:
                    return True

                elif node.type == 'BSDF_PRINCIPLED':
                    return False

                elif node.type == 'MIX_SHADER':
                    mix_node = new_mixrgb_node(mat)
                    mix_node[PRINCIPLED_NODE_TAG] = 1
                    mix_node.inputs['Fac'].default_value = node.inputs['Fac'].default_value
                    mat.node_tree.links.new(mix_node.outputs[0], new_socket)
                    mix_node.label = node_type

                    r = False
                    if node.inputs[0].is_linked:
                        from_socket = node.inputs[0].links[0].from_socket
                        new_socket = mix_node.inputs[0]
                        r = self.prepare_for_bake_factor(mat, from_socket, new_socket, node_type)
                    else:
                        value_node = mat.node_tree.nodes.new(type="ShaderNodeValue")
                        value_node[PRINCIPLED_NODE_TAG] = 1
                        value_node.outputs[0].default_value = node.inputs[0].default_value
                        mat.node_tree.links.new(value_node.outputs[0], new_socket)
                        r = True

                    if node.inputs[1].is_linked:
                        if node.inputs[1].links[0].from_node.type == node_type:
                            mix_node.inputs[1].default_value = [0, 0, 0, 1]
                            mix_node.inputs[2].default_value = [1, 1, 1, 1]
                        from_socket = node.inputs[1].links[0].from_socket
                        new_socket = mix_node.inputs[1]
                        r = self.prepare_for_bake_factor(mat, from_socket, new_socket, node_type)

                    if node.inputs[2].is_linked:
                        if node.inputs[2].links[0].from_node.type == node_type:
                            mix_node.inputs[1].default_value = [1, 1, 1, 1]
                            mix_node.inputs[2].default_value = [0, 0, 0, 1]
                        from_socket = node.inputs[2].links[0].from_socket
                        new_socket = mix_node.inputs[2]
                        r = self.prepare_for_bake_factor(mat, from_socket, new_socket, node_type)
                    return r

    def prepare_for_bake(self, mat, socket, new_socket, input_name):
        if input_name in ['Normal', 'Clearcoat Normal', 'Tangent']:
            color = (0.5, 0.5, 1.0, 1.0)
        else:
            color = (0.0, 0.0, 0.0, 0.0)

        node = socket.node
        if input_name == 'Displacement':
            mat.node_tree.links.new(socket, new_socket)

        elif node.type == 'OUTPUT_MATERIAL':
            from_socket = socket.links[0].from_socket
            self.prepare_for_bake(mat, from_socket, new_socket, input_name)

        elif node.type == 'REROUTE':
            reroute = mat.node_tree.nodes.new(type="NodeReroute")
            reroute[PRINCIPLED_NODE_TAG] = 1
            mat.node_tree.links.new(reroute.outputs[0], new_socket)
            new_socket = reroute.inputs[0]
            from_socket = node.inputs[0].links[0].from_socket
            self.prepare_for_bake(mat, from_socket, new_socket, input_name)

        elif node.type == 'MIX_SHADER':
            mix_node = new_mixrgb_node(mat, color, color)
            mix_node.inputs['Fac'].default_value = node.inputs['Fac'].default_value
            mat.node_tree.links.new(mix_node.outputs[0], new_socket)
            mix_node.label = input_name

            if node.inputs[0].is_linked:
                from_socket = node.inputs[0].links[0].from_socket
                new_socket = mix_node.inputs[0]
                mat.node_tree.links.new(from_socket, new_socket)

            for i in range(1, 3):
                if node.inputs[i].is_linked:
                    next_node = node.inputs[i].links[0].from_node
                    if next_node.type == 'BSDF_TRANSPARENT':
                        if node.inputs[i % 2 + 1].is_linked:
                            from_socket = node.inputs[i % 2 + 1].links[0].from_socket
                            new_socket = mix_node.inputs[i]
                    else:
                        from_socket = node.inputs[i].links[0].from_socket
                        new_socket = mix_node.inputs[i]
                    self.prepare_for_bake(mat, from_socket, new_socket, input_name)

        elif node.type == 'ADD_SHADER':
            mix_node = new_mixrgb_node(mat, color, color)
            mix_node.blend_type = 'ADD'
            mix_node.inputs['Fac'].default_value = 1
            mat.node_tree.links.new(mix_node.outputs[0], new_socket)
            mix_node.label = input_name

            for i in range(0, 2):
                if node.inputs[i].is_linked:
                    from_socket = node.inputs[i].links[0].from_socket
                    new_socket = mix_node.inputs[i + 1]
                    self.prepare_for_bake(mat, from_socket, new_socket, input_name)

        elif node.type in ['BSDF_PRINCIPLED', 'BSDF_DIFFUSE', 'BSDF_TRANSLUCENT', 'EMISSION']:
            if input_name == 'Bump':
                input = node.inputs['Normal']
                if input.is_linked:
                    from_socket = input.links[0].from_socket
                    from_node = from_socket.node
                    if from_node.type == 'BUMP':
                        self.prepare_for_bake(mat, from_socket, new_socket, input_name)
            else:
                if node.type == 'BSDF_PRINCIPLED' and input_name == 'Color':
                    input_name = 'Base Color'
                for input in node.inputs:
                    if input.name == input_name:
                        if input.type == 'RGBA':
                            if input.is_linked:
                                from_socket = input.links[0].from_socket
                                mat.node_tree.links.new(from_socket, new_socket)
                            else:
                                color = node.inputs[input_name].default_value
                                rgb_node = new_rgb_node(mat, color)
                                mat.node_tree.links.new(rgb_node.outputs[0], new_socket)

                        elif input.type == 'VALUE':
                            if input.is_linked:
                                from_socket = input.links[0].from_socket
                                mat.node_tree.links.new(from_socket, new_socket)
                            else:
                                value_node = mat.node_tree.nodes.new(type="ShaderNodeValue")
                                value_node[PRINCIPLED_NODE_TAG] = 1
                                value_node.outputs[0].default_value = node.inputs[input_name].default_value
                                mat.node_tree.links.new(value_node.outputs[0], new_socket)

                        elif input.type == 'VECTOR':
                            if input.is_linked:
                                from_socket = input.links[0].from_socket
                                from_node = from_socket.node
                                if from_node.type == 'NORMAL_MAP':
                                    self.prepare_for_bake(mat, from_socket, new_socket, input_name)

        elif node.type == 'NORMAL_MAP':
            if node.inputs['Color'].is_linked:
                if self.settings.use_normal_strength:
                    color = [0.5, 0.5, 1.0, 1.0]
                    mix_node = new_mixrgb_node(mat, color, color)
                    mix_node[PRINCIPLED_NODE_TAG] = 1
                    mix_node.inputs['Fac'].default_value = node.inputs['Strength'].default_value
                    if node.inputs['Strength'].is_linked:
                        mat.node_tree.links.new(mix_node.inputs['Fac'], node.inputs['Strength'].links[0].from_socket)
                    mat.node_tree.links.new(mix_node.outputs[0], new_socket)
                    new_socket = mix_node.inputs[2]
                from_socket = node.inputs['Color'].links[0].from_socket
                mat.node_tree.links.new(from_socket, new_socket)

        elif node.type == 'BUMP':
            if node.inputs['Height'].is_linked:
                if self.settings.use_bump_strength:
                    math_node = new_math_node(mat, 'MULTIPLY')
                    math_node[PRINCIPLED_NODE_TAG] = 1
                    mat.node_tree.links.new(math_node.inputs[0], node.inputs['Height'].links[0].from_socket)
                    if node.inputs['Strength'].is_linked:
                        mat.node_tree.links.new(math_node.inputs[1], node.inputs['Strength'].links[0].from_socket)
                    else:
                        math_node.inputs[1].default_value = node.inputs['Strength'].default_value
                    mat.node_tree.links.new(math_node.outputs[0], new_socket)
                    new_socket = math_node.inputs[0]

                from_socket = node.inputs['Height'].links[0].from_socket
                mat.node_tree.links.new(from_socket, new_socket)

    def is_input_linked(self, socket, input_name):
        r = False
        if input_name == 'Base Color':
            input_name = 'Color'

        if socket.is_linked:
            node = socket.node

            if socket.type == 'SHADER':
                if node.type == 'OUTPUT_MATERIAL':
                    from_socket = socket.links[0].from_socket
                    r = self.is_input_linked(from_socket, input_name)

                elif node.type == 'REROUTE':
                    from_socket = node.inputs[0].links[0].from_socket
                    r = self.is_input_linked(from_socket, input_name)

                elif node.type == 'MIX_SHADER':
                    for i in range(1, 3):
                        if node.inputs[i].is_linked:
                            from_socket = node.inputs[i].links[0].from_socket
                            if self.is_input_linked(from_socket, input_name):
                                return True

                elif node.type == 'ADD_SHADER':
                    for i in range(0, 2):
                        if node.inputs[i].is_linked:
                            from_socket = node.inputs[i].links[0].from_socket
                            if self.is_input_linked(from_socket, input_name):
                                return True

                elif node.type in ['BSDF_PRINCIPLED', 'BSDF_DIFFUSE', 'BSDF_TRANSLUCENT']:
                    if input_name in ['Bump', 'Normal']:
                        if node.inputs['Normal'].is_linked:
                            from_socket = node.inputs['Normal'].links[0].from_socket
                            r = self.is_input_linked(from_socket, input_name)
                    else:
                        if input_name == 'Color' and node.type == 'BSDF_PRINCIPLED':
                            input_name = 'Base Color'

                        if input_name in node.inputs.keys():
                            if node.inputs[input_name].is_linked:
                                r = True

            elif socket.type == 'VECTOR':
                if input_name == 'Bump':
                    if node.type == 'BUMP':
                        if node.inputs['Height'].is_linked:
                            r = True
                elif input_name == 'Normal':
                    if node.type == 'NORMAL_MAP':
                        if node.inputs['Color'].is_linked:
                            r = True
            return r

    def execute(self, context):
        # scene = context.scene
        self.settings = context.scene.principled_baker_settings
        active_object = context.active_object
        selected_objects = bpy.context.selected_objects

        # bake only works in cycles (for now)
        if not bpy.context.scene.render.engine == 'CYCLES':
            self.report({'ERROR'}, 'Error: Current render engine ({0}) does not support baking'.format(bpy.context.scene.render.engine))
            return {'CANCELLED'}

        # input error handling
        if not active_object.type == 'MESH':
            self.report({'ERROR'}, '{0} is not a mesh object'.format(active_object.name))
            return {'CANCELLED'}
        if self.settings.use_selected_to_active:
            if len(selected_objects) < 2:
                self.report({'ERROR'}, 'Select at least 2 objects!')
                return {'CANCELLED'}
        for obj in selected_objects:
            if not obj.type == 'MESH':
                selected_objects.remove(obj)
                # obj.select = False
                obj.select_set(True)
                # self.report({'ERROR'}, '{0} is not a mesh object'.format(obj.name))
                # return {'CANCELLED'}

        new_images = {}  # {"input_name":image}

        self.joblist = []

        self.new_principled_node_settings = {}

        if self.settings.use_selected_to_active:
            selected_objects.remove(active_object)

        # collect data for later
        material_data = {}  # {material:{socket_to_surface, socket_to_displacement}}
        for obj in selected_objects:
            for mat_slot in obj.material_slots:
                mat = mat_slot.material
                if not 'p_baker_material' in mat.keys():
                    material_output = find_node_by_type(mat, 'OUTPUT_MATERIAL')

                    # error handling
                    if material_output == None:
                        self.report({'ERROR'}, 'Material Output missing in "{0}"'.format(mat.name))
                        if self.settings.use_new_material or self.settings.use_selected_to_active:
                            obj.data.materials.remove(new_mat)
                        return {'CANCELLED'}
                    else:
                        # feeding material_data with data
                        material_data[mat] = {}
                        material_data[mat]['material_output'] = material_output

                        # sockets to Meterial Output to restore links after baking
                        material_data[mat]['socket_to_surface'] = None
                        material_data[mat]['socket_to_displacement'] = None
                        if material_output.inputs['Surface'].is_linked:
                            material_data[mat]['socket_to_surface'] = material_output.inputs['Surface'].links[
                                0].from_socket
                        if material_output.inputs['Displacement'].is_linked:
                            material_data[mat]['socket_to_displacement'] = material_output.inputs['Displacement'].links[
                                0].from_socket

        # prepare materials for baking
        for obj in selected_objects:

            new_images.clear()

            self.joblist.clear()

            # populate joblist
            if self.settings.use_autodetect == True:
                # add to joblist if values differ
                for input_name in PRINCIPLED_INPUTS:
                    if input_name not in self.joblist:
                        if input_name not in ['Bump', 'Subsurface Radius', 'Normal', 'Clearcoat Normal', 'Tangent']:
                            value_list = []
                            for mat_slot in obj.material_slots:
                                mat = mat_slot.material
                                if not 'p_baker_material' in mat.keys():
                                    material_output = find_node_by_type(mat, 'OUTPUT_MATERIAL')
                                    if material_output.inputs['Surface'].is_linked:
                                        socket_to_surface = material_output.inputs['Surface'].links[0].from_socket
                                        value_list.extend(self.get_value_list(socket_to_surface, input_name))
                            if len(value_list) >= 1:
                                if is_list_equal(value_list):
                                    if self.settings.use_new_material or self.settings.use_selected_to_active:
                                        self.new_principled_node_settings[input_name] = value_list[0]
                                else:
                                    self.joblist.append(input_name)

                # add special cases 'Alpha' and 'Displacement' to joblist
                for mat_slot in obj.material_slots:
                    mat = mat_slot.material
                    if not 'p_baker_material' in mat.keys():
                        material_output = find_node_by_type(mat, 'OUTPUT_MATERIAL')

                        if material_output.inputs['Surface'].is_linked:
                            socket_to_surface = material_output.inputs['Surface'].links[0].from_socket
                            if self.has_node_type(mat, socket_to_surface, 'BSDF_TRANSPARENT'):
                                input_name = 'Alpha'
                                if input_name not in self.joblist:
                                    self.joblist.append(input_name)

                            if self.has_node_type(mat, socket_to_surface, 'BSDF_PRINCIPLED'):
                                for input_name in PRINCIPLED_INPUTS:
                                    if self.is_input_linked(socket_to_surface, input_name):
                                        if input_name not in self.joblist:
                                            self.joblist.append(input_name)
                        input_name = 'Displacement'
                        if material_output.inputs[input_name].is_linked:
                            if input_name not in self.joblist:
                                self.joblist.append(input_name)
            else:
                self.fill_joblist()
            if self.settings.use_alpha_to_color:
                if 'Alpha' in self.joblist and not 'Color' in self.joblist:
                    self.joblist.append('Color')
                    print("added Alpha and Color to joblist")
            print(self.joblist)
            # create new mat
            if self.settings.use_new_material or self.settings.use_selected_to_active:
                new_mat_name = active_object.name if self.settings.new_material_prefix == "" else self.settings.new_material_prefix
                has_alpha = True if 'Alpha' in self.joblist else False
                new_mat = self.new_material(new_mat_name, has_alpha)
                if self.settings.use_selected_to_active:
                    active_object.data.materials.append(new_mat)
                else:
                    obj.data.materials.append(new_mat)

            # go through joblist
            for input_name in self.joblist:

                # create image
                suffix = self.get_suffix(input_name)
                prefix = self.settings.image_prefix + obj.name
                image_file_format = IMAGE_FILE_ENDINGS[self.settings.file_format]
                image_file_name = "{0}{1}.{2}".format(prefix, suffix, image_file_format)  # include ending
                image_file_path = self.get_file_path(image_file_name)

                image_is_file = os.path.isfile(image_file_path)

                #                if input_name in ['Alpha', 'Color']:
                if input_name in ['Color']:
                    colorspace = 'sRGB'
                else:
                    colorspace = 'Non-Color'

                if input_name == 'Color' and self.settings.use_alpha_to_color:
                    alpha_channel = 0.0
                elif self.settings.use_alpha:
                    alpha_channel = 0.0
                else:
                    alpha_channel = 1.0

                image_alpha = True if alpha_channel == 0.0 else False

                if input_name == 'Bump':
                    color = (0.5, 0.5, 0.5, alpha_channel)
                else:
                    color = (0.0, 0.0, 0.0, alpha_channel)

                if alpha_channel == 1.0:
                    if input_name in ['Normal', 'Clearcoat Normal', 'Tangent']:
                        color = (0.5, 0.5, 1.0, 1.0)
                    if input_name == 'Bump' and self.settings.use_bump_to_normal:
                        color = (0.5, 0.5, 1.0, 1.0)

                if self.settings.use_overwrite:
                    if image_file_name in bpy.data.images.keys():
                        if image_is_file:
                            image = bpy.data.images[image_file_name]

                            image.use_alpha = self.settings.use_alpha

                            # rescale
                            if not image.size[0] == self.settings.resolution:
                                print("image.size[0]", image.size[0])
                                print("self.settings.resolution", self.settings.resolution)
                                image.scale(self.settings.resolution, self.settings.resolution)
                                print("image.size[0]", image.size[0])
                        else:
                            # new image
                            image = self.new_image(image_file_name, image_alpha)
                            image.colorspace_settings.name = colorspace

                        fill_image(image, color)
                    else:
                        # new image
                        image = self.new_image(image_file_name, image_alpha)
                        image.colorspace_settings.name = colorspace
                        fill_image(image, color)

                elif not self.settings.use_overwrite:
                    if not image_is_file:
                        # new image
                        image = self.new_image(image_file_name, image_alpha)
                        image.colorspace_settings.name = colorspace
                    else:
                        image = bpy.data.images.load(image_file_path, check_existing=False)

                new_images[input_name] = image

                if not self.settings.use_overwrite and image_is_file:
                    # do not bake!
                    self.report({'INFO'}, "baking skipped for '{0}'. File exists.".format(image_file_name))
                else:  # do bake
                    for mat_slot in obj.material_slots:
                        mat = mat_slot.material
                        if not 'p_baker_material' in mat.keys():
                            material_output = find_node_by_type(mat, 'OUTPUT_MATERIAL')

                            # error handling for missing inputs in Material Output
                            if input_name == 'Displacement':
                                if material_output.inputs['Displacement'].is_linked:
                                    socket_to_displacement = material_output.inputs['Displacement'].links[0].from_socket
                            else:
                                if not material_output.inputs['Surface'].is_linked:
                                    self.report({'WARNING'},
                                                'Surface Input missing in Material Output in "{0}"'.format(mat.name))
                                    return {'CANCELLED'}
                                else:
                                    socket_to_surface = material_output.inputs['Surface'].links[0].from_socket

                            # create Diffuse node for baking
                            pb_diffuse_node = self.new_pb_diffuse_node(mat)
                            socket_to_pb_diffuse_node = pb_diffuse_node.inputs['Color']

                            # prepare material for baking
                            if input_name == 'Alpha':
                                node_type = 'BSDF_TRANSPARENT'
                                self.prepare_for_bake_factor(mat, socket_to_surface, socket_to_pb_diffuse_node,
                                                             node_type)
                            elif input_name == 'Displacement':
                                if material_output.inputs['Displacement'].is_linked:
                                    self.prepare_for_bake(mat, socket_to_displacement, socket_to_pb_diffuse_node,
                                                          input_name)
                            else:
                                self.prepare_for_bake(mat, socket_to_surface, socket_to_pb_diffuse_node, input_name)

                            # link pb_diffuse_node to material_output
                            if self.settings.use_bump_to_normal and input_name == 'Bump':
                                socket = pb_diffuse_node.inputs['Color'].links[0].from_socket
                                mat.node_tree.links.new(socket, material_output.inputs['Displacement'])
                            else:
                                mat.node_tree.links.new(pb_diffuse_node.outputs[0], material_output.inputs['Surface'])

                    # create temp image node to bake on
                    if self.settings.use_selected_to_active:
                        bake_image_node = self.new_image_node(new_mat)
                        bake_image_node.color_space = 'COLOR' if colorspace == 'sRGB' else 'NONE'  # 'COLOR' if input_name == 'Color' else 'NONE'
                        bake_image_node.image = image  # add image to node
                        bake_image_node[PRINCIPLED_NODE_TAG] = 1  # tag for clean up
                        # make only bake_image_node active!
                        bake_image_node.select = True
                        new_mat.node_tree.nodes.active = bake_image_node
                    else:
                        for mat_slot in obj.material_slots:
                            mat = mat_slot.material
                            if not 'p_baker_material' in mat.keys():
                                bake_image_node = self.new_image_node(mat)
                                bake_image_node.color_space = 'COLOR' if colorspace == 'sRGB' else 'NONE'  # 'COLOR' if input_name == 'Color' else 'NONE'
                                bake_image_node.image = image  # add image to node
                                bake_image_node[
                                    PRINCIPLED_NODE_TAG] = 1  # tag for clean up
                                # make only bake_image_node active!
                                bake_image_node.select = True
                                mat.node_tree.nodes.active = bake_image_node

                    # bake!
                    self.report({'INFO'}, "baking... '{0}'".format(image.name))

                    if self.settings.use_bump_to_normal and input_name == 'Bump':
                        bake_type = 'NORMAL'
                        pass_filter = set()
                    else:
                        bake_type = 'DIFFUSE'
                        pass_filter = set(['COLOR'])

                    bpy.ops.object.bake(
                        type=bake_type,
                        margin=self.settings.margin,
                        use_clear=False,
                        use_selected_to_active=self.settings.use_selected_to_active,
                        pass_filter=pass_filter)

                    # save image!
                    # self.report({'INFO'}, "saving '{0}' as '{1}'".format(image.name, image_file_name))
                    image.save()

                # clean up!
                # delete all nodes with tag = PRINCIPLED_NODE_TAG
                for mat_slot in obj.material_slots:
                    mat = mat_slot.material
                    for node in mat.node_tree.nodes:
                        if PRINCIPLED_NODE_TAG in node.keys():
                            mat.node_tree.nodes.remove(node)

                if self.settings.use_new_material or self.settings.use_selected_to_active:
                    for node in new_mat.node_tree.nodes:
                        if PRINCIPLED_NODE_TAG in node.keys():
                            new_mat.node_tree.nodes.remove(node)

                # restore links to Material Output
                for mat in material_data:
                    if 'p_baker_material' not in mat.keys():
                        material_output = material_data[mat]['material_output']
                        if not material_data[mat]['socket_to_surface'] == None:
                            mat.node_tree.links.new(material_data[mat]['socket_to_surface'],
                                                    material_output.inputs['Surface'])
                        if material_data[mat]['socket_to_displacement'] == None:
                            if material_output.inputs['Displacement'].is_linked:
                                mat.node_tree.links.remove(material_output.inputs['Displacement'].links[0])
                        else:
                            mat.node_tree.links.new(material_data[mat]['socket_to_displacement'],
                                                    material_output.inputs['Displacement'])

            # add alpha channel to color
            if self.settings.use_alpha_to_color:
                if 'Color' in new_images and 'Alpha' in new_images:
                    combine_images(new_images['Color'], new_images['Alpha'], 0, 3)

            # add new images to new material
            if self.settings.use_new_material:
                self.add_images_to_material(new_mat, new_images)

        # remove tag 'p_baker_material' from new material
        if self.settings.use_new_material or self.settings.use_selected_to_active:
            del new_mat['p_baker_material']

        return {'FINISHED'}
