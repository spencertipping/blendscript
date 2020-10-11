"""
BlendScript implements a Polish-notation calculator you can use to build vector
and matrix expressions. The result is compiled into a Python function.
"""

from itertools import chain

from .peg      import *
from .basic    import *
from .function import *


expr_globals = {}
"""
All global values available to compiled code. Modify this with
defexprglobals().
"""

expr_ops      = dsp()
expr_literals = alt()
expr_var      = p_lword
expr          = pmap(lambda xs: xs[1],
                     seq(maybe(p_ignore),
                         alt(expr_ops, expr_literals, expr_var),
                         maybe(p_ignore)))

compiled_expr = pmap(lambda body: eval(f'lambda: {body}', expr_globals), expr)


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
      raise Exception(
        f'defexprglobals: {g} is already defined as a different value')
    expr_globals[g] = v


def pylist(xs):  return f'[{",".join(xs)}]'
def pytuple(xs): return f'({",".join(xs)},)'

defexprliteral(
  pmap(lambda n:  f'({n})', p_number),
  pmap(lambda ps: pylist(ps[1]), seq(re(r'\['), rep(expr), re(r'\]'))),

  pmap(lambda ps: f'"{ps[1]}"', seq(re(r"'"), p_word)),

  # Parens have no effect, they just help legibility
  pmap(lambda ps: ps[1], seq(re(r'\('), expr, re(r'\)'))),

  # Python expressions within {}
  pmap(lambda m: f'({m.decode()})', re(r'\{([^\}]+)\}')),

  # A currying marker: +3; is the same as (+3) but one byte shorter
  const(None, re(r';')),

  # Underscore always parses as a single identifier, even when immediately
  # followed by ident characters.
  pmap(lambda b: b.decode(), re(r'_')))


defexprglobals(_fn=fn)

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


defexprglobals(_keyify=keyify,
               _chain=chain,
               _list=list,
               _len=len,
               _int=int,
               _range=range)

defexprop(**{
  'I': unop(lambda n: f'_range(_int({n}))'),
  'L': unop(lambda x: f'_list({x})'),

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
  '`[': pmap(lambda ps: f'{pytuple(ps[0])}[-1]',
             seq(rep(expr, min=1), re(r'\]'))),

  '**': binop(lambda x, y: f'({y} ** {x})'),
  '++':  unop(lambda x:    f'_list(_chain(*({x})))'),

  '+': binop(lambda x, y: f'({x} + {y})'),
  '-':  unop(lambda x:    f'(- {x})'),
  '*': binop(lambda x, y: f'({x} * {y})'),
  '/': binop(lambda x, y: f'({y} / {x})'),
  '%': binop(lambda x, y: f'({y} % {x})'),
  '.': binop(lambda x, y: f'({x} @ {y})')})
