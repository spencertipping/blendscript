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

from time import time

from ..compatibility import *

from .peg   import *
from .basic import *
from .expr  import *
from .types import *
from .val   import *

from ..blender.blender_objects import *
from ..blender.bmesh           import *
from ..blender.gc              import *
from ..compiler.types          import *
from ..runtime.fn              import *


try:
  import bmesh
  import bpy
  import mathutils as mu

  def apply_bmesh_op(b, op):
    if getattr(op, '__iter__', None):
      b.push()
      for o in op:
        b = apply_bmesh_op(b, o)
      return b.pop()
    else:
      return op(b)

  def make_bmesh(ops):
    """
    Creates a hash-memoized bmesh object from the specified list of operations.
    """
    def generate_bmesh(ops, name):
      t0 = time()
      b  = bmesh_and_selection(bmesh.new())
      b  = apply_bmesh_op(b, ops)
      m  = b.render(name)
      t1 = time()
      if t1 - t0 > 0.1: print(f'{int((t1 - t0) * 1000)}ms to render mesh {name}')
      return gc_tag(m)

    return add_hashed(bpy.data.meshes, tuple(ops), generate_bmesh)

except ModuleNotFoundError:
  blender_not_found()
  def make_bmesh(ops): print(f'make_bmesh({ops})')


# NOTE: the type system won't understand this to be a callable type, but in
# reality these are preloaded method calls, which are Python functions. This
# prevents the parser from trying to invoke mesh ops on each other in certain
# cases.
t_bmesh_op     = atom_type('B/meshop')
t_bmesh_op_arg = atom_type('B/meshoparg')

t_bmesh_tag   = atom_type('B/meshtag')
t_bmesh_query = atom_type('B/meshquery')

type_expr.bind(**{
  'B/meshop':    t_bmesh_op,
  'B/meshoparg': t_bmesh_op_arg,
  'B/meshtag':   t_bmesh_tag,
  'B/meshquery': t_bmesh_query})


# TODO: convert bmesh_query into a normal expr grammar?
bmesh_query = alt()
bmesh_q_atom = whitespaced(alt(const(val.lit(t_bmesh_query, -1), empty),
                               bmesh_query))

bmesh_query.add(
  iseq(1, lit('('), whitespaced(bmesh_query), lit(')')),

  p_lit(t_bmesh_query, const(None,   lit(':'))),   # select all in scope
  p_lit(t_bmesh_query, const([None], lit('::'))),  # really select all
  p_lit(t_bmesh_query, p_int),                     # select by history
  p_lit(t_bmesh_query, const(-1, lit('_'))),       # shorthand for most-recent output
  p_lit(t_bmesh_query, iseq(1, lit('/'), p_varname)),

  p_typed(t_bmesh_query, p_list(re_str(r'[FEV]|\^[xyzXYZ]'), bmesh_q_atom)),
  p_typed(t_bmesh_query, p_list(re_str(r'[-\+\*]'), bmesh_q_atom, bmesh_q_atom)),
  p_typed(t_bmesh_query, p_list(re_str(r'B'),       val_atom,     val_atom)))


make_bmesh_op_arg = val.of_fn([t_string, t_dynamic], t_bmesh_op_arg,
                              lambda arg, val: (arg, val))

make_bmesh_op = val.of_fn([t_string, t_list(t_bmesh_op_arg)], t_bmesh_op,
                          lambda m, kwps: preloaded_method(m, **dict(kwps)))

def p_bmesh_op_arg(name, p):
  return pmap(make_bmesh_op_arg(val.lit(t_string, name)), p)

def p_bmesh_op(name, *p_args):
  return pmap(make_bmesh_op(val.lit(t_string, name)),
              p_list(*filter(None, p_args)))


bmesh_q = p_bmesh_op_arg('q', bmesh_q_atom)

bmesh_tag = p_lit(t_bmesh_tag, iseq(1, lit('>'), p_lword))
bmesh_r   = p_bmesh_op_arg('r', alt(const(val.lit(t_bmesh_tag, None), empty),
                                    bmesh_tag))


mesh_op_scope = scope()
mesh_op_scope.ops.add(**{
  ':':  p_bmesh_op('bind',         bmesh_q, bmesh_r),
  'V':  p_bmesh_op('create_vert',  bmesh_r, p_bmesh_op_arg('v', val_expr)),
  'V0': p_bmesh_op('create_vert',  bmesh_r),

  'c': p_bmesh_op('create_cube',  bmesh_r, p_bmesh_op_arg('dv', val_expr)),
  'b': p_bmesh_op('create_box',   bmesh_r, p_bmesh_op_arg('v1', val_atom),
                                           p_bmesh_op_arg('v2', val_atom)),
  'q': p_bmesh_op('create_quad',  bmesh_r, p_bmesh_op_arg('du', val_atom),
                                           p_bmesh_op_arg('dv', val_atom)),

  '#': p_bmesh_op('delete', bmesh_q),

  'f':  p_bmesh_op('context_fill', bmesh_q, bmesh_r),
  'bl': p_bmesh_op('bridge_loops', bmesh_q, bmesh_r),
  't':  p_bmesh_op('transform',    bmesh_q, p_bmesh_op_arg('m', val_expr)),
  'g':  p_bmesh_op('grab',         bmesh_q, p_bmesh_op_arg('v', val_expr)),

  'e': p_bmesh_op('extrude',   bmesh_q, bmesh_r),
  'd': p_bmesh_op('duplicate', bmesh_q, bmesh_r),

  's': p_bmesh_op(
    'spin',
    bmesh_q, bmesh_r,
    maybe(p_bmesh_op_arg('angle',  val_expr)),
    maybe(p_bmesh_op_arg('steps',  iseq(1, lit('*'), val_expr))),
    maybe(p_bmesh_op_arg('center', iseq(1, lit('@'), val_expr))),
    maybe(p_bmesh_op_arg('axis',   iseq(1, lit('^'), val_expr))),
    maybe(p_bmesh_op_arg('delta',  iseq(1, lit('+'), val_expr))))})


make_bmesh_fn = val.of_fn([t_list(t_bmesh_op)], t_blendmesh, make_bmesh)
val_atom.ops.add(**{
  'm[': list_subscope(val_atom, mesh_op_scope),
  'm<': pflatmap(const(pmap(make_bmesh_fn,
                            val_atom.scoped_subexpression(mesh_op_scope)),
                       empty))})
