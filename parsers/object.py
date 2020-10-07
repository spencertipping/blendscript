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

For example, a 1x1x1 cube would work like this:

1. Extrude+expand edge along X [frontier has two points]
2. Extrude+expand face along Y [frontier has four points]
3. Extrude+replace faces along Z [frontier has four points]
4. Collapse with edges+face [frontier has one point]

Frontiers need to encode adjacency, which can either be a list or a loop. Each
point on the frontier can be tagged with one or more labels and selected by
tag.

We need different movement options: one for jumps (points), one for edges, and
one for faces+edges. I think it's fine for us to assume that our object will
end up being a shell of some sort -- i.e. no conspicuous holes. So we can
eagerly connect stuff. Make new elements if any point has moved.

Loops need to be preserved across certain types of expand-extrusions. The case
above is simple enough, but what happens if the profile is more complex? Can we
create two disjoint loops? Suppose we select even/odd points and extrude
orthogonally. What would we expect to happen?
"""

"""
Proposed extrusion rules.

Map each point to its new position, which may be the same as its original
position. If any point has moved, create new edges/faces/etc from it. The only
thing we need to do is make sure we don't duplicate new elements.

I think it's fine to say that points extrude to edges, edges extrude to faces.
I don't think we need to model solids as extrusions of faces.

Loops are inferred by traversing the edge graph. We don't rely on edge
directed-ness or ordering for loops because extrusions don't preserve direction
in the right way. For example, "extrude along X; extrude along Y" for a cube
face would produce parallel edges in each direction; there's a diamond but no
loop if you assume a DAG.
"""

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

    self.tags = {'init': [0]}
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
    if query is None:
      return xrange(len(self.front))
    else:
      return self.tags[query]

  def extrude(self, dv, query=None, tag_as=None,
              expand=False, edges=True, faces=False):
    """
    Extrudes the wavefront (or a subset) along a vector, connecting the new
    frontier points either with edges or with faces. New points will inherit
    tags from the original points as well as being assigned any new tag you
    specify.

    If you expand the frontier, new vertices will be linked to the vertices
    they came from.
    """

    # front_edits[fi] = vi0, where self.vertices[vi0] is the original location
    # for the front point now at fi. We use this for fast "did-it-change"
    # queries.
    front_edits = {}
    fis         = self.select(query)

    if tag_as is not None and tag_as not in self.tags:
      self.tags[tag_as] = []

    if expand:
      # Extrude each point by calculating its new location, adding it to the
      # mesh, and logging a new link between the original and the new one.
      for fi in fis:
        vi = self.front[fi]
        self.vertices.append(self.vertices[vi] + dv)
        self.front.append(len(self.vertices) - 1)
        new_fi = len(self.front) - 1
        front_edits[new_fi] = vi
        self.links.append((fi, new_fi))
        if tag_as is not None: self.tags[tag_as].append(new_fi)

        # Anyone who linked to the original should also link to the new point.
        for (f1, f2) in self.links:
          if f1 == fi: self.links.append((new_fi, f2))
          if f2 == fi: self.links.append((f1, new_fi))

    else:
      # Replace self.front[] entries with new extruded vertices. No new links
      # are created.
      for fi in fis:
        vi = self.front[fi]
        front_edits[fi] = vi
        self.vertices.append(self.vertices[vi] + dv)
        self.front[fi] = len(self.vertices) - 1
        if tag_as is not None: self.tags[tag_as].append(fi)

    # Edges are created for (1) any new links; and (2) any existing links whose
    # endpoints have changed. In practice both of these cases are handled by
    # consulting front_edits: new vertices are represented as edits of existing
    # ones.
    if edges:
      for (f1, f2) in self.links:
        # Skip over any links whose endpoints haven't changed (or aren't new).
        if f1 not in front_edits and f2 not in front_edits: continue

        # We can refer directly into self.front[] like this because if the edge
        # is new, it means we produced it by expanding the wavefront -- and
        # that means we have both the old and new points available. Non-new
        # edges always correspond to links within the updated wavefront, which
        # is also covered by what is now self.front[].
        self.edges.append((self.front[f1], self.front[f2]))

    # Faces are a lot like edges, except that we also need to consider the
    # original point locations.
    if faces:
      # TODO
