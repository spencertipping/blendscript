"""
Operators to create and manipulate Blender toplevel objects.
"""

import bpy

from .peg   import *
from .basic import *
from .expr  import *
from .val   import *

from ..compiler.types          import *
from ..compiler.val            import *
from ..blender.blender_objects import *


v_blender_add = val.of_fn(
  t_string, t_fn(t_blendobj, t_blendobj))
