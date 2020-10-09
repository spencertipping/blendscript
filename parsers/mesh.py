"""
Mesh creation via the frontier generator.

There are three basic mesh frontier operations:

1. Expand wavefront
2. Extrude wavefront
3. Collapse wavefront

Each has the following options:

1. dv: the displacement vector (required)
2. query: a tag to specify input points
3. tag_as: a tag for output
4. edges?: True to emit edges along the extrusion
5. faces?: True to emit faces along the extrusion

TODO at some point: arbitrary point->point transforms, not just dv
"""

import bpy

from ..generators.mesh import frontier
from .combinators      import *
from .expr             import *

def frontier_add(fns, name):
  f = frontier(init_tag="o")
  for fn in fns:
    f = fn(f)
  return f.mesh(name)

defexprglobals(frontier=frontier, frontier_add=frontier_add)

defexprop(**{
  'M:': pmap(lambda ps: f'frontier_add({ps[1]}, "{ps[0]}")',
             seq(maybe(p_lword), expr))})

edge_face_spec = alt(
  const(['edges=False,faces=False'], re(r'j')),
  const(['edges=True,faces=False'],  re(r'e')),
  const(['edges=False,faces=True'],  re(r'f')),
  const(['edges=True,faces=True'],   re(r'a')))

def tag_spec(kwarg_name):
  return pmap(
    lambda ps: list(filter(None, ps)),
    seq(maybe(pmap(lambda w: f'query="{w.decode()}"', re(r'/(\w+)'))),
        maybe(pmap(lambda w: f'{kwarg_name}="{w.decode()}"', re(r'>(\w+)')))))

defexprop(**{
  'M*': pmap(
    lambda xs: f'FN(lambda _m: _m.expand({xs[2]}, {",".join([*(xs[0] + xs[1])])}))',
    seq(edge_face_spec, tag_spec("tag_as"), expr)),

  'M':  pmap(
    lambda xs: f'FN(lambda _m: _m.extrude({xs[2]}, {",".join([*(xs[0] + xs[1])])}))',
    seq(edge_face_spec, tag_spec("tag_as"), expr)),

  'M/': pmap(
    lambda xs: f'FN(lambda _m: _m.collapse(dv={xs[2]}, {",".join(xs[0] + xs[1])}))',
    seq(edge_face_spec, tag_spec("target"), expr))})
