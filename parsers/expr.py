"""
Expression grammars.
"""

from .peg import *


p_comment    = re(r'#\s+.*\n?')
p_whitespace = re(r'\s+')
p_ignore     = rep(alt(p_whitespace, p_comment), min=1)

def whitespaced(p):
  """
  Wraps a parser with optional BlendScript whitespace.
  """
  return iseq(1, maybe(p_ignore), p, maybe(p_ignore))


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
  def __init__(self, modifier=whitespaced):
    self.ops      = dsp()
    self.literals = alt()
    self.bindings = dsp()
    self.parser   = modifier(alt(self.ops, self.literals, self.bindings))
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
  last-resort parsing, and a stack of scopes.
  """
  def __init__(self, modifier=whitespaced):
    self.last_resort = alt()
    self.top_scope   = scope()
    self.ops         = self.top_scope.ops
    self.literals    = self.top_scope.literals
    self.scopes      = alt(self.last_resort, self.top_scope)
    self.parser      = modifier(self.scopes)
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
      outer.scopes.add(scope)
      v, i2 = outer(s, i)
      outer.scopes.pop()
      return (v, i2)
    return parserify(p)
