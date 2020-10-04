"""
Basic building blocks for grammars.
"""

import bpy

from .combinators import *

p_word  = re(br'\w+')
p_int   = pmap(int,   re(br'-?\d+'))
p_float = pmap(float, re(br'-?\d*\.\d(?:\d*(?:[eE][+-]?\d+)?)?'
                         + br'|-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?'))

p_comment    = re(br'#.*\n?')
p_whitespace = re(br'\s+')
p_ignore     = rep(alt(p_whitespace, p_comment), min=1)

def pmember_of(h, p):
  return pif(lambda x: x is not None,
             pmap(lambda s: h.get(s.decode(), None), p))

p_object    = pmember_of(bpy.data.objects,    p_word)
p_armature  = pmember_of(bpy.data.armatures,  p_word)
p_mesh      = pmember_of(bpy.data.meshes,     p_word)
p_scene     = pmember_of(bpy.data.scenes,     p_word)
p_workspace = pmember_of(bpy.data.workspaces, p_word)
p_world     = pmember_of(bpy.data.worlds,     p_word)
