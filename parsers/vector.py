"""
Vector specifications.

Vectors are specified as a series of operations applied to an initial value, in
this case always the origin.
"""

from .basic       import *
from .combinators import *

from mathutils import Vector
from functools import reduce

vector_op = alt()
p_vector  = pmap(lambda ops: reduce(lambda v, f: f(v), ops, Vector((0, 0, 0))),
                 rep(vector_op, min=1))

# Numeric broadcasting
vector_op.append(
  pmap(lambda x: lambda v: v + Vector((x, x, x)), p_float)
)

# Single-component selection
# TODO: some precedence to make x2y1 work

vector_op.append(
  pmap(lambda v1: lambda v: v + Vector((v1[1][0], 0, 0)), seq(re(b'x'), p_vector)),
  pmap(lambda v1: lambda v: v + Vector((0, v1[1][1], 0)), seq(re(b'y'), p_vector)),
  pmap(lambda v1: lambda v: v + Vector((0, 0, v1[1][2])), seq(re(b'z'), p_vector)),
  pmap(lambda v1: lambda v: v - v1[1], seq(re(b'-'), p_vector)),
  pmap(lambda v1: lambda v: v + Vector((1 / (v1[1][0] or 1),
                                        1 / (v1[1][1] or 1),
                                        1 / (v1[1][2] or 1))),
       seq(re(b'/'), p_vector))
)
