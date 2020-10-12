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

from .peg               import *
from .basic             import *
from .expr              import *
from ..generators.bmesh import bmesh_and_selection, method


bmesh_ops  = dsp()
bmesh_expr = alt(bmesh_ops, expr)

def defbmeshop(**ps): bmesh_ops.add(**ps)
defexprop(**{
  'M[': pmaps(lambda ps: qtuple(ps[0]), seq(rep(bmesh_expr), re(r'\]')))})


"""
Query grammar.

See docs on bmesh_and_selection.select() for the output values these parsers
generate.

Note that this query grammar, like all BlendScript expressions, produces Python
code that evaluates to the desired query object.
"""
bmesh_query = alt()
bmesh_query.add(
  const('None', re(r':')),              # select all
  pmap(str, p_int),                     # select by history
  const('-1', re(r'_')),                # shorthand for most-recent output
  quoted(p_lword),                      # select by tag (named variable)

  pmap(qtuple, seq(quoted(pmap(method('lower'), re(r'[FEV]'))), bmesh_query)),
  pmap(qtuple, seq(quoted(re(r'[-\+\*]')), bmesh_query, bmesh_query)),
  pmap(qtuple, seq(pmap(method('lower'), re(r'B')), expr, expr)))

bmesh_result = maybe(iseq(1, re(r'>'), p_lword))
bmesh_qr     = seq(bmesh_query, bmesh_result)
