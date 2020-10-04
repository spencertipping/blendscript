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
    if len(m.groups()):
      return ok(m.groups(), m.end())
    else:
      return ok(m.group(0), m.end())
  return parserify(f)

def const(k, p):
  parser(p)
  def f(s, i):
    (_, i2) = p(s, i)
    return (k, i2)
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

def alt(*ps):
  for p in ps: parser(p)
  def f(s, i):
    for p in ps:
      (v, i2) = p(s, i)
      if i2 is not None:
        return (v, i2)
    return fail(None)
  return parserify(f)

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
    return (v, i2) if i2 is None else (f(v), i2)
  return parserify(g)

def pif(f, p):
  parser(p)
  def g(s, i):
    (v, i2) = p(s, i)
    return (v, i2) if i2 is not None and f(v) else (None, None)
  return parserify(g)
