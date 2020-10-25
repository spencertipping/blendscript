"""
Expression grammars.
"""

from .peg import *


p_comment    = re(r'(?:#\s|(?:NB|FIXME|TODO|Q)\W\s).*\n?')
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
    self.parser1  = modifier(alt(self.bindings, self.literals))
    self.parser2  = modifier(self.ops)

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
    self.scopes      = [self.top_scope]

    self.alt1   = alt(self.top_scope.parser1)
    self.alt2   = alt(self.last_resort, self.top_scope.parser2)
    self.parser = modifier(alt(self.alt2, self.alt1))

    parserify(self)

  def __call__(self, s, i):
    return self.parser(s, i)

  def bind(self, **bindings):
    """
    Binds new values within the innermost scope.
    """
    self.scopes[-1].bind(**bindings)
    return self

  def scoped_subexpression(self, scope):
    """
    Returns a parser that applies an additional scope layer while parsing its
    next expression.
    """
    outer = self
    def p(s, i):
      outer.scopes.append(scope)
      outer.alt1.add(scope.parser1)
      outer.alt2.add(scope.parser2)
      try:
        v, i2 = outer(s, i)
      except Exception as e:
        v, i2 = None, None
        outer.scopes.pop()
        outer.alt1.pop()
        outer.alt2.pop()
        raise e

      outer.scopes.pop()
      outer.alt1.pop()
      outer.alt2.pop()
      return (v, i2)

    return parserify(p)
