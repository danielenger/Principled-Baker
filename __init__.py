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
    "version": (0, 1, 8),
    "blender": (2, 80, 0),
    "location": "Node Editor Toolbar",
    "category": "Node",
}

import bpy

# from bpy.props import PointerProperty
# from bpy.types import Panel

from . pbaker_settings import PBAKER_settings
from . pbaker_panel import PBAKER_PT_panel
from . pbaker_bake import PBAKER_OT_bake

def register():
   bpy.utils.register_class(PBAKER_settings)
   bpy.utils.register_class(PBAKER_OT_bake)
   bpy.utils.register_class(PBAKER_PT_panel)
   bpy.types.Scene.principled_baker_settings = bpy.props.PointerProperty(type=PBAKER_settings)
    
def unregister():
   bpy.utils.unregister_class(PBAKER_PT_panel)
   bpy.utils.unregister_class(PBAKER_OT_bake)
   bpy.utils.unregister_class(PBAKER_settings)
   del bpy.types.Scene.principled_baker_settings


if __name__ == "__main__":
    register()