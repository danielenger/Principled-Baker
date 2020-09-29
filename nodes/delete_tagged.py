from ..const import NODE_TAG


def delete_tagged_nodes(material):
    for node in material.node_tree.nodes:
        if NODE_TAG in node.keys():
            material.node_tree.nodes.remove(node)


def delete_tagged_nodes_in_object(obj):
    for mat_slot in obj.material_slots:
        if mat_slot.material:
            delete_tagged_nodes(mat_slot.material)
