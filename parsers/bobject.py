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

  # TODO: move this? Bind a type parser?
  t_blendobjparent = atom_type('OBP')

  def blender_add_and_focus_object(name, obj):
    name = blender_add_object(name, obj)
    blender_focus_on(name)
    return name

  v_add_obj           = val.of_fn([t_string,         t_blendobj], t_string,   blender_add_object)
  v_move_obj          = val.of_fn([t_blendobjparent, t_blendobj], t_blendobj, blender_move_to)
  v_add_and_focus_obj = val.of_fn([t_string,         t_blendobj], t_string,   blender_add_and_focus_object)
  v_focus_obj         = val.of_fn([t_blendobj],                   t_blendobj, blender_focus_on)

  val_atom.bind(**{'b<':  v_add_obj,
                   'b@':  v_move_obj,
                   'b=':  v_focus_obj,
                   'b<=': v_add_and_focus_obj})

except ModuleNotFoundError:
  blender_not_found()
