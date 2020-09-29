import bpy


def save_image_as(image, file_path, file_format, color_mode='RGB', color_depth='8', compression=15, quality=90, tiff_codec='DEFLATE', exr_codec='ZIP'):
    s = bpy.context.scene.render.image_settings
    fm = s.file_format
    cm = s.color_mode
    cd = s.color_depth
    c = s.compression
    q = s.quality
    tc = s.tiff_codec
    ec = s.exr_codec
    vt = bpy.context.scene.view_settings.view_transform

    s.file_format = file_format
    s.color_mode = color_mode
    s.color_depth = color_depth
    s.compression = compression
    s.quality = quality
    s.tiff_codec = tiff_codec
    s.exr_codec = exr_codec
    defalut_vt = 'Standard'
    bpy.context.scene.view_settings.view_transform = defalut_vt

    image.use_view_as_render = False

    abs_path = bpy.path.abspath(file_path)

    image.save_render(abs_path)

    s.file_format = fm
    s.color_mode = cm
    s.color_depth = cd
    s.compression = c
    s.quality = q
    s.tiff_codec = tc
    s.exr_codec = ec
    bpy.context.scene.view_settings.view_transform = vt
