"""
BlendScript type system.

BlendScript value types are more about places those values can be used, not
what those values are made of. Python takes care of structure and we pick up
with semantics.

I want BlendScript to use Hindley-Milner and typeclasses with implicit coercion
pathways. Haskell does this in a few places with things like fromIntegral,
fromList, etc, but it won't search for type-unique functions nor will it form
automatic composition bridges.
"""

from enum import Enum


class blendscript_type:
  """
  An abstract base class that all blendscript types extend from.
  """
  def arg_type(self):    return None
  def return_type(self): return None
  def value_arity(self): return 0

  def unify_with(self, t):
    # TODO: HM stuff
    pass


def isatype(x): return isinstance(x, blendscript_type)


class atom_type(str, blendscript_type):
  """
  A single concrete type whose kind is *.
  """


class dynamic_type(blendscript_type):
  """
  A type that satisfies every type constraint. If addressed as a function, its
  arity is unbounded -- represented by -1.
  """
  def value_arity(self):   return -1
  def arg_type(self):      return t_dynamic
  def return_type(self):   return t_dynamic
  def __str__(self):       return '.'


class unary_type(blendscript_type):
  """
  A type whose kind is (* -> *), applied to a single type argument.
  """
  def __init__(self, name, a):
    self.name = name
    self.a    = a

  def __str__(self): return f'({self.name} {self.a})'
  def __hash__(self): return hash((self.name, self.a))
  def __eq__(self, t):
    return isinstance(t, unary_type) and (self.name, self.a) == (t.name, t.a)


class fn_type(blendscript_type):
  """
  A function whose argument and return types are specified.
  """
  def __init__(self, a, r):
    self.a = a
    self.r = r

  def value_arity(self): return 1 + max(0, self.r.value_arity())
  def arg_type(self):    return self.a
  def return_type(self): return self.r

  def __str__(self): return f'({self.a} -> {self.r})'
  def __hash__(self): return hash((self.a, self.r))
  def __eq__(self, t):
    return isinstance(t, fn_type) and (self.a, self.r) == (t.a, r.r)


def with_typevar(f): return f(typevar())
def typevar():
  # TODO
  return t_dynamic


def list_type(t): return unary_type('[]', t)
def set_type(t):  return unary_type('{}', t)


t_dynamic = dynamic_type()

t_list = list_type
t_set  = set_type
t_fn   = fn_type

t_number = atom_type('N')
t_string = atom_type('S')
t_int    = atom_type('I')
t_bool   = atom_type('B')
