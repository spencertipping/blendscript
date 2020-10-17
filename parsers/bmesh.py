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

from time import time

from .peg            import *
from .basic          import *
from .expr           import *
from ..runtime.fn    import method
from ..blender.bmesh import bmesh_and_selection


# TODO: port this to the new API

bmesh_expr = expr_grammar()

bmesh_expr.last_resort.add(val_expr)

bmesh_expr.ops.add(**{
  'M[': pmap(val.list, iseq(0, rep(bmesh_expr), whitespaced(lit(']'))))})

def make_bmesh(name, ops):
  t0 = time()
  b = bmesh_and_selection(bmesh.new())
  b.create_vert(r="_", v=Vector((0, 0, 0)))
  for o in ops:
    b = o(b)
  m = b.render(name)
  t1 = time()
  if t1 - t0 > 0.1: print(f'{t1 - t0} second(s) to render mesh {name}')
  return m

defexprglobals(_make_bmesh=make_bmesh)
defexprop(
  **{'M:': pmaps(lambda n, l: f'_make_bmesh("{n}", {l})', seq(p_lword, expr))})


bmesh_query = alt()
bmesh_query.add(
  const('None', lit(':')),              # select all
  pmap(str, p_int),                     # select by history
  const('-1', lit('_')),                # shorthand for most-recent output
  quoted(p_lword),                      # select by tag (named variable)

  pmap(qtuple, seq(quoted(pmap(method('lower'), re(r'[FEV]'))), bmesh_query)),
  pmap(qtuple, seq(quoted(re(r'[-\+\*]')), bmesh_query, bmesh_query)),
  pmap(qtuple, seq(pmap(method('lower'), lit('B')), expr, expr)))

bmesh_result = pmap(quoted, iseq(1, lit('>'), p_lword))

bmesh_q  = kwarg('q', bmesh_query)
bmesh_r  = kwarg('r', alt(bmesh_result, const('None', empty)))
bmesh_qr = pmap(qargs, seq(bmesh_q, bmesh_r))


defbmeshop(**{
  '=': pmap(qmethod_call('bind'), bmesh_qr),
  'f': pmap(qmethod_call('context_fill'), bmesh_qr),
  'b': pmap(qmethod_call('bridge_loops'), bmesh_qr),
  't': pmaps(qmethod_call('transform'), seq(bmesh_q, kwarg('m', expr))),

  'e': pmap(qmethod_call('extrude'), bmesh_qr),
  'v': pmaps(qmethod_call('create_vert'), seq(bmesh_r, kwarg('v', expr))),
  'd': pmap(qmethod_call('duplicate'), bmesh_qr),
  's': pmaps(qmethod_call('spin'),
             seq(bmesh_q, bmesh_r,
                 kwarg('angle', pmap(lambda x: f'({x}*_tau)', expr)),
                 maybe(kwarg('steps',  iseq(1, lit('*'), expr))),
                 maybe(kwarg('center', iseq(1, lit('@'), expr))),
                 maybe(kwarg('axis',   iseq(1, lit('^'), expr))),
                 maybe(kwarg('delta',  iseq(1, lit('+'), expr)))))})
