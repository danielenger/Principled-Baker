
def get_value_from_node_by_name(node, value_name):
    tmp_value_name = value_name
    if value_name == 'Color' and node.type == 'BSDF_PRINCIPLED':
        tmp_value_name = "Base Color"

    if tmp_value_name in node.inputs.keys():
        if node.inputs[tmp_value_name].type == 'RGBA':
            r, g, b, a = node.inputs[tmp_value_name].default_value
            return [r, g, b, a]
        else:
            return node.inputs[value_name].default_value
