"""
Units of measure.

Blender's Python API always uses meters as its inputs, but the scene may be
rendered using something else. We need to translate our units into the ones
used for the scene.
"""

from ..compatibility import *


unit_conversions = {
  'METERS':  1,
  'CENTIMETERS': 0.01,
  'MILLIMETERS': 0.001,
  'FEET': 0.3048,
  'INCHES': 0.0254,
}


try:
  import bpy

  def unit_scale(x):
    return x * unit_conversions[bpy.context.scene.unit_settings.length_unit]

except ModuleNotFoundError:
  blender_not_found()

  def unit_scale(x): return x
