"""
Parser combinators.

Combinators are pretty simple: they take a string and an offset, and produce
either a success tuple of (result, offset'), or a failure value of None.
"""

import re as regex

def fail(e):  return (e, None)
def ok(v, i): return (v, i)

def none(): lambda source, index: ok(None, index)

def lit(k):
  def f(s, i):
    sub = s[i:i+len(k)]
    return (sub, i + len(k)) if sub == k else fail(None)
  return f

def re(r):
  r = regex.compile(r)
  def f(s, i):
    m = r.match(memoryview(s)[i:])
    if m is None: return fail(None)
    if len(m.groups()):
      return ok(m.groups(), m.end())
    else:
      return ok(m.group(0), m.end())
  return f

def const(k, p):
  def f(s, i):
    (_, i2) = p(s, i)
    return (k, i2)
  return f

def seq(*ps):
  def f(s, i):
    for p in ps:
      (s, i) = p(s, i)
      if i is None: return (s, i)
    return (s, i)
  return f

def alt(*ps):
  def f(s, i):
    for p in ps:
      (s2, i2) = p(s, i)
      if i2 is not None:
        return (s2, i2)
    return fail(None)

def pmap(f, p):
  def g(s, i):
    (v, i2) = p(s, i)
    return (v, i2) if i2 is None else (f(v), i2)
  return g

def pif(f, p):
  def g(s, i):
    (v, i2) = p(s, i)
    return (v, i2) if i2 is not None and f(v) else (None, None)
  return g
