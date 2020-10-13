"""
BMesh geometry generator.

This is just a bmesh object with a sidecar of named geometry selections.
"""

import bmesh
import bpy

from functools import reduce
from mathutils import Vector

from ..objects.function import method


def faces(xs): return [f for f in xs if isinstance(f, bmesh.types.BMFace)]
def edges(xs): return [e for e in xs if isinstance(e, bmesh.types.BMEdge)]
def verts(xs): return [v for v in xs if isinstance(v, bmesh.types.BMVert)]
def loops(xs): return [l for l in xs if isinstance(l, bmesh.types.BMLoop)]


class bmesh_and_selection:
  """
  A bmesh object that keeps track of the vertex, edge, and face selections
  resulting from each operation.

  Each function takes a "q" argument to select its input elements. Functions
  that return results allow you to store those results by specifying "r". In
  some cases the default is to replace the current selection with the result;
  for instance, extrusions. When that's true the default for "r" is "_".

  Methods that accept "q" and "r" always position them before other arguments.
  """
  def __init__(self, bmesh):
    self.bmesh   = bmesh
    self.subsets = {}
    self.history = []

  def select(self, q): return list(self.select_(q))
  def select_(self, q):
    """
    Evaluates the selection query, returning the result. Options are:

    + None: every object
    + "x": self.subsets[x]
    + int(n): nth history element; -1 is most recent, 0 is oldest
    + ['*', q1, q2, ...]: intersection of queries
    + ['+', q1, q2, ...]: union of queries
    + ['-', q1, q2]: difference of queries
    + ['b', v1, v2]: box-select between vertices
    + ['f', q]: faces from query
    + ['e', q]: edges from query
    + ['v', q]: vertices from query
    """
    vs = self.bmesh.verts
    es = self.bmesh.edges
    fs = self.bmesh.faces

    if q is None:            return vs[:] + es[:] + fs[:]
    elif isinstance(q, str): return self.subsets[q]
    elif isinstance(q, int): return self.history[q]
    elif isinstance(q, tuple):
      c = q[0]
      if c == '*':
        return reduce(method('intersection'),
                      (set(self.select_(s)) for s in q[1:]))
      elif c == '+':
        return reduce(method('union'),
                      (set(self.select_(s)) for s in q[1:]))
      elif c == '-':
        q1, q2 = (set(self.select_(s)) for s in q[1:])
        return q1.difference(q2)
      elif c == 'b':
        l, u = q[1].co, q[2].co
        return [v for v in vs if l[0] <= v[0] <= u[0] and
                                 l[1] <= v[1] <= u[1] and
                                 l[2] <= v[2] <= u[2]]
      elif c == 'f': return faces(self.select_(q[1]))
      elif c == 'e': return edges(self.select_(q[1]))
      elif c == 'v': return verts(self.select_(q[1]))

    raise Exception(f'unsupported bmesh query: {q}')

  def store(self, r, xs):
    """
    Stores the specified result set into a subset, ignoring if r == None. Adds
    the result to the history list in either case.
    """
    if r is not None: self.subsets[r] = xs
    self.history.append(xs)
    return self

  def bind(self, q, r):
    """
    Evaluates a query now and stores the result under a new name.
    """
    self.store(r, self.select(q))
    return self

  def render(self, name):
    """
    Creates a new mesh datablock and renders this bmesh object into it. Doing
    this will render this bmesh wrapper unusable for further interaction.
    """
    m = bpy.data.meshes.new(name)
    self.bmesh.to_mesh(m)
    self.bmesh.free()
    self.bmesh = None
    m.update()
    return m

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

  def extrude(self, q, r='_'):
    """
    Multipurpose extrude. Delegates to individual bmesh methods to extrude
    vertices, edges, and faces, to the extent that the query produces them, and
    aggregates the results as though it had been a single operation. Note that
    this can produce ambiguous results in certain cases.
    """
    q = self.select(q)
    qf = faces(q)
    qe = edges(q)
    qv = verts(q)

    rg = []
    if len(qf):
      rg += bmesh.ops.extrude_discrete_faces(self.bmesh, faces=qf)['faces']

    if len(qe):
      rg += bmesh.ops.extrude_edge_only(self.bmesh, edges=qe)['geom']

    if len(qv):
      rv = bmesh.ops.extrude_vert_indiv(self.bmesh, verts=qv)
      rg += rv['edges'] + rv['verts']

    self.store(r, rg)
    return self

  def create_vert(self, r, v):
    ret = bmesh.ops.create_vert(self.bmesh, co=v)
    self.store(r, ret['vert'])
    return self

  def duplicate(self, q, r):
    ret = bmesh.ops.duplicate(self.bmesh, geom=self.select(q))
    self.store(r, ret['geom'])
    return self

  def spin(self, q, r, angle, steps=45,
           center=Vector((0, 0, 0)),
           axis=Vector((0, 0, 1)),
           delta=Vector((0, 0, 0))):
    ret = bmesh.ops.spin(self.bmesh, geom=self.select(q),
                         cent=center, axis=axis, dvec=delta,
                         angle=angle, steps=steps, use_merge=True)
    self.store(r, ret['geom_last'])
    return self
