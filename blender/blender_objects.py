"""
Blender object references (by name)
"""

import re

from time import time

from ..compatibility import *

from .gc              import *
from .units           import *
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


t_blendobj  = atom_type('OB')
t_blendmesh = atom_type('ME')


try:
  import bpy
  import mathutils as m


  def flatten(xs):
    if type(xs) == list or type(xs) == tuple:
      return (y for x in xs for y in flatten(x))
    else:
      return [xs]


  def resolve_blender_object(x):
    """
    Returns a list of blender objects referred to by "x", in a type-dependent
    way. If x is a string, we dereference it to an object. If x is an object,
    we leave it as-is. If x is a list, we flatten the list and process each
    element.
    """
    def convert(x):
      if type(x) == str and x in bpy.data.objects: return bpy.data.objects[x]
      return x
    return tuple(map(convert, flatten(x)))


  def resolve_blender_parent(x):
    """
    Resolves x to a single object that can be used to parent another Blender
    object. This can either be an actual scene object, or it can be a vector
    that will be become its origin.
    """
    x = resolve_blender_object(x)[0]
    if type(x) == m.Vector: x = unit_scale(x)
    return x


  def blender_add_object(name, obj):
    """
    Adds a Blender scene object with the specified name. If an object with that
    name already exists, it will be unlinked.

    Names can have forward slashes. If they do, those slashes will be
    interpreted as a directory structure: parent directories are created using
    collections. (TODO: not implemented yet)

    TODO: handle obj being a list
    """
    t0 = time()
    if len(name) and name in bpy.data.objects:
      bpy.data.objects.remove(bpy.data.objects[name])

    linked_obj = bpy.data.objects.new(name, obj)
    bpy.context.scene.collection.objects.link(linked_obj)
    bpy.context.view_layer.objects.active = linked_obj
    linked_obj.select_set(True)

    gc_tag(linked_obj)

    t1 = time()
    if t1 - t0 > 0.1:
      print(f'{t1 - t0} second(s) to add object {linked_obj.name}')

    return linked_obj.name


  def blender_move_to(v_or_parent, obj):
    """
    Sets the parent of one or more Blender objects, returning the parent.
    Objects are flattened if they are in a list. If any object is not a Blender
    scene object, it is ignored.
    """
    parent = resolve_blender_parent(v_or_parent)
    objects = resolve_blender_object(obj)
    for o in objects:
      if isinstance(o, bpy.types.Object):
        if type(parent) == m.Vector: o.location = parent
        else:                        o.parent   = parent
    return objects


  def blender_refresh_view():
    """
    Force any meshes to recalculate face shading. Otherwise we sometimes end up
    with shadeless black, which is difficult to parse visually.
    """
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.object.mode_set(mode='OBJECT')


except ModuleNotFoundError:
  blender_not_found()

  def blender_refresh_view(): pass
