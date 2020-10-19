"""
Operators to create and manipulate Blender toplevel objects.
"""

from ..compatibility import *

from .peg   import *
from .basic import *
from .expr  import *
from .val   import *

from ..compiler.types          import *
from ..compiler.val            import *
from ..blender.blender_objects import *


try:
  import bpy

  t_blendobjparent = atom_type('B/objparent')

  v_add_obj  = val.of_fn([t_string,         t_blendobj], t_string,   blender_add_object)
  v_move_obj = val.of_fn([t_blendobjparent, t_blendobj], t_blendobj, blender_move_to)

  val_atom.bind(**{'b<': v_add_obj, 'b@': v_move_obj})

except ModuleNotFoundError:
  blender_not_found()
