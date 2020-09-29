from pathlib import Path

import bpy

from ..const import ALPHA_NODES, NODE_TAG, PB_PACKAGE
from ..functions import get_bake_type_by
from ..nodes.new import new_pb_emission_node, new_pb_output_node
from ..nodes.node import is_node_type_in_node_tree
from ..nodes.outputs import (deactivate_material_outputs,
                                            get_active_output)
from ..prepare.material import (prepare_bake,
                                               prepare_bake_factor,
                                               prepare_material_for_bake)


def prepare_objects_for_bake_matid(objs):

    def create_temp_nodes(mat, color):
        pb_output_node = new_pb_output_node(mat)
        pb_emission_node = new_pb_emission_node(mat, color)

        # activate temp output
        material_output = get_active_output(mat)  # orig mat output
        if material_output:
            material_output.is_active_output = False
        pb_output_node.is_active_output = True

        # link pb_emission_node to material_output
        mat.node_tree.links.new(pb_emission_node.outputs[0],
                                pb_output_node.inputs['Surface'])

    if not isinstance(objs, list):
        objects = [objects]

    materials = []
    for obj in objs:
        for mat_slot in obj.material_slots:
            if mat_slot.material:
                if mat_slot.material not in materials:
                    materials.append(mat_slot.material)

    prefs = bpy.context.preferences.addons[PB_PACKAGE].preferences
    if prefs.mat_id_algorithm == 'HUE':
        from mathutils import Color
        n_materials = len(materials)
        s = prefs.mat_id_saturation
        v = prefs.mat_id_value
        for mat_index, mat in enumerate(materials):
            h = mat_index / n_materials
            c = Color([0, 0, 0])
            c.hsv = h, s, v
            color = c.r, c.g, c.b, 1.0
            create_temp_nodes(mat, color)

    elif prefs.mat_id_algorithm == 'NAME':
        from hashlib import sha1
        for mat in materials:
            s = mat.name.encode('utf-8')
            h = int(sha1(s).hexdigest(), base=16)
            r = h % 256 / 256
            g = (h >> 32) % 256 / 256
            b = (h >> 16) % 256 / 256
            color = r, g, b, 1.0
            create_temp_nodes(mat, color)


def prepare_objects_for_bake_vertex_color(objs, vertex_color_name):
    if not isinstance(objs, list):
        objects = [objects]

    for obj in objs:
        for mat_slot in obj.material_slots:
            if mat_slot.material:
                mat = mat_slot.material

                pb_output_node = new_pb_output_node(mat)
                pb_emission_node = new_pb_emission_node(mat)
                socket_to_pb_emission_node_color = pb_emission_node.inputs['Color']

                # activate temp output
                material_output = get_active_output(mat)
                if material_output:
                    material_output.is_active_output = False
                pb_output_node.is_active_output = True

                attr_node = mat.node_tree.nodes.new(
                    type='ShaderNodeAttribute')
                attr_node[NODE_TAG] = 1  # tag for clean up
                # attr_node.attribute_name = active_vert_col
                attr_node.attribute_name = vertex_color_name
                mat.node_tree.links.new(attr_node.outputs['Color'],
                                        socket_to_pb_emission_node_color)

                # link pb_emission_node to material_output
                mat.node_tree.links.new(pb_emission_node.outputs[0],
                                        pb_output_node.inputs['Surface'])


def prepare_objects_for_bake_wireframe(objs):
    if not isinstance(objs, list):
        objects = [objects]

    for obj in objs:
        for mat_slot in obj.material_slots:
            if mat_slot.material:
                mat = mat_slot.material

                pb_output_node = new_pb_output_node(mat)
                pb_emission_node = new_pb_emission_node(mat)
                socket_to_pb_emission_node_color = pb_emission_node.inputs['Color']

                # activate temp output
                material_output = get_active_output(mat)
                if material_output:
                    material_output.is_active_output = False
                pb_output_node.is_active_output = True

                wf_node = mat.node_tree.nodes.new(type='ShaderNodeWireframe')
                wf_node[NODE_TAG] = 1  # tag for clean up
                settings = bpy.context.scene.principled_baker_settings
                wf_node.inputs[0].default_value = settings.wireframe_size
                wf_node.use_pixel_size = settings.use_pixel_size
                mat.node_tree.links.new(wf_node.outputs[0],
                                        socket_to_pb_emission_node_color)

                # link pb_emission_node to material_output
                mat.node_tree.links.new(pb_emission_node.outputs[0],
                                        pb_output_node.inputs['Surface'])


