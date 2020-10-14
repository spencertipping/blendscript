"""
BlendScript implements a Polish-notation calculator you can use to build vector
and matrix expressions. The result is compiled into a Python function.
"""

from itertools import chain

from .peg               import *
from .basic             import *
from .types             import *

from ..compiler.val     import *
from ..runtime.fn       import *
from ..runtime.method   import *


expr_ops      = dsp()
expr_literals = alt()
expr_var      = p_lword
expr          = whitespaced(alt(expr_ops, expr_literals, expr_var))

compiled_expr = pmap(method('compile'), expr)


expr_literals.add(
  pmap(val.float, p_number),
  pmap(val.str, iseq(1, re(r"'"), p_word)),

  # Python expressions within {}
  pmaps(lambda v, t, _: val(t, v),
        seq(re(r'\{([^\}:]+)::'), type_expr, lit('}'))),

  # Underscore always parses as a single identifier, even when immediately
  # followed by ident characters.
  re(r'_'))


# TODO: convert the partial applications to section() objects once we have them
# (this will enable more specific coercion logic)
def unop(f):
  return pmap(lambda x: f(x)
              if x is not None
              else f'_fn(lambda _x: {f("_x")})',
              maybe(expr))

def binop(f):
  return pmap(lambda xs: f(*xs)
              if xs[1] is not None
              else f'_fn(lambda _x: {f(xs[0], "_x")})',
              seq(expr, maybe(expr)))

def ternop(f):
  return pmap(lambda xs: f(*xs)
              if xs[2] is not None
              else f'_fn(lambda _x: {f(xs[0], xs[1], "_x")})',
              seq(expr, expr, maybe(expr)))


def keyify(x): return x if type(x) == str else int(x)

expr_ops.add(**{
  '(': iseq(0, expr, lit(')')),

  'I': unop(lambda n: f'_range(_int({n}))'),
  'L': unop(lambda x: f'_tuple({x})'),

  '[': pmap(lambda v: val.list(t_free, *v),
            iseq(0, rep(expr), whitespaced(lit(']')))),

  '>':  binop(lambda x, y: f'({y} > {x})'),
  '>=': binop(lambda x, y: f'({y} >= {x})'),
  '<':  binop(lambda x, y: f'({y} < {x})'),
  '<=': binop(lambda x, y: f'({y} <= {x})'),
  '==': binop(lambda x, y: f'({y} == {x})'),
  '&':  binop(lambda x, y: f'({y} and {x})'),
  '|':  binop(lambda x, y: f'({y} or {x})'),
  '!':   unop(lambda x:    f'(not {x})'),

  '?':  ternop(lambda x, y, z: f'({y} if {x} else {z})'),

  '\\': pmap(lambda ps: f'_fn(lambda {ps[0] or "_"}: {ps[1]})',
             seq(maybe(p_lword), expr)),
  '::': pmap(lambda ps: f'(lambda {ps[0]}: {ps[2]})({ps[1]})',
             seq(p_lword, expr, expr)),

  '@':  binop(lambda x, y: f'({y}({x}))'),
  '@*': binop(lambda x, y: f'({y}(*{x}))'),

  '.:': pmap(lambda ps: f'{ps[1]}.{ps[0]}', seq(p_word, expr)),
  '.@': pmap(lambda ps: f'{ps[2]}.{ps[0]}(*{ps[1]})',
             seq(p_word, expr, expr)),

  '/#': unop(lambda x: f'_len({x})'),

  '`': binop(lambda i, xs: f'({xs}[_keyify({i})])'),

  '**': binop(lambda x, y: f'({y} ** {x})'),
  '++':  unop(lambda x:    f'_tuple(_chain(*({x})))'),

  '+': binop(lambda x, y: f'({x} + {y})'),
  '-':  unop(lambda x:    f'(- {x})'),
  '*': binop(lambda x, y: f'({x} * {y})'),
  '/': binop(lambda x, y: f'({y} / {x})'),
  '%': binop(lambda x, y: f'({y} % {x})'),
  '.': binop(lambda x, y: f'({x} @ {y})')})
