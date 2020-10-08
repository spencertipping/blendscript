"""
Blender object references (by name)
"""

import bpy

from .combinators import *
from .basic       import *
from .expr        import *

unsupported_bpy_datas = []

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
    for i in range(1, len(n) + 1):
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
defexprglobals(bpy=bpy)

defexprop(**{
  'B:': pmap(
    lambda ps: (f'state.do({ps[1]}, lambda x: bpy.context.scene.collection.' \
                f'objects.link(bpy.data.objects.new' \
                f'("{(ps[0] or b"").decode()}", x)))'),
    seq(maybe(p_word), expr))})

if len(unsupported_bpy_datas):
  print(f'BlendScript warning: disabling the following unavailable entries '
        f'in bpy.data: {unsupported_bpy_datas}; their parsers will reject '
        f'input')
