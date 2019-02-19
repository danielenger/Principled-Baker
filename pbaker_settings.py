import bpy

from bpy.props import (StringProperty, 
    BoolProperty,
    IntProperty,
    FloatProperty,
    # FloatVectorProperty,
    EnumProperty,
    PointerProperty,
    )


class PBAKER_settings(bpy.types.PropertyGroup):

    use_autodetect : BoolProperty(
        name="Autodetect",
        description="Bake only linked inputs and inputs with values that differ in different Shader nodes",
        default=True
    )

    image_suffix_settings_show : BoolProperty(
        name="Suffix Settings",
        default=True
    )

    custom_resolution : IntProperty(
        name="Resolution",
        default=1024,
        min=1,
        soft_max = 8*1024
    )
    resolution : EnumProperty(
        name="Resolution",
        items=(
            ('custom', 'Custom', ''),
            ('512', '512', '512'),
            ('1024', '1024', '1024'),
            ('2048', '2048', '2048'),
            ('4096', '4096', '4096'),
        ),
        default='1024'
    )

    margin : IntProperty(
        name="Margin",
        default=0,
        min=0,
        max=64
    )

    use_overwrite : BoolProperty(
        name="Overwrite",
        default=False
    )

    use_alpha : BoolProperty(
        name="Image Alpha",
        default=False
    )
    use_float_buffer : BoolProperty(
        name="Float Buffer",
        default=False
    )

    suffix_color : StringProperty(
        name="Color",
        default="_color",
        maxlen=1024,
    )
    suffix_metallic : StringProperty(
        name="Metallic",
        default="_metal",
        maxlen=1024,
    )
    suffix_roughness : StringProperty(
        name="Roughness",
        default="_roughness",
        maxlen=1024,
    )
    
    suffix_specular : StringProperty(
        name="Specular ",
        default="_specular",
        description="invert Roughness for Specular workflow\nDo not confuse with 'Specular' input of Principled BSDF!",
        maxlen=1024,
    )
    use_invert_roughness : BoolProperty(
        name="invert Roughness",
        description="invert Roughness for Specular workflow\nDo not confuse with 'Specular' input of Principled BSDF!",
        default=False
    )

    suffix_normal : StringProperty(
        name="Normal",
        default="_normal",
        maxlen=1024,
    )
    suffix_bump : StringProperty(
        name="Bump (Height)",
        default="_bump",
        maxlen=1024,
    )
    suffix_displacement : StringProperty(
        name="Displacement",
        default="_displacement",
        maxlen=1024,
    )

    image_prefix : StringProperty(
        name="Prefix (Texture Name)",
        description="Object name will be used as prefix, if Prefix not set",
        maxlen=1024,
    )

    use_object_name : BoolProperty(
        name="Object Name as (second) Prefix",
        description="Use object name as prefix.\nObject name will be used as prefix, if Texture Name Prefix not set",
        default=False
    )

    file_path : StringProperty(
        name="",
        description="directory for textures output",
        default="//",
        maxlen=1024,
        subtype='DIR_PATH'
    )

    use_clear : BoolProperty(
        name="Clear",
        default=False
    )

    use_selected_to_active : BoolProperty(
        name="Selected to Active",
        default=False
    )

    use_new_material : BoolProperty(
        name="Add New Material",
        description="Add new material to selected objects with a Principled BSDF.\nIf Selected to Active is active, a new material will be added to active object",
        default=False
    )

    new_material_prefix : StringProperty(
        name="Material Name",
        description="New Material Name. If empty, Material will have name of Object",
        default="",
        maxlen=1024,
    )

    use_bake_bump : BoolProperty(
        name="Bake Bump (Height)",
        description="Bake Bump Map from Bump node Height input",
        default=False
    )
    use_alpha_to_color : BoolProperty(
        name="Alpha channel to Color",
        description="Add alpha channel to Color Texture",
        default=False
    )
    use_exclude_transparent_colors : BoolProperty(
        name="Exclude Transparent Colors",
        description="Exclude colors from nodes with transparency from Color Texture",
        default=True
    )

    use_smart_uv_project : BoolProperty(
        name="Auto Smart UV Project",
        description="",
        default=False
    )
    angle_limit : FloatProperty(
        name="Angle Limit",
        default=66.0,
        min=1.0,
        max=89.0
    )
    island_margin : FloatProperty(
        name="Island Margin",
        default=0.0,
        min=0.0,
        max=1.0
    )
    user_area_weight : FloatProperty(
        name="Area Weight",
        default=0.0,
        min=0.0,
        max=1.0
    )
    use_aspect : BoolProperty(
        name="Correct Aspect",
        default=True
    )
    stretch_to_bounds : BoolProperty(
        name="Stretch to UV Bounds",
        default=True
    )

    use_image_float : BoolProperty(
        name="32 bit float",
        default=False
    )


    file_format : EnumProperty(
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

    suffix_text_mod : EnumProperty(
        name="Convert suffix",
        items=(
            ('custom', 'Custom', ''),
            ('lower', 'Lower', 'Convert suffix to lowercase letters.'),
            ('upper', 'Upper', 'Convert suffix to capital letters.'),
            ('title', 'Title', 'Convert suffix. First letter capital. Rest lowercase letters.'),
        ),
        default='custom'
    )

    use_Alpha : BoolProperty(name="Alpha/Transparency", default=False)
    use_Emission : BoolProperty(name="Emission", default=False)

    use_Base_Color : BoolProperty(name="Color", default=True)
    use_Metallic : BoolProperty(name="Metallic", default=True)
    use_Roughness : BoolProperty(name="Roughness", default=True)

    use_Normal : BoolProperty(name="Normal", default=True)
    use_Bump : BoolProperty(name="Bump (Height)", default=False)
    use_Displacement : BoolProperty(name="Displacement", default=False)

    use_Anisotropic : BoolProperty(name="Anisotropic", default=False)
    use_Anisotropic_Rotation : BoolProperty(name="Anisotropic Rotation", default=False)
    use_Clearcoat : BoolProperty(name="Clearcoat", default=False)
    use_Clearcoat_Normal : BoolProperty(name="Clearcoat Normal", default=False)
    use_Clearcoat_Roughness : BoolProperty(name="Clearcoat Roughness", default=False)
    use_IOR : BoolProperty(name="IOR", default=False)
    use_Sheen : BoolProperty(name="Sheen", default=False)
    use_Sheen_Tint : BoolProperty(name="Sheen Tint", default=False)
    use_Specular : BoolProperty(name="Specular", default=False)
    use_Specular_Tint : BoolProperty(name="Specular Tint", default=False)
    use_Subsurface : BoolProperty(name="Subsurface", default=False)
    use_Subsurface_Color : BoolProperty(name="Subsurface Color", default=False)
    use_Subsurface_Radius : BoolProperty(name="Subsurface Radius", default=False)
    use_Tangent : BoolProperty(name="Tangent", default=False)
    use_Transmission : BoolProperty(name="Transmission", default=False)
    use_Transmission_Roughness : BoolProperty(name="Transmission Roughness", default = False)
