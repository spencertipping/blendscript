"""
Vector/matrix/numeric expressions.

BlendScript implements a Polish-notation calculator you can use to build vector
and matrix expressions. The result is compiled into a Python function.
"""

from mathutils import Matrix, Vector
from functools import reduce
from itertools import chain

from .combinators import *
from .basic       import *


expr_globals = {}
"""
All global values available to compiled code. Modify this with
defexprglobals().
"""

expr_ops  = dsp()
expr_lits = alt()

expr = pmap(lambda xs: xs[1], seq(maybe(p_ignore),
                                  alt(expr_ops, expr_lits),
                                  maybe(p_ignore)))
"""
A recursive grammar element that evaluates to any expression, possibly
surrounded by whitespace and comments.
"""

compiled_expr = pmap(
  lambda body: eval(f'lambda state: {body}', expr_globals),
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
  expr_lits.add(*ps)

def defexprglobals(**gs):
  """
  Binds new globals within the compiled environment.
  """
  for g, v in gs.items():
    if g in expr_globals:
      raise Exception(f'defexprglobals: {g} is already defined')
    expr_globals[g] = v


defexprglobals(Vector=Vector, Matrix=Matrix, chain=chain)

defexprliteral(
  pmap(lambda n:  f'({n})', p_float),
  pmap(lambda n:  f'({n})', p_int),
  pmap(lambda ps: f'[{",".join(ps[1])}]', seq(re(r'\['), rep(expr), re(r'\]'))),

  # Parens have no effect, they just help legibility
  pmap(lambda ps: ps[1], seq(re(br'\('), expr, re(br'\)'))),

  pmap(lambda ps: f'(state["{ps[1].decode()}"])', seq(re(r':'), p_word)),

  # Python expressions within {}
  pmap(lambda ms: f'({ms[0].decode()})', re(br'\{([^\}]+)\}')),

  # TODO: better lambda arg syntax (should just bind a name)
  const('state.get_arg()', re(br'_')))

def unop(f):   return pmap(f, expr)
def binop(f):  return pmap(lambda xs: f(*xs), seq(expr, expr))
def ternop(f): return pmap(lambda xs: f(*xs), seq(expr, expr, expr))

defexprop(**{
  'x': unop(lambda x: f'Vector(({x},0,0))'),
  'y': unop(lambda y: f'Vector((0,{y},0))'),
  'z': unop(lambda z: f'Vector((0,0,{z}))'),

  'i': unop(lambda n: f'range(int({n}))'),

  '>':  binop(lambda x, y: f'({y} > {x})'),
  '>=': binop(lambda x, y: f'({y} >= {x})'),
  '<':  binop(lambda x, y: f'({y} < {x})'),
  '<=': binop(lambda x, y: f'({y} <= {x})'),
  '==': binop(lambda x, y: f'({y} == {x})'),
  '!':  unop( lambda x:    f'(not {x})'),
  '&':  binop(lambda x, y: f'({y} and {x})'),
  '|':  binop(lambda x, y: f'({y} or {x})'),

  '?': ternop(lambda x, y, z: f'({y} if {x} else {z})'),
  '$': ternop(lambda x, y, z: f'state.lerp({x}, {y}, {z})'),

  # TODO: fix lambda stuff; these can probably just be python functions, not
  # state-things
  '\\': unop(lambda x: f'(lambda state: {x})'),
  '@':  binop(lambda x, y: f'(state.invoke({y}, {x}))'),

  '.':  pmap(lambda ps: f'{ps[1]}.{ps[0].decode()}', seq(p_word, expr)),
  '.@': pmap(lambda ps: f'{ps[2]}.{ps[0].decode()}(*{ps[1]})',
             seq(p_word, expr, expr)),

  '*\\': binop(lambda x, y: f'[state.invoke(lambda state: {x}, v) for v in {y}]'),
  '%\\': binop(lambda x, y: f'[v for v in {y} if state.invoke(lambda state: {x})]'),
  '/\\': ternop(
    lambda x, y, z:
    f'reduce(lambda x, y: state.invoke(lambda state: {y}, [x, y]), {z}, {x})'),

  '`': binop(lambda x, y: f'({y}[int({x})])'),

  '**': binop(lambda x, y: f'({y} ** {x})'),
  '++': unop( lambda x:    f'list(chain(*({x})))'),

  '+': binop(lambda x, y: f'({x} + {y})'),
  '-': unop( lambda x:    f'(- {x})'),
  '*': binop(lambda x, y: f'({x} * {y})'),
  '/': binop(lambda x, y: f'({y} / {x})'),
  '%': binop(lambda x, y: f'({y} % {x})'),
  '.': binop(lambda x, y: f'({x} @ {y})'),

  'v': ternop(lambda x, y, z: f'Vector(({x}, {y}, {z}))'),

  'L': pmap(lambda ps:
            f'(state.let("{ps[1].decode()}", {ps[2]}, lambda state: {ps[3]}))',
            seq(maybe(p_ignore), p_word, expr, expr)),

  '=': pmap(lambda ps:
            f'(state.set("{ps[1].decode()}", {ps[2]}), {ps[3]})[1]',
            seq(maybe(p_ignore), p_word, expr, expr))})


# TODO: figure out what we're doing with eval_state and dynamically-scoped
# semantics. Could be a cool thing if we rely only on state methods; then we
# have context-sensitive semantic overloading.

class expr_eval_state:
  """
  Dynamic state for expression evaluation. This state tracks local variables,
  transformation matrices, and any other relevant stuff.
  """
  def __init__(self, *vs, arg=None, parent=None):
    self.parent = parent
    self.arg    = arg
    self.vs     = dict(vs)

  def __getitem__(self, v):
    if v in self.vs: return self.vs[v]
    return None if self.parent is None else self.parent[v]

  def let(self, v, val, expr):
    return expr(expr_eval_state((v, val), parent=self))

  def set(self, v, val):
    self.vs[v] = val
    return self

  def invoke(self, fn, arg):
    return fn(expr_eval_state(arg=arg, parent=self))

  def get_arg(self):
    return self.arg if self.arg is not None else self.parent.get_arg()

  def lerp(self, f, x, y):
    return x * (1 - f) + y * f
