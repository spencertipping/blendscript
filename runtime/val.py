"""
Runtime values and bindings for BlendScript.
"""

from math import *

from ..compiler.types import *
from ..compiler.val   import *
from ..parsers.val    import *
from .fn              import fn


unop_type  = with_typevar(lambda v: fn_type(v, v))
binop_type = with_typevar(lambda v: fn_type(v, fn_type(v, v)))

val_atom.bind(**{
  'tau': val.lit(t_number, tau),

  'sin':  val.of_fn(t_number, t_number, sin),
  'cos':  val.of_fn(t_number, t_number, cos),
  'tan':  val.of_fn(t_number, t_number, tan),
  'asin': val.of_fn(t_number, t_number, asin),
  'acos': val.of_fn(t_number, t_number, acos),
  'atan': val.of_fn(t_number, t_number, atan),

  'sqrt':  val.of_fn(t_number, t_number, sqrt),
  'erf':   val.of_fn(t_number, t_number, erf),
  'gamma': val.of_fn(t_number, t_number, gamma),
  'exp':   val.of_fn(t_number, t_number, exp),
  'log':   val.of_fn(t_number, t_number, log),
  'log2':  val.of_fn(t_number, t_number, log2),

  'L':  with_typevar(lambda v: val.of_fn(t_list(v), t_list(v), list)),

  '+':  val.of(binop_type, fn(lambda x: fn(lambda y: x + y))),
  '*':  val.of(binop_type, fn(lambda x: fn(lambda y: x * y))),
  '-':  val.of(unop_type,  fn(lambda x: -x)),
  '/':  val.of(binop_type, fn(lambda x: fn(lambda y: y / x))),
  '**': val.of(binop_type, fn(lambda x: fn(lambda y: x ** y))),
  '.':  val.of(binop_type, fn(lambda x: fn(lambda y: x @ y)))})
