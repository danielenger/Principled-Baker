import bpy

from .const import ALPHA_NODES, BSDF_NODES, MATERIAL_TAG, NODE_INPUTS, NODE_TAG
from .functions import is_list_equal
from .material import has_material
from .material.has_material import has_material
from .nodes.delete_tagged import delete_tagged_nodes_in_object
from .nodes.node import are_nodes_connected, is_node_type_in_node_tree
from .nodes.value_list import get_value_from_node_by_name
from .prepare.material import prepare_material_for_bake


def get_value_list_from_bsdf_nodes_in_material(material, node, value_name) -> list:
    value_list = []
    for n in material.node_tree.nodes:
        if n.type in BSDF_NODES:
            if are_nodes_connected(n, node):
                val = get_value_from_node_by_name(n, value_name)
                if val is not None:
                    value_list.append(val)
    return value_list


def get_joblist_by_bake_list() -> list:
    joblist = list()

    bakelist = bpy.context.scene.principled_baker_bakelist
    for jobname, data in bakelist.items():
        if data.do_bake:
            joblist.append(jobname)

    return joblist


def get_joblist_by_additional_bake_types() -> list:
    """To extend the joblist by user settings:

    Diffuse, Glossiness, Bump, Material ID, Wireframe
    """

    settings = bpy.context.scene.principled_baker_settings
    joblist = []
    if settings.use_Diffuse:
        joblist.append("Diffuse")
    if settings.use_invert_roughness:
        joblist.append("Roughness")
    if settings.use_Bump:
        joblist.append("Bump")
    if settings.use_material_id:
        joblist.append("Material ID")
    if settings.use_wireframe:
        joblist.append("Wireframe")
    return joblist


def get_vertex_colors_to_bake_from_objects(objs) -> list:
    settings = bpy.context.scene.principled_baker_settings
    vert_col_names = []

    if settings.use_vertex_color:
        vert_col_names = []
        for obj in objs:
            if len(obj.data.vertex_colors) == 0:
                continue

            if settings.bake_vertex_colors == 'ALL':
                for vcol in obj.data.vertex_colors:
                    vert_col_names.append(vcol.name)
            elif settings.bake_vertex_colors == 'SELECTED':
                vert_col_names.append(obj.data.vertex_colors.active.name)
            elif settings.bake_vertex_colors == 'ACTIVE_RENDER':
                for _, v_col in obj.data.vertex_colors.items():
                    if v_col.active_render:
                        vert_col_names.append(v_col.name)
                        break
            else:
                index = int(settings.bake_vertex_colors) - 1
                if index < len(obj.data.vertex_colors):
                    vert_col_names.append(
                        obj.data.vertex_colors[index].name)

    return vert_col_names


def get_joblist_by_value_differ_from_objects(objs) -> list:
    # settings = bpy.context.scene.principled_baker_settings
    joblist = list()

    for value_name in NODE_INPUTS:
        value_list = list()
        if value_name not in joblist and value_name not in {'Subsurface Radius', 'Normal', 'Clearcoat Normal', 'Tangent'}:
            for obj in objs:
                for mat_slot in obj.material_slots:
                    if mat_slot.material:
                        mat = mat_slot.material

                    material_output = None
                    for node in mat.node_tree.nodes:
                        if node.type == "OUTPUT_MATERIAL" and NODE_TAG in node.keys():
                            material_output = node

                    if material_output:
                        value_list.extend(get_value_list_from_bsdf_nodes_in_material(
                            mat, material_output, value_name))
            if value_list:
                if not is_list_equal(value_list):
                    joblist.append(value_name)

    return joblist


