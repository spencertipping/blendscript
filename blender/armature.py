"""
Blender armature and bone support.
"""

from ..compatibility import *

from ..compiler.types      import *
from ..compiler.val        import *
from ..runtime.blendermath import *

from .blender_objects      import *
from .gc                   import *


try:
  import bpy

  def make_armature(bones):
    return add_hashed(bpy.data.armatures, tuple(bones), generate_armature)

  def generate_armature(bones, name):
    """
    Generate an armature from the given bone structure.

    TODO: IK constraints and pole targets
    """


  # example armature python:

  '''
  arm     = bpy.data.armatures.new('pig')
  arm_obj = bpy.data.objects.new('armature', arm)
  bpy.context.scene.collection.objects.link(arm_obj)

  bpy.context.view_layer.objects.active = arm_obj
  bpy.ops.object.mode_set(mode='EDIT', toggle=False)

  b1 = arm_obj.data.edit_bones.new('bone1')
  b1.head = (1, 2, 3)
  b1.tail = (4, 5, 6)

  b2 = arm_obj.data.edit_bones.new('bone2')
  b2.head = (4, 5, 6)
  b2.tail = (9, 8, 7)

  b2.parent = b1

  bpy.ops.object.mode_set(mode='POSE')

  bpy.data.objects['bar'].parent = arm_obj
  bpy.data.objects['bar'].parent_bone = 'bone2'
  bpy.data.objects['bar'].parent_type = 'BONE'
  '''

except ModuleNotFoundError:
  blender_not_found()
