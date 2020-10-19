"""
Operators to create and manipulate Blender toplevel objects.
"""

from .peg   import *
from .basic import *
from .expr  import *
from .val   import *

from ..compiler.types          import *
from ..compiler.val            import *
from ..blender.blender_objects import *


try:
  import bpy

  v_add_obj = val.of_fn([t_string, t_blendobj], t_string, blender_add_object)
  val_atom.bind(**{'b<': v_add_obj})

except ModuleNotFoundError:
  print('warning: blender object support is unavailable')
