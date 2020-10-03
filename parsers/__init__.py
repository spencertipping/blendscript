"""
BlendScript combinatory parsers.
"""

from .cube import parse_commands as cube_p

def parse(source):
  for k in cube_p: print(k)