def prepare_objects_for_bake(objs, jobname):

    def prepare_material(mat):

        # skip already prepared material
        for node in mat.node_tree.nodes:
            if NODE_TAG in node.keys():
                return

        active_output = prepare_material_for_bake(mat)

        # Deselect all nodes
        for node in mat.node_tree.nodes:
            node.select = False

        # temp nodes
        for node in mat.node_tree.nodes:
            if node.type == "OUTPUT_MATERIAL" and NODE_TAG in node.keys():
                material_output = node
        pb_output_node = new_pb_output_node(mat)
        pb_emission_node = new_pb_emission_node(mat, [1, 1, 1, 1])
        pb_output_node.location.x = active_output.location.x
        pb_emission_node.location.x = active_output.location.x

        socket_to_pb_emission_node_color = pb_emission_node.inputs['Color']

        # activate temp output and deactivate others
        deactivate_material_outputs(mat)
        pb_output_node.is_active_output = True

        socket_to_surface = material_output.inputs['Surface'].links[0].from_socket
        bake_type = get_bake_type_by(jobname)

        if bake_type == 'EMIT':
            if jobname in ALPHA_NODES.keys():
                prepare_bake_factor(
                    mat, socket_to_surface, socket_to_pb_emission_node_color, ALPHA_NODES[jobname], 'Fac')

            elif jobname == 'Alpha':
                if is_node_type_in_node_tree(mat, material_output, 'BSDF_TRANSPARENT'):
                    prepare_bake_factor(
                        mat, socket_to_surface, socket_to_pb_emission_node_color, 'BSDF_TRANSPARENT', 'Fac')
                else:
                    prepare_bake(mat, socket_to_surface,
                                 socket_to_pb_emission_node_color, 'Alpha')

            elif jobname == 'Displacement':
                if material_output.inputs['Displacement'].is_linked:
                    socket_to_displacement = material_output.inputs[
                        'Displacement'].links[0].from_socket
                    node = material_output.inputs['Displacement'].links[0].from_node
                    if node.type == 'DISPLACEMENT':
                        prepare_bake(mat, socket_to_displacement,
                                     socket_to_pb_emission_node_color, 'Height')
                    else:
                        from_socket = socket_to_displacement.links[0].from_socket
                        mat.node_tree.links.new(from_socket,
                                                socket_to_pb_emission_node_color)

            elif jobname == 'Bump':
                prepare_bake(mat, socket_to_surface,
                             socket_to_pb_emission_node_color, 'Height')
            elif jobname == 'Ambient Occlusion':
                prepare_bake(mat, socket_to_surface,
                             socket_to_pb_emission_node_color, 'Ambient Occlusion')
            else:
                prepare_bake(mat, socket_to_surface,
                             socket_to_pb_emission_node_color, jobname)

            # link pb_emission_node to material_output
            mat.node_tree.links.new(pb_emission_node.outputs[0],
                                    pb_output_node.inputs['Surface'])

        # put temp nodes in a frame
        p_baker_frame = mat.node_tree.nodes["p_baker_temp_frame"]
        for node in mat.node_tree.nodes:
            if NODE_TAG in node.keys():
                node.parent = p_baker_frame

    if not isinstance(objs, list):
        objs = [objs]

    for obj in objs:
        for mat_slot in obj.material_slots:
            if mat_slot.material:
                mat = mat_slot.material
                if jobname not in {"Emission", "Normal"}:
                    prepare_material(mat)
