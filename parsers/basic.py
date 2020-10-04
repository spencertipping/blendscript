"""
Basic building blocks for grammars.
"""

import bpy
from .combinators import *

p_word  = re(br'\w+')
p_int   = pmap(int,   re(br'-?\d+'))
p_float = pmap(float, re(br'-?\d*\.\d(?:\d*(?:[eE][+-]?\d+)?)?'
                         + br'|-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?'))

p_object = pmap(lambda s: bpy.data.objects[s], p_word)
p_mesh   = pmap(lambda s: bpy.data.meshes[s],  p_word)

p_comment    = re(br'#.*\n?')
p_whitespace = re(br'\s+')
p_ignore     = rep(alt(p_whitespace, p_comment), min=1)
