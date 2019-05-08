import bpy

from bpy.props import (StringProperty, 
    BoolProperty,
    FloatProperty,
    EnumProperty
    )


# Addon prefs
class PBAKER_prefs(bpy.types.AddonPreferences):
    bl_idname = __package__

    switch_to_cycles : BoolProperty(
        name="Bake in Eevee/Workbench (temporarily switch to Cycles)",
        default=False
    )

    mat_id_algorithm : EnumProperty(
        name="Material ID Colors by",
        items=(
            ('HUE', 'Slot/Hue', ''),
            ('NAME', 'Material Name', ''),
        ),
        default='HUE'
    )

    mat_id_saturation : FloatProperty(
        name="Saturation",
        default=1.0,
        min=0.0,
        max=1.0
    )

    mat_id_value : FloatProperty(
        name="Value",
        default=1.0,
        min=0.0,
        max=1.0
    )


    def draw(self, context):
        layout = self.layout
        col = layout.column()

        # 2.80
        if bpy.app.version_string.startswith('2.8'):
            col.prop(self, "switch_to_cycles")
            col.label(text="This may crash Blender 2.80 beta!", icon='ERROR')
            col.separator()

        col.prop(self, "mat_id_algorithm")
        if self.mat_id_algorithm == 'HUE':
            col.prop(self, "mat_id_saturation")
            col.prop(self, "mat_id_value")
        elif self.mat_id_algorithm == 'NAME':
            self.layout.label(text="Duplicate colors are possible!", icon='ERROR')
