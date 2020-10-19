"""
Blender math bindings, if we have them.
"""

from ..compiler.val   import *
from ..compiler.types import *
from ..parsers.peg    import *
from ..parsers.basic  import *
from ..parsers.val    import *
from .fn              import fn


t_vec2   = atom_type('V2')
t_vec3   = atom_type('V3')
t_vec4   = atom_type('V4')
t_mat33  = atom_type('M33')
t_mat44  = atom_type('M44')


try:
  import mathutils as m

  vec3        = val.of_fn([t_list(t_number)], t_vec3, lambda *xs: m.Vector(*xs).freeze())
  translation = val.of_fn([t_vec3],   t_mat44, lambda *xs: m.Matrix.Translation(*xs).freeze())
  scale       = val.of_fn([t_vec3],   t_mat33, lambda *xs: m.Matrix.Diagonal(*xs).freeze())
  rotatex     = val.of_fn([t_number], t_mat33, lambda t: m.Matrix.Rotation(t, 3, 'X').freeze())
  rotatey     = val.of_fn([t_number], t_mat33, lambda t: m.Matrix.Rotation(t, 3, 'Y').freeze())
  rotatez     = val.of_fn([t_number], t_mat33, lambda t: m.Matrix.Rotation(t, 3, 'Z').freeze())

  val_atom.bind(I=val.of(t_mat33, m.Matrix.Identity(3).freeze()))

except ModuleNotFoundError:
  print("warning: vector and matrix math are unavailable")

  vec3        = val.of_fn([t_list(t_number)], t_vec3, tuple)
  translation = val.of_fn([t_vec3],   t_mat44, tuple)
  scale       = val.of_fn([t_vec3],   t_mat33, tuple)
  rotatex     = val.of_fn([t_number], t_mat33, tuple)
  rotatey     = val.of_fn([t_number], t_mat33, tuple)
  rotatez     = val.of_fn([t_number], t_mat33, tuple)

  val_atom.bind(I=val.lit(t_mat33, "identity"))


zero = val.lit(t_number, 0)

val_atom.ops.add(
  x=pmap( lambda x:       vec3(val.list(x, zero, zero)), val_atom),
  y=pmap( lambda y:       vec3(val.list(zero, y, zero)), val_atom),
  z=pmap( lambda z:       vec3(val.list(zero, zero, z)), val_atom),
  X=pmaps(lambda y, z:    vec3(val.list(zero, y, z)), exactly(2, val_atom)),
  Y=pmaps(lambda x, z:    vec3(val.list(x, zero, z)), exactly(2, val_atom)),
  Z=pmaps(lambda x, y:    vec3(val.list(x, y, zero)), exactly(2, val_atom)),
  v=pmaps(lambda x, y, z: vec3(val.list(x, y, z)), exactly(3, val_atom)))

val_atom.bind(
  T=translation,
  S=scale,
  Rx=rotatex,
  Ry=rotatey,
  Rz=rotatez)
