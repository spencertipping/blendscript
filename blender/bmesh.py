"""
BMesh geometry generator.

This is just a bmesh object with a sidecar of named geometry selections.
"""


from math      import tau
from functools import reduce

from ..compatibility import *
from ..runtime.fn    import method
from .units          import *

try:
  import bmesh
  import bpy
  import mathutils as mu


  def faces_(xs): return [f for f in xs if isinstance(f, bmesh.types.BMFace)]
  def edges_(xs): return [e for e in xs if isinstance(e, bmesh.types.BMEdge)]
  def verts_(xs): return [v for v in xs if isinstance(v, bmesh.types.BMVert)]
  def loops_(xs): return [l for l in xs if isinstance(l, bmesh.types.BMLoop)]

  def uniq(xs):  return list(set(xs))
  def faces(xs): return faces_(xs)
  def edges(xs): return uniq(edges_(xs) + [e for f in faces(xs) for e in f.edges])
  def verts(xs): return uniq(verts_(xs) + [v for e in edges(xs) for v in e.verts])


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
        elif c == 'B':
          l, u = q[1].co, q[2].co
          return [v for v in vs if l[0] <= v.co[0] <= u[0] and
                                   l[1] <= v.co[1] <= u[1] and
                                   l[2] <= v.co[2] <= u[2]]
        elif c == 'F': return faces(self.select_(q[1]))
        elif c == 'E': return edges(self.select_(q[1]))
        elif c == 'V': return verts(self.select_(q[1]))

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

      # Scale the entire geometry to match desired units
      bmesh.ops.transform(self.bmesh,
                          matrix=mu.Matrix.Scale(unit_scale(1), 3),
                          verts=self.bmesh.verts)

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

    def grab(self, q, v):
      self.transform(q, mu.Matrix.Translation(mu.Vector(v)))
      return self

    def extrude(self, q, r):
      """
      Multipurpose extrude. Delegates to individual bmesh methods to extrude
      vertices, edges, and faces, to the extent that the query produces them, and
      aggregates the results as though it had been a single operation. Note that
      this can produce ambiguous results in certain cases.
      """
      q = self.select(q)
      qf = faces_(q)
      qe = edges_(q)
      qv = verts_(q)

      rg = []
      if len(qf): rg += bmesh.ops.extrude_discrete_faces(self.bmesh, faces=qf)['faces']
      if len(qe): rg += bmesh.ops.extrude_edge_only(self.bmesh, edges=qe)['geom']
      if len(qv):
        rv = bmesh.ops.extrude_vert_indiv(self.bmesh, verts=qv)
        rg += rv['edges'] + rv['verts']

      self.store(r, rg)
      return self

    def delete(self, q):
      q = self.select(q)
      bmesh.ops.delete(self.bmesh, geom=verts(q), context='VERTS')
      bmesh.ops.delete(self.bmesh, geom=edges(q), context='EDGES')
      bmesh.ops.delete(self.bmesh, geom=faces(q), context='FACES_KEEP_BOUNDARY')
      return self

    def create_cube(self, r, dv=mu.Vector((1, 1, 1))):
      ret = bmesh.ops.create_cube(self.bmesh, size=1, matrix=mu.Matrix.Diagonal(dv))
      self.store(r, ret['verts'])
      return self

    def create_box(self, r, v1=mu.Vector((0, 0, 0)), v2=mu.Vector((1, 1, 1))):
      scale_matrix = mu.Matrix.Diagonal(v2 - v1)
      ret = bmesh.ops.create_cube(self.bmesh, size=1, matrix=scale_matrix)
      bmesh.ops.translate(self.bmesh,
                          verts=ret['verts'],
                          vec=v1 + scale_matrix @ mu.Vector((0.5, 0.5, 0.5)))

      self.store(r, ret['verts'])
      return self

    def create_quad(self, r, du=mu.Vector((1, 0, 0)), dv=mu.Vector((0, 1, 0))):
      v0 = bmesh.ops.create_vert(self.bmesh, co=mu.Vector((0, 0, 0)))['vert'][0]
      v1 = bmesh.ops.extrude_vert_indiv(self.bmesh, verts=[v0])
      v2 = bmesh.ops.extrude_vert_indiv(self.bmesh, verts=v1['verts'])
      v3 = bmesh.ops.extrude_vert_indiv(self.bmesh, verts=v2['verts'])

      vs = [v0]
      for v in [v1, v2, v3]: vs += v['verts']

      bmesh.ops.translate(self.bmesh, vec=du, verts=[vs[1], vs[2]])
      bmesh.ops.translate(self.bmesh, vec=dv, verts=[vs[2], vs[3]])
      ret = bmesh.ops.contextual_create(self.bmesh, geom=[vs[0], vs[3]])

      rv = vs + ret['edges'] + ret['faces']
      for v in [v1, v2, v3]: rv += v['edges']
      self.store(r, rv)
      return self

    def create_vert(self, r, v=mu.Vector((0, 0, 0))):
      ret = bmesh.ops.create_vert(self.bmesh, co=v)
      self.store(r, ret['vert'])
      return self

    def duplicate(self, q, r):
      ret = bmesh.ops.duplicate(self.bmesh, geom=self.select(q))
      self.store(r, ret['geom'])
      return self

    def spin(self, q, r, angle=tau, steps=45,
            center=mu.Vector((0, 0, 0)),
            axis=mu.Vector((0, 0, 1)),
            delta=mu.Vector((0, 0, 0))):
      ret = bmesh.ops.spin(self.bmesh, geom=self.select(q),
                          cent=center, axis=axis, dvec=delta,
                          angle=angle, steps=steps, use_merge=True)
      self.store(r, ret['geom_last'])
      return self


except ModuleNotFoundError:
  blender_not_found()
