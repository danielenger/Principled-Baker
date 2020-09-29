import bpy
from bpy.props import (BoolProperty, EnumProperty, FloatProperty, IntProperty,
                       StringProperty)
from bpy.types import PropertyGroup


def color_mode_items(scene, context):
    if scene.file_format in ['PNG', 'TARGA', 'TIFF', 'OPEN_EXR']:
        items = [
            ('RGB', "RGB", ""),
            ('RGBA', "RGBA", ""),
            # ('BW', "BW", ""),  # TODO reenable and auto set to RGB/RGBA, if needed
        ]
    else:
        items = [
            ('BW', "BW", ""),
            ('RGB', "RGB", "")
        ]
    return items


def color_depth_individual_items(scene, context):
    if scene.file_format == 'OPEN_EXR':
        items = [
            ('16', "Float (Half)", ""),
            ('32', "Float (Full)", ""),
            ('INDIVIDUAL', "Individual", ""),
        ]
    else:
        items = [
            ('8', "8", ""),
            ('16', "16", ""),
            ('INDIVIDUAL', "Individual", ""),
        ]
    return items


def color_depth_items(scene, context):
    if scene.file_format == 'OPEN_EXR':
        items = [
            ('16', "Float (Half)", ""),
            ('32', "Float (Full)", ""),
        ]
    else:
        items = [
            ('8', "8", ""),
            ('16', "16", ""),
        ]
    return items


def reset_bake_list(context, value):
    bpy.ops.principled_baker_bakelist.update()


