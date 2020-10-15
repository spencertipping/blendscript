"""
BlendScript type system.

BlendScript value types are more about places those values can be used, not
what those values are made of. Python takes care of structure and we pick up
with semantics.
"""


class blendscript_type:
  def upper_bound(self, t):
    ...

  def convert_value(self, t, v):
    ...


class atom_type(str, blendscript_type):
  """
  A concrete type of kind *.
  """

  atom_coercions = {}
  """
  A dictionary of (atom, atom) pairings defining valid coercion paths.
  """

  def upper_bound(self, t):
    return self

  def convert_value(self, t, v):
    # TODO: coercion or something
    return v


class variable_type(str, blendscript_type):
  """
  An unknown type variable that collects coercion constraints.
  """

  def __init__(self, *args):
    super(self, str).__init__(self, *args)
    self.constraints = set()

  def upper_bound(self, t): return self.solve().upper_bound(t)

  def convert_value(self, t, v):
    self.constraints.add(('to', t))
    # TODO: return a value that won't be defined until we solve the type
    return v


class dynamic_type(blendscript_type):
  """
  A type that is never coerced at compile-time; we assume any coercion happens
  within the runtime environment.
  """
  def __init__(self): pass
  def upper_bound(self, t): return self
  def convert_value(self, t, v): return v
  def __str__(self): return '.'


class any_type(blendscript_type):
  """
  The _ wildcard type, which can never become constrained and whose values
  cannot be inspected in any way.
  """
  def __init__(self): pass
  def upper_bound(self, t): return self
  def convert_value(self, t, v):
    if t == self: return v
    raise Exception(f'{v} :: _ cannot be converted to type {t}')
  def __str__(self): return '_'


t_any     = any_type()
t_dynamic = dynamic_type()

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


def t_list(elem_type):
  """
  A homogeneous list of BlendScript values. Note that these will be represented
  by tuples in Python because lists are mutable and therefore not hashable.
  """
  # TODO
  return t_dynamic


def t_fn(rtype, atype):
  """
  A function with a specified return type and argument type. The return type
  is always represented first, as the thing the arrow points to.
  """
  # TODO
  return t_dynamic
