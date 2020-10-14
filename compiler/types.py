"""
BlendScript type system.

BlendScript value types are more about places those values can be used, not
what those values are made of. Python takes care of structure and we pick up
with semantics.
"""

blendscript_type_conversions = {}
"""
A dictionary of {(fromtype, totype): lambda} values that transform blendscript
vals between compile-time types. Define new ones with deftypeconv().
"""

blendscript_type_transitive_paths = {}
"""
A cache of solved transitive paths between types. If a direct pairing doesn't
exist, BlendScript will search for an intermediate bridge type that it can
convert through. If one is found, that bridge type is cached here.
"""

blendscript_all_types = set()


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


def transitive_conversion_bridge(fromtype, totype):
  """
  Attempts to find a bridge type for which (fromtype, bridge) and (bridge,
  totype) are defined. If one is found, we return it and save it in
  blendscript_type_transitive_paths; otherwise we return None.

  If multiple bridges exist, one is chosen arbitrarily.
  """
  tk     = (fromtype, totype)
  bridge = blendscript_type_transitive_paths.get(tk)
  if bridge is not None: return bridge

  for b in blendscript_all_types:
    if (fromtype, b) in blendscript_type_conversions and \
        (b, totype) in blendscript_type_conversions:
      blendscript_type_transitive_paths[tk] = b
      return b

  return None


class blendscript_type:
  """
  A data class used to represent BlendScript types as Python values.
  BlendScript types are defined primarily by their conversion mechanics.

  Structurally, BlendScript types are encoded like S-expressions: a type name
  with zero or more arguments, each of which is itself a BlendScript type.
  """
  def __init__(self, name, *args):
    self.name = name
    self.args = args
    self.h    = hash(name, tuple(args))
    blendscript_all_types.add(self)

  def convert_to(self, v, t):
    """
    Returns a **string of code** that converts "v" (also a string of code) from
    this type to the blendscript type "t", or throws an error at compile-time
    if the value cannot be converted.
    """
    if self == t: return v

    converter = blendscript_type_conversions.get((self, t))
    if converter is not None:
      return converter(v, fromtype=self, totype=t)

    bridge = blendscript_type_transitive_paths.get((self, t))
    if bridge is not None:
      c1 = blendscript_type_conversions[(self, bridge)]
      c2 = blendscript_type_conversions[(bridge, t)]
      return c2(c1(v, self, bridge), bridge, t)

    raise Exception(
      f'blendscript_type: no converter or bridge between {self} and {t}')

  def __str__(self):
    """
    A human-readable representation of this type, written in Polish notation
    like everything else in BlendScript. So, you know, not entirely
    human-readable.
    """
    xs = ''
    if   len(args) == 1: xs = ' ' + str(self.args[0])
    elif len(args) >  1: xs = f'[{" ".join(self.args)}]'
    return f'{self.name}{xs}'

  def __hash__(self): return self.h
  def __eq__(self, v): return type(self) == type(v) and \
                              self.h    == v.h      and \
                              self.name == v.name   and \
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

def t_fn(rtype, atype):
  """
  A function with a specified return type and argument type. The return type
  is always represented first, as the thing the arrow points to.
  """
  return blendscript_type('->', rtype, atype)
