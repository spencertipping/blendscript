"""
Value parsers.

Parsers for blendscript values. Types have a separate grammar that is used
contextually within value-expressions.
"""

from .peg   import *
from .basic import *
from .expr  import *
from .types import *

from ..compiler.val import *


val_expr = expr_grammar()

val_expr.last_resort.add(
  lambda_let_binding(val_expr, alt(p_lword, re(r"'([^\s()\[\]{}]+)"))))

val_expr.literals.add(
  pmap(val.float, p_float),
  pmap(val.int,   p_int),
  pmap(val.str,   re(r'"([^\s()\[\]{}]*)')),

  # Python expressions within {}
  pmaps(lambda t, v: val(t, f'({v})'),
        iseq([1, 2], lit('{'), type_expr, re('([^\}]+)\}'))))

val_expr.ops.add(**{
  '(': iseq(0, val_expr, lit(')')),
  '[': pmaps(val.list, iseq(0,
                            rep(iseq(0, val_expr, maybe(lit(',')))),
                            whitespaced(lit(']')))),

  '?':  pmaps(lambda x, y, z: x.__if__(y, z), exactly(3, val_expr)),

  # TODO: rewrite these
  '\\': pmap(lambda ps: f'_fn(lambda {ps[0] or "_"}: {ps[1]})',
             seq(maybe(p_lword), val_expr)),
  ':': pmap(lambda ps: f'(lambda {ps[0]}: {ps[2]})({ps[1]})',
            seq(p_lword, val_expr, val_expr))})