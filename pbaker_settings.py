import bpy
from bpy.types import Panel

from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
    # FloatProperty,
    # FloatVectorProperty,
                       EnumProperty,
                       PointerProperty,
                       )

from bpy.types import (Panel,
                       Operator,
                       PropertyGroup,
                       )


class PBAKER_settings(bpy.types.PropertyGroup):

    resolution : IntProperty(
        name="resolution",
        default=2048,
        min=1,
        max = 16*1024
    )
    
    margin : IntProperty(
        name="margin",
        default=0,
        min=0,
        max=64
    )

    use_overwrite : BoolProperty(
        name="Overwrite",
        default=True
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
    suffix_normal : StringProperty(
        name="Normal",
        default="_normal",
        maxlen=1024,
    )
    suffix_bump : StringProperty(
        name="Bump",
        default="_bump",
        maxlen=1024,
    )
    suffix_displacement : StringProperty(
        name="Displacement",
        default="_disp",
        maxlen=1024,
    )
    suffix_bump_to_normal : StringProperty(
        name="Bump to Normal",
        default="_normal2",
        maxlen=1024,
    )

    image_prefix : StringProperty(
        name="Texture Name Prefix",
        default="",
        maxlen=1024,
    )

    file_path : StringProperty(
        name="",
        description="Choose a directory:",
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
        name="New Material",
        default=False
    )

    new_material_prefix : StringProperty(
        name="Material Name",
        description="New Material Name. If empty, Material will have name of Object",
        default="",
        maxlen=1024,
    )

    use_bump_to_normal : BoolProperty(
        name="Bump as Normal Map",
        description="bake bump map as normal map",
        default=False
    )

    use_bump_strength : BoolProperty(
        name="use Bump Strength",
        default=False
    )

    use_normal_strength : BoolProperty(
        name="use Normal Map Strength",
        default=False
    )

    use_alpha_to_color : BoolProperty(
        name="alpha channel to color",
        default=True
    )

    file_format : EnumProperty(
        name="File Format",
        items=(
            ("PNG", "PNG", ""),
            ("BMP", "BMP", ""),
            ("JPEG", "JPEG", ""),
            ("TIFF", "TIFF", ""),
            ("TARGA", "TARGA", ""),
        ),
        default='PNG'
    )

    use_autodetect : BoolProperty(name='Autodetect',
                                  description="Bake only linked inputs and inputs with values that differ in different Principled BSDF nodes",
                                  default=False)

    use_Alpha : BoolProperty(name='Alpha/Transparency', default=False)

    use_Base_Color : BoolProperty(name='Color', default=True)
    use_Metallic : BoolProperty(name='Metallic', default=True)
    use_Roughness : BoolProperty(name='Roughness', default=True)
    use_Specular : BoolProperty(name='Specular', default=False)

    use_Normal : BoolProperty(name='Normal', default=True)
    use_Bump : BoolProperty(name='Bump', default=False)
    use_Displacement : BoolProperty(name='Displacement', default=False)

    use_Anisotropic : BoolProperty(name='Anisotropic', default=False)
    use_Anisotropic_Rotation : BoolProperty(name='Anisotropic Rotation', default=False)
    use_Clearcoat : BoolProperty(name='Clearcoat', default=False)
    use_Clearcoat_Normal : BoolProperty(name='Clearcoat Normal', default=False)
    use_Clearcoat_Roughness : BoolProperty(name='Clearcoat Roughness', default=False)
    use_IOR : BoolProperty(name='IOR', default=False)
    use_Sheen : BoolProperty(name='Sheen', default=False)
    use_Sheen_Tint : BoolProperty(name='Sheen Tint', default=False)
    use_Specular_Tint : BoolProperty(name='Specular Tint', default=False)
    use_Subsurface : BoolProperty(name='Subsurface', default=False)
    use_Subsurface_Color : BoolProperty(name='Subsurface Color', default=False)
    use_Subsurface_Radius : BoolProperty(name='Subsurface Radius', default=False)
    use_Tangent : BoolProperty(name='Tangent', default=False)
    use_Transmission : BoolProperty(name='Transmission', default=False)
    use_Transmission_Roughness : BoolProperty(name='Transmission Roughness', default = False)
