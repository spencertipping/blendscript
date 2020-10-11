"""
Basic building blocks for grammars.
"""

from .peg import *

p_word  = pmap(lambda s: s.decode(), re(r'[A-Za-z][A-Za-z0-9_\.]*'))
p_lword = pmap(lambda s: s.decode(), re(r'[a-z][A-Za-z0-9_\.]*'))

p_int    = pmap(int,   re(r'-?\d+'))
p_number = pmap(float, re(r'-?\d*\.\d(?:\d*(?:[eE][-+]?\d+)?)?',
                          r'-?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?'))

p_comment    = re(r'#\s+.*\n?')
p_whitespace = re(r'\s+')
p_ignore     = rep(alt(p_whitespace, p_comment), min=1)