class PBAKER_settings(PropertyGroup):

    file_format: EnumProperty(
        name="File Format",
        items=(
            ('PNG', 'PNG', ''),
            ('BMP', 'BMP', ''),
            ('JPEG', 'JPEG', ''),
            ('TIFF', 'TIFF', ''),
            ('TARGA', 'Targa', ''),
            ('OPEN_EXR', 'OpenEXR', ''),
        ),
        default='PNG'
    )

    color_mode: EnumProperty(
        name="Color",
        items=color_mode_items
    )

    color_depth: EnumProperty(
        name="Color Depth",
        items=color_depth_individual_items
    )

    compression: IntProperty(
        name="Quality",
        default=15,
        min=0,
        soft_max=100,
        step=1,
        subtype='PERCENTAGE'
    )

    exr_codec: EnumProperty(
        name="Codec",
        items=(
            ('NONE', 'None', ''),
            ('PXR24', 'Pxr24 (lossy)', ''),
            ('ZIP', 'ZIP (lossless)', ''),
            ('PIZ', 'PIZ (lossless)', ''),
            ('RLE', 'RLE (lossless)', ''),
            ('ZIPS', 'ZIPS (lossless)', ''),
            ('DWAA', 'DWAA (lossy)', ''),
        ),
        default='ZIP'
    )

    tiff_codec: EnumProperty(
        name="Compression",
        items=(
            ('NONE', 'None', ''),
            ('DEFLATE', 'Deflate', ''),
            ('LZW', 'LZW', ''),
            ('PACKBITS', 'Packbits', '')
        ),
        default='DEFLATE'
    )

    quality: IntProperty(
        name="Quality",
        default=90,
        min=0,
        soft_max=100,
        step=1,
        subtype='PERCENTAGE'
    )

    use_autodetect: BoolProperty(
        name="Autodetect",
        description="Bake linked inputs and/or inputs with values that differ in different Shader nodes.\n\nThis depends on the selected Detection Options",
        default=True
    )

    image_prefix: StringProperty(
        name="Prefix",
        maxlen=1024,
    )

    use_object_name: BoolProperty(
        name="Object Name",
        description="Use Object Name as part of Texture Name to get unique names",
        default=True
    )

    use_first_material_name: BoolProperty(
        name="First Material Name as (second) Prefix",
        description="Use first material name as prefix.",
        default=False
    )

    image_suffix_settings_show: BoolProperty(
        name="Suffix Settings",
        default=True
    )

    custom_resolution: IntProperty(
        name="Resolution",
        default=1024,
        min=1,
        soft_max=8 * 1024
    )
    resolution: EnumProperty(
        name="Resolution",
        items=(
            ('CUSTOM', 'Custom', ''),
            ('512', '512', ''),
            ('1024', '1024', ''),
            ('2048', '2048', ''),
            ('4096', '4096', ''),
        ),
        default='1024'
    )

    margin: IntProperty(
        name="Margin",
        default=0,
        min=0,
        max=64
    )

    # removed. now part of bake list
    samples: IntProperty(
        name="Samples",
        default=128,
        min=1
    )
    individual_samples: BoolProperty(
        name="Individual Samples",
        default=False,
    )

    use_overwrite: BoolProperty(
        name="Overwrite",
        description="Be careful with Overwrite! It does what it says!",
        default=False
    )

    use_alpha: BoolProperty(
        name="Image Alpha",
        default=False
    )

    suffix_color: StringProperty(
        name="Color",
        default="_color",
        maxlen=1024,
    )
    suffix_metallic: StringProperty(
        name="Metallic",
        default="_metal",
        maxlen=1024,
    )
    suffix_roughness: StringProperty(
        name="Roughness",
        default="_roughness",
        maxlen=1024,
    )
    suffix_glossiness: StringProperty(
        name="Glossiness",
        default="_glossiness",
        maxlen=1024,
    )

    suffix_specular: StringProperty(
        name="Specular ",
        default="_specular",
        maxlen=1024,
    )
    use_invert_roughness: BoolProperty(
        name="Glossiness",
        description="Glossiness from inverted Roughness.\n\nBakes Roughness texture and inverts the image.",
        default=False
    )

    suffix_normal: StringProperty(
        name="Normal",
        default="_normal",
        maxlen=1024,
    )
    suffix_bump: StringProperty(
        name="Bump (Height)",
        default="_bump",
        maxlen=1024,
    )
    suffix_displacement: StringProperty(
        name="Displacement",
        default="_displacement",
        maxlen=1024,
    )
    suffix_vertex_color: StringProperty(
        name="Vertex Color",
        default="_vertex",
        maxlen=1024,
    )
    suffix_material_id: StringProperty(
        name="Material ID",
        default="_MatID",
        maxlen=1024,
    )
    suffix_diffuse: StringProperty(
        name="Diffuse",
        default="_diffuse",
        maxlen=1024,
    )
    suffix_wireframe: StringProperty(
        name="Wireframe",
        default="_wireframe",
        maxlen=1024,
    )

    samples_bump: IntProperty(
        name="Bump (Height)",
        default=128,
        min=1
    )
    samples_vertex_color: IntProperty(
        name="Vertex Color",
        default=128,
        min=1
    )
    samples_material_id: IntProperty(
        name="Material ID",
        default=128,
        min=1
    )
    samples_diffuse: IntProperty(
        name="Diffuse",
        default=128,
        min=1
    )
    samples_wireframe: IntProperty(
        name="Wireframe",
        default=128,
        min=1
    )

    color_depth_diffuse: EnumProperty(
        name="Diffuse Color Depth",
        items=color_depth_items
    )
    color_depth_bump: EnumProperty(
        name="Bump (Height) Color Depth",
        items=color_depth_items
    )
    color_depth_vertex_color: EnumProperty(
        name="Vertex Color Color Depth",
        items=color_depth_items
    )
    color_depth_material_id: EnumProperty(
        name="Material ID Color Depth",
        items=color_depth_items
    )
    color_depth_diffuse: EnumProperty(
        name="Diffuse Color Depth",
        items=color_depth_items
    )
    color_depth_wireframe: EnumProperty(
        name="Wireframe Color Depth",
        items=color_depth_items
    )

    file_path: StringProperty(
        name="",
        description="directory for textures output",
        default="//",
        # maxlen=1024,
        subtype='DIR_PATH'
    )

    use_texture_folder: BoolProperty(
        name="Texture Folder",
        description="""Create a texture directory per object named by objects.
        \nCombined or Selected to Active: Folder named by active object.\nSingle/Batch: Folder(s) named by object(s)""",
        default=False
    )

    use_batch: BoolProperty(
        name="Single/Batch",
        default=False
    )

    use_selected_to_active: BoolProperty(
        name="Selected to Active",
        default=False
    )

    bake_mode: EnumProperty(
        name="Bake Mode",
        items=(
            ('COMBINED', 'Combined', 'Bake a single selected object or bake multiple objects with shared UV maps.\n\nThis is like Blenders default bake'),
            ('BATCH', 'Single/Batch', 'Bake every selected object separately.'),
            ('SELECTED_TO_ACTIVE', 'Selected to Active', ''),
        ),
        default='COMBINED'
    )

    make_new_material: BoolProperty(
        name="Create New Material",
        description="Create new materials",
        default=False
    )
    add_new_material: BoolProperty(
        name="Add New Material",
        description="Add new material to selected objects.\nIf Selected to Active is active, a new material will be added to active object",
        default=False
    )

    new_material_prefix: StringProperty(
        name="Material Name",
        description="New Material Name. If empty, Material will have name of Object",
        default="",
        maxlen=1024,
    )

    use_bake_bump: BoolProperty(
        name="Bake Bump (Height)",
        description="Bake Bump Map from Bump node Height input",
        default=False
    )
    use_alpha_to_color: BoolProperty(
        name="Alpha channel to Color",
        description="Add alpha channel to Color Texture",
        default=False
    )
    use_exclude_transparent_colors: BoolProperty(
        name="Exclude Transparent Colors",
        description="Exclude colors from nodes with transparency from Color Texture",
        default=True
    )

    use_smart_uv_project: BoolProperty(
        name="Auto Smart UV Project",
        description="",
        default=False
    )

    auto_uv_project: EnumProperty(
        name="Auto UV Project",
        items=(
            ('OFF', 'Off', ''),
            ('SMART', 'Smart UV Project', ''),
            ('LIGHTMAP', 'Lightmap Pack', ''),
        ),
        default='OFF'
    )
    new_uv_map: BoolProperty(
        name="New UV Map",
        default=False,
        description="Add a new UV Map and select.\nIf object has 8 UV maps, no UV map will be added and the selected UV map will not be altered"
    )

    # Smart UV Project:
    angle_limit: FloatProperty(
        name="Angle Limit",
        default=66.0,
        min=1.0,
        max=89.0
    )
    island_margin: FloatProperty(
        name="Island Margin",
        default=0.0,
        min=0.0,
        max=1.0
    )
    user_area_weight: FloatProperty(
        name="Area Weight",
        default=0.0,
        min=0.0,
        max=1.0
    )
    use_aspect: BoolProperty(
        name="Correct Aspect",
        default=True
    )
    stretch_to_bounds: BoolProperty(
        name="Stretch to UV Bounds",
        default=True
    )

    # Lightmap Pack:
    share_tex_space: BoolProperty(
        name="Share Tex Space",
        default=True
    )
    new_image: BoolProperty(
        name="New Image",
        default=False
    )
    image_size: IntProperty(
        name="Image Size",
        default=512,
        min=64,
        max=5000
    )
    pack_quality: IntProperty(
        name="Pack Quality",
        default=12,
        min=1,
        max=48
    )
    lightmap_margin: FloatProperty(
        name="Margin",
        default=0.10,
        min=0.0,
        max=1.0
    )

    use_image_float: BoolProperty(
        name="32 bit float",
        default=False
    )

    suffix_text_mod: EnumProperty(
        name="Convert suffix",
        items=(
            ('CUSTOM', 'Custom', ''),
            ('lower', 'Lower', 'Convert suffix to lowercase letters.'),
            ('upper', 'Upper', 'Convert suffix to capital letters.'),
            ('title', 'Title', 'Capitalize every word.'),
        ),
        default='CUSTOM'
    )

    auto_smooth: EnumProperty(
        name="Auto Smooth",
        items=(
            ('OBJECT', 'Object', 'Auto Smooth per Object'),
            ('ON', 'ON', 'Bake with Auto Smooth'),
            ('OFF', 'OFF', 'Bake without Auto Smooth'),
        ),
        default='OBJECT'
    )

    use_Bump: BoolProperty(name="Bump (Height)", default=False)

    use_vertex_color: BoolProperty(name="Vertex Color", default=False)

    bake_vertex_colors: EnumProperty(
        name="Vertex Colors",
        description='Select Vertex Colors to bake',
        items=(
            ('SELECTED', 'Selected', ''),
            ('ACTIVE_RENDER', 'Active Render', ''),
            ('ALL', 'All', ''),
            ('1', '1', ''),
            ('2', '2', ''),
            ('3', '3', ''),
            ('4', '4', ''),
            ('5', '5', ''),
            ('6', '6', ''),
            ('7', '7', ''),
            ('8', '8', ''),
        ),
        default='SELECTED'
    )

    use_material_id: BoolProperty(name="Material ID", default=False)

    # Diffuse
    use_Diffuse: BoolProperty(
        name="Diffuse",
        description='Does only work in "Combined" and "Single/Batch"',
        default=False)

    select_uv_map: EnumProperty(
        name="UV Map",
        description='Select UV Map to bake on',
        items=(
            ('SELECTED', 'Selected', ''),
            ('ACTIVE_RENDER', 'Active Render', ''),
            ('1', '1', ''),
            ('2', '2', ''),
            ('3', '3', ''),
            ('4', '4', ''),
            ('5', '5', ''),
            ('6', '6', ''),
            ('7', '7', ''),
            ('8', '8', ''),
        ),
        default='SELECTED'
    )

    set_selected_uv_map: BoolProperty(
        name="Set as selected UV Map",
        description='',
        default=False)

    select_set_active_render_uv_map: BoolProperty(
        name="Set as active render",
        description='',
        default=False)

    use_shortlist: BoolProperty(
        name="Short List",
        description='Show the most common Bake Types only',
        default=False,
        update=reset_bake_list,
    )

    use_wireframe: BoolProperty(
        name="Wireframe",
        default=False)

    use_pixel_size: BoolProperty(
        name="Pixel Size",
        default=False)

    wireframe_size: FloatProperty(
        name="Size",
        default=0.01,
        min=0.0,
        # max=100.0,
        soft_max=100.0
    )

    duplicate_objects: BoolProperty(
        name="Duplicate Objects",
        description='',
        default=False)

    join_duplicate_objects: BoolProperty(
        name="Join Duplicate Objects",
        description='',
        default=False)

    copy_modifiers: BoolProperty(
        name="Copy Modifiers",
        description='',
        default=True)

    duplicate_objects_prefix: StringProperty(
        name="Prefix",
        default="",
        maxlen=1024,
    )

    duplicate_objects_suffix: StringProperty(
        name="Suffix",
        default="",
        maxlen=1024,
    )

    duplicate_object_loc_offset_x: FloatProperty(name="offset x", default=0.0,)
    duplicate_object_loc_offset_y: FloatProperty(name="offset y", default=0.0,)
    duplicate_object_loc_offset_z: FloatProperty(name="offset z", default=0.0,)

    use_value_differ: BoolProperty(
        name="Value Differences",
        description='Detect value differences in shader nodes.\n\nThis setting is for Autodetect and for manual detection in the Bake List',
        default=True
    )

    use_connected_inputs: BoolProperty(
        name="Connected Inputs",
        description='Detect connected inputs in shader nodes.\n\nThis setting is for Autodetect and for manual detection in the Bake List',
        default=True
    )
