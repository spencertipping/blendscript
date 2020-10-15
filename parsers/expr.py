"""
BlendScript implements a Polish-notation calculator you can use to build vector
and matrix expressions. The result is compiled into a Python function.

This module defines the structure of all expression grammars.
"""

from functools import reduce

from .peg           import *
from .basic         import *
from .types         import *

from ..compiler.val import *
from ..runtime.fn   import *


class scope:
  """
  A single scope layer. This consists of a few elements and some accessors to
  modify them:

  1. An ops dsp(), which contains new complex syntax
  2. A literals alt(), which lets you define new open-ended literal parsers
  3. A bound-variable dsp()

  Scopes are unaware of their parents; parenting is managed by a toplevel alt()
  stack.
  """
  def __init__(self):
    self.ops      = dsp()
    self.literals = alt()
    self.bindings = dsp()
    self.parser   = whitespaced(alt(self.ops, self.literals, self.bindings))
    parserify(self)

  def __call__(self, s, i):
    return self.parser(s, i)

  def bind(self, **bindings):
    for b, v in bindings.items():
      self.bindings.add(**{b: const(v, empty)})
    return self


class expr_grammar:
  """
  A lexically-scoped expression grammar with extensible ops, literals,
  last-resort parsing, and scopes.
  """
  def __init__(self):
    self.last_resort = alt()
    self.top_alt     = alt(self.last_resort, scope())
    self.ops         = self.top_alt.last().ops
    self.literals    = self.top_alt.last().literals
    self.parser      = whitespaced(self.top_alt)
    parserify(self)

  def __call__(self, s, i):
    return self.parser(s, i)

  def scoped_subexpression(self, scope):
    """
    Returns a parser that applies an additional scope layer while parsing its
    next expression.
    """
    outer = self
    def p(s, i):
      outer.top_alt.add(scope)
      v, i2 = outer(s, i)
      outer.top_alt.pop()
      return (v, i2)
    return parserify(p)
