"""
BlendScript compile-time values.

A "val" is a chunk of code (which may be splayed out into a list of other vals)
and a blendscript_type that describes what the result will be. BlendScript has
enough static type information that it can apply specific conversions before
the resulting Python code is compiled.
"""

from .types import *


class val:
  """
  A BlendScript value produced by the specified code and having type t. code
  can be either a string or a sequence of stringable things that will later be
  concatenated.
  """
  bound_globals = {}
  gensym_id = 0

  def __init__(self, t, code, ref=None):
    # Validate the code object here because I know I'm going to screw this up
    # somewhere
    if type(code) != str:
      for c in code:
        if type(c) != val and type(c) != str:
          raise Exception(f'instantiating val with invalid code: {code}')

    if not isinstance(t, blendscript_type):
      raise Exception(f'instantiating val with invalid type: {t}')

    self.t    = t
    self.code = code
    self.ref  = ref

  @classmethod
  def of(cls, t, v):
    """
    Binds a global value and produces a val that refers to it.
    """
    gs = f'_G{val.gensym_id}'
    gensym_id += 1
    bound_globals[gs] = v
    return val(t, gs, ref=v)

  @classmethod
  def lit(cls, t, v):
    """
    Returns a val that compiles to a literal.
    """
    if eval(repr(v)) != v: raise Exception(
      f'{v} is not sufficiently serializable to use with val.lit()')

    return val(t, repr(v), ref=v)

  @classmethod
  def list(cls, t, *xs):
    """
    Returns a val representing a homogeneous list of elements. This will be
    compiled as a Python tuple.
    """
    if len(xs) == 0: return val(t_list(t), '()')

    ys = ['(']
    for x in xs:
      ys.append(x.convert_to(t)).append(',')
    ys.append(')')
    return val(t_list(t), ys)

  def compile(self):
    return eval(str(self), globals=bound_globals)

  def __str__(self):
    return self.code if type(self.code) == str else ''.join(self.code)

  def convert_to(self, t):
    return self.t.convert_to(self.code, t)

  def __call__(self, x):
    """
    Coerce the argument into the required type, then apply the function and
    reduce to the return type.
    """
    if self.t.name != '->':
      raise Exception(f'cannot call non-function {self} on {x}')

    rtype, atype = self.t.args
    return val(rtype, [self, '(', x.convert_to(atype), ')'])
