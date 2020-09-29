import bpy

from ..const import ALPHA_NODES, NODE_TAG, NORMAL_INPUTS
from ..nodes.duplicate import duplicate_nodes
from ..nodes.new import new_mixrgb_node, new_rgb_node
from ..nodes.node import (get_all_nodes_linked_from,
                                         is_mixnode_in_node_tree,
                                         is_node_type_in_node_tree)
from ..nodes.outputs import get_active_output
from ..nodes.ungroup import ungroup_nodes


def prepare_bake_factor(mat, socket, new_socket, node_type, factor_name='Fac'):
    node = socket.node
    if node.type == node_type:
        to_node = node.outputs[0].links[0].to_node
        if factor_name in to_node.inputs.keys():
            socket = to_node.inputs[factor_name]
            prepare_bake(mat, socket, new_socket, factor_name)
    else:
        for input_socket in node.inputs:
            if input_socket.is_linked:
                from_socket = input_socket.links[0].from_socket
                prepare_bake_factor(
                    mat, from_socket, new_socket, node_type, factor_name)


def prepare_bake_ao(mat, socket, new_socket):

    node = socket.node

    if node.type == 'MIX_RGB':
        if node.inputs[1].is_linked and node.inputs[2].is_linked:
            from_node_1 = node.inputs[1].links[0].from_node
            from_node_2 = node.inputs[2].links[0].from_node
            is_ao_in_1 = is_node_type_in_node_tree(mat,
                                                   from_node_1, 'AMBIENT_OCCLUSION')
            is_ao_in_2 = is_node_type_in_node_tree(mat,
                                                   from_node_2, 'AMBIENT_OCCLUSION')
            if is_ao_in_1 and is_ao_in_2:
                from_socket = socket
                mat.node_tree.links.new(from_socket, new_socket)
                return

    if is_node_type_in_node_tree(mat, node, 'AMBIENT_OCCLUSION'):
        if not is_mixnode_in_node_tree(node):
            if not socket.type == 'SHADER':
                from_socket = socket
                mat.node_tree.links.new(from_socket, new_socket)
            else:
                for input_socket in node.inputs:
                    if input_socket.is_linked:
                        from_socket = input_socket.links[0].from_socket
                        prepare_bake_ao(mat, from_socket, new_socket)
        else:
            for input_socket in node.inputs:
                if input_socket.is_linked:
                    from_socket = input_socket.links[0].from_socket
                    prepare_bake_ao(mat, from_socket, new_socket)
    else:
        for input_socket in node.inputs:
            if input_socket.is_linked:
                from_socket = input_socket.links[0].from_socket
                prepare_bake_ao(mat, from_socket, new_socket)


def prepare_bake_color(mat, from_socket, new_socket):
    node = from_socket.node

    # find and unlink AO trees in tagged nodes
    for node in mat.node_tree.nodes:
        if node.type == 'MIX_RGB' and NODE_TAG in node.keys():
            for i, node_input in enumerate(node.inputs[1:]):
                if node_input.is_linked:
                    from_node = node_input.links[0].from_node
                    if not is_mixnode_in_node_tree(from_node):
                        if is_node_type_in_node_tree(mat, from_node, 'AMBIENT_OCCLUSION'):
                            mat.node_tree.links.remove(node_input.links[0])

                            # if 'Fac' not linked, set to 0 or 1
                            fac_in = node.inputs[0]
                            if not fac_in.is_linked:
                                fac_in.default_value = 0 if i == 1 else 1

    mat.node_tree.links.new(from_socket, new_socket)


