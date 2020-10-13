"""
BlendScript value wrappers.

BlendScript can lean on Python for most of its behavior, but there are cases
where we need context-sensitive coercion or other things Python doesn't give
us.
"""

class method_call_op:
  """
  A single operation applied to an object via method call.
  """
  def __init__(self, method, *args):
    self.method = method
    self.args   = tuple(args)

  def __hash__(self):      return hash((self.method, self.args))
  def __call__(self, obj): return getattr(obj, method)(*args)
  def __str__(self):       return f'call("f{self.method}", *{self.args})'
