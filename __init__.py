#    Principled Baker
#    Copyright (C) 2019 Daniel Engler

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

bl_info = {
    "name": "Principled Baker",
    "description": "bakes all inputs of Principled BSDF to image textures",
    "author": "Daniel Engler",
    "version": (0, 3, 7),
    "blender": (2, 80, 0),
    "location": "Shader Editor Toolbar",
    "category": "Node",
}

import bpy

from .pbaker_bake import PBAKER_OT_bake
from .pbaker_list import *
from .pbaker_panel import PBAKER_PT_panel
from .pbaker_prefs import PBAKER_prefs
from .pbaker_settings import PBAKER_settings
from .pbaker_preset import *

classes = (
    PBAKER_OT_bake,
    PBAKER_PT_panel,
    PBAKER_prefs,
    PBAKER_settings,
    PBAKER_UL_List,
    PBAKER_ListItem,
    PBAKER_BAKELIST_OT_Init,
    PBAKER_BAKELIST_OT_Update,
    PBAKER_BAKELIST_OT_Delete,
    PBAKER_BAKELIST_OT_Reset,
    PBAKER_BAKELIST_OT_Disable_All,
    PBAKER_BAKELIST_OT_MoveItem_Up,
    PBAKER_BAKELIST_OT_MoveItem_Down,
    PBAKER_AddPresetObjectDisplay,
    PBAKER_MT_display_presets,
)

def register():
   for cls in classes:
      bpy.utils.register_class(cls)

   bpy.types.Scene.principled_baker_settings = bpy.props.PointerProperty(type=PBAKER_settings)
   bpy.types.Scene.principled_baker_bakelist = bpy.props.CollectionProperty(type = PBAKER_ListItem)
   bpy.types.Scene.principled_baker_bakelist_index = bpy.props.IntProperty(name="Bakelist Index", default = 0)

    
def unregister():
   for cls in reversed(classes):
      bpy.utils.unregister_class(cls)

   del bpy.types.Scene.principled_baker_settings
   del bpy.types.Scene.principled_baker_bakelist_index


if __name__ == "__main__":
   register()
