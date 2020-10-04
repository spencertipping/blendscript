"""
Basic building blocks for grammars.
"""

import bpy

from .combinators import *

p_word  = re(br'\w+')
p_int   = pmap(int,   re(br'-?\d+'))
p_float = pmap(float, re(br'-?\d*\.\d(?:\d*(?:[eE][+-]?\d+)?)?'
                         + br'|-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?'))

p_comment    = re(br'#.*\n?')
p_whitespace = re(br'\s+')
p_ignore     = rep(alt(p_whitespace, p_comment), min=1)


# Blender object references (by name)
def p_member_of(h, p):
  return pif(lambda x: x is not None,
             pmap(lambda s: h.get(s.decode(), None), p))

# From https://docs.blender.org/api/current/bpy.types.BlendData.html
for t in ('actions armatures brushes cache_files collections curves '
          'filepath fonts grease_pencils hairs images lattices libraries '
          'lightprobes lights linestyles masks materials meshes metaballs '
          'movieclips node_groups objects paint_curves palettes particles '
          'pointclouds scenes screens shape_keys simulations sounds '
          'speakers texts textures volumes window_managers worlds').split(' '):
  try:
    exec(f'p_{t} = p_member_of(bpy.data.{t}, p_word)', globals(), None)
  except:
    exec(f'p_{t} = lambda s, i: fail(None)', globals(), None)
    print(f'BlendScript warning: your version of Blender lacks support for {t}')
