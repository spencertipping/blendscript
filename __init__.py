"""
Blender scripting language with a focus on brevity.

The goal is to make it possible to drive Blender using just a script and using
fewer keystrokes than you'd use against the normal UI. This library is oriented
towards CAD, engineering, and precision editing.

BlendScript is largely expression-driven and is parsed using combinatory PEG.

+ parsers/combinators.py : PEG library
+ parsers/basic.py       : shared lexer basics (numbers, comments, etc)
+ parsers/expr.py        : Polish-notation expression language
+ parsers/mesh.py        : mesh expr extensions
"""

# TODO BlendScript examples

from .parsers.expr import compiled_expr
from .parsers.mesh import *

def compile(source):
  """
  Compiles the specified BlendScript source, throwing an error or returning a
  Python function. The resulting function can be invoked on no arguments to
  execute it, or you can provide a single expr_eval_state object to override
  the evaluation state.
  """
  if type(source) == str: source = source.encode()
  f, i = compiled_expr(source, 0)

  if i is None: raise Exception(
    f'blendscript.compile(): failed to parse {source}')

  if i != len(source): raise Exception(
    f'blendscript.compile(): failed to parse beyond {i}: {source[i:]}')

  def compiled(state=expr_eval_state()): return f(state)
  return compiled

def run(source, eval_state=None):
  """
  Runs the given source directly. This is a shorthand for compile(source)().
  """
  f = compile(source)
  if eval_state is not None:
    return f(eval_state)
  else:
    return f()
