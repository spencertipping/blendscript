"""
Mesh creation via the frontier generator.

This module adds the M<name>[ops...] expression to the "expr" grammar alt,
making it possible to create meshes and use them as expression values.

"frontier" defines two main operations, extrude and collapse, which
collectively expand into a number of logical elements:

1. Extrude+expand  dv {tagged|all} {->tag|nop} edges? faces?
2. Extrude+replace dv {tagged|all} {->tag|nop} edges? faces?
3. Collapse           {tagged|all} {->tag|nop} edges? faces?
4. Collapse dv        {tagged|all} {->tag|nop} edges? faces?

We can merge (3) and (4) by specifying a zero displacement for two bytes: x0.
This means we really have three functions, each with identical operands:

1. Extrude+expand  dv {tagged|all} {->tag|nop} edges? faces?
2. Extrude+replace dv {tagged|all} {->tag|nop} edges? faces?
3. Collapse dv        {tagged|all} {->tag|nop} edges? faces?

The edge/face flags can also be collapsed into a single byte following the
operator: "j" for jump (neither), "e" for edges only, "f" for faces only, and
"a" for all. As for the operators themselves, "e", "r", and "c" should work for
(1), (2), and (3) respectively.

Now all we have left is to encode the tag arguments, which amount to two words
each of which is optional. If we place these before the displacement vector
expression, we can use arbitrary syntax; let's go with `/` for the query and
`>` for the destination or new tag.
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
  'M:': pmap(lambda ps: f'frontier_add({ps[1]}, "{(ps[0] or b"").decode()}")',
             seq(maybe(p_word), expr))})

edge_face_spec = alt(
  const(['edges=False,faces=False'], re(r'j')),
  const(['edges=True,faces=False'],  re(r'e')),
  const(['edges=False,faces=True'],  re(r'f')),
  const(['edges=True,faces=True'],   re(r'a')))

def tag_spec(kwarg_name):
  return pmap(
    lambda ps: list(filter(None, ps)),
    seq(maybe(pmap(lambda ps: f'query="{ps[0].decode()}"', re(r'/(\w+)'))),
        maybe(pmap(lambda ps: f'{kwarg_name}="{ps[0].decode()}"', re(r'>(\w+)')))))

# TODO: better operator allocation; seems silly to have three toplevel letters
# for these
defexprop(**{
  'e': pmap(lambda xs: f'lambda f: f.extrude({xs[2]}, {",".join(["expand=True", *(xs[0] + xs[1])])})',
            seq(edge_face_spec, tag_spec("tag_as"), expr)),

  'r': pmap(lambda xs: f'lambda f: f.extrude({xs[2]}, {",".join(["expand=False", *(xs[0] + xs[1])])})',
            seq(edge_face_spec, tag_spec("tag_as"), expr)),

  'c': pmap(lambda xs: f'lambda f: f.collapse(dv={xs[2]}, {",".join(xs[0] + xs[1])})',
            seq(edge_face_spec, tag_spec("target"), expr))})
