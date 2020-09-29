def get_all_nodes_linked_from(node):
    nodes = []

    def linked_from(node):
        if node:
            nodes.append(node)
            for input_socket in node.inputs:
                if input_socket.is_linked:
                    from_node = input_socket.links[0].from_node
                    linked_from(from_node)
    linked_from(node)
    return nodes


def is_mixnode_in_node_tree(node):
    """return True only if mix node is higher in tree"""
    
    node_type = 'MIX_RGB'
    if node.type == node_type:
        return True
    elif node.type == 'AMBIENT_OCCLUSION':
        return False
    else:
        for input_socket in node.inputs:
            if input_socket.is_linked:
                from_node = input_socket.links[0].from_node
                if is_mixnode_in_node_tree(from_node):
                    return True
        return False


def are_nodes_connected(node, to_node):
    if node == to_node:
        return True
    for output_socket in node.outputs:
        if output_socket.is_linked:
            to_node_tmp = output_socket.links[0].to_node
            return are_nodes_connected(to_node_tmp, to_node)


def get_sibling_node(node):
    if node.outputs[0].is_linked:
        parent_node = node.outputs[0].links[0].to_node
        for input_socket in parent_node.inputs:
            if input_socket.is_linked:
                child_node = input_socket.links[0].from_node
                if not child_node == node:
                    if input_socket.type == node.outputs[0].links[0].to_socket.type:
                        return child_node


def is_node_type_in_node_tree(material, node, node_type):
    for n in material.node_tree.nodes:
        if n.type == node_type:
            if are_nodes_connected(n, node):
                return True
