"""
BlendScript implements a Polish-notation calculator you can use to build vector
and matrix expressions. The result is compiled into a Python function.
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

  def __call__(self, source, index):
    return self.parser(source, index)

  def bind(self, **bindings):
    for b, v in bindings.items():
      self.bindings.add(**{b: const(v, empty)})
    return self


expr_last_resort = alt()
expr = alt(expr_last_resort, scope())

def scoped_expr(scope):
  """
  Returns a parser that applies an additional scope layer while parsing its
  next expression.
  """
  def p(s, i):
    expr.add(scope)
    v, i2 = expr(s, i)
    expr.pop()
    return (v, i2)
  return parserify(p)


unbound_name = p_lword
let_binding = pflatmap(
  pmaps(lambda n, v: scoped_expr(scope().bind(**{n: v})),
        seq(unbound_name, expr)))

expr_last_resort.add(let_binding)


expr.last().literals.add(
  pmap(val.float, p_float),
  pmap(val.int,   p_int),
  pmap(val.str,   iseq(1, re(r"'"), p_word)),

  # Python expressions within {}
  pmaps(lambda v, t, _: val(t, v),
        iseq([1, 2], lit('{'), type_expr, re('([^\}]+)\}'))))


def list_type(xs):
  if len(xs) == 0: return t_dynamic
  return reduce(lambda x, y: x.upper_bound(y), (x.t for x in xs))


expr.last().ops.add(**{
  '(': iseq(0, expr, lit(')')),

  '[': pmap(lambda v: val.list(list_type(v), *v),
            iseq(0, rep(iseq(0, expr, maybe(lit(',')))),
                 whitespaced(lit(']')))),

  '?':  pmaps(lambda x, y, z: x.__if__(y, z), rep(expr, min=3, max=3)),

  '\\': pmap(lambda ps: f'_fn(lambda {ps[0] or "_"}: {ps[1]})',
             seq(maybe(p_lword), expr)),
  ':': pmap(lambda ps: f'(lambda {ps[0]}: {ps[2]})({ps[1]})',
            seq(p_lword, expr, expr))})
