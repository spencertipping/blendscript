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

  TODO: replace type_arity() with curried kind structures
  """
  def type_arity(self): ...
  def value_arity(self): ...
  def is_value_type(self): ...
  def arg_type(self): ...
  def return_type(self): ...

  def unify_with(self, t):
    # TODO: HM stuff
    pass

  def __call__(self, *args):
    t = self
    for a in args:
      t = apply_type(t, a)
    return t


def isatype(x): return isinstance(x, blendscript_type)


class atom_type(str, blendscript_type):
  """
  A single concrete type whose kind is *.
  """
  def type_arity(self):    return 0
  def value_arity(self):   return 0
  def is_value_type(self): return True
  def arg_type(self):      return None
  def return_type(self):   return None


class higher_kinded_type(blendscript_type):
  """
  A higher-kinded type.
  """
  def __init__(self, name, a, r):
    self.name = name
    self.a    = a
    self.r    = r

  def type_arity(self):    return 1 + self.r.type_arity()
  def is_value_type(self): return False
  def arg_type(self):      return None
  def return_type(self):   return None

  def __str__(self):  return f'{self.name} :: ({self.a} -> {self.r})'
  def __hash__(self): return hash((self.name, self.a, self.r))
  def __eq__(self, t):
    return isinstance(t, higher_kinded_type) \
      and  (self.name, self.a, self.r) == (t.name, t.a, t.r)


class dynamic_type(blendscript_type):
  """
  A type that satisfies every type constraint. If addressed as a function, its
  arity is unbounded -- represented by -1.
  """
  def __init__(self):      pass
  def type_arity(self):    return 0
  def value_arity(self):   return -1
  def is_value_type(self): return True
  def arg_type(self):      return t_dynamic
  def return_type(self):   return t_dynamic
  def __str__(self):       return '.'


class apply_type(blendscript_type):
  """
  A higher-kinded type name applied to an argument.
  """
  def __init__(self, head, arg):
    if head.type_arity() is None: raise Exception(
        f'{head} cannot be applied to {arg} (not a concrete type)')

    if head.type_arity() == 0: raise Exception(
        f'{head} cannot be applied to {arg} (too many type arguments)')

    self.head = head
    self.arg  = arg

  def type_arity(self):    return self.head.type_arity() - 1
  def is_value_type(self): return self.arity() <= 0

  def arg_type(self):
    if isinstance(self.head, apply_type) and self.head.head == t_fn:
      return self.head.arg
    else:
      return None

  def return_type(self):
    if isinstance(self.head, apply_type) and self.head.head == t_fn:
      return self.arg
    else:
      return None

  def __hash__(self): return hash((self.head, self.arg))
  def __eq__(self, t):
    return isinstance(t, apply_type) \
      and  (self.head, self.arg) == (t.head, t.arg)

  def __str__(self):
    if isinstance(self.head, apply_type):
      return f'({self.head}) {self.arg}'
    else:
      return f'{self.head} {self.arg}'


def typevar():
  # TODO
  return t_dynamic


t_dynamic = dynamic_type()
t_functor = higher_kinded_type('->', '*', t_dynamic)
t_fn      = higher_kinded_type('->', '*', t_functor)
t_list    = atom_type('[]', 1)

t_number = atom_type('N')
t_string = atom_type('S')
t_int    = atom_type('I')
t_bool   = atom_type('B')
t_vec2   = atom_type('V2')
t_vec3   = atom_type('V3')
t_vec4   = atom_type('V4')
t_mat33  = atom_type('M33')
t_mat44  = atom_type('M44')

t_blendobj  = atom_type('B/obj')
t_blendmesh = atom_type('B/mesh')
