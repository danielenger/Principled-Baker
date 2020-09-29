import bpy

from ..image.save_as import save_image_as


def save_image(image, jobname):
    """Wrapper for save_image_as() to get all parameters from settings."""

    settings = bpy.context.scene.principled_baker_settings

    if jobname == 'Color' and settings.use_alpha_to_color:
        color_mode = 'RGBA'
    else:
        color_mode = settings.color_mode

    # color depth
    color_depth = settings.color_depth
    if color_depth == 'INDIVIDUAL':
        bakelist = bpy.context.scene.principled_baker_bakelist
        if jobname in bakelist.keys():
            color_depth = bakelist[jobname].color_depth
        else:
            if jobname == "Diffuse":
                color_depth = settings.color_depth_diffuse
            elif jobname == "Bump":
                color_depth = settings.color_depth_bump
            elif jobname == "Vertex Color":
                color_depth = settings.color_depth_vertex_color
            elif jobname == "Material ID":
                color_depth = settings.color_depth_material_id
            elif jobname == "Wireframe":
                color_depth = settings.color_depth_wireframe

    save_image_as(image,
                  file_path=image.filepath,
                  file_format=settings.file_format,
                  color_mode=color_mode,
                  color_depth=color_depth,
                  compression=settings.compression,
                  quality=settings.quality,
                  tiff_codec=settings.tiff_codec,
                  exr_codec=settings.exr_codec)
