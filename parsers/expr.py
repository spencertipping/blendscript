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
  pmap(val.float, p_float),
  pmap(val.int,   p_int),
  pmap(val.str,   iseq(1, re(r"'"), p_word)),

  # Python expressions within {}
  pmaps(lambda v, t, _: val(t, v),
        seq(re(r'\{([^\}:]+)::'), type_expr, lit('}'))),

  # Underscore always parses as a single identifier, even when immediately
  # followed by ident characters.
  re(r'_'))


# TODO: parse-time lambda parameter type assignment, binding, and identifier
# resolution

# TODO: full hindley-milner


expr_ops.add(**{
  '(': iseq(0, expr, lit(')')),

  '[': pmap(lambda v: val.list(v[0].t if len(v) else t_free, *v),
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
