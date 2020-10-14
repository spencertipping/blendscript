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

  def __repr__(self):
    valstr = str(self)
    if self.ref is not None: valstr += f' (== {self.ref})'
    return f'{valstr} :: {str(self.t)}'

  def compile(self):
    return eval(str(self), globals=val.bound_globals)

  @classmethod
  def of(cls, t, v):
    """
    Binds a global value and produces a val that refers to it.
    """
    gs = f'_G{cls.gensym_id}'
    cls.gensym_id += 1
    cls.bound_globals[gs] = v
    return val(t, gs, ref=v)

  @classmethod
  def lit(cls, t, v):
    """
    Returns a val that compiles to a literal.
    """
    if eval(repr(v)) != v: raise Exception(
      f'{v} is not sufficiently serializable to use with val.lit()')

    return cls(t, repr(v), ref=v)

  @classmethod
  def fn(cls, rt, at, f):
    """
    Converts a unary Python function with the specified argument types into a
    BlendScript function.
    """
    return cls.of(t_fn(rt, at), f)

  @classmethod
  def list(cls, t, *xs):
    """
    Returns a val representing a homogeneous list of elements. This will be
    compiled as a Python tuple.
    """
    if len(xs) == 0: return cls(t_list(t), '()')

    ys = ['(']
    for x in xs:
      ys.append(x.convert_to(t))
      ys.append(',')
    ys.append(')')
    return cls(t_list(t), ys)

  def str_into(self, l):
    if type(self.code) == str:
      l.append(self.code)
      return self
    for c in self.code:
      if type(c) == str: l.append(c)
      else:              c.str_into(l)
    return self

  def __str__(self):
    l = []
    self.str_into(l)
    return ''.join(l)

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
