"""
Objects and basic object interactions.

In terms of object creation, I think it's fine if we always start with a single
point and proceed inductively, with each step one of a few operations:

1. Extrude along vector, expanding frontier and connecting with edges
2. Extrude along vector, expanding frontier and connecting with edges+faces
3. Extrude along vector, replacing frontier and connecting with edges
4. Extrude along vector, replacing frontier and connecting with edges+faces
5. Collapse frontier, connecting with edges
6. Collapse frontier, connecting with edges+faces

For example, a 1x1x1 cube works like this:

> f = frontier()
> m = f.extrude(Vector((1, 0, 0)), expand=True,  edges=True)
>      .extrude(Vector((0, 1, 0)), expand=True,  edges=True, faces=True)
>      .extrude(Vector((0, 0, 1)), expand=False, edges=True, faces=True)
>      .collapse(edges=True, faces=True)
>      .mesh('cube')
"""

import bpy

from mathutils import Vector

class frontier:
  """
  A frontier-oriented mesh generator.
  """
  def __init__(self, init=Vector((0, 0, 0))):
    self.vertices = [init]
    self.edges    = []
    self.faces    = []

    self.front = [0]
    """
    A list of vertex indices representing the current extrusion wavefront.
    Unqualified extrusions will operate on this full set. self.front[i]
    contains an index used to access self.vertices[].
    """

    self.links = []
    """
    Links between points within the wavefront. These are pairs of indexes into
    self.front[].
    """

    self.tags = {'e': [0]}
    """
    The mapping of tags used to select subsets of the wavefront to operate on.
    Values are lists of indexes into self.front[].
    """

  def select(self, query):
    """
    Generates a list of indices into self.front[] corresponding to points
    selected by the specified query.

    For now, queries are just tag names or `None` to select everything.
    """
    if query is None: return range(len(self.front))
    else:             return self.tags[query]

  def mesh(self, name, debug=False):
    """
    Create and return a new Blender mesh from the current geometry state.

    All vertex normals are set to +Z to meet Blender's mesh validation
    requirements. This should probably be improved at some point in the future.
    """
    if debug:
      print(f"frontier.mesh({name})")
      for i in range(len(self.vertices)): print(f"  v[{i}] = {self.vertices[i]}")
      for (v1, v2) in self.edges: print(f"  edge: {v1} <-> {v2}")
      for f in self.faces: print(f"  face: {f}")

    m = bpy.data.meshes.new(name)
    m.from_pydata(self.vertices, self.edges, self.faces)
    for v in m.vertices: v.normal = Vector((0, 0, 1))

    if m.validate(verbose=True): raise Exception(
      f'frontier.mesh({name}): failed to validate (see console trace)')

    m.update()
    return m

  def extrude(self, dv, query=None, tag_as=None,
              expand=False, edges=True, faces=False):
    """
    Extrudes the wavefront (or a subset) along a vector, connecting the new
    frontier points either with edges or with faces. New points be assigned any
    new tag you specify.

    If you expand the frontier, new vertices will be linked to the vertices
    they came from.
    """
    # front_edits[fi] = vi0, where self.vertices[vi0] is the original location
    # for the front point now at fi. We use this for fast "did-it-change"
    # queries.
    front_edits = {}

    if tag_as is not None and tag_as not in self.tags:
      self.tags[tag_as] = []

    if expand:
      # Extrude each point by calculating its new location, adding it to the
      # mesh, and logging a new link between the original and the new one.
      front_moves = {}
      for fi in self.select(query):
        vi = self.front[fi]
        self.front.append(self.vertex(self.vertices[vi] + dv))
        new_fi = len(self.front) - 1
        front_edits[new_fi] = vi
        front_moves[fi] = new_fi
        self.links.append((fi, new_fi))
        if tag_as is not None: self.tags[tag_as].append(new_fi)

      # If f1 and/or f2 refer to points that have moved, add a new edge to the
      # destination.
      for (f1, f2) in self.links:
        if f1 in front_moves or f2 in front_moves:
          self.links.append((front_moves.get(f1, f1), front_moves.get(f2, f2)))

    else:
      # Replace self.front[] entries with new extruded vertices. No new links
      # are created.
      for fi in self.select(query):
        vi = self.front[fi]
        self.front[fi] = self.vertex(self.vertices[vi] + dv)
        front_edits[fi] = vi
        if tag_as is not None: self.tags[tag_as].append(fi)

    if edges: self.create_edges(front_edits)
    if faces: self.create_faces(front_edits)
    return self

  def collapse(self, dv=None, query=None, target=None,
               edges=True, faces=False):
    """
    Collapses multiple points down to a single point within the wavefront,
    optionally emitting one or more faces in the process. You can specify a
    target query to select which point will be the result; if specified, the
    target must identify one of the points being collapsed. If unspecified, one
    of the points being collapsed is chosen arbitrarily (but
    deterministically).
    """
    front_edits = {}
    fis         = self.select(query)

    # Any point in the target will do so long as it's also in the query set.
    tfi = None
    for t in self.select(target):
      if t in fis:
        tfi = t
        break

    if tfi is None: raise Exception(
      "frontier.collapse(): target query must specify a point within "
      "the wavefront being collapsed")

    # Displace the target if any displacement was requested. Otherwise we're
    # just collapsing the selected points to wherever the target is now.
    if dv is not None:
      front_edits[tfi] = self.front[tfi]
      self.front[tfi] = self.vertex(self.vertices[self.front[tfi]] + dv)

    # Create edit records for all points that aren't the target. Since we're
    # collapsing down to a smaller set, we hang onto the originals for
    # reference and zero out all but one of the ones in the original query.
    for fi in fis:
      if fi != tfi:
        front_edits[fi] = self.front[fi]
        self.front[fi] = self.front[tfi]

    if edges: self.create_edges(front_edits)
    if faces: self.create_faces(front_edits)

    # Now for the hard part: we need to remove newly-duplicated points from
    # self.front[]. This will result in the indexes changing, which means we
    # also need to rewrite self.links[] and self.tags[].
    new_front = []
    front_map = {}
    for fi in range(len(self.front)):
      # "edit" == "remove" in this context, so exclude from the new front. The
      # only exception is the target point, which may have been displaced but
      # will always be included.
      if fi == tfi or fi not in front_edits:
        new_front.append(self.front[fi])
        front_map[fi] = len(new_front) - 1

    self.front = new_front
    self.links = [(front_map[f1], front_map[f2])
                  for (f1, f2) in self.links
                  if f1 in front_map and f2 in front_map
                      and front_map[f1] != front_map[f2]]
    self.tags  = dict([(t, [front_map[fi]
                            for fi in self.tags[t]
                            if fi in front_map])
                       for t in self.tags])
    return self

  def vertex(self, v):
    """
    Adds a vertex to the geometry, returning its vi. If the vertex already
    exists, you'll get the existing vi for it.
    """
    for i in range(len(self.vertices)):
      if self.vertices[i] == v: return i
    self.vertices.append(v.freeze())
    return len(self.vertices) - 1

  def edge(self, vi1, vi2):
    """
    Adds an edge to the geometry, provided that the edge won't violate any
    constraints (for instance, it can't already exist and its endpoints can't
    be the same).
    """
    if vi1 == vi2: return self
    for (v1, v2) in self.edges:
      if v1 == vi1 and v2 == vi2 or v1 == vi2 and v2 == vi1:
        return self

    self.edges.append((vi1, vi2))
    return self

  def face(self, *vs):
    """
    Adds a face to the geometry, provided that the face won't violate any
    constraints. Duplicate vertices are removed.
    """
    uniq_vs = []
    for v in vs:
      if v not in uniq_vs: uniq_vs.append(v)
    if len(uniq_vs) > 2: self.faces.append(tuple(uniq_vs))
    return self

  def create_edges(self, front_edits):
    """
    Creates all edges resulting from a series of edits to the wavefront.

    Edges are created for (1) any new links; and (2) any existing links whose
    endpoints have changed. In practice both of these cases are handled by
    consulting front_edits: new vertices are represented as edits of existing
    ones.
    """
    for (f1, f2) in self.links:
      if f1 in front_edits or f2 in front_edits:
        # We can refer directly into self.front[] like this because if the
        # edge is new, it means we produced it by expanding the wavefront --
        # and that means we have both the old and new points available.
        # Non-new edges always correspond to links within the updated
        # wavefront, which is also covered by what is now self.front[].
        self.edge(self.front[f1], self.front[f2])

    # Moving a point creates an edge even if there is no link between the old
    # and new locations.
    for fi in front_edits:
      self.edge(front_edits[fi], self.front[fi])

  def create_faces(self, front_edits):
    """
    Creates all faces resulting from a series of edits to the wavefront.

    Faces are a lot like edges, except that we also need to incorporate
    original point locations. Faces arise from links one or both of whose
    endpoints have moved, and there are two possibilities:

    1. One endpoint moved: create a triangle
    2. Both endpoints moved: create a quad
    """
    for (f1, f2) in self.links:
      v1  = self.front[f1]
      v2  = self.front[f2]
      v10 = front_edits.get(f1, v1)
      v20 = front_edits.get(f2, v2)

      if v10 != v1 and v20 != v2: self.face(v10, v1, v2, v20)
      elif v10 != v1:             self.face(v10, v1, v2)
      elif v20 != v2:             self.face     (v1, v2, v20)
