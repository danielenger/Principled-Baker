# Principled-Baker
bake all inputs of Principled BSDFs (and other nodes) to image textures
---

[Principled Baker for Blender 2.79](https://github.com/danielenger/Principled-Baker_for_2-79)


Features:
--
- Autodetection of what needs to be baked
- Manual selection for texture channels
- Bake single
- Bake batch
- Bake Selected to Active

---
Limitations/Warnings:
--
- **Be careful with Overwrite! It does what it says!**

- Baking works in Cycles only. (for now)

- Displacement works only with a Displacement node. (Blender 2.80)
Vector Displacement does not work.

- Color inputs of transparent nodes (Transparent, Translucent, Glass) will be ignored by default.
This prevents false colors at transitions from being baked into the Color Texture.
Deactivate "Exclude Transparent Colors" to bake transparent inputs to Color Texture.

- Autodetection:
If just a Bump node is in the node tree, the Normal Map will always be baked.
If a Normal Map and a Bump Map is baked, the Bump node will not be linked in newly created material.

- Some results from complex mixed shader node trees might not be useful

- no bake from Ambient Occlusion Shader in 2.79

- bake Ambient Occlusion only from one node per material (highest node in tree)

- new Ambient Occlusion texture is not connected in newly generated material

- Vertex Color baking only works, if the object has a material (will be fixed)

- known issues:
  * results for Subsurface Radius is not useful 
  * results for Tangent might not be useful
  * batch baking with shared materials can give useless, half baked image textures
  * typo in github name (can not be solved?)


***
Thread on blenderartists:
https://blenderartists.org/t/principled-baker-bake-pbr-textures-from-principled-bsdf/1102187
