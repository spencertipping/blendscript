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


class blendscript_type:
  """
  An abstract base class that all blendscript types extend from.
  """
  def arity(self): ...

  def __call__(self, *args):
    t = self
    for a in args:
      t = apply_type(t, a)
    return t


def isatype(x): return isinstance(x, blendscript_type)


class atom_type(blendscript_type):
  """
  A single type whose kind arity is fixed.
  """
  def __init__(self, name, kind_arity=0):
    self.name       = name
    self.kind_arity = kind_arity

  def arity(self):    return self.kind_arity
  def __str__(self):  return f'{self.name} :: *{" -> *" * self.kind_arity}'
  def __hash__(self): return hash((self.name, self.kind_arity))
  def __eq__(self, t):
    return isinstance(t, atom_type) \
      and  (self.name, self.kind_arity) == (t.name, t.kind_arity)


class dynamic_type(blendscript_type):
  """
  A type that satisfies every type constraint.
  """
  def __init__(self): pass
  def arity(self):    return -1
  def __str__(self):  return '.'


class forall_type(blendscript_type):
  """
  The _ wildcard type, which satisfies no type constraint.
  """
  def __init__(self): pass
  def arity(self):    return None
  def __str__(self):  return '_'


class apply_type(blendscript_type):
  """
  A higher-kinded type name applied to an argument.
  """
  def __init__(self, head, arg):
    if head.arity() is None: raise Exception(
        f'{head} cannot be applied to {arg} (not a concrete type)')

    if head.arity() == 0: raise Exception(
        f'{head} cannot be applied to {arg} (too many type arguments)')

    self.head = head
    self.arg  = arg

  def arity(self):    return self.head.arity() - 1
  def __hash__(self): return hash((self.head, self.arg))
  def __eq__(self, t):
    return isinstance(t, apply_type) \
      and  (self.head, self.arg) == (t.head, t.arg)

  def __str__(self):
    if isinstance(self.head, apply_type):
      return f'({self.head}) {self.arg}'
    else:
      return f'{self.head} {self.arg}'


t_forall  = forall_type()
t_dynamic = dynamic_type()

t_fn   = atom_type('->', 2)
t_list = atom_type('[]', 1)

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
