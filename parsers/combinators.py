"""
Parser combinators.

Combinators are pretty simple: they take a string and an offset, and produce
either a success tuple of (result, offset'), or a failure value of None.
"""

import re as regex

def parserify(f):
  f.is_parser = True
  return f

def parser(f):
  if not f.is_parser:
    raise str(f) + ' is not a parser'
  return f

def fail(e):  return (e, None)
def ok(v, i): return (v, i)

def none(): return parserify(lambda source, index: ok(None, index))

def lit(k):
  def f(s, i):
    sub = s[i:i+len(k)]
    return (sub, i + len(k)) if sub == k else fail(None)
  return parserify(f)

def re(r):
  r = regex.compile(r)
  def f(s, i):
    m = r.match(memoryview(s)[i:])
    if m is None: return fail(None)
    return ok(m.groups() if len(m.groups()) else m.group(0), i + m.end())
  return parserify(f)

def const(k, p):
  parser(p)
  def f(s, i):
    (_, i2) = p(s, i)
    return (k if i2 is not None else None, i2)
  return parserify(f)

def seq(*ps):
  for p in ps: parser(p)
  def f(s, i):
    vs = []
    for p in ps:
      (v, i) = p(s, i)
      if i is None: return (v, i)
      vs.append(v)
    return (vs, i)
  return parserify(f)

# alt is a class so we can dynamically add new alternatives
class alt:
  def __init__(self, *ps):
    self.ps = []
    parserify(self)
    self.append(*ps)

  def __call__(self, s, i):
    for p in self.ps:
      (v, i2) = p(s, i)
      if i2 is not None:
        return (v, i2)
    return fail(None)

  def append(self, *ps):
    for p in ps: self.ps.append(parser(p))
    return self

def rep(p, min=0, max=None):
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
  parser(p)
  def f(s, i):
    (v, i2) = p(s, i)
    return ok(v, i2) if i2 is not None else ok(None, i)
  return parserify(f)

def pmap(f, p):
  parser(p)
  def g(s, i):
    (v, i2) = p(s, i)
    return (v if i2 is None else f(v), i2)
  return parserify(g)

def pif(f, p):
  parser(p)
  def g(s, i):
    (v, i2) = p(s, i)
    return (v, i2) if i2 is not None and f(v) else (None, None)
  return parserify(g)
