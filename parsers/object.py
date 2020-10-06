"""
Objects and basic object interactions.

In terms of object creation, I think it's fine if we always start with a single
point and proceed using one of a few operations:

1. Extrude along vector, expanding frontier
2. Extrude along vector, replacing frontier
3. Close current frontier with edge/face/both and jump by vector, starting a
   new frontier

For example, a 1x1x1 cube would work like this:

1. Extrude+expand along X
2. Extrude+expand along Y
3. Extrude+replace along Z
4. Close frontier with face+edges

Not all shapes can be created this way. How would we make a prism? For that
we'd need to extrude parts of the frontier by different distances.

Two options I suppose. One is to move the whole frontier and cons up quads. The
other is to split the frontier and make triangles. We'd need triangles for the
latter case anyway because there's no guarantee that all four points from two
independent extrusions would end up being coplanar.

Frontiers need to encode adjacency, which can either be a list or a loop. Each
point on the frontier can be tagged with one or more labels and selected by tag.

We need different movement options: one for jumps (points), one for edges, and
one for faces+edges. I think it's fine for us to assume that our object will
end up being a shell of some sort -- i.e. no conspicuous holes. So we can
eagerly connect stuff. Make new elements if any point has moved.
"""
