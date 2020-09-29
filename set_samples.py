import bpy


def set_samples(jobname):
    """Set samples by user settings.

    Must be restored afer baking!
    """
    
    settings = bpy.context.scene.principled_baker_settings
    samples = settings.samples
    if settings.individual_samples and not settings.use_autodetect:
        bakelist = bpy.context.scene.principled_baker_bakelist
        if jobname in bakelist.keys():
            samples = bakelist[jobname].samples
        else:
            if jobname == "Diffuse":
                samples = settings.samples_diffuse
            elif jobname == "Bump":
                samples = settings.samples_bump
            elif jobname == "Vertex Color":
                samples = settings.samples_vertex_color
            elif jobname == "Material ID":
                samples = settings.samples_material_id
            elif jobname == "Wireframe":
                samples = settings.samples_wireframe
    bpy.context.scene.cycles.samples = samples
