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

  '_':  const(t_any,     empty),
  '.':  const(t_dynamic, empty),
  'I':  const(t_int,     empty),
  'B':  const(t_bool,    empty),
  'N':  const(t_number,  empty),
  'S':  const(t_string,  empty),
  'V2': const(t_vec2,    empty),
  'V3': const(t_vec3,    empty),
  'V4': const(t_vec4,    empty),
  'M3': const(t_mat33,   empty),
  'M4': const(t_mat44,   empty),

  '[]': pmap(t_list, type_expr),
  '->': pmaps(t_fn, seq(type_expr, type_expr))})
