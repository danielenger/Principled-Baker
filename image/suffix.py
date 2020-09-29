import bpy


def get_image_suffix(jobname):
    """:returns: Image suffix by job name and altered by user settings."""

    settings = bpy.context.scene.principled_baker_settings
    suffixlist = bpy.context.scene.principled_baker_suffixlist
    suffix = suffixlist[jobname]['suffix']

    if settings.suffix_text_mod == 'lower':
        suffix = suffix.lower()
    elif settings.suffix_text_mod == 'upper':
        suffix = suffix.upper()
    elif settings.suffix_text_mod == 'title':
        suffix = suffix.title()
    return suffix
