"""
Value parsers.

Parsers for blendscript values. Types have a separate grammar that is used
contextually within value-expressions.
"""

import ast

from .peg   import *
from .basic import *
from .expr  import *
from .types import *

from ..compiler.val import *
from ..runtime.fn   import fn


val_atom = expr_grammar()
val_expr = add_fncalls(val_atom)


val_atom.literals.add(
  iseq(1, lit('('), val_expr, lit(')')),

  pflatmap(
    const(lambda_let_binding(val_atom, add_fncalls, re(r':([^:\s()\[\]{}]+)')),
          empty)),

  pmap(val.int,   p_int),
  pmap(val.float, p_float),
  pmap(val.str,   re(r'"([^\s()\[\]{}]*)')),

  # Python expressions within {}
  pmaps(lambda t, v: val(t, ast.parse(v).body[0].value),
        iseq([1, 2], lit('{'), type_expr, re('([^\}]+)\}'))))

val_atom.ops.add(**{
  '[': pmaps(val.list, iseq(0,
                            rep(iseq(0, val_expr, maybe(lit(',')))),
                            whitespaced(lit(']')))),

  '\\': pflatmap(
    pmaps(lambda an, at: lambda_parser(val_atom, add_fncalls,
                                       an or "_", at or typevar()),
          seq(maybe(p_varname), maybe(type_expr)))),

  '?': pmaps(lambda x, y, z: x.__if__(y, z), exactly(3, val_atom))})
