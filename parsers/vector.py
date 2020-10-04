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
                 rep(vector_op))

# TODO: vector op design
