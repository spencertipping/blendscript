"""
Matrix and quaternion transformation expressions.
"""

from mathutils import Vector, Matrix, Quaternion
from math      import pi

from .basic import *
from .expr  import *
from .peg   import *


defexprglobals(tau = pi * 2,
               _Vector = Vector,
               _Matrix=Matrix,
               _Quaternion=Quaternion)

defexprop(**{
  'x':   unop(lambda x:       f'_Vector(({x},0,0))'),
  'y':   unop(lambda y:       f'_Vector((0,{y},0))'),
  'z':   unop(lambda z:       f'_Vector((0,0,{z}))'),
  'Z':  binop(lambda x, y:    f'_Vector(({x},{y},0))'),
  'Y':  binop(lambda x, z:    f'_Vector(({x},0,{z}))'),
  'X':  binop(lambda y, z:    f'_Vector((0,{y},{z}))'),
  'V': ternop(lambda x, y, z: f'_Vector(({x},{y},{z}))'),

  'Q':  lambda expr: pmap(lambda ps: f'_Quaternion(({",".join(ps)}))',
                          rep(expr, min=4, max=4)),

  '~':  unop(lambda x: f'{x}.normalized()'),
  '^':  unop(lambda m: f'{m}.inverted()'),

  'T':  unop(lambda v: f'_Matrix.Translation({v})'),

  'Rx': unop(lambda x: f'_Matrix.Rotation(({x}) * tau, 4, "X")'),
  'Ry': unop(lambda x: f'_Matrix.Rotation(({x}) * tau, 4, "Y")'),
  'Rz': unop(lambda x: f'_Matrix.Rotation(({x}) * tau, 4, "Z")'),
  'R': binop(lambda ps: f'_Matrix.Rotation(({ps[1]}) * tau, 4, {ps[0]})'),

  'Sx': unop(lambda x: f'_Matrix.Scale({x}, 4, "X")'),
  'Sy': unop(lambda x: f'_Matrix.Scale({x}, 4, "Y")'),
  'Sz': unop(lambda x: f'_Matrix.Scale({x}, 4, "Z")'),
  'S': binop(lambda ps: f'_Matrix.Scale({ps[1]}, 4, {ps[0]})')})
