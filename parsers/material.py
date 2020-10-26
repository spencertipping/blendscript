"""
Operators to create materials.
"""

from ..compatibility import *

from .peg   import *
from .basic import *
from .expr  import *
from .val   import *

from ..blender.gc     import *
from ..compiler.types import *
from ..compiler.val   import *


try:
  import bpy

  t_material = atom_type('MAT')
  t_color    = atom_type('CV3')

  def blender_make_material(name, color):
    ms = bpy.data.materials
    if name in ms: ms.remove(ms[name])
    m = ms.new(name)
    m.diffuse_color = (color[0], color[1], color[2], 1)
    return gc_tag(m)

  val_atom.bind(**{
    'M<': val.of_fn([t_string, t_color], t_material, blender_make_material)
  })

except ModuleNotFoundError:
  blender_not_found()
