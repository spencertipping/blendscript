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

from time      import time
from mathutils import Vector

from .peg   import *
from .basic import *
from .expr  import *
from .types import type_expr
from .val   import *

from ..blender.bmesh  import bmesh_and_selection
from ..compiler.types import *
from ..runtime.fn     import method, preloaded_method


# NOTE: the type system won't understand this to be a callable type, but in
# reality these are preloaded method calls, which are functions. This prevents
# the parser from trying to invoke mesh ops on each other in certain cases.
t_bmesh_op     = atom_type('B/mesh/op')
t_bmesh_op_arg = atom_type('B/mesh/op/arg')

t_bmesh_tag   = atom_type('B/mesh/tag')
t_bmesh_query = atom_type('B/mesh/query')

# TODO: get rid of some slashes
type_expr.bind(**{
  'B/mesh/op':     t_bmesh_op,
  'B/mesh/op/arg': t_bmesh_op,
  'B/mesh/tag':    t_bmesh_tag,
  'B/mesh/query':  t_bmesh_query})


def make_bmesh(ops):
  name = '_%016x' % hash(tuple(ops))
  if name in bpy.data.meshes:
    return bpy.data.meshes[name]

  t0 = time()
  b  = bmesh_and_selection(bmesh.new())
  b.create_vert(r="_", v=Vector((0, 0, 0)))
  for o in ops:
    b = o(b)
  m = b.render(name)
  t1 = time()
  if t1 - t0 > 0.1: print(f'{int((t1 - t0) * 1000)}ms to render mesh {name}')
  return m


val_atom.bind(**{
  'M<<': val.of_fn(t_list(t_bmesh_op), t_blendmesh, make_bmesh)})


bmesh_tag   = p_lit(t_bmesh_tag, iseq(1, lit('>'), p_lword))
bmesh_query = alt()
bmesh_query.add(
  p_lit(t_bmesh_query, const(None, lit(':'))),  # select all
  p_lit(t_bmesh_query, p_int),                  # select by history
  p_lit(t_bmesh_query, const(-1, lit('_'))),    # shorthand for most-recent output
  p_lit(t_bmesh_query, p_lword),                # select by tag (named variable)

  p_typed(t_bmesh_query, p_list(re_str(r'[fev]'),   bmesh_query)),
  p_typed(t_bmesh_query, p_list(re_str(r'[-\+\*]'), bmesh_query, bmesh_query)),
  p_typed(t_bmesh_query, p_list(re_str(r'b'),       val_atom,    val_atom)))


make_bmesh_op = val.of_fn(
  t_string, t_fn(t_list(t_bmesh_op_arg), t_bmesh_op),
  fn(lambda m: fn(lambda kwpairs: preloaded_method(m, **kwpairs))))


make_bmesh_op_arg = val.of_fn(
  t_string, t_fn(t_dynamic, t_bmesh_op_arg),
  fn(lambda arg: fn(lambda val: (arg, val))))

def p_bmesh_op_arg(name, p):
  return pmap(make_bmesh_op_arg(val.lit(t_string, name), p))


bmesh_q = p_bmesh_op_arg('q', bmesh_query)
bmesh_r = p_bmesh_op_arg('r', alt(bmesh_tag, const(val.lit(t_bmesh_tag, None), empty)))

def p_bmesh_op(name, *p_args):
  return pmap(make_bmesh_op(name), p_list(*filter(None, p_args)))


# TODO: use pflatmap to create an m[] list variant that binds the mesh-op
# subscope. Just like let-bindings, but with a constant set of bindings rather
# than a parser output.

mesh_op_scope = scope().ops.add(**{
  ':': p_bmesh_op('bind',         bmesh_q, bmesh_r),
  'f': p_bmesh_op('context_fill', bmesh_q, bmesh_r),
  'b': p_bmesh_op('bridge_loops', bmesh_q, bmesh_r),
  't': p_bmesh_op('transform',    bmesh_q, p_bmesh_op_arg('m', val_atom)),

  'e': p_bmesh_op('extrude',     bmesh_q, bmesh_r),
  'v': p_bmesh_op('create_vert', bmesh_r, p_bmesh_op_arg('v', val_atom)),
  'd': p_bmesh_op('duplicate',   bmesh_q, bmesh_r),

  's': p_bmesh_op(
    'spin',
    bmesh_q, bmesh_r,
    p_bmesh_op_arg('angle', val_atom),
    maybe(p_bmesh_op_arg('steps',  iseq(1, lit('*'), val_atom))),
    maybe(p_bmesh_op_arg('center', iseq(1, lit('@'), val_atom))),
    maybe(p_bmesh_op_arg('axis',   iseq(1, lit('^'), val_atom))),
    maybe(p_bmesh_op_arg('delta',  iseq(1, lit('+'), val_atom))))})
