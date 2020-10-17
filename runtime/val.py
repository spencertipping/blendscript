"""
Runtime values and bindings for BlendScript.
"""

from math             import pi

from ..compiler.types import *
from ..compiler.val   import *
from ..parsers.val    import *
from .fn              import fn


# TODO: once we have HM, replace these with a -> a -> a and such
unop_type  = fn_type(t_dynamic, t_dynamic)
binop_type = fn_type(t_dynamic, unop_type)

tau = pi * 2

val_atom.bind(**{
  'tau': val.lit(t_number, pi * 2),

  'L':  with_typevar(lambda v: val.of_fn(t_list(v), t_list(v), list)),

  '+':  val.of(binop_type, fn(lambda x: fn(lambda y: x + y))),
  '*':  val.of(binop_type, fn(lambda x: fn(lambda y: x * y))),
  '-':  val.of(unop_type,  fn(lambda x: -x)),
  '/':  val.of(binop_type, fn(lambda x: fn(lambda y: y / x))),
  '**': val.of(binop_type, fn(lambda x: fn(lambda y: x ** y))),
  '.':  val.of(binop_type, fn(lambda x: fn(lambda y: x @ y)))})
