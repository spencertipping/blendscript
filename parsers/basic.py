"""
Basic building blocks for grammars.
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
  return pflatmap(
    pmaps(
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
