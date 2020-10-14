"""
Parsers that produce types.

These parsers are used to provide type constraints for function arguments, and
anywhere else where a type constraint might be necessary.
"""

from .peg   import *
from .basic import *

from ..compiler.types import *


type_ops  = dsp()
type_expr = whitespaced(type_ops)

type_ops.add(**{
  '(':  iseq(0, type_expr, lit(')')),

  ':':  const(t_none,   empty),
  '_':  const(t_any,    empty),
  'i':  const(t_int,    empty),
  'n':  const(t_number, empty),
  's':  const(t_string, empty),
  'v2': const(t_vec2,   empty),
  'v3': const(t_vec3,   empty),
  'v4': const(t_vec4,   empty),
  'm3': const(t_mat33,  empty),
  'm4': const(t_mat44,  empty),

  '[]': pmap(t_list, type_expr),
  '->': pmaps(t_fn, seq(type_expr, type_expr))})
