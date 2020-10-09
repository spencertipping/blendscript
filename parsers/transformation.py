"""
Matrix and quaternion transformation expressions.
"""

from mathutils import Matrix, Quaternion
from math      import pi

from .combinators import *
from .basic       import *
from .expr        import *


defexprglobals(tau = pi * 2,
               Matrix=Matrix,
               Quaternion=Quaternion)


defexprop(**{
  'N':  unop(lambda x: f'{x}.normalized()'),
  'I':  unop(lambda m: f'{m}.inverted()'),

  'Q':  pmap(lambda ps: f'Quaternion(({",".join(ps)}))',
             rep(expr, min=4, max=4)),

  'T':  unop(lambda v: f'Matrix.Translation({v})'),

  'Rx': unop(lambda x: f'Matrix.Rotation(({x}) * tau, 4, "X")'),
  'Ry': unop(lambda x: f'Matrix.Rotation(({x}) * tau, 4, "Y")'),
  'Rz': unop(lambda x: f'Matrix.Rotation(({x}) * tau, 4, "Z")'),
  'R': binop(lambda ps: f'Matrix.Rotation(({ps[1]}) * tau, 4, {ps[0]})'),

  'Sx': unop(lambda x: f'Matrix.Scale({x}, 4, "X")'),
  'Sy': unop(lambda x: f'Matrix.Scale({x}, 4, "Y")'),
  'Sz': unop(lambda x: f'Matrix.Scale({x}, 4, "Z")'),
  'S': binop(lambda ps: f'Matrix.Scale({ps[1]}, 4, {ps[0]})')})
