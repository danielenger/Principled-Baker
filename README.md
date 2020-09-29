# Principled-Baker
A Blender Add-on: Bake PBR textures with a few clicks
---

[Principled Baker for Blender 2.79](https://github.com/danielenger/Principled-Baker_for_2-79)


Features:
--
- Autodetection of what needs to be baked by connected inputs
- Manual selection for texture channels
- bake almost all Principled BSDF (and more) inputs (Color, Metallic, Roughness, etc.) to image textures
- Autodetection/Manual selection also for Alpha, Emission, Ambient Occlusion (from node; 2.80 only), Diffuse, Glossiness (invert Roughness), Bump (as hightmap), Vertex Color, Material ID
- 3 Bake Modes:
  - Combined: Bake a single selected object or bake multiple selected objects with shared UV maps. This is like Blenders default bake.
  - Single/Batch: Bake every selected object separately.
  - Selected to Active: Does what it says.
- Create new material with new image texture nodes (most image nodes connected)
- Auto Smooth from object/on/off
- Auto UV unwrap option: Smart UV Project/Lightmap Pack

---
Limitations/Warnings:
--
- **Be careful with Overwrite! It does what it says!**

- Baking works in Cycles only. (see preferences Bake "in" Eevee)

- Displacement works only with a Displacement node. (Blender 2.80)
Vector Displacement does not work.

- Color inputs of transparent nodes (Transparent, Translucent, Glass) will be ignored by default.
This prevents false colors at transitions from being baked into the Color Texture.
Deactivate "Exclude Transparent Colors" to bake transparent inputs to Color Texture.

- Autodetection:
If just a Bump node is in the node tree, the Normal Map will always be baked.
If a Normal Map and a Bump Map is baked, the Bump node will not be linked in newly created material.

- Some results from complex mixed shader node trees might not be useful

- with Material Name to define the Material ID Colors: Duplicate colors are possible!

- Baking "in" Eevee might crash Blender!

- known issues:
  * results for Subsurface Radius is not useful 
  * results for Tangent might not be useful
  * batch baking with shared materials can give useless, half baked image textures
  * typo in github name (can not be solved?)


***
Thread on blenderartists:
https://blenderartists.org/t/addon-principled-baker/1102187
