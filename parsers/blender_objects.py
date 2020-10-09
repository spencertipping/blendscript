"""
Blender object references (by name)

This module defines two things. First, each object type gets a series of
namespaced accessors starting with two-letter prefixes of the type and
proceeding up to the full type name. For example, you could refer to a mesh
called "Cube" using any of these words:

me/Cube
mes/Cube
mesh/Cube
meshe/Cube
meshes/Cube

Most of the time these prefixes don't collide, but when they do, for instance
for "screens" and "scenes", "sc/X" would retrieve either.

The other thing this module defines is the "B:" operator, which creates a
Blender object and links it into the scene. You can use this to finalize "M:"
meshes.
"""

import bpy

from .combinators import *
from .basic       import *
from .expr        import *

unsupported_bpy_datas = []

# FIXME: we should have individual functions to dereference Blender objects and
# throw errors (not fail the parse) if said objects don't exist
def bpy_data_parser(name):
  try:
    return eval(f'p_member_of(bpy.data.{name}, p_word)', globals())
  except:
    unsupported_bpy_datas.append(name)
    return parserify(lambda s, i: fail(None))

def bpy_data_parser_ops(names):
  prefixes = {}
  for n in names:
    p = bpy_data_parser(n)
    for i in range(2, len(n) + 1):
      sub = n[:i]
      if sub not in prefixes: prefixes[sub] = alt()
      prefixes[sub].add(p)
  return prefixes

# From https://docs.blender.org/api/current/bpy.types.BlendData.html
bpy_parsers = (
  'actions armatures brushes cache_files collections curves '
  'filepath fonts grease_pencils hairs images lattices libraries '
  'lightprobes lights linestyles masks materials meshes metaballs '
  'movieclips node_groups objects paint_curves palettes particles '
  'pointclouds scenes screens shape_keys simulations sounds '
  'speakers texts textures volumes window_managers worlds').split(' ')

blender_object_parser = \
  dsp(**dict([(f'{k}/', p)
              for k, p in bpy_data_parser_ops(bpy_parsers).items()]))

defexprliteral(blender_object_parser)


def blender_add_object(name, obj):
  linked_obj = bpy.data.objects.new(name, obj)
  bpy.context.scene.collection.objects.link(linked_obj)
  return linked_obj.name


defexprglobals(bpy=bpy,
               blender_add_object=blender_add_object)

defexprop(**{
  'B:': pmap(lambda ps: f'blender_add_object("{ps[0] or ""}", {ps[1]})',
             seq(maybe(p_lword), expr))})

if len(unsupported_bpy_datas):
  print(f'BlendScript warning: disabling the following unavailable entries '
        f'in bpy.data: {unsupported_bpy_datas}; their parsers will reject '
        f'input')
