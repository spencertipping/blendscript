"""
Basic building blocks for grammars.
"""

from .combinators import *

p_word  = pmap(lambda s: s.decode(), re(r'[A-Za-z][A-Za-z0-9_\.]*'))
p_lword = pmap(lambda s: s.decode(), re(r'[a-z][A-Za-z0-9_\.]*'))

p_int   = pmap(int,   re(r'-?\d+'))
p_float = pmap(float, re(r'-?\d*\.\d(?:\d*(?:[eE][-+]?\d+)?)?',
                         r'-?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?'))

p_comment    = re(r'#.*\n?')
p_whitespace = re(r'\s+')
p_ignore     = rep(alt(p_whitespace, p_comment), min=1)


def p_member_of(h, p):
  return pmap(lambda s: h[s], pif(lambda s: s in h, p))
