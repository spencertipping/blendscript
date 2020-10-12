"""
Function objects and utilities for BlendScript runtime values.
"""

from functools import reduce

def method(m): return fn(lambda x, *ys: getattr(x, m)(*ys))

class fn:
  """
  A function with overloaded operators:

  (f * xs) == map(f, xs)
  (f % xs) == filter(f, xs)
  (f / xs) == reduce(f, xs)
  (f @ g)  == compose(f, g)

  For convenience we also have:

  (f + g)(x) == f(x) + g(x)
  (-f)(x)    == -f(x)
  """
  def __init__(self, f): self.f = f.f if type(f) == type(self) else f

  def __call__(self, *xs): return self.f(*xs)

  def __add__(self, g): return fn(lambda *xs: self.f(*xs) + g(*xs))
  def __neg__(self):    return fn(lambda *xs: -self.f(*xs))

  def __mul__(self, xs): return map(self.f, xs)
  def __div__(self, xs): return reduce(self.f, xs)
  def __mod__(self, xs): return filter(self.f, xs)

  def __matmul__(self, g): return fn(lambda *xs: self.f(g(*xs)))
