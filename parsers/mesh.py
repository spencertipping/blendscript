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

def frontier_add(f, name):
  m = f.mesh(name)
  o = bpy.data.objects.new(name, m)
  bpy.context.scene.collection.objects.link(o)
  return o

expr_globals['frontier'] = frontier
expr_globals['frontier_add'] = frontier_add

meshcmd = alt()

# TODO: make these into first-class objects so we can emit them from looping
# constructs
exprs.append(
  pmap(lambda ps: ''.join(['frontier_add(',
                           ".".join(['frontier(init_tag="o")', *ps[3]]),
                           f', "{ps[1].decode()}")']),
       seq(re(br'M'), p_word, re(br'\['), rep(meshcmd), re(br'\]'))))

edge_face_spec = alt(
  const(['edges=False,faces=False'], re(br'j')),
  const(['edges=True,faces=False'],  re(br'e')),
  const(['edges=False,faces=True'],  re(br'f')),
  const(['edges=True,faces=True'],   re(br'a')))

def tag_spec(kwarg_name):
  return pmap(lambda ps: list(filter(None, ps)),
              seq(maybe(pmap(lambda ps: f'query="{ps[0].decode()}"', re(br'/(\w+)'))),
                  maybe(pmap(lambda ps: f'{kwarg_name}="{ps[0].decode()}"', re(br'>(\w+)')))))

meshcmd.append(
  pmap(lambda xs: f'extrude({xs[3]}, {",".join(["expand=True", *(xs[1] + xs[2])])})',
       seq(re(br'e'), edge_face_spec, tag_spec("tag_as"), expr)),

  pmap(lambda xs: f'extrude({xs[3]}, {",".join(["expand=False", *(xs[1] + xs[2])])})',
       seq(re(br'r'), edge_face_spec, tag_spec("tag_as"), expr)),

  pmap(lambda xs: f'collapse(dv={xs[3]}, {",".join(xs[1] + xs[2])})',
       seq(re(br'c'), edge_face_spec, tag_spec("target"), expr)))
