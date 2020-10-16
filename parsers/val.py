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

def associate_fncalls(xs):
  """
  Looks holistically at a series of terms placed next to each other and finds a
  way to associate those terms such that no function is overapplied. Normally
  function application associates leftward in curried languages, but we want to
  modify that when it's clear that leftward association wasn't what the user
  intended. For example, "+ 1 * 2 3" should be understood as ((+ 1) ((* 2) 3)),
  not ((((+ 1) *) 2) 3). We understand it this way because (+) has arity 2 --
  that means it can't be applied to four arguments.
  """
  ...


val_expr = pmap(associate_fncalls, plus(val_atom))


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
