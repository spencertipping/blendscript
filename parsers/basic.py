"""
A library of parse elements that are used in multiple places within BlendScript.
"""

from .peg  import *
from .expr import *

from ..compiler.val import *


p_word  = re(r'[A-Za-z][A-Za-z0-9_\.]*')
p_lword = re(r'[a-z][A-Za-z0-9_\.]*')

p_varname = re(r'[a-z][a-z0-9_]*')

p_int   = pmap(int,   re(r'-?\d+'))
p_float = pmap(float, re(r'-?\d*\.\d(?:\d*(?:[eE][-+]?\d+)?)?',
                         r'-?\d+\.(?:\d*)?(?:[eE][-+]?\d+)?'))

p_number = alt(p_float, p_int)


def re_str(r):     return pmap(lambda s: val.lit(t_string, s), re(r))
def p_list(*ps):   return pmap(lambda xs: val.list(*filter(None, xs)), seq(*ps))
def p_lit(t, p):   return pmap(lambda v: val.lit(t, v), p)
def p_typed(t, p): return pmap(lambda v: v.typed(t), p)


def rewrite_let_binding(expr, modifier, unbound_name):
  """
  Parse-time let binding and rewriting.

  Note that this let-binding applies as a _rewrite_, not as a normal lambda
  expression. For a lambda expression, use lambda_let_binding.
  """
  return pflatmap(pmaps(
    lambda n, v: modifier(expr.scoped_subexpression(scope().bind(**{n: v}))),
    seq(unbound_name, expr)))


def lambda_let_binding(expr, modifier, unbound_name):
  """
  Runtime let-binding and parse extension.
  """
  def bind(n, v):
    var_entry = val.var_ref(v.t, n)
    return pmap(
      lambda e: val.bind_var(n, v, e),
      modifier(expr.scoped_subexpression(scope().bind(**{n: var_entry}))))

  return pflatmap(pmaps(bind, seq(unbound_name, expr)))


def lambda_parser(expr, modifier, argname, argtype):
  """
  Parses a lambda body within a subscope, with the specified argname and
  argtype bound as a local variable, returning a lambda val.
  """
  argref = val.var_ref(argtype, argname)
  return pmap(
    lambda e: val.fn(argtype, argname, e),
    modifier(expr.scoped_subexpression(scope().bind(**{argname: argref}))))


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

  # Apply all deferred right-associations.
  while len(vs) > 1:
    v = vs.pop()
    vs[-1] = vs[-1](v)

  return vs[-1]


def add_fncalls(atom):
  return pmap(associate_fncalls, plus(atom))


def list_subscope(atom, subscope):
  """
  Parses a list of values within a subscope. This parser includes the closing
  "]" list delimiter and is intended to be used as the right-hand side of a
  scope ops binding.
  """
  return pflatmap(const(
      pmaps(val.list, iseq(
        0,
        rep(iseq(0,
                 add_fncalls(atom.scoped_subexpression(subscope)),
                 maybe(lit(',')))),
        whitespaced(lit(']')))),
      empty))
