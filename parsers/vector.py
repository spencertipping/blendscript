"""
Vectors have two main uses in BlendScript: specifying the location of an
object, and specifying displacements or relative movements, e.g. as part of a
mesh extrusion frontier. Specifying a location might require arbitrarily much
computation, including from variables or points within other meshes.

Relative movements are more interesting because we might want to use a stack of
transformation matrices and we might want to modify those matrices while
specifying movements. Although vectors are parsed individually, that parse
action also impacts a dynamically-scoped matrix state. The matrix state is
itself a variable, which means that the parse output from a vector is a
_function_, not a plain vector value.
"""

from .basic       import *
from .combinators import *

from mathutils import Vector
from functools import reduce
