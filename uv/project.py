import bpy


def auto_uv_project(objs):
    """Auto unwraps UV Map by user settings."""

    settings = bpy.context.scene.principled_baker_settings

    def smart_project():
        """wrapper for bpy.ops.uv.smart_project() to get all parameters from settings."""
        
        bpy.ops.uv.smart_project(angle_limit=settings.angle_limit,
                                 island_margin=settings.island_margin,
                                 user_area_weight=settings.user_area_weight,
                                 use_aspect=settings.use_aspect,
                                 stretch_to_bounds=settings.stretch_to_bounds)

    def lightmap_pack():
        """wrapper for bpy.ops.uv.lightmap_pack() to get all parameters from settings."""

        bpy.ops.uv.lightmap_pack(PREF_CONTEXT='ALL_FACES',
                                 PREF_PACK_IN_ONE=settings.share_tex_space,
                                 PREF_NEW_UVLAYER=False,  # see new UV Map
                                 PREF_APPLY_IMAGE=settings.new_image,
                                 PREF_IMG_PX_SIZE=settings.image_size,
                                 PREF_BOX_DIV=settings.pack_quality,
                                 PREF_MARGIN_DIV=settings.lightmap_margin)

    if settings.auto_uv_project == 'OFF':
        return

    if settings.new_uv_map:
        for obj in objs:
            bpy.context.view_layer.objects.active = obj
            bpy.ops.mesh.uv_texture_add()

    for obj in objs:
        bpy.context.view_layer.objects.active = obj
        if settings.auto_uv_project == 'SMART':
            smart_project()
        elif settings.auto_uv_project == 'LIGHTMAP':
            lightmap_pack()
