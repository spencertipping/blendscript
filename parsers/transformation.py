"""
Matrix and quaternion transformation expressions.
"""

from mathutils import Matrix, Quaternion
from math      import pi

from .combinators import *
from .basic       import *
from .expr        import *


defexprglobals(tau = pi * 2,
              _Matrix=Matrix,
              _Quaternion=Quaternion)

defexprop(**{
  '~':  unop(lambda x: f'{x}.normalized()'),
  '^':  unop(lambda m: f'{m}.inverted()'),

  'Q':  pmap(lambda ps: f'_Quaternion(({",".join(ps)}))',
            rep(expr, min=4, max=4)),

  'T':  unop(lambda v: f'_Matrix.Translation({v})'),

  'Rx': unop(lambda x: f'_Matrix.Rotation(({x}) * tau, 4, "X")'),
  'Ry': unop(lambda x: f'_Matrix.Rotation(({x}) * tau, 4, "Y")'),
  'Rz': unop(lambda x: f'_Matrix.Rotation(({x}) * tau, 4, "Z")'),
  'R': binop(lambda ps: f'_Matrix.Rotation(({ps[1]}) * tau, 4, {ps[0]})'),

  'Sx': unop(lambda x: f'_Matrix.Scale({x}, 4, "X")'),
  'Sy': unop(lambda x: f'_Matrix.Scale({x}, 4, "Y")'),
  'Sz': unop(lambda x: f'_Matrix.Scale({x}, 4, "Z")'),
  'S': binop(lambda ps: f'_Matrix.Scale({ps[1]}, 4, {ps[0]})')})
