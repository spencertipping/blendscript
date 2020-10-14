"""
BlendScript implements a Polish-notation calculator you can use to build vector
and matrix expressions. The result is compiled into a Python function.
"""

from itertools import chain

from .peg               import *
from .basic             import *
from ..compiler.val     import *
from ..runtime.fn       import *
from ..runtime.method   import *


expr_ops      = dsp()
expr_literals = alt()
expr_var      = p_lword
expr          = whitespaced(alt(expr_ops, expr_literals, expr_var))

compiled_expr = pmap(method('compile'), expr)


# NOTE: we don't parse anything into lists because lists are mutable and thus
# not hashable. Instead, we rely exclusively on tuples to represent sequence
# data.
def qtuple(xs): return f'({",".join(xs)},)' if len(xs) > 0 else '()'
def qargs(xs):  return ','.join(filter(None, xs))

def qmethod_call(m):
  return lambda *args: f'_method_call_op("{m}", {qargs(args)})'

def quoted(p):   return pmap(repr, p)
def kwarg(k, p): return pmap(lambda s: f'{k}={s}', p)


expr_literals.add(
  pmap(lambda n: f'({n})', p_number),

  quoted(iseq(1, re(r"'"), p_word)),

  # Parens have no effect, they just help legibility
  iseq(1, lit('('), expr, lit(')')),

  # Python expressions within {}
  pmap(lambda m: f'({m.decode()})', re(r'\{([^\}]+)\}')),

  # A currying marker: +3; is the same as (+3) but one byte shorter
  const(None, re(r';')),

  # Underscore always parses as a single identifier, even when immediately
  # followed by ident characters.
  pmap(method('decode'), re(r'_')))


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
  'I': unop(lambda n: f'_range(_int({n}))'),
  'L': unop(lambda x: f'_tuple({x})'),

  '[': pmap(qtuple, iseq(0, rep(expr), whitespaced(lit(']')))),

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
  '`[': pmap(lambda ps: f'{qtuple(ps[0])}[-1]',
             seq(rep(expr, min=1), re(r'\]'))),

  '**': binop(lambda x, y: f'({y} ** {x})'),
  '++':  unop(lambda x:    f'_tuple(_chain(*({x})))'),

  '+': binop(lambda x, y: f'({x} + {y})'),
  '-':  unop(lambda x:    f'(- {x})'),
  '*': binop(lambda x, y: f'({x} * {y})'),
  '/': binop(lambda x, y: f'({y} / {x})'),
  '%': binop(lambda x, y: f'({y} % {x})'),
  '.': binop(lambda x, y: f'({x} @ {y})')})
