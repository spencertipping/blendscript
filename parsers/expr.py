"""
Vector/matrix/numeric expressions.

BlendScript implements a Polish-notation calculator you can use to build vector
and matrix expressions. The result is compiled into a Python function.
"""

from mathutils import Vector
from itertools import chain

from .combinators import *
from .basic       import *
from .function    import *


expr_globals = {}
"""
All global values available to compiled code. Modify this with
defexprglobals().
"""

expr_ops      = dsp()
expr_literals = alt()

expr = pmap(lambda xs: xs[1], seq(maybe(p_ignore),
                                  alt(expr_ops, expr_literals),
                                  maybe(p_ignore)))
"""
A recursive grammar element that evaluates to any expression, possibly
surrounded by whitespace and comments.
"""

compiled_expr = pmap(
  lambda body: eval(f'lambda: {body}', expr_globals),
  expr)


def defexprop(**ps):
  """
  Defines new operators, each with a constant string prefix.
  """
  expr_ops.add(**ps)

def defexprliteral(*ps):
  """
  Defines new literal forms, each a bare parser consuming input and producing a
  Python expression as a string.
  """
  expr_literals.add(*ps)

def defexprglobals(**gs):
  """
  Binds new globals within the compiled environment.
  """
  for g, v in gs.items():
    if g in expr_globals and expr_globals[g] != v:
      raise Exception(f'defexprglobals: {g} is already defined as a different value')
    expr_globals[g] = v


defexprliteral(
  pmap(lambda n:  f'({n})', p_float),
  pmap(lambda n:  f'({n})', p_int),
  pmap(lambda ps: f'[{",".join(ps[1])}]', seq(re(r'\['), rep(expr), re(r'\]'))),

  # Parens have no effect, they just help legibility
  pmap(lambda ps: ps[1], seq(re(r'\('), expr, re(r'\)'))),

  # Python expressions within {}
  pmap(lambda ms: f'({ms[0].decode()})', re(r'\{([^\}]+)\}')),

  # A currying marker: +3; is the same as (+3) but one byte shorter
  const(None, re(r';')),

  # Underscore always parses as a single identifier, even when immediately
  # followed by ident characters.
  pmap(lambda b: b.decode(), re(r'_')),

  # Last resort: assume it's a variable. In practice this case will probably
  # get used frequently.
  p_lword)


defexprglobals(FN=fn)

def unop(f):
  return pmap(lambda x: f(x)
              if x is not None
              else f'FN(lambda _x: {f("_x")})',
              maybe(expr))

def binop(f):
  return pmap(lambda xs: f(*xs)
              if xs[1] is not None
              else f'FN(lambda _x: {f(xs[0], "_x")})',
              seq(expr, maybe(expr)))

def ternop(f):
  return pmap(lambda xs: f(*xs)
              if xs[2] is not None
              else f'FN(lambda _x: {f(xs[0], xs[1], "_x")})',
              seq(expr, expr, maybe(expr)))


defexprglobals(Vector=Vector, reduce=reduce, chain=chain)

defexprop(**{
  'x':   unop(lambda x:       f'Vector(({x},0,0))'),
  'y':   unop(lambda y:       f'Vector((0,{y},0))'),
  'z':   unop(lambda z:       f'Vector((0,0,{z}))'),
  'xy': binop(lambda x, y:    f'Vector(({x},{y},0))'),
  'xz': binop(lambda x, z:    f'Vector(({x},0,{z}))'),
  'yz': binop(lambda y, z:    f'Vector((0,{y},{z}))'),
  'v': ternop(lambda x, y, z: f'Vector(({x},{y},{z}))'),

  'i': unop(lambda n: f'range(int({n}))'),
  'L': unop(lambda x: f'list({x})'),

  '>':  binop(lambda x, y: f'({y} > {x})'),
  '>=': binop(lambda x, y: f'({y} >= {x})'),
  '<':  binop(lambda x, y: f'({y} < {x})'),
  '<=': binop(lambda x, y: f'({y} <= {x})'),
  '==': binop(lambda x, y: f'({y} == {x})'),
  '!':  unop( lambda x:    f'(not {x})'),
  '&':  binop(lambda x, y: f'({y} and {x})'),
  '|':  binop(lambda x, y: f'({y} or {x})'),

  '?':  ternop(lambda x, y, z: f'({y} if {x} else {z})'),

  '\\': pmap(lambda ps: f'FN(lambda {ps[0] or "_"}: {ps[1]})',
             seq(maybe(p_lword), expr)),
  '::': pmap(lambda ps: f'(lambda {ps[0]}: {ps[2]})({ps[1]})',
             seq(p_lword, expr, expr)),

  '@':  binop(lambda x, y: f'({y}({x}))'),
  '@*': binop(lambda x, y: f'({y}(*{x}))'),

  '.:': pmap(lambda ps: f'{ps[1]}.{ps[0]}', seq(p_word, expr)),
  '.@': pmap(lambda ps: f'{ps[2]}.{ps[0]}(*{ps[1]})',
             seq(p_word, expr, expr)),

  '/#': unop(lambda x: f'len({x})'),

  '`': binop(lambda i, xs: f'({xs}[int({i})])'),
  '`[': pmap(lambda ps: f'({",".join(ps[0])},)[-1]',
             seq(rep(expr, min=1), re(r'\]'))),

  '**': binop(lambda x, y: f'({y} ** {x})'),
  '++': unop( lambda x:    f'list(chain(*({x})))'),

  '+': binop(lambda x, y: f'({x} + {y})'),
  '-': unop( lambda x:    f'(- {x})'),
  '*': binop(lambda x, y: f'({x} * {y})'),
  '/': binop(lambda x, y: f'({y} / {x})'),
  '%': binop(lambda x, y: f'({y} % {x})'),
  '.': binop(lambda x, y: f'({x} @ {y})')})
