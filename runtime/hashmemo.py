"""
Blender objects whose inputs can be hashed for memoization.
"""

import importlib

try:
  bpy = importlib.import_module('bpy')

  # TODO: a function that synchronizes blender state to defined object state,
  # for all objects that were generated

except ModuleNotFoundError:
  print('warning: blender hashmemo is not available (failed to import bpy)')
