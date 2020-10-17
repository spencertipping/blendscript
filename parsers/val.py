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
from ..runtime.fn   import fn


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

  This all leads to an obvious question: what happens when there are multiple
  functions that can be reduced? When that ambiguity exists, we prefer to leave
  toplevel functions undersaturated, consuming arguments in as many
  sub-functions as we can.
  """
  vs        = [xs[0]]
  rem_arity = len(xs)

  for x in xs[1:]:
    rem_arity -= 1
    if vs[-1].t.value_arity() < 0:
      vs[-1] = vs[-1](x)
    elif rem_arity > vs[-1].t.value_arity() and x.t.arg_type() is not None:
      # We need to reduce arity because the head expression isn't a dynamic and
      # we have too many arguments. Begin collapsing them opportunistically.
      # Note that dynamics aren't opportunistic functions; folding happens only
      # when the type of a value is known to be a function.
      vs.append(x)
    else:
      # Apply the top value to x. Back out of paren-groups as long as the top
      # values are saturated, since we wouldn't be able to apply those to any
      # further values.
      vs[-1] = vs[-1](x)
      while vs[-1].t.value_arity() == 0 and len(vs) > 1:
        v = vs.pop()
        vs[-1] = vs[-1](v)

  while len(vs) > 1:
    v = vs.pop()
    vs[-1] = vs[-1](v)

  return vs[-1]


def add_fncalls(atom): return pmap(associate_fncalls, plus(atom))
val_expr = add_fncalls(val_atom)


val_atom.last_resort.add(
  lambda_let_binding(val_atom, add_fncalls, alt(p_lword, re(r"'([^\s()\[\]{}]+)"))))

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
                            rep(iseq(0, val_expr, maybe(lit(',')))),
                            whitespaced(lit(']')))),

  '\\': pflatmap(
    pmaps(lambda an, at: lambda_parser(val_atom, add_fncalls,
                                       an or "_", at or typevar()),
          seq(maybe(p_varname), maybe(type_expr)))),

  '?': pmaps(lambda x, y, z: x.__if__(y, z), exactly(3, val_atom))})
