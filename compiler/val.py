"""
BlendScript compile-time values.

A "val" is a chunk of code (which may be splayed out into a list of other vals)
and a blendscript_type that describes what the result will be. BlendScript has
enough static type information that it can apply specific conversions before
the resulting Python code is compiled.
"""

from functools import partial, reduce

from ..runtime.fn import fn
from .types       import *


def sanitize_identifier(s):
  """
  Quotes disallowed characters from identifier names, if any exist. Each
  disallowed character is replaced with '_xx', where xx is its hex code.
  """
  import re
  def hex_quote(m):
    return ''.join(['_%02x' % ord(c) for c in m.group(0)])

  non_ident = re.compile(r'^[^a-zA-Z_]|[^a-zA-Z0-9_]+')
  return re.sub(non_ident, hex_quote, s)


class val:
  """
  A BlendScript value produced by the specified code and having type t. code
  can be either a string or a sequence of stringable things that will later be
  concatenated.
  """
  bound_globals = {}
  global_vals = {}
  gensym_id = 0

  def __init__(self, t, code, ref=None):
    # Validate the code object here because I know I'm going to screw this up
    # somewhere
    if type(code) == val:
      raise TypeError(f'trying to call val({t}) on {code}, which is already a val')

    if type(code) != str:
      for c in code:
        if type(c) != val and type(c) != str:
          raise Exception(f'instantiating val with invalid code: {code}')

    if not isatype(t):
      raise Exception(f'instantiating val with invalid type: {t}')

    self.t    = t
    self.code = code
    self.ref  = ref

  def __repr__(self):
    typestr = '' if self.t == t_dynamic else f' :: {str(self.t)}'
    return f'{str(self) if self.ref is None else repr(self.ref)}{typestr}'

  def compile(self):
    """
    Compiles this value into a nullary lambda that will return the result when
    invoked.
    """
    return eval('lambda: ' + str(self), val.bound_globals)

  @classmethod
  def of(cls, t, v):
    """
    Binds a global value and produces a val that refers to it. Note that this
    global value lives forever, so don't go binding tons of these. If possible,
    you should use val.lit() instead to drop a literal string into the code.
    """
    if v in cls.global_vals: return cls.global_vals[v]

    import re
    words = '_'.join(re.compile(r'\w+').findall(repr(v)))
    gs = f'_G{words}{cls.gensym_id}'
    r = val(t, gs, ref=v)
    cls.gensym_id += 1
    cls.bound_globals[gs] = v
    cls.global_vals[v] = r
    return r

  @classmethod
  def lit(cls, t, v):
    """
    Returns a val that compiles to a literal. No global references are created,
    which means the value is free to be GC'd at the end of this function. (This
    works because the value is serialized into the compiled output, not
    referenced via the global gensym table.)
    """
    r = repr(v)
    ok = False
    try: ok = eval(r) == v
    except: pass

    if not ok: raise Exception(
      f'{repr(v)} is not sufficiently serializable to use with val.lit()')
    return cls(t, repr(v), ref=v)

  @classmethod
  def var_ref(cls, t, name):
    """
    Refers to a variable by its symbolic name. If the variable contains
    characters that Python disallows, they are replaced by hex escapes.
    """
    return cls(t, sanitize_identifier(name))

  @classmethod
  def bind_var(cls, name, val, expr):
    """
    Wraps expr within a lexical context that binds name to val. name is
    sanitized in a way that's consistent with var_ref, which you should use to
    refer to it within expr.
    """
    return cls(expr.t, [f'(lambda {sanitize_identifier(name)}:', expr, ')',
                        '(', val, ')'])

  @classmethod
  def int(cls, i): return cls.lit(t_int, int(i))

  @classmethod
  def str(cls, s): return cls.lit(t_string, str(s))

  @classmethod
  def float(cls, n): return cls.lit(t_number, float(n))

  @classmethod
  def of_fn(cls, ats, rt, f):
    """
    Converts a unary Python function with the specified argument types into a
    BlendScript function. If multiple arguments are specified, the type will be
    appropriately recursive and the function you provide will automatically be
    curried.
    """
    n_args = len(ats)
    def g(*xs):
      if len(xs) == n_args:
        return f(*xs)
      else:
        return fn(partial(g, *xs), source=f'{f}({", ".join(map(str, xs))}, ...)')

    t = rt
    for a in reversed(ats):
      t = t_fn(a, t)

    return cls.of(t, fn(g, source=str(t)))

  @classmethod
  def fn(cls, at, argname, body):
    """
    Compiles to a lambda with the specified val as the body.
    """
    return cls(t_fn(at, body.t),
               [fn_val, f'(lambda {argname}:', body, ')'])

  @classmethod
  def list(cls, *xs):
    """
    Returns a val representing a homogeneous list of elements. This will be
    compiled as a Python tuple. The type is inferred as the upper bound of all
    member types.
    """
    t  = None
    ys = ['(']
    for x in xs:
      if t is None: t = x.t
      x.t.unify_with(t)
      ys.append(x)
      ys.append(',')
    ys.append(')')
    return cls(t_list(t or typevar()), ys)

  def typed(self, t):
    """
    Returns a new val that holds the same quantity, but which has a different
    type.
    """
    return val(t, self.code, ref=self.ref)

  def __str__(self):
    l = []
    self.str_into(l)
    return ''.join(l)

  def str_into(self, l):
    if type(self.code) == str:
      l.append(self.code)
    else:
      for c in self.code:
        if type(c) == str: l.append(c)
        else:              c.str_into(l)
    return self

  def __call__(self, x):
    """
    Coerce the argument into the required type, then apply the function and
    reduce to the return type.
    """
    a = self.t.arg_type()
    r = self.t.return_type()
    if r is None: raise Exception(f'cannot call non-function {self} on {x}')

    x.t.unify_with(a)
    return val(r, [self, '(', x, ')'])

  def __if__(self, t, f):
    """
    Create a ternary expression.
    """
    t.t.unify_with(f.t)
    self.t.unify_with(t_bool)
    return val(t.t, ['(', t, ' if ', self, ' else ', f, ')'])


fn_val = with_typevars(lambda v: val.of_fn([v], v, fn))
