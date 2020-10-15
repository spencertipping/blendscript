"""
Basic building blocks for grammars.
"""

from .peg  import *
from .expr import *

from ..compiler.val import *


p_word  = re(r'[A-Za-z][A-Za-z0-9_\.]*')
p_lword = re(r'[a-z][A-Za-z0-9_\.]*')

p_int   = pmap(int,   re(r'-?\d+'))
p_float = pmap(float, re(r'-?\d*\.\d(?:\d*(?:[eE][-+]?\d+)?)?',
                         r'-?\d+\.(?:\d*)?(?:[eE][-+]?\d+)?'))


def rewrite_let_binding(expr, unbound_name):
  """
  Parse-time let binding and rewriting.

  Note that this let-binding applies as a _rewrite_, not as a normal lambda
  expression. For a lambda expression, use lambda_let_binding.
  """
  return pflatmap(
    pmaps(lambda n, v: expr.scoped_subexpression(scope().bind(**{n: v})),
          seq(unbound_name, expr)))


def lambda_let_binding(expr, unbound_name):
  """
  Runtime let-binding and parse extension.
  """
  def bind(n, v):
    var_entry = val.var_ref(v.t, n)
    return pmap(
      lambda e: val.bind_var(n, v, e),
      expr.scoped_subexpression(scope().bind(**{n: var_entry})))

  return pflatmap(pmaps(bind, seq(unbound_name, expr)))
