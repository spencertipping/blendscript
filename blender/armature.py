"""
Blender armature and bone support.
"""

from ..compatibility import *

from ..compiler.types import *
from ..compiler.val   import *
from .blender_objects import *
from .blendermath     import *


try:
  import bpy

except ModuleNotFoundError:
  blender_not_found()
