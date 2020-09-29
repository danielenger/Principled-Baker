import bpy


def select_uv_map(obj):
    """selects a UV Map of given object by user settings.

    Must be restored afer baking!
    """

    settings = bpy.context.scene.principled_baker_settings

    uv_layers = obj.data.uv_layers

    if not settings.select_uv_map == 'SELECTED':
        if settings.select_uv_map == 'ACTIVE_RENDER':
            for i, uv_layer in enumerate(obj.data.uv_layers):
                if uv_layer.active_render:
                    uv_layers.active_index = i
                    break
        else:
            index_uv_layer = int(settings.select_uv_map) - 1
            if index_uv_layer <= len(obj.data.uv_layers) - 1:
                uv_layers.active_index = index_uv_layer

    if settings.select_set_active_render_uv_map:
        if settings.select_uv_map == 'ACTIVE_RENDER':
            return
        elif settings.select_uv_map == 'SELECTED':
            index_uv_layer = uv_layers.active_index
        else:
            index_uv_layer = int(settings.select_uv_map) - 1
        if index_uv_layer <= len(obj.data.uv_layers) - 1:
            uv_layers[index_uv_layer].active_render = True
