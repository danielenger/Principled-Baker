from ..nodes.socket_index import *


def duplicate_node(mat, node):

    node_type = str(type(node)).split('.')[-1][:-2]
    new_node = mat.node_tree.nodes.new(type=node_type)

    # copy attributes
    for attr in dir(node):
        try:
            a = getattr(node, attr)
            setattr(new_node, attr, a)
        except AttributeError:
            pass

    # Color Ramp
    if node.type == 'VALTORGB':
        for attr in dir(node.color_ramp):
            try:
                a = getattr(node.color_ramp, attr)
                setattr(new_node.color_ramp, attr, a)
            except AttributeError:
                pass

        for i, col_ramp_elem in enumerate(node.color_ramp.elements):
            try:
                new_node.color_ramp.elements[i].color = col_ramp_elem.color
                new_node.color_ramp.elements[i].position = col_ramp_elem.position
            except IndexError:
                pos = col_ramp_elem.position
                new_elem = new_node.color_ramp.elements.new(pos)
                new_elem.color = col_ramp_elem.color

    # Curve
    if node.type == 'CURVE_RGB':
        for attr in dir(node.mapping):
            try:
                a = getattr(node.mapping, attr)
                setattr(new_node.mapping, attr, a)
            except AttributeError:
                pass

        # copy every point in every curve
        for i, curve in enumerate(node.mapping.curves):
            for j, point in enumerate(curve.points):
                try:
                    new_node.mapping.curves[i].points[j].location = point.location
                    new_node.mapping.curves[i].points[j].handle_type = point.handle_type
                except IndexError:
                    pos = point.location[0]
                    val = point.location[1]
                    new_node.mapping.curves[i].points.new(pos, val)

    # copy values inputs
    for i, input in enumerate(node.inputs):
        try:
            new_node.inputs[i].default_value = input.default_value
        except:
            pass

    # copy values outputs
    for i, output in enumerate(node.outputs):
        try:
            new_node.outputs[i].default_value = output.default_value
        except:
            pass

    return new_node


def duplicate_nodes(mat, nodes, keep_inputs=False):

    new_nodes = {}

    for node in set(nodes):
        new_node = duplicate_node(mat, node)
        new_nodes[node] = new_node

    if keep_inputs:
        for node, new_node in new_nodes.items():
            len_inputs = len(node.inputs)
            if len_inputs > 0:
                for i, input in enumerate(node.inputs):
                    if input.is_linked:
                        link = input.links[0]
                        from_node = link.from_node
                        to_socket = new_node.inputs[i]
                        if from_node in new_nodes.keys():
                            from_socket_index = socket_index(link.from_socket)
                            from_socket = new_nodes[from_node].outputs[from_socket_index]
                        else:
                            from_socket = link.from_socket
                        mat.node_tree.links.new(from_socket, to_socket)

    return list(new_nodes.values())
