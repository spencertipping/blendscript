"""
Runtime values and bindings for BlendScript.
"""

from math import *

from ..compiler.types import *
from ..compiler.val   import *
from ..parsers.val    import *
from .fn              import fn


def number_fn(f): return val.of_fn([t_number], t_number, f)

def unop_fn(f):
  return with_typevar(lambda v: val.of_fn([v], v, f))

def binop_fn(f):
  return with_typevar(lambda v: val.of_fn([v, v], v, f))

def cmp_fn(f):
  return with_typevar(lambda v: val.of_fn([v, v], t_bool, f))


range_fn = val.of_fn([t_int], t_list(t_int), range)

val_atom.ops.add(i=pmap(range_fn, p_lit(t_int, p_int)))


val_atom.bind(**{
  'tau': val.lit(t_number, tau),

  'dr':   number_fn(radians),
  'rd':   number_fn(degrees),
  'tr':   number_fn(lambda t: tau * t),
  'qr':   number_fn(lambda q: tau * q / 4),

  'sin':  number_fn(sin),
  'cos':  number_fn(cos),
  'tan':  number_fn(tan),
  'asin': number_fn(asin),
  'acos': number_fn(acos),
  'atan': number_fn(atan),

  'sqrt':  number_fn(sqrt),
  'erf':   number_fn(erf),
  'gamma': number_fn(gamma),
  'exp':   number_fn(exp),
  'log':   number_fn(log),
  'log2':  number_fn(log2),

  'L':  with_typevar(lambda v: val.of_fn([t_list(v)], t_list(v), list)),

  '`':  with_typevar(lambda v: val.of_fn([t_int, t_list(v)], v,
                                         lambda i, xs: xs[i])),

  '+':  binop_fn(lambda x, y: x + y),
  '*':  binop_fn(lambda x, y: y * x),
  '/':  binop_fn(lambda x, y: y / x),
  '%':  binop_fn(lambda x, y: y % x),
  '**': binop_fn(lambda x, y: y ** x),
  '.':  binop_fn(lambda x, y: x @ y),
  '-':  unop_fn(lambda x: -x),
  '!':  unop_fn(lambda x: not x),

  '==': cmp_fn(lambda x, y: x == y),
  '!=': cmp_fn(lambda x, y: x != y),
  '<=': cmp_fn(lambda x, y: x <= y),
  '>=': cmp_fn(lambda x, y: x >= y),
  '>':  cmp_fn(lambda x, y: x > y),
  '<':  cmp_fn(lambda x, y: x < y),

  '~':  unop_fn(lambda x: ~x),
  '&':  binop_fn(lambda x, y: x & y),
  '|':  binop_fn(lambda x, y: x | y),
  '^':  binop_fn(lambda x, y: x ^ y)})
