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


val_atom = expr_grammar()

val = alt()
val.add(iseq(1, lit('('), val, lit(')')))

val_applied = pmap(
  ...,
  plus(val_atom)
)

val_atom.last_resort.add(
  lambda_let_binding(val_atom, alt(p_lword, re(r"'([^\s()\[\]{}]+)"))))

val_atom.literals.add(
  pmap(val.float, p_float),
  pmap(val.int,   p_int),
  pmap(val.str,   re(r'"([^\s()\[\]{}]*)')),

  # Python expressions within {}
  pmaps(lambda t, v: val(t, f'({v})'),
        iseq([1, 2], lit('{'), type_expr, re('([^\}]+)\}'))))

val_atom.ops.add(**{
  '[': pmaps(val.list, iseq(0,
                            rep(iseq(0, val, maybe(lit(',')))),
                            whitespaced(lit(']')))),

  '?': pmaps(lambda x, y, z: x.__if__(y, z), exactly(3, val_atom))})
