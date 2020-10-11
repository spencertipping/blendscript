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

def method(m): return lambda x, *ys: getattr(x, m)(*ys)

class bmesh_and_selection:
  """
  A bmesh object that keeps track of the vertex, edge, and face selections
  resulting from each operation.

  Each function takes a "q" argument to select its input elements. Functions
  that return results allow you to store those results by specifying "r". In
  some cases the default is to replace the current selection with the result;
  for instance, extrusions. When that's true the default for "r" is "_".
  """
  def __init__(self, bmesh):
    self.bmesh   = bmesh
    self.subsets = {}

  def select(self, q):
    """
    Evaluates the selection query, returning the result. Options are:

    1. None: every object
    2. "x": self.subsets[x]
    3. ['*', q1, q2, ...]: intersection of queries
    4. ['+', q1, q2, ...]: union of queries
    5. ['-', q1, q2]: difference of queries
    6. ['b', v1, v2]: box-select between vertices
    7. ['f', q]: faces from query
    8. ['e', q]: edges from query
    9. ['v', q]: vertices from query
    """
    vs = self.bmesh.verts
    es = self.bmesh.edges
    fs = self.bmesh.faces

    if q is None:            return vs[:] + es[:] + fs[:]
    elif isinstance(q, str): return self.subsets[q]
    elif isinstance(q, list):
      c = q[0]
      if c == '*':
        return reduce(method('intersection'),
                      [set(self.select(s)) for s in q[1:]])
      elif c == '+':
        return reduce(method('union'),
                      [set(self.select(s)) for s in q[1:]])
      elif c == '-':
        q1, q2 = [set(self.select(s)) for s in q[1:]]
        return q1.difference(q2)
      elif c == 'b':
        l, u = q[1].co, q[2].co
        return [v for v in vs if l[0] <= v[0] <= u[0] and
                                 l[1] <= v[1] <= u[1] and
                                 l[2] <= v[2] <= u[2]]
      elif c == 'f': return faces(self.select(q[1]))
      elif c == 'e': return edges(self.select(q[1]))
      elif c == 'v': return verts(self.select(q[1]))

    raise Exception(f'unsupported bmesh query: {q}')

  def store(self, r, xs):
    """
    Stores the specified result set into a subset, ignoring if r == None.
    """
    if r is not None: self.subsets[r] = xs
    return self

  def context_fill(self, q=None, r=None):
    ret = bmesh.ops.contextual_create(self.bmesh, geom=self.select(q))
    self.store(r, ret['edges'] + ret['faces'])
    return self

  def bridge_loops(self, q, r):
    ret = bmesh.ops.bridge_loops(self.bmesh, edges=edges(self.select(q)))
    self.store(r, ret['edges'] + ret['faces'])
    return self

  def transform(self, q, m):
    bmesh.ops.transform(self.bmesh, matrix=m, verts=verts(self.select(q)))
    return self

  def extrude_faces(self, q, r='_'):
    ret = bmesh.ops.extrude_discrete_faces(
      self.bmesh, faces=faces(self.select(q)))
    self.store(r, ret['faces'])
    return self

  def extrude_edges(self, q, r='_'):
    ret = bmesh.ops.extrude_edge_only(self.bmesh, edges=edges(self.select(q)))
    self.store(r, ret['geom'])
    return self

  def extrude_verts(self, q, r='_'):
    ret = bmesh.ops.extrude_vert_indiv(self.bmesh, verts=verts(self.select(q)))
    self.store(r, ret['edges'] + ret['verts'])
    return self

  def duplicate(self, q, r):
    ret = bmesh.ops.duplicate(self.bmesh, geom=self.select(q))
    self.store(r, ret['geom'])
    return self

  def spin(self, q, r, angle, steps=45,
           cent=Vector((0, 0, 0)),
           axis=Vector((0, 0, 1)),
           delta=Vector((0, 0, 0))):
    ret = bmesh.ops.spin(self.bmesh, geom=self.select(q),
                         cent=cent, axis=axis, dvec=delta,
                         angle=angle, steps=steps)
    self.store(r, ret['geom_last'])
    return self