def get_joblist_by_connected_inputs_from_objects(objs) -> list:
    settings = bpy.context.scene.principled_baker_settings
    joblist = list()

    # search material for jobs by connected node types
    for obj in objs:
        for mat_slot in obj.material_slots:
            if mat_slot.material:
                mat = mat_slot.material

                if MATERIAL_TAG not in mat_slot.material.keys():
                    material_output = None
                    for node in mat.node_tree.nodes:
                        if node.type == "OUTPUT_MATERIAL" and NODE_TAG in node.keys():
                            material_output = node

                    if material_output:
                        # add special cases:
                        # Alpha node: Transparent
                        if is_node_type_in_node_tree(mat, material_output, 'BSDF_TRANSPARENT'):
                            # if not 'Alpha' in joblist:
                            joblist.append('Alpha')

                        # Alpha for nodes: Translucent, Glass
                        for alpha_name, n_type in ALPHA_NODES.items():
                            if is_node_type_in_node_tree(mat, material_output, n_type):
                                # if not alpha_name in joblist:
                                joblist.append(alpha_name)

                        # Emission
                        if is_node_type_in_node_tree(mat, material_output, 'EMISSION'):
                            # if not 'Emission' in joblist:
                            joblist.append('Emission')

                        # AO
                        if is_node_type_in_node_tree(mat, material_output, 'AMBIENT_OCCLUSION'):
                            # if not 'Ambient Occlusion' in joblist:
                            joblist.append('Ambient Occlusion')

                        # Displacement
                        socket_name = 'Displacement'
                        if material_output.inputs[socket_name].is_linked:
                            joblist.append(socket_name)

                        # Bump
                        socket_name = 'Bump'
                        if settings.use_Bump and is_node_type_in_node_tree(mat, material_output, 'BUMP'):
                            if socket_name not in joblist:
                                joblist.append(socket_name)

                        # BSDF nodes
                        for node in mat.node_tree.nodes:
                            if NODE_TAG in node.keys():
                                if node.type in BSDF_NODES:
                                    for socket in node.inputs:
                                        socket_name = socket.name
                                        if socket_name in NODE_INPUTS + ['Base Color']:
                                            if socket.is_linked:
                                                if are_nodes_connected(node, material_output):
                                                    socket_name = 'Color' if socket_name == 'Base Color' else socket_name
                                                    # if not socket_name in joblist:
                                                    joblist.append(socket_name)

    return joblist


def get_joblist_by_autodetection_from_objects(objs) -> list:

    joblist = []

    # Prepare materials - see clean up!
    materials = []
    for obj in objs:
        for mat_slot in obj.material_slots:
            if mat_slot.material:
                materials.append(mat_slot.material)
    materials = set(materials)
    for mat in materials:
        prepare_material_for_bake(mat, do_ungroup_values=False)

    settings = bpy.context.scene.principled_baker_settings
    if settings.use_value_differ:
        joblist.extend(get_joblist_by_value_differ_from_objects(objs))

    if settings.use_connected_inputs:
        joblist.extend(get_joblist_by_connected_inputs_from_objects(objs))

    # Clean up! - delete temp nodes
    for obj in objs:
        delete_tagged_nodes_in_object(obj)

    return joblist


def get_joblist_from_objects(objs) -> list:
    settings = bpy.context.scene.principled_baker_settings
    joblist = []

    # if one object has no material, the joblist has only "Normal"!
    if settings.bake_mode == 'SELECTED_TO_ACTIVE':
        for obj in objs:
            if not has_material(obj):
                joblist.append("Normal")
                return joblist

    if settings.use_autodetect:
        joblist.extend(get_joblist_by_autodetection_from_objects(objs))

    # force bake of Color, if user wants alpha in color
    if settings.use_alpha_to_color and settings.color_mode == 'RGBA':
        joblist.append('Color')
        joblist.append('Alpha')

    if not settings.use_autodetect:
        joblist.extend(get_joblist_by_bake_list())

    joblist.extend(get_joblist_by_additional_bake_types())

    if settings.use_vertex_color:
        joblist.append("Vertex Color")

    joblist = list(set(joblist))

    return joblist
