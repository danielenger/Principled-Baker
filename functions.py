import bpy

from .const import NORMAL_INPUTS, NOT_ALLOWED_SIGNS
from .nodes.find import find_node_by_type


def is_list_equal(list):
    """:returns: True, if all items in list are equal"""

    if not list:
        return False  # False, if list is empty
    first = list[0]
    return all(first == item for item in list[1:])


def get_only_meshes(objects) -> list:
    l = []
    for o in objects:
        if o.type == 'MESH':
            l.append(o)
    return l


def get_bake_type_by(jobname) -> str:
    if jobname in NORMAL_INPUTS:
        return 'NORMAL'
    if jobname in {'Diffuse'}:
        return 'DIFFUSE'
    else:
        return 'EMIT'


def remove_not_allowed_signs(string) -> str:
    """
    :returns: String (eg. from object name) 
    without all signs not allowed in file names and paths.
    """

    for s in NOT_ALLOWED_SIGNS:
        string = string.replace(s, "")
    return string
