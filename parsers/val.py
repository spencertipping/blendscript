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

def apply_series(xs):
  """
  Walks forwards through a series of values that have been juxtaposed, e.g.
  "f x y z 3", and infers sub-applications based on function arity saturation
  when possible. If no such type information is available, for instance because
  all values have dynamic type, then the sequence is interpreted as it would be
  in Haskell: left-associative function application.

  apply_series is perhaps better understood as trying to infer parentheses
  based on type information. The goal is to make it possible to omit parens in
  common cases; for example, "* 4 + 5 6" -- we obviously don't intend to
  multiply "4" by "+" and then have "5" and "6" be extra values. Instead, we
  should use the type information we have about "+" and "*" to infer that we
  meant "* 4 (+ 5 6)".

  We don't have any concept of precedence in this language. Everything comes
  down to types and argument compatibility. Here's how this works.

  First, we do nothing unless the arguments oversaturate the function -- i.e.
  net saturation is positive. If that's the case:

  1. If the current argument can't be applied to anything, then
  """
  vs = [xs[0]]
  for x in xs[1:]:

    pass

  # Fold up deferred calls
  while len(vs) > 1:
    v = vs.pop()
    vs[-1] = vs[-1](v)

  return v

val_expr = pmap(apply_series, plus(val_atom))


val_atom.last_resort.add(
  lambda_let_binding(val_atom, alt(p_lword, re(r"'([^\s()\[\]{}]+)"))))

val_atom.literals.add(
  iseq(1, lit('('), val_expr, lit(')')),

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
