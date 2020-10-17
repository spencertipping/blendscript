"""
Blender math bindings, if we have them.
"""

import importlib

from ..compiler.val   import *
from ..compiler.types import *
from ..parsers.peg    import *
from ..parsers.basic  import *
from ..parsers.val    import *
from .fn              import fn

try:
  m = importlib.import_module('mathutils')

  vec3        = val.of_fn(t_list(t_number), t_vec3, fn(m.Vector3))
  translation = val.of_fn(t_vec3,   t_mat44, fn(m.Matrix.Translation))
  scale       = val.of_fn(t_vec3,   t_mat33, fn(m.Matrix.Diagonal))
  rotatex     = val.of_fn(t_number, t_mat33, fn(lambda t: m.Matrix.Rotation(t, 3, 'X')))
  rotatey     = val.of_fn(t_number, t_mat33, fn(lambda t: m.Matrix.Rotation(t, 3, 'Y')))
  rotatez     = val.of_fn(t_number, t_mat33, fn(lambda t: m.Matrix.Rotation(t, 3, 'Z')))

  val_atom.ops.add(
    x=pmap( lambda x:       vec3(val.list(x, 0, 0)), val_atom),
    y=pmap( lambda y:       vec3(val.list(0, y, 0)), val_atom),
    z=pmap( lambda z:       vec3(val.list(0, 0, z)), val_atom),
    X=pmaps(lambda y, z:    vec3(val.list(0, y, z)), exactly(2, val_atom)),
    Y=pmaps(lambda x, z:    vec3(val.list(x, 0, z)), exactly(2, val_atom)),
    Z=pmaps(lambda x, y:    vec3(val.list(x, y, 0)), exactly(2, val_atom)),
    v=pmaps(lambda x, y, z: vec3(val.list(x, y, z)), exactly(3, val_atom)))

  val_atom.bind(
    I=val.of(t_mat33, m.Matrix.Identity(3)),
    T=translation,
    S=scale,
    Rx=rotatex,
    Ry=rotatey,
    Rz=rotatez)

except ModuleNotFoundError:
  print("warning: vector and matrix math are unavailable")
