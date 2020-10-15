"""
Basic building blocks for grammars.
"""

from .peg  import *
from .expr import *


p_word  = re(r'[A-Za-z][A-Za-z0-9_\.]*')
p_lword = re(r'[a-z][A-Za-z0-9_\.]*')

p_int   = pmap(int,   re(r'-?\d+'))
p_float = pmap(float, re(r'-?\d*\.\d(?:\d*(?:[eE][-+]?\d+)?)?',
                         r'-?\d+\.(?:\d*)?(?:[eE][-+]?\d+)?'))


def let_binding(unbound_name, expr):
  """
  Opportunistic let-binding when an unbound name is encountered. The unbound
  name followed by its binding creates a subcontext in which that name is
  bound.
  """

  # TODO: make a real let-binding in Python; we don't want the parser to
  # copy/paste subexpressions.
  return pflatmap(
    pmaps(lambda n, v: expr.scoped_subexpression(scope().bind(**{n: v})),
          seq(unbound_name, expr)))
