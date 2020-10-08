"""
Vector/matrix/numeric expressions.

BlendScript implements a Polish-notation calculator you can use to build vector
and matrix expressions. The result is compiled into a Python function.
"""

from mathutils import Matrix, Vector
from functools import reduce

from .combinators import *
from .basic       import *

expr_globals = {
  'Vector': Vector,
  'Matrix': Matrix
}

exprs = alt()
expr  = pmap(lambda xs: xs[1], seq(maybe(p_ignore), exprs, maybe(p_ignore)))

compiled_expr = pmap(
  lambda body: eval(f'lambda state: {body}', expr_globals),
  expr)

exprs.append(
  pmap(lambda n: f'({n})', p_float),
  pmap(lambda n: f'({n})', p_int),

  pmap(lambda ps: f'Vector(({ps[1]},0,0))', seq(re(br'x'), expr)),
  pmap(lambda ps: f'Vector((0,{ps[1]},0))', seq(re(br'y'), expr)),
  pmap(lambda ps: f'Vector((0,0,{ps[1]}))', seq(re(br'z'), expr)),

  pmap(lambda ps: f'range(int({ps[1]}))', seq(re(br'i'), expr)),

  pmap(lambda ps: f'({ps[2]} > {ps[1]})',   seq(re(br'>'),  expr, expr)),
  pmap(lambda ps: f'({ps[2]} >= {ps[1]})',  seq(re(br'>='), expr, expr)),
  pmap(lambda ps: f'({ps[2]} < {ps[1]})',   seq(re(br'<'),  expr, expr)),
  pmap(lambda ps: f'({ps[2]} <= {ps[1]})',  seq(re(br'<='), expr, expr)),
  pmap(lambda ps: f'({ps[2]} == {ps[1]})',  seq(re(br'=='), expr, expr)),
  pmap(lambda ps: f'(not {ps[1]})',         seq(re(br'!'),  expr)),
  pmap(lambda ps: f'({ps[2]} and {ps[1]})', seq(re(br'&'),  expr, expr)),
  pmap(lambda ps: f'({ps[2]} or {ps[1]})',  seq(re(br'\|'), expr, expr)),

  pmap(lambda ps: f'({ps[2]} if {ps[1]} else {ps[3]})',
       seq(re(br'\?'), expr, expr, expr)),

  pmap(lambda ps: f'state.lerp({ps[1]}, {ps[2]}, {ps[3]})',
       seq(re(br'\$'), expr, expr, expr)),

  pmap(lambda ps: f'(lambda state: {ps[1]})', seq(re(br'\\'), expr)),
  pmap(lambda ps: f'(state.invoke({ps[1]}, {ps[2]}))',
       seq(re(br'@'), expr, expr)),

  pmap(lambda ps: f'{ps[3]}.{ps[1].decode()}(*{ps[2]})',
       seq(re(br'\.@'), p_word, expr, expr)),
  pmap(lambda ps: f'{ps[2]}.{ps[1].decode()}', seq(re(br'\.'), p_word, expr)),

  pmap(lambda ps: f'[{",".join(ps[1])}]',
       seq(re(br'\['), rep(expr), re(br'\]'))),

  const('state.get_arg()', re(br'_')),

  pmap(lambda ps: f'[state.invoke(x, lambda state: {ps[1]}) for x in {ps[2]}]',
       seq(re(br'\*\\'), expr, expr)),
  pmap(lambda ps: f'[x for x in {ps[2]} if state.invoke(x, lambda state: {ps[1]})]',
       seq(re(br'%\\'), expr, expr)),
  pmap(lambda ps: f'reduce(lambda x, y: state.invoke([x, y], lambda state: {ps[2]}), {ps[3]}, {ps[1]})',
       seq(re(br'/\\'), expr, expr, expr)),

  pmap(lambda ps: f'({ps[2]}[int({ps[1]})])', seq(re(br'`'), expr, expr)),

  pmap(lambda ps: f'({ps[2]} ** {ps[1]})', seq(re(br'\*\*'), expr, expr)),

  pmap(lambda ps: f'({ps[1]} + {ps[2]})', seq(re(br'\+'), expr, expr)),
  pmap(lambda ps: f'(- {ps[1]})',         seq(re(br'-'),  expr)),
  pmap(lambda ps: f'({ps[1]} * {ps[2]})', seq(re(br'\*'), expr, expr)),
  pmap(lambda ps: f'({ps[2]} / {ps[1]})', seq(re(br'/'),  expr, expr)),
  pmap(lambda ps: f'({ps[2]} % {ps[1]})', seq(re(br'%'),  expr, expr)),
  pmap(lambda ps: f'({ps[1]} @ {ps[2]})', seq(re(br'\.'), expr, expr)),

  pmap(lambda xs: f'Vector(({xs[1]}, {xs[2]}, {xs[3]}))',
       seq(re(br'v'), expr, expr, expr)),

  pmap(lambda ps: ps[1], seq(re(br'\('), expr, re(br'\)'))),

  pmap(lambda ps: f'(state["{ps[1]}"])', seq(re(br':'), p_word)),
  pmap(lambda ps: f'(state.let("{ps[1]}", {ps[2]}, lambda state: {ps[3]}))',
       seq(re(br'l\s*'), p_word, expr, expr)),

  pmap(lambda ps: f'(state.set("{ps[1]}", {ps[2]}), {ps[3]})[1]',
       seq(re(br'=\s*'), p_word, expr, expr)),

  # Python expressions within {}
  pmap(lambda ms: f'({ms[0].decode()})', re(br'\{([^\}]+)\}')),
)

class expr_state:
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
    return expr(expr_state((v, val), parent=self))

  def set(self, v, val):
    self.vs[v] = val
    return self

  def invoke(self, arg, fn):
    return fn(expr_state(arg=arg, parent=self))

  def get_arg(self):
    return self.arg if self.arg is not None else self.parent.get_arg()

  def lerp(self, f, x, y):
    return x * (1 - f) + y * f
