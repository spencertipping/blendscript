"""
Parsers that produce types.

These parsers are used to provide type constraints for function arguments, and
anywhere else where a type constraint might be necessary.
"""

from .peg   import *
from .basic import *
from .expr  import *

from ..compiler.types import *


# TODO: easier currying for ->; we should have it be arbitrarily applicable, so
# you could write (-> a b c d) and end up with d -> c -> b -> a or something.

type_expr = expr_grammar()

type_expr.ops.add(**{
  '(':  iseq(0, type_expr, lit(')')),
  '[]': pmap(t_list, type_expr),
  '->': pmaps(t_fn, seq(type_expr, type_expr))})

type_expr.bind(**{
  '.': t_dynamic,
  'I': t_int,
  'B': t_bool,
  'N': t_number,
  'S': t_string})
