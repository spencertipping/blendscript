"""
Basic building blocks for grammars.
"""

from .combinators import *

p_word  = re(br'\w+')
p_int   = pmap(int,   re(br'-?\d+'))
p_float = pmap(float, re(br'-?\d*\.\d(?:\d*(?:[eE][+-]?\d+)?)?'
                         + br'|-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?'))

p_comment    = re(br'#.*\n?')
p_whitespace = re(br'\s+')
p_ignore     = rep(alt(p_whitespace, p_comment), min=1)


def p_member_of(h, p):
  return pif(lambda x: x is not None,
             pmap(lambda s: h.get(s.decode(), None), p))
