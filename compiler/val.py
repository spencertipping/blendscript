"""
BlendScript compile-time value wrappers.
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
