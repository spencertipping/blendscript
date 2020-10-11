"""
Operators that apply to bmesh objects. These are accessible using the M[] list
syntax.

BlendScript doesn't support mutability, so the general strategy for
manipulating mutable quantities like bmesh objects is to produce a list of
modification objects. The mesh generator then reduces the list against a new
bmesh object, finalizing it and creating a Blender mesh that can be added to a
scene.

Most bmesh operations apply to a customizable subset of the geometry, which is
sometimes the set of objects returned from the prior operation (particularly
for extrusions), but can also be something else. Because bmesh geometry objects
are scoped strictly to that bmesh, it doesn't make sense for us to bind local
variables to hold onto them; instead what we want is a scoped context within
which we can refer to specific collections.
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


def faces(xs): return [f for f in xs if isinstance(f, bmesh.types.BMFace)]
def edges(xs): return [e for e in xs if isinstance(e, bmesh.types.BMEdge)]
def verts(xs): return [v for v in xs if isinstance(v, bmesh.types.BMVert)]
def loops(xs): return [l for l in xs if isinstance(l, bmesh.types.BMLoop)]

class bmesh_and_selection:
  """
  A bmesh object that keeps track of the vertex, edge, and face selections
  resulting from each operation.
  """
  def __init__(self, bmesh):
    self.bmesh      = bmesh
    self.selections = {}
    self.last       = None
