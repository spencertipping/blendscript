"""
Blender object references (by name)
"""

import bpy

from .peg   import *
from .basic import *
from .expr  import *

from ..objects.function import *


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

def clear_blendscript():
  for p in dir(bpy.data):
    d = getattr(bpy.data, p)
    if getattr(d, '__iter__', False):
      for x in d:
        if x.get('added_by_blendscript'):
          d.remove(x)


def blender_add_object(name, obj):
  if len(name) and name in bpy.data.objects:
    bpy.data.objects.remove(bpy.data.objects[name])
  linked_obj = bpy.data.objects.new(name, obj)
  linked_obj['added_by_blendscript'] = True
  bpy.context.scene.collection.objects.link(linked_obj)
  bpy.context.view_layer.objects.active = linked_obj
  linked_obj.select_set(True)

  bpy.ops.object.mode_set(mode='EDIT')
  bpy.ops.object.mode_set(mode='OBJECT')
  return linked_obj.name


defexprglobals(_blender_add_object=blender_add_object,
               _clear_blendscript=fn(clear_blendscript))
defexprop(**{
  'BC': const('_clear_blendscript()', empty),
  'B:': pmaps(lambda n, o: f'_blender_add_object("{n or ""}", {o})',
              seq(maybe(p_lword), expr))})
