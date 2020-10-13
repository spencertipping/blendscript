"""
Parsing expression grammars.
"""

# TODO
# Redo this to track failures and build a backtrace. This involves turning each
# parser into a class.


import re as regex

def parserify(f):
  """
  Returns f after turning it into a parser for the parser() assertion.
  """
  f.is_parser = True
  return f

def parser(f):
  """
  Returns f after verifying that it is a parser. This is just for type safety.
  """
  if not f.is_parser: raise Exception(f'{f} is not a parser')
  return f

def fail(e):  return (e, None)
def ok(v, i): return (v, i)

none  = parserify(lambda source, index: fail(None))
empty = parserify(lambda source, index: ok(None, index))

def lit(k):
  """
  Parses a literal string, returning it.
  """
  if isinstance(k, str): k = k.encode()
  def f(s, i):
    sub = s[i:i+len(k)]
    return (sub.decode(), i + len(k)) if sub == k else fail(None)
  return parserify(f)

def re(*rs):
  """
  Parses a regular expression, returning the entire matched area (if the regex
  defines no groups), the contents of the only match group (if the regex
  defines exactly one match group), or a tuple of all match groups (if the
  regex defines more than one). Note that the return value depends on the
  number of groups _defined by the regex_, not necessarily the number _that
  match_.
  """
  rs = [f'(?:{r})' if type(r) == str else f'(?:{r.decode()})' for r in rs]
  r  = regex.compile(b'|'.join([r.encode() for r in rs]))
  def f(s, i):
    m = r.match(memoryview(s)[i:])
    if m is None: return fail(None)
    gs = len(m.groups())
    if gs < 2: return ok(m.group(gs).decode(), i + m.end())
    else:      return ok([x.decode() for x in m.groups()], i + m.end())

  return parserify(f)

def const(k, p):
  """
  Succeeds iff p succeeds, but always returns k.
  """
  parser(p)
  def f(s, i):
    (_, i2) = p(s, i)
    return (k if i2 is not None else None, i2)
  return parserify(f)

def seq(*ps):
  """
  Parses a sequence of elements, returning a list of their results and
  succeeding only if all parsers succeed.
  """
  for p in ps: parser(p)
  def f(s, i):
    vs = []
    for p in ps:
      (v, i) = p(s, i)
      if i is None: return (v, i)
      vs.append(v)
    return (vs, i)
  return parserify(f)

class alt:
  """
  Early-commit alternative choices. The first parser that succeeds will be
  chosen. alt() is a class that you can later modify by using .add(*ps).
  """
  def __init__(self, *ps):
    self.ps = []
    parserify(self)
    self.add(*ps)

  def __call__(self, s, i):
    for p in self.ps:
      (v, i2) = p(s, i)
      if i2 is not None:
        return (v, i2)
    return fail(None)

  def add(self, *ps):
    for p in ps: self.ps.append(parser(p))
    return self

class dsp:
  """
  Constant-prefix dispatch parsing. The longest matching prefix will chosen
  _regardless of whether its parser then succeeds or fails_.
  """
  def __init__(self, **ps):
    self.ps = {}
    self.length_dicts = []
    parserify(self)
    self.add(**ps)

  def __call__(self, s, i):
    for l, d in self.length_dicts:
      sub = s[i:i+l]
      if sub in d: return d[sub](s, i+l)
    return fail(None)

  def regen_length_dicts(self):
    lks = {}
    for k, p in self.ps.items():
      i = len(k)
      if i not in lks: lks[i] = {}
      lks[i][k] = p
    self.length_dicts = sorted(lks.items(), key=lambda i: -i[0])
    return self

  def add(self, **ps):
    for prefix, p in ps.items():
      if type(prefix) == str: prefix = prefix.encode()
      if prefix in self.ps:
        raise Exception(
          f'dsp() collision at key {prefix} (we have {self.ps.keys()})')
      self.ps[prefix] = parser(p)
    return self.regen_length_dicts()

def rep(p, min=0, max=None):
  """
  Zero or more repetitions of the specified parser, the results returned in a
  list. You can customize the min and max limits, both of which are inclusive
  if specified. If max=None (default), then there is no upper limit on the
  number of times the parser will be repeated.
  """
  parser(p)
  def f(s, i):
    vs = []
    while max is None or len(vs) < max:
      (v, i2) = p(s, i)
      if i2 is None:
        if min <= len(vs) and (max is None or len(vs) <= max):
          return ok(vs, i)
        else:
          return fail(None)
      else:
        vs.append(v)
        i = i2
    return ok(vs, i)
  return parserify(f)

def maybe(p):
  """
  Attempts the parser, successfully returning None if it fails. If it succeeds,
  its value is returned.
  """
  parser(p)
  def f(s, i):
    (v, i2) = p(s, i)
    return ok(v, i2) if i2 is not None else ok(None, i)
  return parserify(f)

def pmap(f, p):
  """
  Transforms a parser's value using the specified function, if the parser
  succeeds. If it fails then the function isn't called.
  """
  parser(p)
  def g(s, i):
    (v, i2) = p(s, i)
    return (v if i2 is None else f(v), i2)
  return parserify(g)

def pif(f, p):
  """
  Succeeds iff the parser succeeds, and if f returns true on its value.
  """
  parser(p)
  def g(s, i):
    (v, i2) = p(s, i)
    return (v, i2) if i2 is not None and f(v) else (None, None)
  return parserify(g)

def pmaps(f, p):
  """
  Just like pmap, but assumes the parser returns a list and splays the
  arguments into the function.
  """
  return pmap(lambda xs: f(*xs), p)

def iseq(ix, *ps):
  """
  A variant of seq() that selects a specific subset of parse results. ix can be
  either a sequence or an integer; if ix is an integer, then just that
  subparser's result will be returned.
  """
  return pmap(
    lambda xs: xs[ix] if isinstance(ix, int) else [xs[i] for i in ix],
    seq(*ps))
