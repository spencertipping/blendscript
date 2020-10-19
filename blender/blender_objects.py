"""
Blender object references (by name)
"""

from time import time

from ..compatibility import *

from ..compiler.types import *
from ..runtime.fn     import *


"""
Some design notes.

Blender uses a few different object hierarchies. One is the scene graph,
focused on collections. Another is object/object parenting, which doesn't
impact the graph but does link transformations. A third is that a cube _object_
contains a cube _mesh_ and possibly cube _materials_, etc. This is a type-based
nesting.

We can say that objects have logical paths. If we do, we'll be working in terms
of collections. Object/object parenting is different.

We should create a custom property on all BlendScript objects and auto-nuke
them when we set up the scene context. That way BlendScript is declarative.
"""


t_blendobj  = atom_type('B/obj')
t_blendmesh = atom_type('B/mesh')


try:
  import bpy
  import mathutils as m

  def blendify(x):
    if type(x) == str and x in bpy.data.objects:
      return bpy.data.objects[x]
    return x


  def blender_add_object(name, obj):
    t0 = time()
    if len(name) and name in bpy.data.objects:
      bpy.data.objects.remove(bpy.data.objects[name])
    linked_obj = bpy.data.objects.new(name, obj)
    bpy.context.scene.collection.objects.link(linked_obj)
    bpy.context.view_layer.objects.active = linked_obj
    linked_obj.select_set(True)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.object.mode_set(mode='OBJECT')
    t1 = time()

    if t1 - t0 > 0.1:
      print(f'{t1 - t0} second(s) to add object {linked_obj.name}')

    return linked_obj.name


  def blender_move_to(v_or_parent, obj):
    obj = blendify(obj)
    if type(v_or_parent) == m.Vector: obj.location = v_or_parent
    else:                             obj.parent = blendify(v_or_parent)
    return obj


except ModuleNotFoundError:
  blender_not_found()
