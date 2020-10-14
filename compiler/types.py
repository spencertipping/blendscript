"""
BlendScript type system.

BlendScript value types are more about places those values can be used, not
what those values are made of. Python takes care of structure and we pick up
with semantics.
"""

blendscript_type_conversions = {}

def deftypeconv(fromtype, totype, f):
  """
  Defines a function that converts BlendScript values from "fromtype" to
  "totype". "fromtype" and "totype" are just the "name" part of a
  blendscript_type; the conversion function will receive the full type objects
  as keyword arguments.

  Conversion functions are called like this:

  converted_value = f(original_value, fromtype=f, totype=t)

  Both converted_value and original_value are Python code strings.
  """
  if (fromtype, totype) in blendscript_type_conversions: raise Exception(
    f'a type conversion from {fromtype} to {totype} already exists')
  blendscript_type_conversions[(fromtype, totype)] = f


class blendscript_type:
  """
  A data class used to represent BlendScript types as Python values.
  BlendScript types are defined primarily by their conversion mechanics, which
  are managed externally using a dictionary from name to name.

  Structurally, BlendScript types are encoded like S-expressions: a type name
  with zero or more arguments, each of which is itself a BlendScript type.
  """
  def __init__(self, name, *args):
    self.name = name
    self.args = tuple(args)

  def convert_to(self, v, t):
    """
    Returns a **string of code** that converts "v" (also a string of code) from
    this type to the blendscript type "t", or throws an error at compile-time
    if the value cannot be converted.
    """
    if self == t: return v

    converter = blendscript_type_conversions.get((self.name, t.name))
    if converter is None: raise Exception(
      f'blendscript_type.convert_to: no converter between {self} and {t}')
    return converter(v, fromtype=self, totype=t)

  def __str__(self):
    """
    A human-readable representation of this type, written in Polish notation
    like everything else in BlendScript. So, you know, not entirely
    human-readable.
    """
    xs = ''
    if len(args) == 1: xs = ' ' + str(self.args[0])
    elif len(args) > 1: xs = f'[{" ".join(self.args)}]'
    return f'{self.name}{xs}'

  def __hash__(self): return hash((self.name, self.args))
  def __eq__(self, v): return type(self) == type(v) and \
                              self.name == v.name and \
                              self.args == v.args


t_number = blendscript_type('n')
t_string = blendscript_type('s')
t_int    = blendscript_type('i')
t_vec2   = blendscript_type('v2')
t_vec3   = blendscript_type('v3')
t_vec4   = blendscript_type('v4')
t_mat33  = blendscript_type('m33')
t_mat44  = blendscript_type('m44')

t_blendobj  = blendscript_type('b/obj')
t_blendmesh = blendscript_type('b/mesh')

def t_list(elem_type):
  """
  A homogeneous list of BlendScript values. Note that these will be represented
  by tuples in Python because lists are mutable and therefore not hashable.
  """
  return blendscript_type('[]', elem_type)

def t_fn(rtype, *args):
  """
  A function with a specified return type and argument types. The return type
  is always represented first, as the thing the arrow points to.
  """
  return blendscript_type('->', rtype, *args)
