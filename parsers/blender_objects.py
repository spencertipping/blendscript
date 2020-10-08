"""
Blender object references (by name)
"""

from .combinators import *
from .basic       import *
from .expr        import *

unsupported_bpy_datas = []

def bpy_data_parser(name):
  try:
    return eval(f'p_member_of(bpy.data.{name}, p_word)')
  except:
    unsupported_bpy_datas.append(name)
    return lambda s, i: fail(None)

def bpy_data_parser_ops(names):
  pass

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
    unsupported_bpy_datas.append(t)

if len(unsupported_bpy_datas):
  print(f'BlendScript warning: disabling the following unavailable entries '
        f'in bpy.data: {unsupported_bpy_datas}; their parsers will reject '
        f'input')

defexprop(**{
  ':ac/': p_actions,
  ':ar/': p_armatures,
  ':br/': p_brushes,
  ':ca/': p_cache_files,
  ':co/': p_collections,
  ':cu/': p_curves,
  ':fi/': p_filepaths
  ':fo/': p_fonts,
  ':gr/': p_grease_pencils,
  ':ha/': p_hairs,
  ':'
})
