"""
Lexical scoping.

BlendScript doesn't parse arbitrary identifiers. Instead, it waits for you to
define a variable and then modifies the parser to recognize that variable,
dropping in a reference to the variable alongside its calculated type when you
refer to it. This is all done lexically, just like lambda scoping in Python.
"""

from .peg import *


class scope:
  """
  A lexical scope that binds names to val objects. Those bindings take
  precedence over operator parsing, so you should make sure the identifier
  space is disjoint from operators you might care about.

  Scopes are mutable in two ways. First, you can bind new variables; and
  second, you can enter sub-scopes that persist until you pop them. Mutability
  is required within a parser-combinator context because expressions will refer
  to the scope as a parse element.

  Structurally, scope() is just an alt() that has some convenience functions
  for dealing with dsp() entries.
  """

  def __init__(self, parser_lambda, binding_dsp):
    self.dsps   = [parser(binding_dsp)]
    self.parser = parser(parser_lambda(parserify(self)))

  def __call__(self, source, index):
    for d in self.dsps.reverse():
      r, i = d(source, index)
      if i is not None: return (r, i)
    return self.parser(source, index)

  def bind(self, **bindings):
    """
    Adds bindings to the innermost scope. The bindings must be new for that
    scope; you can't replace bindings that already exist.
    """
    self.dsps[-1].add(**bindings)
    return self

  def subscope(self, binding_dsp=dsp()):
    """
    Creates a new subscope around the specified dsp.
    """
    self.dsps.append(parser(binding_dsp))
    return self

  def exit_subscope(self):
    """
    Removes the innermost scope, discarding its bindings.
    """
    self.dsps.pop()
    return self
