"""
Parsers that produce types. This is used to provide type constraints for
function arguments.
"""

from .peg   import *
from .basic import *

from ..compiler.types import *


type_ops  = dsp()
type_expr = whitespaced(type_ops)

type_ops.add(**{
  ':':  const(t_none,   empty),
  'i':  const(t_int,    empty),
  'n':  const(t_number, empty),
  's':  const(t_string, empty),
  'v2': const(t_vec2,   empty),
  'v3': const(t_vec3,   empty),
  'v4': const(t_vec4,   empty),
  'm3': const(t_mat33,  empty),
  'm4': const(t_mat44,  empty),

  '[':  pmap(t_list, iseq(0, type_expr, lit(']'))),
  '->': pmaps(t_fn, seq(type_expr, type_expr))})
