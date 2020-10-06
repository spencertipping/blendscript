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
