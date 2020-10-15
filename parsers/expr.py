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


expr_ops      = dsp()
expr_literals = alt()
expr          = whitespaced(alt(expr_ops, expr_literals))

compiled_expr = pmap(method('compile'), expr)


expr_literals.add(
  pmap(val.float, p_float),
  pmap(val.int,   p_int),
  pmap(val.str,   iseq(1, re(r"'"), p_word)),

  # Python expressions within {}
  pmaps(lambda v, t, _: val(t, v),
        iseq([1, 2], lit('{'), type_expr, re('([^\}]+)\}'))),

  # Underscore always parses as a single identifier, even when immediately
  # followed by ident characters.
  re(r'_'))


# TODO: parse-time lambda parameter type assignment, binding, and identifier
# resolution

# TODO: full hindley-milner


def list_type(xs):
  if len(xs) == 0: return t_dynamic
  return reduce(lambda x, y: x.upper_bound(y), (x.t for x in xs))


expr_ops.add(**{
  '(': iseq(0, expr, lit(')')),

  '[': pmap(lambda v: val.list(list_type(v), *v),
            iseq(0, rep(iseq(0, expr, maybe(lit(',')))),
                 whitespaced(lit(']')))),

  '?':  pmaps(lambda x, y, z: x.__if__(y, z), rep(expr, min=3, max=3)),

  '\\': pmap(lambda ps: f'_fn(lambda {ps[0] or "_"}: {ps[1]})',
             seq(maybe(p_lword), expr)),
  '::': pmap(lambda ps: f'(lambda {ps[0]}: {ps[2]})({ps[1]})',
             seq(p_lword, expr, expr)),


  '.:': pmap(lambda ps: f'{ps[1]}.{ps[0]}', seq(p_word, expr)),
  '.@': pmap(lambda ps: f'{ps[2]}.{ps[0]}(*{ps[1]})',
             seq(p_word, expr, expr))})
