"""
BlendScript value wrappers.

BlendScript can lean on Python for most of its behavior, but there are cases
where we need context-sensitive coercion or other things Python doesn't give
us.
"""

from .types import *


class val:
  """
  A BlendScript value produced by the specified code and having type t. code
  can be either a string or a sequence of stringable things that will later be
  concatenated.
  """
  def __init__(self, code, t):
    self.code = code
    self.t    = t

  def __str__(self):
    return self.code if type(self.code) == str else ''.join(self.code)

  def convert(self, t):
    return self.t.convert_to(self.code, t)


class method_call_op:
  """
  A single operation applied to an object via method call.
  """
  def __init__(self, method, *args, **kwargs):
    self.method = method
    self.args   = tuple(args)
    self.kwargs = kwargs

  def __hash__(self):
    return hash((self.method, self.args, self.kwargs))

  def __call__(self, obj):
    return getattr(obj, self.method)(*self.args, **self.kwargs)

  def __str__(self):
    return f'call("f{self.method}", *{self.args}, **{self.kwargs})'
