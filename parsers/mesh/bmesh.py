"""
Operators that apply to bmesh objects. These are accessible using the M[] list
syntax.

BlendScript doesn't support mutability, so the general strategy for
manipulating mutable quantities like bmesh objects is to produce a list of
modification objects. The mesh generator then reduces the list against a new
bmesh object, finalizing it and creating a Blender mesh that can be added to a
scene.
"""

import bmesh
import bpy

from ..peg   import *
from ..basic import *
from ..expr  import *


bmesh_ops  = dsp()
bmesh_expr = alt(bmesh_ops, expr)

def defbmeshop(**ps): bmesh_ops.add(**ps)
defexprop(**{
  'M[': pmap(lambda ps: pylist(ps[0]), seq(rep(bmesh_expr), re(r'\]')))})


# Q: how do we pass selection context between operators? Let's build a
# composite bmesh + stuff object that gets reduced -- and let's have that
# object manage hashing.
