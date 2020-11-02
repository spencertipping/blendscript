"""
Function objects and utilities for BlendScript runtime values.
"""

from functools import reduce


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
  def __init__(self, f, source=None):
    self.f      = f.f if type(f) == type(self) else f
    self.source = source
    if getattr(self.f, '__call__', None) is None: raise RuntimeError(
      f'tried to create fn() of non-callable object {self.f}')

  def __str__(self):       return self.source or str(self.f)
  def __repr__(self):      return str(self)
  def __call__(self, *xs): return self.f(*xs)

  def __add__(self, g):       return fn(lambda *xs: self.f(*xs) + g(*xs))
  def __neg__(self):          return fn(lambda *xs: -self.f(*xs))
  def __rmul__(self, xs):     return map(self.f, xs)
  def __rtruediv__(self, xs): return reduce(self.f, xs)
  def __rmod__(self, xs):     return filter(self.f, xs)
  def __matmul__(self, g):    return compose(self.f, g)

  def __and__(self, g): return fn(lambda *xs: self.f(*xs) & g(*xs))
  def __or__(self, g):  return fn(lambda *xs: self.f(*xs) | g(*xs))
  def __xor__(self, g): return fn(lambda *xs: self.f(*xs) ^ g(*xs))



def compose(f, g):
  """
  Composition of two functions. The inner function will be invoked on all args
  and kwargs; the outer function just receives a singular result from the inner
  one.
  """
  return fn(lambda *xs, **d: f(g(*xs, **d)))


def method(m):
  """
  Returns a fn() that invokes the specified method on whichever object is
  passed in as the first argument. Remaining arguments are passed to the
  method.
  """
  return fn(lambda x, *ys, **d: getattr(x, m)(*ys, **d),
            source=f'.{m}(...)')


def preloaded_method(_, *args, **kwargs):
  """
  Returns a fn() that invokes the specified method on an object and returns the
  result. The method will be invoked with the specified set of preloaded
  parameters.
  """
  return fn(lambda o: getattr(o, _)(*args, **kwargs),
            source=f'.{_}(*{args}, **{kwargs})')
