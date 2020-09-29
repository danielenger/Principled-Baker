PB_PACKAGE = __package__

NODE_TAG = 'p_baker_node'
MATERIAL_TAG = 'p_baker_material'
MATERIAL_TAG_VERTEX = 'p_baker_material_vertex'

NODE_INPUTS = [
    'Color',
    'Subsurface',
    # 'Subsurface Radius', # TODO?
    'Subsurface Color',
    'Metallic',
    'Specular',
    'Specular Tint',
    'Roughness',
    'Anisotropic',
    'Anisotropic Rotation',
    'Sheen',
    'Sheen Tint',
    'Clearcoat',
    'Clearcoat Roughness',
    'IOR',
    'Transmission',
    'Transmission Roughness',
    'Emission',
    'Alpha',
    'Normal',
    'Clearcoat Normal',
    'Tangent'
]

# for new material to have images nicely sorted
NODE_INPUTS_SORTED = [
    'Color',
    'Ambient Occlusion',
    'Subsurface',
    'Subsurface Radius',
    'Subsurface Color',
    'Metallic',
    'Specular',
    'Specular Tint',
    'Roughness',
    'Glossiness',
    'Anisotropic',
    'Anisotropic Rotation',
    'Sheen',
    'Sheen Tint',
    'Clearcoat',
    'Clearcoat Roughness',
    'IOR',
    'Transmission',
    'Transmission Roughness',
    'Emission',
    'Alpha',
    'Normal',
    'Clearcoat Normal',
    'Tangent',
    'Bump',
    'Displacement',
    'Diffuse',
    'Wireframe',
    'Material ID'
]

NORMAL_INPUTS = {'Normal', 'Clearcoat Normal', 'Tangent'}

ALPHA_NODES = {
    # "Alpha":'BSDF_TRANSPARENT',
    "Translucent_Alpha": 'BSDF_TRANSLUCENT',
    "Glass_Alpha": 'BSDF_GLASS'
}

BSDF_NODES = {
    'BSDF_PRINCIPLED',
    'BSDF_DIFFUSE',
    'BSDF_TOON',
    'BSDF_VELVET',
    'BSDF_GLOSSY',
    'BSDF_TRANSPARENT',
    'BSDF_TRANSLUCENT',
    'BSDF_GLASS'
}

IMAGE_FILE_FORMAT_ENDINGS = {
    "BMP": "bmp",
    "PNG": "png",
    "JPEG": "jpg",
    "TIFF": "tif",
    "TARGA": "tga",
    "OPEN_EXR": "exr",
}

# signs not allowed in file names or paths
NOT_ALLOWED_SIGNS = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