def prepare_bake(mat, socket, new_socket, input_socket_name):
    settings = bpy.context.scene.principled_baker_settings

    if input_socket_name in NORMAL_INPUTS:
        color = (0.5, 0.5, 1.0, 1.0)
    else:
        color = (0, 0, 0, 0)

    node = socket.node

    if node.type == 'OUTPUT_MATERIAL':
        from_socket = socket.links[0].from_socket
        prepare_bake(mat, from_socket, new_socket, input_socket_name)

    elif node.type == 'MIX_SHADER':
        color2 = [1, 1, 1, 0] if input_socket_name == 'Fac' else color
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
                if settings.use_exclude_transparent_colors:
                    if next_node.type in ALPHA_NODES.values() or next_node.type == 'BSDF_TRANSPARENT':
                        other_i = i % 2 + 1
                        mix_node.inputs[i].default_value = (0, 0, 0, 0)
                        mix_node.inputs[other_i].default_value = (1, 1, 1, 0)
                        if node.inputs[other_i].is_linked:
                            from_socket = node.inputs[other_i].links[0].from_socket
                            new_socket = mix_node.inputs[i]
                    else:
                        from_socket = node.inputs[i].links[0].from_socket
                        new_socket = mix_node.inputs[i]
                    prepare_bake(mat, from_socket, new_socket,
                                 input_socket_name)

    elif node.type == 'ADD_SHADER' and not input_socket_name == 'Fac':
        mix_node = new_mixrgb_node(mat, 1, color, color)
        mix_node.blend_type = 'ADD'
        mat.node_tree.links.new(mix_node.outputs[0], new_socket)
        mix_node.label = input_socket_name

        for i, input in enumerate(node.inputs):
            if input.is_linked:
                from_socket = input.links[0].from_socket
                new_socket = mix_node.inputs[i + 1]
                prepare_bake(mat, from_socket, new_socket, input_socket_name)

    # exclude some colors from color
    elif node.type in {'EMISSION'}:
        return
    else:
        if node.type == 'BSDF_PRINCIPLED' and input_socket_name == 'Color':
            input_socket_name = 'Base Color'

        if input_socket_name == 'Ambient Occlusion':
            # AO: remove all non-ao branches
            for tmp_node in mat.node_tree.nodes:
                if tmp_node.type == 'MIX_RGB' and NODE_TAG in tmp_node.keys():
                    for i, node_input in enumerate(tmp_node.inputs[1:]):
                        if node_input.is_linked:
                            from_node = node_input.links[0].from_node
                            if not is_node_type_in_node_tree(mat, from_node, 'AMBIENT_OCCLUSION'):
                                mat.node_tree.links.remove(node_input.links[0])

                                # if 'Fac' not linked, set to 0 or 1
                                fac_in = tmp_node.inputs[0]
                                if not fac_in.is_linked:
                                    fac_in.default_value = 0 if i == 1 else 1

                    # if Colors not linked, set to white
                    white = [1, 1, 1, 1]
                    col1_in = tmp_node.inputs[1]
                    col2_in = tmp_node.inputs[2]
                    if not col1_in.is_linked:
                        col1_in.default_value = white
                    if not col2_in.is_linked:
                        col2_in.default_value = white

            # AO: link ao branch
            for input_socket in node.inputs:
                if input_socket.type == 'RGBA':
                    if input_socket.is_linked:
                        from_node = input_socket.links[0].from_node
                        if is_node_type_in_node_tree(mat, from_node, 'AMBIENT_OCCLUSION'):
                            from_socket = input_socket.links[0].from_socket
                            mat.node_tree.links.new(from_socket, new_socket)

        elif input_socket_name in node.inputs.keys():
            input_socket = node.inputs[input_socket_name]

            if input_socket.type == 'RGBA':
                if input_socket.is_linked:
                    o = input_socket.links[0].from_socket
                    prepare_bake_color(mat, o, new_socket)
                else:
                    color = node.inputs[input_socket_name].default_value
                    rgb_node = new_rgb_node(mat, color)
                    mat.node_tree.links.new(rgb_node.outputs[0], new_socket)

            elif input_socket.type == 'VALUE':
                if input_socket.is_linked:
                    from_socket = input_socket.links[0].from_socket
                    if from_socket.type == 'VALUE':
                        mat.node_tree.links.new(from_socket, new_socket)
                    else:  # RGB to BW
                        node = mat.node_tree.nodes.new(
                            type="ShaderNodeRGBToBW")
                        node[NODE_TAG] = 1
                        mat.node_tree.links.new(from_socket, node.inputs[0])
                        mat.node_tree.links.new(node.outputs[0], new_socket)
                else:
                    value_node = mat.node_tree.nodes.new(
                        type="ShaderNodeValue")
                    value_node[NODE_TAG] = 1
                    value_node.outputs[0].default_value = node.inputs[input_socket_name].default_value
                    mat.node_tree.links.new(value_node.outputs[0], new_socket)

            elif input_socket.type == 'VECTOR':
                if input_socket.name == input_socket_name:
                    if input_socket.is_linked:
                        from_socket = input_socket.links[0].from_socket
                        mat.node_tree.links.new(from_socket, new_socket)

        else:
            for input_socket in node.inputs:
                if input_socket.is_linked:
                    from_socket = input_socket.links[0].from_socket
                    prepare_bake(mat, from_socket, new_socket,
                                 input_socket_name)


def prepare_material_for_bake(mat, do_ungroup_values=True):

    # Duplicate node tree from active output
    active_output = get_active_output(mat)
    selected_nodes = get_all_nodes_linked_from(active_output)
    selected_nodes = duplicate_nodes(mat, selected_nodes, keep_inputs=True)

    # TAG all selected nodes for clean up
    for node in selected_nodes:
        node[NODE_TAG] = 1

    # Ungroup all groups in selected nodes
    group_nodes = [n for n in selected_nodes if n.type == 'GROUP']
    selected_nodes = ungroup_nodes(
        mat, group_nodes, do_ungroup_values=do_ungroup_values)

    # TAG all selected nodes for clean up
    for node in selected_nodes:
        node[NODE_TAG] = 1

    # put temp nodes in frame
    p_baker_frame = mat.node_tree.nodes.new(type="NodeFrame")
    for node in mat.node_tree.nodes:
        if NODE_TAG in node.keys():
            node.parent = p_baker_frame
    p_baker_frame.name = "p_baker_temp_frame"
    p_baker_frame.label = "PRINCIPLED BAKER NODES (If you see this, something went wrong!)"
    p_baker_frame.use_custom_color = True
    p_baker_frame.color = (1, 0, 0)
    p_baker_frame[NODE_TAG] = 1
    p_baker_frame.label_size = 64

    new_output = None
    for node in mat.node_tree.nodes:
        if NODE_TAG in node.keys() and node.type == "OUTPUT_MATERIAL":
            new_output = node
            new_output.is_active_output = True
    return new_output
